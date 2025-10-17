"""Database diagnostics utility.

Checks:
- Can connect to the database using DATABASE_URL
- Prints SQLAlchemy version and server version
- Shows current Alembic head vs database revision

Usage:
    python -m src.db.diagnostics
"""

import os
from dotenv import load_dotenv
from sqlalchemy import text
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext

from .session import init_engine_and_session, _get_database_url  # type: ignore
from .session import SessionLocal

load_dotenv()


def get_current_db_revision(alembic_cfg: Config) -> str | None:
    script = ScriptDirectory.from_config(alembic_cfg)
    current_rev: str | None = None

    def _process_revision(context, revision, directives):  # type: ignore[no-untyped-def]
        nonlocal current_rev
        current_rev = revision
        return []

    def _retrieve_db_rev(rev, context):  # type: ignore[no-untyped-def]
        return []

    with EnvironmentContext(alembic_cfg, script, fn=_retrieve_db_rev, as_sql=False) as env:
        with env:
            conn = env.get_bind()
            if conn is None:
                return None
            result = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            if result:
                current_rev = result[0]
    return current_rev


def main() -> None:
    from sqlalchemy import __version__ as sa_version
    try:
        init_engine_and_session()
        assert SessionLocal is not None
        db = SessionLocal()
        try:
            server_version = db.execute(text("SELECT version()")).scalar()
            print(f"SQLAlchemy version: {sa_version}")
            print(f"Connected to: {server_version}")
        finally:
            db.close()
    except Exception as exc:
        print("Failed to connect to database.")
        print(f"Reason: {exc}")
        return

    # Alembic head and current DB revision
    alembic_cfg = Config("alembic.ini")
    alembic_head = ScriptDirectory.from_config(alembic_cfg).get_current_head()
    db_rev = get_current_db_revision(alembic_cfg)

    print(f"Alembic head: {alembic_head}")
    print(f"Database revision: {db_rev}")
    if db_rev != alembic_head:
        print("Note: Database is not at head. Run `alembic -c alembic.ini upgrade head`.")


if __name__ == "__main__":
    main()
