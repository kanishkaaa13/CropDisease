"""
Declarative base — imported by:
  - All model files (to define tables)
  - alembic/env.py (to auto-generate migrations)

Kept separate from connection.py to avoid circular imports.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""
    pass
