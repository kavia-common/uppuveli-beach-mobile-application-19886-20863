import os
from contextlib import contextmanager
from typing import Iterator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

# Ensure deterministic testing environment
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("SEED_DEMO", "false")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("DATABASE_URL", "sqlite://")  # not used directly since we override engine

from app.main import create_app  # noqa: E402
from app.db import get_session as prod_get_session  # noqa: E402
from app.core import security as security_module  # noqa: E402
from app.core.config import get_settings  # noqa: E402

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite://"

# Create a dedicated test engine (check_same_thread False for TestClient threads)
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


def create_db():
    """Create all tables in the in-memory database."""
    SQLModel.metadata.create_all(test_engine)


@contextmanager
def get_test_session() -> Iterator[Session]:
    """Yield a session bound to the in-memory test engine."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def _prepare_db() -> Generator[None, None, None]:
    """Create tables once per test session."""
    create_db()
    yield


@pytest.fixture()
def app():
    """
    Build a fresh FastAPI app per test function with dependency overrides:
    - Override get_session to use in-memory session
    - Freeze JWT settings via env already set above
    """
    # Clear cached settings to pick up env overrides within tests if needed
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass

    application = create_app()

    # Override DB session dependency
    application.dependency_overrides[prod_get_session] = get_test_session

    # Optionally, ensure oauth2 tokenUrl remains consistent
    security_module.oauth2_scheme.model.tokenUrl = "/auth/login"

    return application


@pytest.fixture()
def client(app) -> TestClient:
    """Return a TestClient bound to the overridden app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def register_user(client):
    """Helper to register a user; returns dict with created user's info and plaintext password."""
    def _create(email: str = "alice@example.com", password: str = "password123", name: str = "Alice"):
        payload = {"email": email, "password": password, "name": name, "phone": "1234567890"}
        resp = client.post("/auth/register", json=payload)
        # 200 on success; 400 if already exists. For idempotent tests we handle both.
        if resp.status_code == 200:
            data = resp.json()["data"]
            return {"email": data["email"], "id": data["id"], "name": data["name"], "password": password}
        elif resp.status_code == 400:
            # Already registered; still return identity
            return {"email": email, "id": None, "name": name, "password": password}
        else:
            pytest.fail(f"Unexpected status during register: {resp.status_code}, body={resp.text}")
    return _create


@pytest.fixture()
def auth_token(client, register_user):
    """Register a user and return a Bearer token string."""
    user = register_user()
    resp = client.post("/auth/login", json={"email": user["email"], "password": user["password"]})
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]
    return f"Bearer {token}"
