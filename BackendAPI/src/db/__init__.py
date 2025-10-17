"""Database package initialization for SQLAlchemy models and sessions.

This package exposes:
- Base: SQLAlchemy declarative base for models
- get_db: FastAPI dependency to yield a DB session
- SessionLocal: Session factory
"""

from .session import Base, get_db, SessionLocal  # noqa: F401
