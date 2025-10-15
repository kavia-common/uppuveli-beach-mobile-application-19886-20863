"""
Database access layer for the BackendAPI.

This module provides:
- An async connection pool to PostgreSQL using asyncpg
- Safe, parameterized helper functions for common operations:
  * fetch_one: return a single record or None
  * fetch_all: return a list of records
  * execute: run INSERT/UPDATE/DELETE and return command status/row count
- Application lifecycle hooks to initialize and close the pool.

Configuration:
- DATABASE_URL must be provided via environment variables handled by src.api.config.

Usage:
    from src.api.db import fetch_one, fetch_all, execute

    user = await fetch_one("SELECT * FROM users WHERE id=$1", user_id)
    rows = await fetch_all("SELECT * FROM bookings WHERE status=$1", "confirmed")
    status = await execute("UPDATE users SET name=$1 WHERE id=$2", "Alice", 123)

Note:
- All query parameters MUST be passed as separate function args to ensure safe parameterization.
- Do not use string interpolation for SQL parameters.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

from src.api.config import get_settings

# Global pool reference. Access via getters to avoid direct manipulation.
_pool: Optional[asyncpg.Pool] = None


async def _create_pool(database_url: str) -> asyncpg.Pool:
    """Create an asyncpg connection pool with sane defaults."""
    # Configure min/max sizes for typical small deployment; tune via env as needed later
    min_size = 1
    max_size = 10
    return await asyncpg.create_pool(
        dsn=database_url,
        min_size=min_size,
        max_size=max_size,
        command_timeout=60,  # seconds
        # Prefer UTC timestamps; leave statement cache default on
    )


# PUBLIC_INTERFACE
async def init_db_pool() -> None:
    """Initialize the global database connection pool if DATABASE_URL is set.

    If DATABASE_URL is not configured, initialization is skipped to allow the
    app to start for non-DB endpoints (e.g., health checks).
    """
    global _pool
    if _pool is not None:
        return

    settings = get_settings()
    db_url = settings.database_url.strip()

    if not db_url:
        logging.warning("DATABASE_URL is not set; database pool will not be initialized.")
        return

    try:
        _pool = await _create_pool(db_url)
        # Quick connectivity check
        async with _pool.acquire() as conn:  # type: ignore[union-attr]
            await conn.execute("SELECT 1;")
        logging.info("Database pool initialized successfully.")
    except Exception as exc:
        # Do not crash the whole app; log error. DB-required routes should handle unavailability.
        logging.error("Failed to initialize database pool: %s", exc)
        # Keep _pool as None to indicate not available
        _pool = None


# PUBLIC_INTERFACE
async def close_db_pool() -> None:
    """Close the global database pool if it exists."""
    global _pool
    if _pool is not None:
        try:
            await _pool.close()
            logging.info("Database pool closed.")
        finally:
            _pool = None


def _ensure_pool_available() -> asyncpg.Pool:
    """Internal helper to ensure pool is available or raise a clear error."""
    if _pool is None:
        raise RuntimeError(
            "Database is not initialized. Ensure DATABASE_URL is set and init_db_pool() has run."
        )
    return _pool


# PUBLIC_INTERFACE
async def fetch_one(sql: str, *params: Any) -> Optional[Dict[str, Any]]:
    """Fetch a single record as a dict or return None if no row.

    Parameters:
    - sql: The SQL query string with placeholders like $1, $2 (asyncpg style).
    - *params: The parameters to bind to the SQL query.

    Returns:
    - A dictionary representing the row, or None.
    """
    pool = _ensure_pool_available()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *params)
        if row is None:
            return None
        return dict(row)


# PUBLIC_INTERFACE
async def fetch_all(sql: str, *params: Any) -> List[Dict[str, Any]]:
    """Fetch all rows for a query as a list of dicts.

    Parameters:
    - sql: The SQL query string with placeholders like $1, $2.
    - *params: The parameters to bind to the SQL query.

    Returns:
    - List of dictionaries for each row.
    """
    pool = _ensure_pool_available()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]


# PUBLIC_INTERFACE
async def execute(sql: str, *params: Any) -> str:
    """Execute a statement (INSERT/UPDATE/DELETE) and return the status string.

    Parameters:
    - sql: The SQL statement with placeholders like $1, $2.
    - *params: The parameters to bind to the SQL statement.

    Returns:
    - The command status returned by asyncpg (e.g., 'UPDATE 1').
    """
    pool = _ensure_pool_available()
    async with pool.acquire() as conn:
        status = await conn.execute(sql, *params)
        return status


# PUBLIC_INTERFACE
async def execute_many(sql: str, param_sets: List[Tuple[Any, ...]]) -> List[str]:
    """Execute a statement for multiple parameter sets in a single connection.

    Useful for batch operations. All executions occur sequentially within a single
    acquired connection but outside an explicit transaction. Wrap with your own
    transaction if atomicity is required.

    Parameters:
    - sql: The SQL statement with placeholders.
    - param_sets: A list of tuples representing parameter sets.

    Returns:
    - List of status strings for each execution.
    """
    pool = _ensure_pool_available()
    results: List[str] = []
    async with pool.acquire() as conn:
        for params in param_sets:
            results.append(await conn.execute(sql, *params))
    return results
