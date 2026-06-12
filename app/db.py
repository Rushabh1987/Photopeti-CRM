"""Database engine, session factory, and the declarative Base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,       # recycle before PgBouncer/Supabase closes idle connections
    pool_pre_ping=True,     # validate connection before use (catches stale connections)
    pool_timeout=30,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency: yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Safe to call repeatedly."""
    import app.models  # noqa: F401  (register models on Base)
    Base.metadata.create_all(bind=engine)
