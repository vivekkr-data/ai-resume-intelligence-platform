"""ATS checks and actionable resume improvement guidance."""
from __future__ import annotations

import re
from typing import Any

ACTION_VERBS = {
    "built",
    "created",
    "developed",
    "designed",
    "implemented",
    "improved",
    "optimized",
    "deployed",
    "automated",
    "analyzed",
    "led",
    "managed",
    "reduced",
    "increased",
    "achieved",
    "trained",
    "integrated",
    "delivered",
    "evaluated",
    "collaborated",
}


def ats_checklist(profile: dict[str, Any]) -> list[dict[str, Any]]:
    word_count = profile.get("word_count", 0)
    checks = [
        {
            "check": "Contact information",
            "passed": bool(profile.get("emails") and profile.get("phones")),
            "detail": "Professional email and phone number are clearly detectable.",
        },
        {
            "check": "Professional summary",
            "passed": bool(profile.get("has_summary")),
            "detail": "A focused 2–3 line summary helps recruiters understand role fit quickly.",
        },
        {
            "check": "Skills section",
            "passed": bool(profile.get("has_skills_section") and len(profile.get("skills", [])) >= 5),
            "detail": "A dedicated skills section with relevant, truthful technologies is ATS-friendly.",
        },
        {
            "check": "Projects or experience",
            "passed": bool(profile.get("has_projects") or profile.get("has_experience")),
            "detail": "Evidence of applied work is more valuable than a skills list alone.",
        },
        {
            "check": "Education section",
            "passed": bool(profile.get("has_education")),
            "detail": "Education should use a standard heading and include degree, institute and dates.",
        },
        {
            "check": "Achievement metrics",
            "passed": profile.get("metric_count", 0) >= 2,
            "detail": "Quantified outcomes such as accuracy, latency or records processed improve credibility.",
        },
        {
            "check": "Readable length",
            "passed": 250 <= word_count <= 1100,
            "detail": "For students and early-career candidates, one concise page is usually strongest.",
        },
        {
            "check": "Portfolio links",
            "passed": bool(profile.get("links")),
            "detail": "LinkedIn, GitHub or a portfolio lets recruiters verify projects.",
        },
    ]
    return checks


def resume_quality_score(profile: dict[str, Any]) -> float:
    checks = ats_checklist(profile)
    checklist_score = 75 * sum(item["passed"] for item in checks) / len(checks)
    text = profile.get("raw_text", "").lower()
    action_count = sum(bool(re.search(rf"\b{verb}\b", text)) for verb in ACTION_VERBS)
    action_score = min(15, action_count * 1.5)
    skill_score = min(10, len(profile.get("skills", [])) * 0.65)
    return round(min(100.0, checklist_score + action_score + skill_score), 2)


def build_strengths(
    resume_profile: dict[str, Any],
    matched_skills: list[str],
    semantic_score: float,
) -> list[str]:
    strengths: list[str] = []
    if semantic_score >= 70:
        strengths.append("The resume demonstrates strong meaning-level alignment with the role responsibilities.")
    elif semantic_score >= 55:
        strengths.append("The resume contains relevant experience, but the role connection can be stated more directly.")
    if len(matched_skills) >= 5:
        strengths.append(f"Strong technical overlap across {len(matched_skills)} detected job skills.")
    elif matched_skills:
        strengths.append(f"Relevant foundation detected in {', '.join(matched_skills[:4])}.")
    if resume_profile.get("has_projects"):
        strengths.append("Projects provide practical evidence of applied skills.")
    if resume_profile.get("metric_count", 0) >= 2:
        strengths.append("Quantified achievements make the resume more credible and outcome-oriented.")
    if resume_profile.get("link_types", {}).get("github"):
        strengths.append("GitHub is available for technical project verification.")
    return strengths[:5]


def build_learning_roadmap(missing_skills: list[str]) -> list[dict[str, str]]:
    roadmap: list[dict[str, str]] = []
    for index, skill in enumerate(missing_skills[:6]):
        priority = "High" if index < 3 else "Medium"
        roadmap.append(
            {
                "skill": skill,
                "priority": priority,
                "action": (
                    f"Learn the fundamentals of {skill}, build one small demonstrable project, "
                    "and add it only after you can explain the implementation and trade-offs."
                ),
            }
        )
    return roadmap


def build_suggestions(
    resume_profile: dict[str, Any],
    job_profile: dict[str, Any],
    missing_skills: list[str],
) -> list[str]:
    suggestions: list[str] = []
    text = resume_profile.get("raw_text", "")

    if missing_skills:
        suggestions.append(
            "Prioritize these genuine skill gaps: "
            + ", ".join(missing_skills[:8])
            + ". Add a skill only after completing a project, course or practical exercise that you can defend in an interview."
        )
    if not resume_profile.get("has_summary"):
        suggestions.append(
            f"Add a 2–3 line professional summary tailored to the {job_profile.get('title', 'target role')} role and your strongest evidence."
        )
    if not resume_profile.get("has_projects") and resume_profile.get("experience_years", 0) < 1:
        suggestions.append(
            "Add a Projects section with problem statement, your contribution, technology stack and measurable result."
        )
    if len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text)) < 3:
        suggestions.append(
            "Quantify project outcomes, for example model accuracy, response-time improvement, dataset size or users served."
        )
    if resume_profile.get("bullet_count", 0) < 4:
        suggestions.append(
            "Replace long paragraphs with concise bullets that begin with action verbs such as Built, Developed, Evaluated or Deployed."
        )
    if resume_profile.get("word_count", 0) < 250:
        suggestions.append("The resume is too short; add relevant projects, coursework, achievements and technical responsibilities.")
    elif resume_profile.get("word_count", 0) > 1100:
        suggestions.append("Reduce low-value detail and keep an early-career resume close to one focused page.")
    if not resume_profile.get("emails") or not resume_profile.get("phones"):
        suggestions.append("Place a professional email and active phone number in the top header.")
    if not resume_profile.get("links"):
        suggestions.append("Add LinkedIn and GitHub links so recruiters can verify your profile and projects.")
    suggestions.append(
        "Tailor the summary and project bullets for each job description, while keeping every claim truthful and interview-defensible."
    )
    suggestions.append(
        "Use standard headings and a simple single-column structure; avoid text boxes, graphics and complex tables that can confuse ATS parsers."
    )
    return suggestions[:10]
