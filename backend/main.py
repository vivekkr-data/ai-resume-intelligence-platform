"""FastAPI service for the AI Resume Intelligence Platform."""
from __future__ import annotations

import secrets
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import database_health, get_db, init_db
from backend.models import AnalysisFeedback, AnalysisRecord, JobPosting
from backend.schemas import (
    AnalysisResponse,
    DashboardSummary,
    FeedbackRequest,
    HistoryItem,
    JobCreate,
    JobResponse,
)
from backend.services.analyzer import analyze_resume
from backend.services.document_parser import DocumentParseError, extract_text_from_bytes
from backend.services.job_recommender import recommend_jobs


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db(seed=True)
    yield


app = FastAPI(
    title="AI Resume Intelligence API",
    version=settings.app_version,
    description=(
        "Explainable semantic resume matching, ATS analysis, skill-gap detection, "
        "PostgreSQL persistence and database-backed job recommendations."
    ),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allow_origins),
    allow_credentials=settings.allow_origins != ("*",),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is disabled. Set ADMIN_API_KEY to enable it.",
        )
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin API key.")


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/v1/health")
@app.get("/health", include_in_schema=False)
def health() -> dict[str, object]:
    db_ok, db_detail = database_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": {"healthy": db_ok, "backend": db_detail},
        "embedding_model": settings.embedding_model,
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
@app.post("/analyze", response_model=AnalysisResponse, include_in_schema=False)
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(..., min_length=30),
    job_title: str = Form("Target Role"),
    session_id: str = Form(default=""),
    db: Session = Depends(get_db),
):
    try:
        file_bytes = await resume.read()
        if len(file_bytes) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")
        filename = (resume.filename or "resume").replace("/", "_").replace("\\", "_")
        resume_text = extract_text_from_bytes(file_bytes, filename)
        return analyze_resume(
            resume_text=resume_text,
            job_description=job_description,
            filename=filename,
            job_title=job_title,
            session_id=session_id or uuid.uuid4().hex,
            db=db,
        )
    except DocumentParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/recommend")
@app.post("/recommend", include_in_schema=False)
async def recommend(
    resume: UploadFile = File(...),
    top_k: int = Form(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    try:
        file_bytes = await resume.read()
        if len(file_bytes) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")
        resume_text = extract_text_from_bytes(file_bytes, resume.filename or "resume.pdf")
        recommendations, model_used = recommend_jobs(resume_text, top_k=top_k, db=db)
        return {"model_used": model_used, "recommendations": recommendations}
    except (DocumentParseError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/history", response_model=list[HistoryItem])
@app.get("/history", response_model=list[HistoryItem], include_in_schema=False)
def history(
    session_id: str = Query(min_length=4, max_length=64),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    statement = (
        select(AnalysisRecord)
        .where(AnalysisRecord.session_id == session_id)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement))


@app.get("/api/v1/history/{analysis_id}")
def history_detail(
    analysis_id: int,
    session_id: str = Query(min_length=4, max_length=64),
    db: Session = Depends(get_db),
):
    record = db.get(AnalysisRecord, analysis_id)
    if not record or record.session_id != session_id:
        raise HTTPException(status_code=404, detail="Analysis not found for this session.")
    return record.result


@app.post("/api/v1/history/{analysis_id}/feedback", status_code=201)
def save_feedback(
    analysis_id: int,
    payload: FeedbackRequest,
    session_id: str = Query(min_length=4, max_length=64),
    db: Session = Depends(get_db),
):
    record = db.get(AnalysisRecord, analysis_id)
    if not record or record.session_id != session_id:
        raise HTTPException(status_code=404, detail="Analysis not found for this session.")
    feedback = AnalysisFeedback(
        analysis_id=analysis_id,
        helpful=payload.helpful,
        comments=payload.comments,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"id": feedback.id, "saved": True}


@app.get("/api/v1/jobs", response_model=list[JobResponse])
def jobs(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    statement = select(JobPosting).order_by(JobPosting.created_at.desc())
    if active_only:
        statement = statement.where(JobPosting.is_active.is_(True))
    return list(db.scalars(statement))


@app.post(
    "/api/v1/jobs",
    response_model=JobResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    job = JobPosting(
        title=payload.title,
        company=payload.company,
        location=payload.location,
        description=payload.description,
        skills=payload.skills,
        apply_url=str(payload.apply_url) if payload.apply_url else None,
        source=payload.source,
        is_active=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.delete(
    "/api/v1/jobs/{job_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def deactivate_job(job_id: int, db: Session = Depends(get_db)) -> None:
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    job.is_active = False
    db.commit()


@app.get(
    "/api/v1/admin/dashboard",
    response_model=DashboardSummary,
    dependencies=[Depends(require_admin)],
)
def dashboard(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(AnalysisRecord.id))) or 0
    average = db.scalar(select(func.avg(AnalysisRecord.overall_score))) or 0.0
    high_match = db.scalar(
        select(func.count(AnalysisRecord.id)).where(AnalysisRecord.overall_score >= 70)
    ) or 0
    total_jobs = db.scalar(
        select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
    ) or 0
    feedback_count = db.scalar(select(func.count(AnalysisFeedback.id))) or 0
    return DashboardSummary(
        total_analyses=total,
        average_score=round(float(average), 2),
        high_match_count=high_match,
        total_jobs=total_jobs,
        feedback_count=feedback_count,
        database_backend=settings.database_backend,
    )
