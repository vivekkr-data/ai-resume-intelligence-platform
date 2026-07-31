# AI-Powered Resume Analyzer and Job Recommendation System Using NLP

## Abstract

The AI Resume Intelligence Platform is an end-to-end NLP application that analyzes candidate resumes against job descriptions using semantic embeddings rather than relying only on exact keyword overlap. It extracts contact information, education, experience, projects and technical skills; distinguishes required from preferred job skills; generates an explainable score; identifies skill gaps; evaluates ATS quality; recommends suitable roles; and stores sanitized results in PostgreSQL. The system includes a Streamlit interface, FastAPI service, SQLAlchemy ORM models, Alembic migrations, Docker Compose and automated tests.

## 1. Introduction

Recruiters and candidates frequently use Applicant Tracking Systems to compare resumes with job requirements. Basic systems often reward keyword repetition and provide little explanation. This project addresses that limitation by aligning job-requirement chunks with resume evidence using Sentence Transformer embeddings and cosine similarity.

The project is intended as a decision-support and candidate-improvement tool. It is not designed to automatically reject applicants.

## 2. Objectives

1. Parse PDF, DOCX and TXT resumes.
2. Extract candidate profile information and a categorized skill set.
3. Compare resume and JD meaning using semantic embeddings.
4. Show explainable requirement-to-resume evidence.
5. Separate required and preferred skills.
6. Calculate a transparent weighted score.
7. Generate ATS checks and improvement guidance.
8. Recommend suitable database-backed roles.
9. Persist privacy-safe history in PostgreSQL.
10. Expose functionality through Streamlit and FastAPI.
11. Support testing, migrations, Docker and cloud deployment.

## 3. Functional Requirements

- Resume upload and validation
- Job title and job description input
- Candidate profile extraction
- Semantic fit score
- Skill coverage score
- Experience alignment
- Resume quality score
- Matched and missing skills
- ATS checklist
- Improvement suggestions
- Learning roadmap
- Explainable evidence
- Downloadable reports
- Job recommendations
- Session history
- Admin analytics
- API access

## 4. Non-Functional Requirements

- Explainability
- Privacy by design
- Graceful model fallback
- Database portability
- Testability
- Deployment readiness
- Responsive user interface
- Responsible-AI disclosure

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| API | FastAPI, Uvicorn |
| NLP | Sentence Transformers, TF-IDF |
| Machine learning utilities | Scikit-learn, NumPy |
| Document extraction | PyMuPDF, python-docx |
| Database | PostgreSQL / SQLite fallback |
| ORM | SQLAlchemy 2 |
| Migration | Alembic |
| Validation | Pydantic |
| Testing | Pytest, FastAPI TestClient |
| Deployment | Streamlit Cloud, Render, Docker Compose |
| CI | GitHub Actions |

## 6. System Architecture

The user uploads a resume and provides a target JD. The document parser extracts text. The profile parser identifies sections, skills, education and experience. The semantic matcher creates chunks and embeddings. The scoring service combines semantic alignment, skill coverage, experience and ATS quality. The result is displayed and a sanitized copy is stored in the database.

```text
User → Streamlit/FastAPI → Document Parser → Profile Extraction
     → Embedding Matcher → Explainable Evidence → Weighted Scoring
     → PostgreSQL → History / Dashboard / Recommendations
```

## 7. Resume Parsing

The parser performs:

- text normalization
- heading detection
- name estimation
- email, phone and URL extraction
- skill extraction using taxonomy and aliases
- education line extraction
- bullet and metric counting
- experience estimation from explicit duration or date ranges

Heuristics were selected because they are transparent and do not require a labelled NER dataset. A future version can combine them with a trained entity-recognition model.

## 8. Semantic Matching

### 8.1 Chunking

Resume and JD text are split into short chunks. Headings influence chunk boundaries so the evidence remains readable.

### 8.2 Embeddings

