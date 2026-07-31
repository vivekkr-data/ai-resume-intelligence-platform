# Viva and Interview Guide

## 1. Explain the project in 30 seconds.

I built an explainable NLP-based resume intelligence platform. It extracts candidate information from PDF, DOCX or TXT resumes, compares resume evidence with job requirements using Sentence Transformer embeddings, detects required and preferred skill gaps, calculates an ATS-aware fit score, recommends roles and stores privacy-safe analysis history in PostgreSQL. The application has a Streamlit interface, a versioned FastAPI backend, SQLAlchemy models, Alembic migrations, Docker Compose and automated tests.

## 2. Why is it better than keyword matching?

Keyword matching only checks whether the same words appear. Semantic embeddings represent meaning, so related phrases can match even when wording differs. The system also aligns every JD requirement chunk with the closest resume chunk and shows that evidence.

## 3. What is an embedding?

An embedding is a dense numeric vector representing the semantic meaning of text. Similar text has vectors pointing in similar directions.

## 4. What is cosine similarity?

Cosine similarity measures the angle between two vectors:

```text
cosine_similarity(A, B) = (A · B) / (||A|| ||B||)
```

The model returns normalized embeddings, so dot product directly gives cosine similarity.

## 5. Why chunk the resume and JD?

A single embedding for the entire document can hide individual requirements. Chunking allows requirement-level matching and explainability. It also prevents a strong unrelated section from dominating the whole score.

## 6. How is the semantic score calculated?

For every job chunk, the system finds the maximum similarity with any resume chunk. It combines average requirement coverage with a lower percentile, so several weak requirements cannot be hidden by one excellent match. It then adds a smaller whole-document similarity component.

## 7. Why is semantic similarity weighted 60%?

The main research question is meaning-level job fit, so semantic evidence is the strongest signal. Skills, experience and ATS structure support the score but do not replace it.

## 8. How are required and preferred skills separated?

The JD parser extracts all skills. Skills found on lines containing phrases such as `preferred`, `nice to have`, `good to have`, `bonus` or `plus` are classified as preferred. Remaining detected skills are required.

## 9. How does the system extract skills?

It uses a curated skill taxonomy with categories and aliases. For example, `sklearn` maps to `Scikit-learn`, `Postgres` maps to `PostgreSQL`, and `NLP` maps to `Natural Language Processing`.

## 10. Why not use a generative LLM for everything?

A deterministic pipeline is cheaper, faster, easier to test and does not require a paid API key. Sentence embeddings solve semantic matching directly. An optional LLM could later rewrite suggestions, but the score should remain reproducible and auditable.

## 11. What happens if the transformer model fails?

The application logs the failure and uses a calibrated TF-IDF fallback. The UI and API clearly display the model used, so the fallback is transparent.

## 12. Why use PostgreSQL instead of only SQLite?

SQLite is excellent for local single-user development, but cloud local files may be temporary and concurrent writes are limited. PostgreSQL provides durable shared storage, indexing, relational constraints and better concurrency.

## 13. Explain the database tables.

- `analysis_records`: sanitized reports and analytics columns.
- `analysis_feedback`: helpful/not-helpful human feedback linked by foreign key.
- `job_postings`: active job catalog with JSON skill arrays.

## 14. Why store scores as columns and also store JSON?

Columns make filtering, grouping and dashboard queries efficient. JSON preserves the complete report structure without creating a table for every nested output.

## 15. Why store a JD hash?

The SHA-256 hash can identify repeated job descriptions without storing the full JD text, which reduces sensitive-data retention.

## 16. How is user history protected?

Each browser receives a random session ID. Normal history queries filter by that ID. The admin dashboard requires a secret PIN in public deployment.

## 17. Is session ID full authentication?

No. It is lightweight isolation for a demo. Production should use proper authentication, signed sessions, authorization roles and possibly row-level security.

## 18. What privacy protections exist?

Raw resume text is never persisted. Email is masked, phone and links are removed from stored JSON by default, admin access uses secrets, and credentials are never committed to GitHub.

## 19. How does job recommendation work?

Active jobs are read from PostgreSQL. The resume is semantically compared with each role description. Final recommendation score is 75% semantic fit and 25% catalog-skill coverage.

## 20. Why are the bundled jobs not claimed as live vacancies?

Using demo data avoids unauthorized scraping, expired links and third-party API failures. A production system can ingest jobs from an approved provider without changing the recommendation pipeline.

## 21. What is SQLAlchemy dependency injection in FastAPI?

`get_db()` creates a database session for each request and closes it after the request. FastAPI injects it into endpoint functions using `Depends`.

## 22. Why version API routes?

Routes use `/api/v1` so future breaking changes can be released under `/api/v2` without immediately breaking existing clients.

## 23. How are admin endpoints protected?

They require an `X-Admin-Key` header. The server compares it with the configured secret using constant-time comparison. For production, OAuth/JWT and role-based authorization would be stronger.

## 24. Why use Alembic if tables are created automatically?

Automatic creation makes the demo easy to run. Alembic provides controlled, repeatable and reversible schema changes for production.

## 25. What automated tests are included?

Tests cover skill aliases, resume parsing, ATS checks, required/preferred JD skill extraction, explainable analysis response shape, PostgreSQL URL normalization, API health and session validation.

## 26. What are the project limitations?

- Scanned PDFs require OCR.
- Rule-based profile extraction can miss unusual layouts.
- The skill taxonomy is finite.
- Similarity scores need calibration using labelled recruiter decisions.
- Session isolation is not full authentication.
- Bias and fairness require larger evaluation datasets.

## 27. How would you evaluate the model scientifically?

Create a labelled dataset of resume–JD pairs rated by multiple recruiters. Measure rank correlation, precision@k, recall@k and calibration. Compare keyword baseline, TF-IDF, bi-encoder embeddings and a cross-encoder reranker. Also measure inter-rater agreement.

## 28. What is a bi-encoder?

A bi-encoder independently encodes resume and JD text, making comparison fast and reusable. Sentence Transformers commonly use this design.

## 29. What is a cross-encoder, and why not use it now?

A cross-encoder reads both texts together and can be more accurate, but it is slower because it must run separately for every pair. A production system can use a bi-encoder for retrieval and a cross-encoder for top-result reranking.

## 30. What responsible-AI risks exist?

Resume screening can reproduce historical bias, overvalue writing style, penalize non-standard careers and create false confidence. Therefore the system excludes intentional protected-attribute scoring, provides explanations and must not automatically reject candidates.

## 31. What was the most difficult engineering decision?

Balancing explainability with semantic accuracy. Whole-document similarity was easy but not informative, so I implemented requirement-level chunk alignment and stored evidence excerpts while avoiding raw resume persistence.

## 32. What would you build next?

Authentication, OCR, approved live-job ingestion, a richer skill ontology, cross-encoder reranking, recruiter-labelled evaluation, fairness dashboards, background queues and cloud observability.
