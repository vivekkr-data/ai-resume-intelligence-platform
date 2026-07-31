"""Heuristic resume and job-description profile extraction."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from backend.services.skills import extract_skills, group_skills

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_CANDIDATE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{8,}\d)(?!\w)")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s|]+", re.I)
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.I)
METRIC_RE = re.compile(r"\b(?:\d+(?:\.\d+)?%|\d{2,}[+]?|₹\s?\d+|\$\s?\d+)\b")
DATE_RANGE_RE = re.compile(
    r"(?P<start_month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?"
    r"\s*(?P<start_year>20\d{2}|19\d{2})\s*(?:-|–|—|to)\s*"
    r"(?:(?P<end_month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?"
    r"\s*(?P<end_year>20\d{2}|19\d{2})|(?P<present>present|current|now))",
    re.I,
)

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "profile", "objective", "about me", "professional summary"),
    "skills": ("skills", "technical skills", "core competencies", "technologies"),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "internships",
        "internship",
    ),
    "projects": ("projects", "academic projects", "personal projects", "key projects"),
    "education": ("education", "academic background", "qualifications"),
    "certifications": ("certifications", "certificates", "courses", "training"),
    "achievements": ("achievements", "awards", "accomplishments"),
}

DEGREE_PATTERNS = [
    "b.tech",
    "btech",
    "b.e",
    "bachelor",
    "m.tech",
    "mtech",
    "m.e",
    "master",
    "b.sc",
    "bsc",
    "m.sc",
    "msc",
    "phd",
    "diploma",
    "computer science",
    "information technology",
    "artificial intelligence",
]

OPTIONAL_MARKERS = ("preferred", "nice to have", "good to have", "bonus", "plus")


def normalize_text(text: str) -> str:
    text = text.replace("\u2022", "•").replace("\uf0b7", "•")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _detect_heading(line: str) -> str | None:
    cleaned = re.sub(r"[^a-z ]", "", line.lower()).strip()
    for section, aliases in SECTION_ALIASES.items():
        if cleaned in aliases:
            return section
    return None


def extract_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = _detect_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items() if lines}


def _guess_name(text: str) -> str | None:
    blocked = {alias for aliases in SECTION_ALIASES.values() for alias in aliases}
    for line in text.splitlines()[:8]:
        candidate = re.sub(r"\s+", " ", line).strip(" |,-")
        words = candidate.split()
        if (
            2 <= len(words) <= 5
            and candidate.lower() not in blocked
            and not EMAIL_RE.search(candidate)
            and not PHONE_CANDIDATE_RE.search(candidate)
            and not URL_RE.search(candidate)
            and not any(char.isdigit() for char in candidate)
            and len(candidate) <= 60
        ):
            return candidate.title() if candidate.isupper() else candidate
    return None


def _extract_phones(text: str) -> list[str]:
    phones: list[str] = []
    for match in PHONE_CANDIDATE_RE.finditer(text):
        candidate = re.sub(r"\s+", " ", match.group(0)).strip(" .,-")
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 13 and candidate not in phones:
            phones.append(candidate)
    return sorted(phones)[:3]


def _month_number(value: str | None, default: int) -> int:
    if not value:
        return default
    names = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    return names.get(value[:3].lower(), default)


def _date_based_experience_years(experience_text: str) -> float:
    intervals: list[tuple[int, int]] = []
    now = datetime.now()
    for match in DATE_RANGE_RE.finditer(experience_text):
        start_year = int(match.group("start_year"))
        start_month = _month_number(match.group("start_month"), 1)
        if match.group("present"):
            end_year, end_month = now.year, now.month
        else:
            end_year = int(match.group("end_year"))
            end_month = _month_number(match.group("end_month"), 12)
        start_index = start_year * 12 + start_month
        end_index = end_year * 12 + end_month
        if 0 <= end_index - start_index <= 240:
            intervals.append((start_index, end_index))

    if not intervals:
        return 0.0
    intervals.sort()
    merged: list[list[int]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    months = sum(end - start + 1 for start, end in merged)
    return round(months / 12, 1)


def _extract_experience_years(text: str, experience_text: str = "") -> float:
    explicit = [float(value) for value in YEARS_RE.findall(text)]
    explicit_value = max(explicit, default=0.0)
    date_value = _date_based_experience_years(experience_text) if experience_text else 0.0
    return max(explicit_value, date_value)


def _education_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if any(pattern in lower for pattern in DEGREE_PATTERNS):
            cleaned = line.strip()
            if cleaned and cleaned not in lines:
                lines.append(cleaned)
    return lines[:8]


def _link_types(links: list[str]) -> dict[str, list[str]]:
    typed = {"linkedin": [], "github": [], "portfolio": []}
    for link in links:
        lower = link.lower()
        if "linkedin.com" in lower:
            typed["linkedin"].append(link)
        elif "github.com" in lower or "gitlab.com" in lower:
            typed["github"].append(link)
        else:
            typed["portfolio"].append(link)
    return typed


def parse_resume(text: str) -> dict[str, Any]:
    text = normalize_text(text)
    sections = extract_sections(text)
    emails = sorted(set(EMAIL_RE.findall(text)))
    phones = _extract_phones(text)
    links = sorted(set(URL_RE.findall(text)))
    skills = extract_skills(text)
    experience_text = sections.get("experience", "")
    experience_source = "\n".join(
        part for part in [sections.get("summary", ""), experience_text] if part
    )

    return {
        "name": _guess_name(text),
        "emails": emails,
        "phones": phones,
        "links": links[:8],
        "link_types": _link_types(links[:8]),
        "skills": skills,
        "skill_groups": group_skills(skills),
        "experience_years": _extract_experience_years(experience_source, experience_text),
        "education": _education_lines(sections.get("education", text)),
        "sections_found": sorted(section for section in sections if section != "header"),
        "word_count": len(text.split()),
        "bullet_count": len(re.findall(r"(?:^|\n)\s*(?:[•\-*]|\d+[.)])\s+", text)),
        "metric_count": len(METRIC_RE.findall(text)),
        "has_summary": "summary" in sections,
        "has_projects": "projects" in sections,
        "has_experience": "experience" in sections,
        "has_education": "education" in sections,
        "has_skills_section": "skills" in sections,
        "has_certifications": "certifications" in sections,
        "raw_text": text,
    }


def parse_job_description(text: str, title: str = "Target Role") -> dict[str, Any]:
    clean = normalize_text(text)
    all_skills = set(extract_skills(clean))
    preferred: set[str] = set()
    for line in clean.splitlines():
        if any(marker in line.lower() for marker in OPTIONAL_MARKERS):
            preferred.update(extract_skills(line))
    required = all_skills - preferred
    if not required and all_skills:
        required = set(all_skills)
        preferred.clear()

    education_requirements = [
        degree for degree in DEGREE_PATTERNS if degree in clean.lower()
    ]
    return {
        "title": title.strip() or "Target Role",
        "skills": sorted(all_skills, key=str.lower),
        "required_skills": sorted(required, key=str.lower),
        "preferred_skills": sorted(preferred, key=str.lower),
        "skill_groups": group_skills(sorted(all_skills, key=str.lower)),
        "experience_years": _extract_experience_years(clean),
        "education_requirements": sorted(set(education_requirements)),
        "word_count": len(clean.split()),
        "raw_text": clean,
    }
