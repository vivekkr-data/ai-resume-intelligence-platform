# AI Resume Intelligence Platform

**Final-year AI/NLP project for explainable resume analysis, recruiter-fit scoring and job recommendations.**

The platform extracts a candidate profile from PDF/DOCX/TXT resumes, compares it with a job description using **Sentence Transformer embeddings**, explains which resume evidence supports each requirement, identifies skill gaps, evaluates ATS quality, recommends suitable roles and stores privacy-safe history in **PostgreSQL**.

## Why this is not a keyword counter

The job description and resume are divided into meaningful chunks. The application generates normalized embeddings and compares every requirement chunk with the closest resume chunk using cosine similarity. The final score combines:

| Component | Weight |
|---|---:|
| Semantic requirement alignment | 60% |
| Required/preferred skill coverage | 25% |
| Experience alignment | 10% |
| ATS/resume quality | 5% |

If the Sentence Transformer cannot load, a calibrated TF-IDF matcher keeps the application usable and clearly reports that fallback.

## Recruiter-ready features

- Explainable resume-to-JD semantic score
- Required vs preferred skill extraction
- Matched skills, missing skills and a learning roadmap
- ATS checklist and actionable resume suggestions
- Candidate strengths and recruiter-friendly verdict
- PDF, DOCX and TXT parsing
- Database-backed job recommendation catalog
- PostgreSQL analysis history and admin analytics
- Session-isolated user history
- Privacy-safe persistence: raw resume text is never stored
- PII masking unless `STORE_PII=true`
- Feedback table for a future human-in-the-loop evaluation cycle
- FastAPI REST API with Swagger/OpenAPI
- Docker Compose with PostgreSQL
- Alembic migration setup
- GitHub Actions CI
- Streamlit/Render deployment configuration
- Downloadable JSON, Markdown and HTML reports

## Architecture

```mermaid
flowchart LR
    U[Candidate / Recruiter] --> S[Streamlit UI]
    U --> A[FastAPI API]
    S --> P[Document Parser]
    A --> P
    P --> R[Resume & JD Profile Extraction]
    R --> E[Sentence Transformer Embeddings]
    E --> X[Explainable Similarity Evidence]
    R --> K[Skill + Experience + ATS Scoring]
    X --> F[Final Fit Score]
    K --> F
    F --> DB[(PostgreSQL)]
    DB --> D[Recruiter Dashboard]
    DB --> J[Job Recommendation Catalog]
```

## Database design

```mermaid
erDiagram
    ANALYSIS_RECORDS ||--o{ ANALYSIS_FEEDBACK : receives
    ANALYSIS_RECORDS {
        int id PK
        string session_id
        string filename
        string job_title
        float overall_score
        float semantic_score
        float skill_score
        string model_used
        int processing_ms
        json result
    }
    ANALYSIS_FEEDBACK {
        int id PK
        int analysis_id FK
        boolean helpful
        text comments
    }
    JOB_POSTINGS {
        int id PK
        string title
        string company
        string location
        text description
        json skills
        boolean is_active
    }
```

## Project structure

```text
ai_resume_analyzer_pro/
├── streamlit_app.py
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── services/
│       ├── analyzer.py
│       ├── matcher.py
│       ├── resume_parser.py
│       ├── suggestions.py
│       ├── job_recommender.py
│       ├── document_parser.py
│       └── report.py
├── migrations/
├── data/jobs.csv
├── sample_data/
├── tests/
├── docs/
├── database/demo_queries.sql
├── postman/AI_Resume_Intelligence.postman_collection.json
├── .github/workflows/ci.yml
├── docker-compose.yml
├── render.yaml
└── requirements.txt
```

## Run locally on Windows

Python **3.11** is recommended.

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

FastAPI:

```powershell
uvicorn backend.main:app --reload
```

Open Swagger: `http://localhost:8000/docs`.

One-click alternatives:

- Run `setup_windows.bat` once.
- Run `run_streamlit.bat` for the UI.
- Run `run_api.bat` for FastAPI.

## Run the full PostgreSQL stack with Docker

```bash
docker compose up --build
```

- Streamlit: `http://localhost:8501`
- FastAPI Swagger: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

The Docker configuration creates a persistent volume named `postgres_data`.

## Hosted PostgreSQL

The recommended free-demo setup is:

1. Create a hosted PostgreSQL database such as Neon.
2. Copy its connection string.
3. Set it as `DATABASE_URL` in `.env` locally or in hosting secrets.

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
STORE_PII=false
ADMIN_DASHBOARD_PIN=your-private-pin
ADMIN_API_KEY=your-long-random-api-key
```

The application automatically converts standard `postgresql://` and legacy `postgres://` URLs to the SQLAlchemy psycopg driver format.

Detailed deployment instructions: [`docs/DEPLOY_STREAMLIT_NEON.md`](docs/DEPLOY_STREAMLIT_NEON.md)

## Database migrations

For the current demo, tables are also created automatically. For an interview, explain that production schema changes should use migrations:

```bash
alembic upgrade head
```

## Tests

```bash
pytest -q
```

The GitHub Actions workflow also compiles the project and runs tests on every push and pull request.

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Application and database health |
| POST | `/api/v1/analyze` | Upload resume and analyze against a JD |
| POST | `/api/v1/recommend` | Rank active job postings |
| GET | `/api/v1/history` | Session-isolated history |
| POST | `/api/v1/history/{id}/feedback` | Human feedback event |
| GET | `/api/v1/jobs` | Active job catalog |
| POST | `/api/v1/jobs` | Admin-protected job creation |
| GET | `/api/v1/admin/dashboard` | Admin analytics |

## Responsible AI and privacy

- The output is decision support, not an automatic hiring decision.
- Raw resume text is never persisted.
- Email and phone are masked by default.
- Protected personal characteristics are not intentional ranking features.
- User history is isolated by browser session.
- Administrative endpoints require a secret key.
- Human review is mandatory because embeddings and heuristic extraction can be imperfect.

## Important demo note

The bundled job catalog contains **demonstration roles**, not verified live vacancies. This is intentional: it avoids unauthorized scraping and broken third-party APIs. A production version can ingest jobs through an approved provider while keeping the same `job_postings` schema.

## Interview resources

- [`docs/INTERVIEW_DEMO_SCRIPT.md`](docs/INTERVIEW_DEMO_SCRIPT.md)
- [`docs/10_DAY_INTERVIEW_PLAN.md`](docs/10_DAY_INTERVIEW_PLAN.md)
- [`docs/VIVA_GUIDE.md`](docs/VIVA_GUIDE.md)
- [`docs/DATABASE_DESIGN.md`](docs/DATABASE_DESIGN.md)
- [`docs/API_GUIDE.md`](docs/API_GUIDE.md)
- [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md)
