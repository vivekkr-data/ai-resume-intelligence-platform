# FastAPI Guide

Run:

```bash
uvicorn backend.main:app --reload
```

Interactive Swagger documentation:

```text
http://localhost:8000/docs
```

## Analyze a resume

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "resume=@sample_data/sample_resume.txt" \
  -F "job_title=AI / Machine Learning Intern" \
  -F "session_id=demo-session-001" \
  -F "job_description=<paste job description>"
```

The response includes score breakdown, matched/missing skills, ATS checks, semantic evidence, learning roadmap, model name and processing time.

## Get session history

```bash
curl "http://localhost:8000/api/v1/history?session_id=demo-session-001"
```

## Create an admin job posting

Set `ADMIN_API_KEY`, then:

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: YOUR_SECRET" \
  -d '{
    "title": "NLP Intern",
    "company": "Demo Company",
    "location": "Remote",
    "description": "Build and evaluate NLP prototypes using Python and transformers.",
    "skills": ["Python", "Natural Language Processing", "Transformers"]
  }'
```

## Design choices to explain

- `multipart/form-data` is used because resume bytes and JD text are sent together.
- Pydantic validates response and admin request schemas.
- Dependency injection provides SQLAlchemy sessions.
- Admin routes use `X-Admin-Key` and constant-time comparison.
- Legacy routes remain hidden for compatibility, while `/api/v1` is the public versioned API.
