import time
from fastapi.testclient import TestClient
import os

from src.api.main import app

assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set for tests."

client = TestClient(app)


def _register_and_get_token():
    email = f"rooms_{int(time.time())}@example.com"
    password = "password123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_rooms_requires_auth():
    r = client.get("/api/v1/rooms")
    assert r.status_code in (401, 403)


def test_rooms_with_auth():
    token = _register_and_get_token()
    r = client.get("/api/v1/rooms", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
