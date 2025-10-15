"""
Database access layer for the BackendAPI using SQLAlchemy.

This module provides:
- SQLAlchemy engine and session factory bound to DATABASE_URL
- get_db() dependency for FastAPI routes to obtain database sessions
- Application lifecycle hooks to initialize and dispose the engine
- Base metadata for ORM models

Configuration:
- DATABASE_URL must be provided via environment variables handled by src.api.config.

Usage:
    from fastapi import Depends
    from sqlalchemy.orm import Session
    from src.api.db import get_db
    
    @app.get("/users")
    def list_users(db: Session = Depends(get_db)):
        return db.query(User).all()

Note:
- This is a synchronous SQLAlchemy setup with psycopg2 for simplicity
- All sessions are automatically closed after request completion
- Use Base.metadata.create_all(engine) to create tables if needed
"""

import logging
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from src.api.config import get_settings

# SQLAlchemy Base for ORM models
Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionLocal = None


def _create_engine_from_url(database_url: str):
    """Create SQLAlchemy engine with appropriate settings."""
    # For PostgreSQL with psycopg2, use standard configuration
    # Pool settings: pool_size=5, max_overflow=10 for typical deployment
    return create_engine(
        database_url,
        pool_pre_ping=True,  # verify connections before using
        pool_size=5,
        max_overflow=10,
        echo=False,  # set to True for SQL debug logging
    )


# PUBLIC_INTERFACE
def init_db_engine() -> None:
    """Initialize the global SQLAlchemy engine and session factory.
    
    If DATABASE_URL is not configured, initialization is skipped to allow the
    app to start for non-DB endpoints (e.g., health checks).
    """
    global _engine, _SessionLocal
    
    if _engine is not None:
        return
    
    settings = get_settings()
    db_url = settings.database_url.strip()
    
    if not db_url:
        logging.warning("DATABASE_URL is not set; database engine will not be initialized.")
        return
    
    try:
        _engine = _create_engine_from_url(db_url)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        
        # Quick connectivity check
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logging.info("Database engine initialized successfully.")
        
        # Optionally create tables if CREATE_TABLES env flag is set
        if os.getenv("CREATE_TABLES", "").lower() in ("true", "1", "yes"):
            logging.info("CREATE_TABLES flag detected; creating all tables...")
            Base.metadata.create_all(bind=_engine)
            logging.info("All tables created successfully.")
            
    except Exception as exc:
        logging.error("Failed to initialize database engine: %s", exc)
        _engine = None
        _SessionLocal = None


# PUBLIC_INTERFACE
def dispose_db_engine() -> None:
    """Dispose the global SQLAlchemy engine and release resources."""
    global _engine, _SessionLocal
    
    if _engine is not None:
        try:
            _engine.dispose()
            logging.info("Database engine disposed.")
        finally:
            _engine = None
            _SessionLocal = None


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session.
    
    Yields a SQLAlchemy Session for use within a request context.
    The session is automatically closed after the request completes.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database is not initialized. Ensure DATABASE_URL is set and init_db_engine() has run."
        )
    
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def get_engine():
    """Return the global SQLAlchemy engine instance.
    
    Useful for direct operations or migrations.
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine is not initialized. Ensure DATABASE_URL is set and init_db_engine() has run."
        )
    return _engine


# ============================================================================
# Backward Compatibility Layer for asyncpg-style helpers
# ============================================================================
# The following functions maintain compatibility with existing router code
# that uses asyncpg-style fetch_one, fetch_all, execute patterns.
# These wrap synchronous SQLAlchemy operations.

from typing import Any, Dict, List, Optional, Tuple


# PUBLIC_INTERFACE
async def fetch_one(sql: str, *params: Any) -> Optional[Dict[str, Any]]:
    """Fetch a single record as a dict or return None if no row.
    
    Backward-compatible wrapper for asyncpg-style usage.
    Note: This is now synchronous under the hood but wrapped as async for compatibility.
    
    Parameters:
    - sql: The SQL query string with placeholders like $1, $2 (asyncpg style).
    - *params: The parameters to bind to the SQL query.
    
    Returns:
    - A dictionary representing the row, or None.
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database is not initialized. Ensure DATABASE_URL is set and init_db_engine() has run."
        )
    
    # Convert asyncpg-style $1, $2 placeholders to SQLAlchemy :param_0, :param_1
    converted_sql, param_dict = _convert_asyncpg_placeholders(sql, params)
    
    db = _SessionLocal()
    try:
        result = db.execute(text(converted_sql), param_dict)
        row = result.fetchone()
        if row is None:
            return None
        return dict(row._mapping)
    finally:
        db.close()


