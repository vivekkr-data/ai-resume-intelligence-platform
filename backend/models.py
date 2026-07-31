"""Relational database models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    candidate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    candidate_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str] = mapped_column(String(255), default="Target Role", index=True)
    job_description_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    semantic_score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    model_used: Mapped[str] = mapped_column(String(255), nullable=False)
    processing_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_skill_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_skill_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resume_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    feedback: Mapped[list["AnalysisFeedback"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class AnalysisFeedback(Base):
    __tablename__ = "analysis_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    analysis: Mapped[AnalysisRecord] = relationship(back_populates="feedback")


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("title", "company", name="uq_job_title_company"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    apply_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source: Mapped[str] = mapped_column(String(255), default="Demo catalog", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
