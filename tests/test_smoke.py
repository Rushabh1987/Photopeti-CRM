"""Phase 1 smoke tests: the app imports, the DB initializes, health responds."""
from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_models_register():
    from app.db import Base
    import app.models  # noqa: F401
    tables = set(Base.metadata.tables)
    assert {"clients", "leads", "messages", "shoots", "editing_tasks", "reminders"} <= tables
