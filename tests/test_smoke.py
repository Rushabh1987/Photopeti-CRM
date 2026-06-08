"""Smoke tests: the app imports, models register, health responds."""
import os

import pytest
from fastapi.testclient import TestClient


def test_models_register():
    from app.db import Base
    import app.models  # noqa: F401
    tables = set(Base.metadata.tables)
    assert {"brands", "leads", "messages", "shoots", "reminders"} <= tables


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping live DB test",
)
def test_health():
    from app.main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
