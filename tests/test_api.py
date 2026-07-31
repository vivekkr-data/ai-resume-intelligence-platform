from fastapi.testclient import TestClient

from backend.main import app


def test_health_and_job_catalog():
    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["database"]["healthy"] is True

        jobs = client.get("/api/v1/jobs")
        assert jobs.status_code == 200
        assert len(jobs.json()) >= 10


def test_history_requires_session_id():
    with TestClient(app) as client:
        response = client.get("/api/v1/history")
        assert response.status_code == 422


def test_history_schema_accepts_database_record_shape():
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from backend.schemas import HistoryItem

    record = SimpleNamespace(
        id=1,
        created_at=datetime.now(timezone.utc),
        filename="resume.pdf",
        job_title="AI Intern",
        overall_score=75.0,
        model_used="test-model",
        processing_ms=120,
    )
    item = HistoryItem.model_validate(record)
    assert item.id == 1
    assert item.processing_ms == 120
