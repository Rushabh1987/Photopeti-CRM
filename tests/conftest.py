"""Set required env vars before any app module is imported."""
import os

# Provides a dummy URL so pydantic-settings doesn't fail on import.
# Tests that need a real DB connection are skipped unless DATABASE_URL is set externally.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
