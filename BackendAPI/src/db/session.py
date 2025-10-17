import os
from contextlib import contextmanager
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Load environment variables from .env if present
load_dotenv()

# Global base for models
Base = declarative_base()

_engine = None  # type: ignore[var-annotated]
SessionLocal: Optional[sessionmaker[Session]] = None


def _get_database_url() -> str:
    """Read DATABASE_URL from environment variables."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Please configure it in your environment or .env file."
        )
    return db_url


# PUBLIC_INTERFACE
def init_engine_and_session(force: bool = False) -> None:
    """Initialize the SQLAlchemy Engine and Session factory.

    Args:
        force: If True, reinitialize engine/session even if already initialized.
    """
    global _engine, SessionLocal
    if _engine is not None and SessionLocal is not None and not force:
        return

    database_url = _get_database_url()

    # Use psycopg2 driver for PostgreSQL in sync mode
    _engine = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
        class_=Session,
        future=True,
    )


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    if SessionLocal is None:
        init_engine_and_session()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session.

    Yields:
        Session: A SQLAlchemy session bound to the configured engine.
    """
    if SessionLocal is None:
        init_engine_and_session()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
