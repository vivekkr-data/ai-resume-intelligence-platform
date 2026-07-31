# 5-Minute Recruiter Demo Script

## Before the call

- Open the deployed app once so the embedding model is cached.
- Keep the sample resume and demo JD ready.
- Open GitHub, live app and FastAPI Swagger in separate tabs.
- Verify the sidebar shows PostgreSQL connected.
- Keep the admin dashboard PIN private and ready.

## 0:00–0:30 — Problem statement

> Recruiters receive many resumes, and basic ATS tools often rely heavily on exact keywords. I built an explainable NLP platform that compares the meaning of resume evidence with job requirements, then combines semantic alignment with skills, experience and ATS quality.

## 0:30–1:10 — Upload and score

1. Upload `sample_data/sample_resume.txt`.
2. Click **Load recruiter demo job description**.
3. Run explainable analysis.
4. Show overall, semantic, skills, experience and ATS scores.

Say:

> Semantic similarity has the highest weight, so repeating keywords alone is not enough. Required and preferred skills are handled separately.

## 1:10–2:00 — Explainability

Scroll to **Explainable semantic evidence**.

> For each requirement chunk, the system retrieves the closest resume evidence and shows the similarity. This helps users understand why the score was produced instead of treating the model as a black box.

Mention the TF-IDF fallback:

> If the transformer model is unavailable, the application degrades gracefully and reports a TF-IDF fallback rather than crashing.

## 2:00–2:40 — ATS and skill roadmap

Show matched skills, missing skills, ATS checks and learning roadmap.

> The system never tells a candidate to fake a skill. It recommends learning and building a demonstrable project before adding the skill.

## 2:40–3:20 — PostgreSQL and privacy

Show My Analyses and the database status.

> The public app uses PostgreSQL for persistence. Normal history is isolated by browser session. Raw resume text is never stored, PII is masked by default and the JD is persisted only as a hash.

## 3:20–4:00 — Job recommendation

Upload the same resume in Job Matches.

> Jobs are stored in the database and ranked using semantic fit plus skill coverage. The bundled roles are demo data, which avoids unreliable scraping and makes the architecture easy to replace with an approved jobs API.

## 4:00–4:35 — Backend engineering

Open Swagger.

> I exposed the pipeline through a versioned FastAPI API, used Pydantic validation and SQLAlchemy dependency injection, protected admin routes, added Alembic migrations and included Docker Compose with PostgreSQL.

## 4:35–5:00 — Responsible AI and next step

> This is decision support, not an automated rejection system. A production version needs fairness evaluation, user authentication, OCR for scanned resumes, a larger skill ontology and labelled recruiter feedback for model calibration.

## Strong closing line

> The project combines NLP, backend APIs, relational database design, deployment, testing and responsible-AI thinking in one end-to-end system.