The default model is `all-MiniLM-L6-v2`. It converts text into normalized dense vectors.

### 8.3 Requirement coverage

For every JD chunk, the closest resume chunk is identified. The algorithm combines:

- mean of best requirement similarities
- 35th percentile of requirement similarities
- whole-document similarity

The lower percentile reduces the chance that one excellent section hides several weak requirements.

### 8.4 Fallback

If the embedding model cannot load, TF-IDF with unigram and bigram features is used. The UI reports the fallback model transparently.

## 9. Scoring Formula

```text
Overall = 0.60 × Semantic
        + 0.25 × Skill Coverage
        + 0.10 × Experience
        + 0.05 × ATS Quality
```

Required skills receive most of the skill score. Preferred skills contribute a smaller part when explicitly detected.

## 10. ATS Quality Analysis

The ATS module checks:

- contact information
- summary
- dedicated skill section
- project or experience evidence
- education section
- quantified results
- readable length
- portfolio links

It also checks action verbs, number of detected skills, bullet use and resume length.

## 11. Job Recommendation

Active roles are stored in `job_postings`. Each role receives:

```text
Recommendation = 0.75 × Semantic Fit + 0.25 × Skill Coverage
```

The result includes fit reason, matched skills and missing skills.

## 12. Database Design

### `analysis_records`

Stores session ID, filename, role, component scores, model, processing time, counts and sanitized JSON result.

### `analysis_feedback`

Stores human usefulness feedback linked through a foreign key.

### `job_postings`

Stores active role information and skill arrays. A unique title/company constraint prevents duplicate seeding.

## 13. Security and Privacy

- Raw resume text is never stored.
- Email is masked by default.
- Phone and links are removed from persisted JSON.
- JD text is replaced with SHA-256 hash.
- History is filtered by browser session.
- Admin routes use a secret API key.
- Dashboard uses a secret PIN.
- `.env` and Streamlit secrets are excluded from Git.

## 14. API Design

The API is versioned under `/api/v1`. It supports analysis, recommendations, history, feedback, job catalog management, health checks and admin analytics. Pydantic schemas validate inputs and outputs. SQLAlchemy sessions are provided using FastAPI dependency injection.

## 15. Testing

Automated tests verify:

- aliases and skill extraction
- profile and ATS parsing
- required/preferred skill separation
- explainable response structure
- database URL conversion
- API health
- job catalog seeding
- history parameter validation

GitHub Actions runs compilation and tests on pushes and pull requests.

## 16. Deployment

### Local

SQLite requires no setup. PostgreSQL can be started using Docker Compose.

### Cloud

Streamlit Community Cloud hosts the UI, and an external PostgreSQL database stores persistent results. Secrets are configured outside the repository.

## 17. Results

The sample final-year resume produces:

- structured candidate profile
- semantic and skill component scores
- requirement-level evidence
- ATS checklist
- skill-gap roadmap
- database record
- ranked job recommendations

Exact scores depend on the installed model and input text. The output includes the model name so results remain auditable.

## 18. Limitations

- Image-only PDFs require OCR.
- Complex two-column layouts may reduce extraction quality.
- The skill taxonomy does not cover every domain.
- Experience extraction is heuristic.
- Similarity thresholds need recruiter-labelled calibration.
- Browser session isolation is not full user authentication.
- Bias cannot be ruled out without systematic fairness evaluation.

## 19. Future Scope

- OCR for scanned resumes
- OAuth/JWT authentication
- role-based authorization
- approved live-job API integration
- skill ontology database
- cross-encoder reranking
- recruiter-labelled benchmark dataset
- fairness and calibration dashboard
- background task queue
- cloud logging and tracing

## 20. Conclusion

The project demonstrates an integrated application of NLP, machine learning, backend API development, relational database design, testing, deployment and responsible-AI principles. Its strongest feature is explainability: the platform not only generates a score but also shows the resume evidence responsible for semantic alignment.
