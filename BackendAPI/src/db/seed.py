"""Seed the database with initial data.

Creates:
- One admin user
- A few sample rooms

Usage:
    python -m src.db.seed
"""

import os

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import select

from .models import AdminUser, Room
from .session import init_engine_and_session, session_scope

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def seed_admin_user() -> None:
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@uppuvelibeach.com")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "change_me_admin")
    with session_scope() as db:
        existing = (
            db.execute(
                select(AdminUser).where(AdminUser.email == admin_email)
            ).scalar_one_or_none()
        )
        if existing:
            return
        admin = AdminUser(
            email=admin_email,
            password_hash=_hash_password(admin_password),
            name="Administrator",
            is_superuser=True,
        )
        db.add(admin)


def seed_rooms() -> None:
    sample_rooms = [
        dict(room_number="101", room_type="Deluxe Sea View", price=150.00, is_available=True),
        dict(room_number="102", room_type="Standard Garden View", price=90.00, is_available=True),
        dict(room_number="201", room_type="Suite Ocean Front", price=250.00, is_available=True),
    ]
    with session_scope() as db:
        existing_numbers = {r[0] for r in db.query(Room.room_number).all()}
        for r in sample_rooms:
            if r["room_number"] in existing_numbers:
                continue
            room = Room(**r)
            db.add(room)


def main() -> None:
    # Ensure engine/session are initialized
    init_engine_and_session()
    # Note: Tables should be created via Alembic migrations prior to seeding.
    seed_admin_user()
    seed_rooms()


if __name__ == "__main__":
    main()
