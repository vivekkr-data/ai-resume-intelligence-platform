"""Generate recruiter-friendly Markdown and HTML reports."""
from __future__ import annotations

import html
from typing import Any


def markdown_report(result: dict[str, Any]) -> str:
    scores = result["scores"]
    profile = result["resume_profile"]
    matched = ", ".join(result.get("matched_skills", [])) or "None detected"
    missing = ", ".join(result.get("missing_skills", [])) or "None"
    strengths = "\n".join(f"- {item}" for item in result.get("strengths", [])) or "- No major strengths detected"
    suggestions = "\n".join(
        f"{index}. {item}" for index, item in enumerate(result.get("suggestions", []), 1)
    )
    checks = "\n".join(
        f"- {'PASS' if item['passed'] else 'IMPROVE'} — **{item['check']}**: {item['detail']}"
        for item in result.get("ats_checks", [])
    )
    evidence = "\n".join(
        f"- **{item['similarity']:.1f}%** requirement: {item['requirement']}  \n  Resume evidence: {item['resume_evidence']}"
        for item in result.get("evidence", [])
    ) or "- No evidence available"

    return f"""# AI Resume Intelligence Report

## Executive summary

- **Candidate:** {profile.get('name') or 'Not detected'}
- **Target role:** {result.get('job_title', 'Target Role')}
- **Verdict:** {result.get('verdict', '')}
- **Overall fit:** {scores['overall']:.2f}%
- **Model:** {result.get('model_used', '')}
- **Processing time:** {result.get('processing_ms', 0)} ms

## Score breakdown

| Component | Score |
|---|---:|
| Semantic alignment | {scores['semantic']:.2f}% |
| Required skill coverage | {scores['skills']:.2f}% |
| Experience alignment | {scores['experience']:.2f}% |
| ATS/resume quality | {scores['resume_quality']:.2f}% |
| **Overall** | **{scores['overall']:.2f}%** |

## Candidate strengths

{strengths}

## Skill comparison

- **Matched required skills:** {matched}
- **Missing required skills:** {missing}

## ATS checklist

{checks}

## Explainable semantic evidence

{evidence}

## Improvement plan

{suggestions}

## Responsible-use note

This score is decision support, not an automatic hiring decision. The system does not intentionally rank protected personal attributes, does not store raw resume text, and requires human review.
"""


def html_report(result: dict[str, Any]) -> str:
    scores = result["scores"]
    profile = result["resume_profile"]

    def pills(items: list[str], class_name: str) -> str:
        if not items:
            return "<span class='muted'>None</span>"
        return "".join(
            f"<span class='pill {class_name}'>{html.escape(item)}</span>" for item in items
        )

    checks = "".join(
        f"<li><strong>{'✓' if item['passed'] else '○'} {html.escape(item['check'])}</strong> — {html.escape(item['detail'])}</li>"
        for item in result.get("ats_checks", [])
    )
    suggestions = "".join(
        f"<li>{html.escape(item)}</li>" for item in result.get("suggestions", [])
    )
    evidence = "".join(
        "<div class='evidence'>"
        f"<strong>{item['similarity']:.1f}% alignment</strong>"
        f"<p><b>Requirement:</b> {html.escape(item['requirement'])}</p>"
        f"<p><b>Resume evidence:</b> {html.escape(item['resume_evidence'])}</p>"
        "</div>"
        for item in result.get("evidence", [])
    )

    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>Resume Analysis Report</title>
<style>
body{{font-family:Inter,Arial,sans-serif;background:#f5f7fb;color:#172033;margin:0;padding:32px}}
.page{{max-width:980px;margin:auto;background:white;padding:36px;border-radius:18px;box-shadow:0 8px 30px #dbe2ef}}
h1{{margin:0}} .muted{{color:#64748b}} .hero{{border-bottom:3px solid #4f46e5;padding-bottom:20px}}
.grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:24px 0}}
.card{{background:#f8fafc;border:1px solid #e2e8f0;padding:14px;border-radius:12px;text-align:center}}
.score{{font-size:24px;font-weight:700}} .pill{{display:inline-block;padding:5px 10px;margin:4px;border-radius:99px;font-size:13px}}
.good{{background:#dcfce7;color:#166534}} .gap{{background:#fee2e2;color:#991b1b}}
.evidence{{border-left:4px solid #6366f1;background:#f8fafc;padding:12px 16px;margin:10px 0;border-radius:8px}}
li{{margin:8px 0}} @media(max-width:700px){{.grid{{grid-template-columns:1fr 1fr}}body{{padding:10px}}.page{{padding:18px}}}}
</style></head><body><main class='page'>
<section class='hero'><h1>AI Resume Intelligence Report</h1>
<p class='muted'>{html.escape(profile.get('name') or 'Candidate')} → {html.escape(result.get('job_title', 'Target Role'))}</p>
<h2>{html.escape(result.get('verdict', ''))}</h2></section>
<section class='grid'>
<div class='card'><div class='score'>{scores['overall']:.1f}%</div>Overall</div>
<div class='card'><div class='score'>{scores['semantic']:.1f}%</div>Semantic</div>
<div class='card'><div class='score'>{scores['skills']:.1f}%</div>Skills</div>
<div class='card'><div class='score'>{scores['experience']:.1f}%</div>Experience</div>
<div class='card'><div class='score'>{scores['resume_quality']:.1f}%</div>ATS quality</div>
</section>
<h2>Matched skills</h2>{pills(result.get('matched_skills', []), 'good')}
<h2>Missing skills</h2>{pills(result.get('missing_skills', []), 'gap')}
<h2>ATS checklist</h2><ul>{checks}</ul>
<h2>Semantic evidence</h2>{evidence}
<h2>Improvement plan</h2><ol>{suggestions}</ol>
<hr><p class='muted'>Model: {html.escape(result.get('model_used', ''))} · Processing: {result.get('processing_ms', 0)} ms · Human review required.</p>
</main></body></html>"""
