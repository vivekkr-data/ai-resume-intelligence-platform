"""Database-backed job recommendation with CSV fallback."""
from __future__ import annotations

import csv
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import JobPosting
from backend.services.matcher import rank_texts
from backend.services.skills import extract_skills


def _catalog_from_csv() -> list[dict[str, Any]]:
    if not settings.jobs_csv.exists():
        raise FileNotFoundError(f"Job catalog not found: {settings.jobs_csv}")
    with settings.jobs_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        {
            "id": None,
            "title": row.get("title", "Untitled role"),
            "company": row.get("company", "Demo company"),
            "location": row.get("location", "Not specified"),
            "description": row.get("description", ""),
            "skills": [item.strip() for item in row.get("skills", "").split(";") if item.strip()],
            "apply_url": row.get("apply_url", ""),
            "source": "Bundled demo catalog",
        }
        for row in rows
    ]


def _catalog_from_db(db: Session) -> list[dict[str, Any]]:
    jobs = list(
        db.scalars(
            select(JobPosting)
            .where(JobPosting.is_active.is_(True))
            .order_by(JobPosting.created_at.desc())
        )
    )
    return [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "skills": job.skills or [],
            "apply_url": job.apply_url or "",
            "source": job.source,
        }
        for job in jobs
    ]


def recommend_jobs(
    resume_text: str,
    top_k: int = 5,
    db: Session | None = None,
) -> tuple[list[dict[str, Any]], str]:
    catalog = _catalog_from_db(db) if db is not None else _catalog_from_csv()
    if not catalog:
        catalog = _catalog_from_csv()

    documents = [
        f"{job['title']}. {job['description']} Required skills: {', '.join(job['skills'])}"
        for job in catalog
    ]
    semantic_scores, model_used = rank_texts(resume_text, documents)
    resume_skills = set(extract_skills(resume_text))

    recommendations: list[dict[str, Any]] = []
    for job, semantic in zip(catalog, semantic_scores):
        required = set(job["skills"])
        skill_score = 100 * len(resume_skills & required) / len(required) if required else 70.0
        final_score = round(0.75 * semantic + 0.25 * skill_score, 2)
        matched = sorted(resume_skills & required, key=str.lower)
        missing = sorted(required - resume_skills, key=str.lower)
        recommendations.append(
            {
                **job,
                "semantic_score": round(semantic, 2),
                "skill_score": round(skill_score, 2),
                "recommendation_score": final_score,
                "matched_skills": matched,
                "missing_skills": missing,
                "fit_reason": (
                    f"Meaning-level fit {semantic:.0f}% with {len(matched)} matched catalog skills."
                ),
            }
        )

    recommendations.sort(key=lambda item: item["recommendation_score"], reverse=True)
    return recommendations[: max(1, min(top_k, 20))], model_used
