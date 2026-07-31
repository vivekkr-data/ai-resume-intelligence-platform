# 10-Day Interview Preparation Plan

## Day 1 — Run and understand every screen

- Run Streamlit and FastAPI locally.
- Analyze the sample resume three times with different JDs.
- Explain every displayed score without reading notes.

## Day 2 — NLP fundamentals

Study embeddings, cosine similarity, chunking, TF-IDF, semantic similarity and why normalized embeddings make dot product equal cosine similarity.

## Day 3 — Code walkthrough

Be able to explain:

- `resume_parser.py`
- `matcher.py`
- `analyzer.py`
- `job_recommender.py`

Draw the pipeline on paper from memory.

## Day 4 — PostgreSQL and SQLAlchemy

- Run Docker Compose.
- Inspect all three tables.
- Practice joins, group by, indexes, foreign keys, JSON columns and migrations.
- Explain why SQLite is local fallback and PostgreSQL is used in deployment.

## Day 5 — FastAPI

- Open Swagger.
- Call analyze, recommend, jobs and history endpoints.
- Explain request validation, dependency injection, status codes and admin authentication.

## Day 6 — Deployment

- Deploy to Streamlit Community Cloud.
- Connect Neon PostgreSQL through secrets.
- Verify persistence after reload.
- Keep a backup Render deployment plan.

## Day 7 — Testing and failure cases

Test:

- empty file
- unsupported format
- scanned PDF
- very short JD
- unavailable transformer model
- database connection failure

Explain graceful fallback and safe error handling.

## Day 8 — Responsible AI

Prepare answers about bias, privacy, false positives, human review, protected attributes, explainability and data retention.

## Day 9 — Mock interview

Give the complete 5-minute demo twice. Answer all questions in `VIVA_GUIDE.md` without reading.

## Day 10 — Final polish

- Recheck live URL and GitHub README.
- Warm the model cache.
- Confirm no secrets are committed.
- Keep screenshots or a short screen recording as backup.
- Sleep properly and avoid last-minute major code changes.
