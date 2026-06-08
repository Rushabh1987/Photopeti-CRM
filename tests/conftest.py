"""Set required env vars before any app module is imported."""
import os

import pytest

# Provides a dummy URL so pydantic-settings doesn't fail on import.
# Tests that need a real DB connection are skipped unless DATABASE_URL is set externally.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")


@pytest.fixture
def db_session():
    """In-memory SQLite session for unit tests — no real DB needed."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import app.models  # noqa: F401 — register models on Base
    from app.db import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
