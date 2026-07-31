"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _as_bool(name: str, default: bool = False) -> bool:
    """Convert an environment-variable value into a Boolean."""

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def normalize_database_url(url: str) -> str:
    """Normalize hosted PostgreSQL URLs for SQLAlchemy and psycopg 3."""

    cleaned = url.strip()

    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://") :]

    if cleaned.startswith("postgresql://") and not cleaned.startswith(
        "postgresql+psycopg://"
    ):
        cleaned = (
            "postgresql+psycopg://"
            + cleaned[len("postgresql://") :]
        )

    return cleaned


@dataclass(frozen=True)
class Settings:
    """Central application settings."""

    app_name: str = os.getenv(
        "APP_NAME",
        "AI Resume Intelligence Platform",
    )

    app_version: str = os.getenv(
        "APP_VERSION",
        "2.0.0",
    )

    environment: str = os.getenv(
        "APP_ENV",
        "development",
    )

    database_url: str = normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'resume_analyzer.db'}",
        )
    )

    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    # Optional AI configuration.
    # The application will use the local fallback when GEMINI_API_KEY is empty.
    gemini_api_key: str = os.getenv(
        "GEMINI_API_KEY",
        "",
    )

    gemini_model: str = os.getenv(
        "GEMINI_MODEL",
        "",
    )

    gemini_timeout_seconds: int = int(
        os.getenv(
            "GEMINI_TIMEOUT_SECONDS",
            "25",
        )
    )

    jobs_csv: Path = Path(
        os.getenv(
            "JOBS_CSV",
            str(BASE_DIR / "data" / "jobs.csv"),
        )
    )

    max_upload_mb: int = int(
        os.getenv(
            "MAX_UPLOAD_MB",
            "10",
        )
    )

    allow_origins: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv("ALLOW_ORIGINS", "*").split(",")
        if item.strip()
    )

    store_pii: bool = _as_bool(
        "STORE_PII",
        False,
    )

    admin_api_key: str = os.getenv(
        "ADMIN_API_KEY",
        "",
    )

    admin_dashboard_pin: str = os.getenv(
        "ADMIN_DASHBOARD_PIN",
        "",
    )

    enable_admin_dashboard: bool = _as_bool(
        "ENABLE_ADMIN_DASHBOARD",
        True,
    )

    debug: bool = _as_bool(
        "DEBUG",
        False,
    )

    @property
    def database_backend(self) -> str:
        """Return the active database backend name."""

        if self.database_url.startswith("postgresql"):
            return "PostgreSQL"

        return "SQLite"


settings = Settings()
