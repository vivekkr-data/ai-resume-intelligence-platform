"""Initial PostgreSQL-ready schema.

Revision ID: 20260731_0001
Revises:
Create Date: 2026-07-31
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260731_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("apply_url", sa.String(length=1000), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("title", "company", name="uq_job_title_company"),
    )
    op.create_index("ix_job_postings_id", "job_postings", ["id"])
    op.create_index("ix_job_postings_title", "job_postings", ["title"])
    op.create_index("ix_job_postings_is_active", "job_postings", ["is_active"])

    op.create_table(
        "analysis_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
        sa.Column("candidate_email", sa.String(length=255), nullable=True),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("job_description_hash", sa.String(length=64), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False),
        sa.Column("skill_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("model_used", sa.String(length=255), nullable=False),
        sa.Column("processing_ms", sa.Integer(), nullable=False),
        sa.Column("matched_skill_count", sa.Integer(), nullable=False),
        sa.Column("missing_skill_count", sa.Integer(), nullable=False),
        sa.Column("resume_word_count", sa.Integer(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
    )
    op.create_index("ix_analysis_records_id", "analysis_records", ["id"])
    op.create_index("ix_analysis_records_created_at", "analysis_records", ["created_at"])
    op.create_index("ix_analysis_records_session_id", "analysis_records", ["session_id"])
    op.create_index("ix_analysis_records_job_title", "analysis_records", ["job_title"])
    op.create_index("ix_analysis_records_overall_score", "analysis_records", ["overall_score"])

    op.create_table(
        "analysis_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analysis_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("helpful", sa.Boolean(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_feedback_analysis_id", "analysis_feedback", ["analysis_id"])


def downgrade() -> None:
    op.drop_table("analysis_feedback")
    op.drop_table("analysis_records")
    op.drop_table("job_postings")
