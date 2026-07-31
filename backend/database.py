"""SQLAlchemy setup for local SQLite and hosted PostgreSQL."""
from __future__ import annotations

import csv
import logging
from collections.abc import Generator

from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine_kwargs: dict = {
    "pool_pre_ping": True,
    "future": True,
}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        {
            "pool_recycle": 300,
            "pool_size": 5,
            "max_overflow": 10,
        }
    )

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db(seed: bool = True) -> None:
    """Create tables and seed the bundled demonstration job catalog."""
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if seed:
        seed_jobs()


def seed_jobs() -> int:
    from backend.models import JobPosting

    if not settings.jobs_csv.exists():
        logger.warning("Job seed file not found: %s", settings.jobs_csv)
        return 0

    with SessionLocal() as db:
        existing = db.scalar(select(JobPosting.id).limit(1))
        if existing is not None:
            return 0

        created = 0
        with settings.jobs_csv.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                skills = [item.strip() for item in row.get("skills", "").split(";") if item.strip()]
                db.add(
                    JobPosting(
                        title=row.get("title", "Untitled role").strip(),
                        company=row.get("company", "Demo company").strip(),
                        location=row.get("location", "Not specified").strip(),
                        description=row.get("description", "").strip(),
                        skills=skills,
                        apply_url=row.get("apply_url", "").strip() or None,
                        source="Bundled demo catalog",
                        is_active=True,
                    )
                )
                created += 1
        try:
            db.commit()
            return created
        except IntegrityError:
            # Another web process may have seeded the same catalog concurrently.
            db.rollback()
            return 0


def database_health() -> tuple[bool, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, settings.database_backend
    except Exception as exc:  # pragma: no cover - environment-specific
        logger.exception("Database health check failed")
        return False, str(exc)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
