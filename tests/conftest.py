"""Set required env vars before any app module is imported."""
import os

import pytest

# Provides a dummy URL so pydantic-settings doesn't fail on import.
# Tests that need a real DB connection are skipped unless DATABASE_URL is set externally.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

# Override insecure defaults so the startup validator doesn't reject test config.
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-for-tests-only-32chars!!")
os.environ.setdefault("APP_PASSWORD", "test-password-not-for-production")


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
