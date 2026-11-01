"""
LostLink Database Connection and Session Management.
Supports both SQLite (local development / testing) and PostgreSQL (production / Docker).
"""
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger(__name__)


def normalize_database_url(raw_url: str) -> str:
    """
    Normalizes database connection URLs:
    - Replaces legacy postgres:// scheme with postgresql://
    - Automatically selects postgresql+psycopg (v3) or postgresql+psycopg2 driver
    - Preserves sqlite:/// paths intact
    """
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if url.startswith("postgresql://"):
        try:
            import psycopg  # noqa: F401
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        except ImportError:
            try:
                import psycopg2  # noqa: F401
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            except ImportError:
                pass
    return url


DATABASE_URL = normalize_database_url(settings.DATABASE_URL)

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,  # Discards stale or dropped connections automatically
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