# PUBLIC_INTERFACE
async def fetch_all(sql: str, *params: Any) -> List[Dict[str, Any]]:
    """Fetch all rows for a query as a list of dicts.
    
    Backward-compatible wrapper for asyncpg-style usage.
    
    Parameters:
    - sql: The SQL query string with placeholders like $1, $2.
    - *params: The parameters to bind to the SQL query.
    
    Returns:
    - List of dictionaries for each row.
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database is not initialized. Ensure DATABASE_URL is set and init_db_engine() has run."
        )
    
    converted_sql, param_dict = _convert_asyncpg_placeholders(sql, params)
    
    db = _SessionLocal()
    try:
        result = db.execute(text(converted_sql), param_dict)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    finally:
        db.close()


# PUBLIC_INTERFACE
async def execute(sql: str, *params: Any) -> str:
    """Execute a statement (INSERT/UPDATE/DELETE) and return the status string.
    
    Backward-compatible wrapper for asyncpg-style usage.
    
    Parameters:
    - sql: The SQL statement with placeholders like $1, $2.
    - *params: The parameters to bind to the SQL statement.
    
    Returns:
    - The command status string (e.g., 'UPDATE 1').
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database is not initialized. Ensure DATABASE_URL is set and init_db_engine() has run."
        )
    
    converted_sql, param_dict = _convert_asyncpg_placeholders(sql, params)
    
    db = _SessionLocal()
    try:
        result = db.execute(text(converted_sql), param_dict)
        db.commit()
        # Return a status string similar to asyncpg format
        rowcount = result.rowcount
        command = sql.strip().split()[0].upper()
        return f"{command} {rowcount}"
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# PUBLIC_INTERFACE
async def execute_many(sql: str, param_sets: List[Tuple[Any, ...]]) -> List[str]:
    """Execute a statement for multiple parameter sets.
    
    Backward-compatible wrapper for asyncpg-style usage.
    
    Parameters:
    - sql: The SQL statement with placeholders.
    - param_sets: A list of tuples representing parameter sets.
    
    Returns:
    - List of status strings for each execution.
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database is not initialized. Ensure DATABASE_URL is set and init_db_engine() has run."
        )
    
    results: List[str] = []
    db = _SessionLocal()
    try:
        for params in param_sets:
            converted_sql, param_dict = _convert_asyncpg_placeholders(sql, params)
            result = db.execute(text(converted_sql), param_dict)
            command = sql.strip().split()[0].upper()
            results.append(f"{command} {result.rowcount}")
        db.commit()
        return results
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _convert_asyncpg_placeholders(sql: str, params: tuple) -> tuple:
    """Convert asyncpg-style $1, $2 placeholders to SQLAlchemy named parameters.
    
    Returns:
    - tuple of (converted_sql, param_dict)
    """
    import re
    
    # Find all $1, $2, etc. placeholders
    placeholders = re.findall(r'\$(\d+)', sql)
    
    if not placeholders:
        # No placeholders, return as-is
        return sql, {}
    
    # Build parameter dictionary
    param_dict = {}
    converted_sql = sql
    
    # Sort by number descending to avoid replacing $1 in $10
    for idx in sorted(set(placeholders), key=int, reverse=True):
        param_name = f"param_{int(idx)-1}"
        param_dict[param_name] = params[int(idx)-1] if int(idx) <= len(params) else None
        converted_sql = converted_sql.replace(f"${idx}", f":{param_name}")
    
    return converted_sql, param_dict
