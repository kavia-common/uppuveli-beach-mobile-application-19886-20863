"""CLI utility to create or update an admin user.

This script:
1) Loads env from BackendAPI/.env (DATABASE_URL, JWT settings)
2) Connects using existing SQLAlchemy session (src.db.session)
3) Upserts an AdminUser by email
4) Sets password hash using src.core.security.hash_password
5) Optionally prints a signed admin JWT with {"admin": True}

Usage:
    python -m src.scripts.create_admin --email admin@example.com --password "Strong#Pass1"

Environment:
- DATABASE_URL, JWT_SECRET are required in BackendAPI/.env
- JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES are optional

Notes:
- Idempotent: reruns update password and flags.
- Does NOT modify application code paths; offline utility.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

# Ensure 'src' is importable whether run as a module or direct file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from sqlalchemy import select  # noqa: E402

from src.core.security import hash_password, create_access_token  # noqa: E402
from src.db.models import AdminUser  # noqa: E402
from src.db.session import init_engine_and_session, session_scope  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="create_admin",
        description="Create or update an admin user (idempotent).",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Admin user email (unique).",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Plain password to set for the admin user.",
    )
    parser.add_argument(
        "--name",
        required=False,
        default="Administrator",
        help='Display name for the admin user (default: "Administrator").',
    )
    parser.add_argument(
        "--superuser",
        action="store_true",
        help="Mark admin as superuser.",
    )
    parser.add_argument(
        "--print-token",
        action="store_true",
        help="Also print a JWT for quick testing (contains admin=true).",
    )
    return parser.parse_args()


def main() -> None:
    # init_engine_and_session reads DATABASE_URL via src.db.session
    try:
        init_engine_and_session()
    except Exception:
        print(
            "Failed to initialize DB engine/session. "
            "Ensure DATABASE_URL is set in BackendAPI/.env."
        )
        raise

    args = _parse_args()
    email: str = args.email.strip().lower()
    plain_password: str = args.password
    name: Optional[str] = args.name
    is_superuser: bool = bool(args.superuser)

    if not email or "@" not in email:
        print("Invalid --email provided.")
        sys.exit(2)
    if not plain_password:
        print("Empty --password provided.")
        sys.exit(2)

    password_hash = hash_password(plain_password)

    # Upsert admin by email
    with session_scope() as db:
        existing = (
            db.execute(select(AdminUser).where(AdminUser.email == email))
            .scalar_one_or_none()
        )
        if existing:
            # Update password and optional flags; keep name if none provided
            existing.password_hash = password_hash
            if name:
                existing.name = name
            if is_superuser:
                existing.is_superuser = True
            db.add(existing)
            db.flush()
            admin = existing
            created = False
        else:
            admin = AdminUser(
                email=email,
                password_hash=password_hash,
                name=name or "Administrator",
                is_superuser=is_superuser,
            )
            db.add(admin)
            db.flush()
            created = True

        # Compose success message
        action = "created" if created else "updated"
        print(
            f"Success: admin user {action}: {admin.email} "
            f"(id={admin.id}, superuser={admin.is_superuser})"
        )

        if args.print_token:
            # Generate a token with admin claim for immediate testing
            token = create_access_token(subject=admin.id, extra_claims={"admin": True})
            print("Admin JWT (bearer):")
            print(token)


if __name__ == "__main__":
    main()
