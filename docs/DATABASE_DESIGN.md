# PostgreSQL Database Design

## Why PostgreSQL

SQLite is excellent for local development but public cloud instances often use temporary filesystems. PostgreSQL provides shared, durable and concurrent storage for recruiter demos, API requests and admin analytics.

## Tables

### `analysis_records`

Stores one privacy-safe analysis result.

Important fields:

- `session_id`: isolates normal user history.
- `job_description_hash`: detects repeated JDs without storing the JD text.
- `model_used`: supports model comparison and auditing.
- `processing_ms`: supports performance monitoring.
- component scores: enables analytics without reading JSON.
- `result`: sanitized complete report for history display.

Raw resume text is not stored.

### `analysis_feedback`

Stores helpful/not-helpful events linked to an analysis through a foreign key. This creates the foundation for a human-in-the-loop evaluation dataset.

### `job_postings`

Stores the role catalog used by the recommender. `is_active` performs soft deletion, and the title/company pair is unique to prevent duplicate seeding.

## Relationships

```text
analysis_records (1) ──────< analysis_feedback (many)
job_postings is independent and used for recommendation ranking
```

## Indexes

The schema indexes:

- session ID for user history
- creation time for recent analytics
- job title for role grouping
- overall score for threshold queries
- active jobs for recommendation retrieval
- feedback foreign key

## Privacy choices

- `STORE_PII=false` by default.
- Candidate email is masked.
- Phone numbers and links are removed from stored JSON.
- JD text is represented by SHA-256 hash.
- Session-specific history prevents casual cross-user access.
- Admin dashboard requires a secret PIN in public deployment.

## Migration strategy

The application uses `create_all` to make first-run demos easy, while Alembic is included for controlled schema changes.

```bash
alembic upgrade head
```

In production, run migrations during deployment before starting the app.

## Useful PostgreSQL queries

```sql
-- Number of analyses per target role
SELECT job_title, COUNT(*) AS analyses, ROUND(AVG(overall_score)::numeric, 2) AS avg_fit
FROM analysis_records
GROUP BY job_title
ORDER BY analyses DESC;

-- Recent high-fit analyses
SELECT id, created_at, job_title, overall_score, model_used
FROM analysis_records
WHERE overall_score >= 70
ORDER BY created_at DESC
LIMIT 20;

-- Feedback usefulness rate
SELECT
  COUNT(*) FILTER (WHERE helpful) AS helpful,
  COUNT(*) AS total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE helpful) / NULLIF(COUNT(*), 0), 2) AS helpful_rate
FROM analysis_feedback;
```
