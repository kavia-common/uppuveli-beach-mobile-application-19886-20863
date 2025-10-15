from typing import Generator

from sqlmodel import SQLModel, Session, create_engine, select  # import select for querying

from app.core.config import settings
from app.models.booking import Booking
from app.models.user import User
from app.core.security import get_password_hash

# Create engine (SQLite by default)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


# PUBLIC_INTERFACE
def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database Session and ensures it is closed."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def seed_demo_data():
    """Seed minimal demo data if empty."""
    with Session(engine) as session:
        # Seed a demo user
        demo_email = "demo@uppuveli.com"
        # Correct SQLModel/SQLAlchemy 2.0 style select usage
        existing_user = session.exec(select(User).where(User.email == demo_email)).first()
        if not existing_user:
            demo_user = User(
                email=demo_email,
                name="Demo User",
                phone="0000000000",
                hashed_password=get_password_hash("password123"),
                is_active=True,
            )
            session.add(demo_user)
            session.commit()
            session.refresh(demo_user)

            # Seed a demo booking
            from datetime import date, timedelta

            b = Booking(
                room_id="R-101",
                guest_id=str(demo_user.id),
                check_in=date.today(),
                check_out=date.today() + timedelta(days=2),
                status="confirmed",
            )
            session.add(b)
            session.commit()
