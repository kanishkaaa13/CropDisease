from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base  # single source of truth for the declarative base

__all__ = ["engine", "SessionLocal", "Base", "get_db"]

engine = create_engine(
    settings.db_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
    # Enable pgbouncer-compatible connection pooling later
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
