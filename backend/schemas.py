"""Pydantic request and response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScoreBreakdown(BaseModel):
    overall: float = Field(ge=0, le=100)
    semantic: float = Field(ge=0, le=100)
    skills: float = Field(ge=0, le=100)
    experience: float = Field(ge=0, le=100)
    resume_quality: float = Field(ge=0, le=100)


class MatchEvidence(BaseModel):
    requirement: str
    resume_evidence: str
    similarity: float = Field(ge=0, le=100)


class AtsCheck(BaseModel):
    check: str
    passed: bool
    detail: str


class RoadmapItem(BaseModel):
    skill: str
    priority: str
    action: str


class AnalysisResponse(BaseModel):
    analysis_id: int | None = None
    filename: str
    job_title: str
    verdict: str
    scores: ScoreBreakdown
    resume_profile: dict[str, Any]
    job_profile: dict[str, Any]
    matched_skills: list[str]
    missing_skills: list[str]
    preferred_skill_gaps: list[str]
    strengths: list[str]
    suggestions: list[str]
    ats_checks: list[AtsCheck]
    learning_roadmap: list[RoadmapItem]
    evidence: list[MatchEvidence]
    model_used: str
    processing_ms: int
    scoring_formula: dict[str, float]
    privacy: dict[str, Any]


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    filename: str
    job_title: str
    overall_score: float
    model_used: str
    processing_ms: int


class FeedbackRequest(BaseModel):
    helpful: bool
    comments: str | None = Field(default=None, max_length=1000)


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    company: str = Field(min_length=2, max_length=255)
    location: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=30)
    skills: list[str] = Field(default_factory=list)
    apply_url: HttpUrl | None = None
    source: str = Field(default="Admin", max_length=255)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str
    description: str
    skills: list[str]
    apply_url: str | None
    source: str
    is_active: bool


class DashboardSummary(BaseModel):
    total_analyses: int
    average_score: float
    high_match_count: int
    total_jobs: int
    feedback_count: int
    database_backend: str
