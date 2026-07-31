"""End-to-end resume analysis, explainability and safe persistence."""
from __future__ import annotations

import hashlib
import time
from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import AnalysisRecord
from backend.services.matcher import semantic_similarity_detailed
from backend.services.resume_parser import parse_job_description, parse_resume
from backend.services.suggestions import (
    ats_checklist,
    build_learning_roadmap,
    build_strengths,
    build_suggestions,
    resume_quality_score,
)


def _skill_score(
    resume_skills: set[str], required_skills: set[str], preferred_skills: set[str]
) -> float:
    if not required_skills and not preferred_skills:
        return 70.0
    required_coverage = (
        len(resume_skills & required_skills) / len(required_skills)
        if required_skills
        else 1.0
    )
    preferred_coverage = (
        len(resume_skills & preferred_skills) / len(preferred_skills)
        if preferred_skills
        else required_coverage
    )
    weight_required = 0.85 if preferred_skills else 1.0
    score = 100 * (
        weight_required * required_coverage
        + (1 - weight_required) * preferred_coverage
    )
    return round(score, 2)


def _experience_score(candidate_years: float, required_years: float) -> float:
    if required_years <= 0:
        return 90.0 if candidate_years <= 0 else 100.0
    if candidate_years >= required_years:
        return 100.0
    return round(max(20.0, candidate_years / required_years * 100), 2)


def _verdict(score: float) -> str:
    if score >= 82:
        return "Excellent fit — ready for recruiter review"
    if score >= 68:
        return "Strong fit — minor tailoring recommended"
    if score >= 52:
        return "Moderate fit — improve evidence and skill alignment"
    return "Developing fit — close key gaps before applying"


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    visible = local[:2] if len(local) >= 2 else local[:1]
    return f"{visible}{'*' * max(2, len(local) - len(visible))}@{domain}"


def _safe_persisted_result(result: dict[str, Any]) -> dict[str, Any]:
    persisted = deepcopy(result)
    if not settings.store_pii:
        profile = persisted.get("resume_profile", {})
        profile["emails"] = [_mask_email(value) for value in profile.get("emails", [])]
        profile["phones"] = ["***" + value[-4:] for value in profile.get("phones", []) if len(value) >= 4]
        profile["links"] = []
        profile["link_types"] = {"linkedin": [], "github": [], "portfolio": []}
    return persisted


def analyze_resume(
    *,
    resume_text: str,
    job_description: str,
    filename: str,
    job_title: str = "Target Role",
    session_id: str = "local-demo",
    db: Session | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    resume_profile = parse_resume(resume_text)
    job_profile = parse_job_description(job_description, job_title)

    resume_skills = set(resume_profile["skills"])
    required_skills = set(job_profile["required_skills"])
    preferred_skills = set(job_profile["preferred_skills"])
    matched_skills = sorted(resume_skills & required_skills, key=str.lower)
    missing_skills = sorted(required_skills - resume_skills, key=str.lower)
    preferred_skill_gaps = sorted(preferred_skills - resume_skills, key=str.lower)

    semantic_score, model_used, evidence = semantic_similarity_detailed(
        resume_text, job_description
    )
    skill_score = _skill_score(resume_skills, required_skills, preferred_skills)
    experience_score = _experience_score(
        resume_profile["experience_years"], job_profile["experience_years"]
    )
    quality_score = resume_quality_score(resume_profile)

    overall = round(
        0.60 * semantic_score
        + 0.25 * skill_score
        + 0.10 * experience_score
        + 0.05 * quality_score,
        2,
    )
    checks = ats_checklist(resume_profile)
    suggestions = build_suggestions(resume_profile, job_profile, missing_skills)
    strengths = build_strengths(resume_profile, matched_skills, semantic_score)
    roadmap = build_learning_roadmap(missing_skills)

    public_resume_profile = {
        key: value for key, value in resume_profile.items() if key != "raw_text"
    }
    public_job_profile = {
        key: value for key, value in job_profile.items() if key != "raw_text"
    }
    processing_ms = int((time.perf_counter() - started) * 1000)

    result: dict[str, Any] = {
        "analysis_id": None,
        "filename": filename,
        "job_title": job_profile["title"],
        "verdict": _verdict(overall),
        "scores": {
            "overall": overall,
            "semantic": semantic_score,
            "skills": skill_score,
            "experience": experience_score,
            "resume_quality": quality_score,
        },
        "resume_profile": public_resume_profile,
        "job_profile": public_job_profile,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "preferred_skill_gaps": preferred_skill_gaps,
        "strengths": strengths,
        "suggestions": suggestions,
        "ats_checks": checks,
        "learning_roadmap": roadmap,
        "evidence": evidence,
        "model_used": model_used,
        "processing_ms": processing_ms,
        "scoring_formula": {
            "semantic": 0.60,
            "skills": 0.25,
            "experience": 0.10,
            "resume_quality": 0.05,
        },
        "privacy": {
            "raw_resume_stored": False,
            "pii_stored": settings.store_pii,
            "history_scope": "browser session unless admin access is used",
        },
    }

    if db is not None:
        persisted = _safe_persisted_result(result)
        email = next(iter(resume_profile.get("emails", [])), None)
        record = AnalysisRecord(
            session_id=(session_id or "anonymous")[:64],
            filename=filename[:255],
            candidate_name=resume_profile.get("name") if settings.store_pii else None,
            candidate_email=email if settings.store_pii else _mask_email(email),
            job_title=job_profile["title"][:255],
            job_description_hash=hashlib.sha256(job_description.encode("utf-8")).hexdigest(),
            overall_score=overall,
            semantic_score=semantic_score,
            skill_score=skill_score,
            experience_score=experience_score,
            quality_score=quality_score,
            model_used=model_used[:255],
            processing_ms=processing_ms,
            matched_skill_count=len(matched_skills),
            missing_skill_count=len(missing_skills),
            resume_word_count=resume_profile["word_count"],
            result=persisted,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        result["analysis_id"] = record.id
        persisted["analysis_id"] = record.id
        record.result = persisted
        db.commit()

    return result
