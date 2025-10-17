import time
from fastapi.testclient import TestClient
import os

from src.api.main import app

assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set for tests."

client = TestClient(app)


def test_register_and_login():
    email = f"testuser_{int(time.time())}@example.com"
    password = "password123!"

    # register
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Test"},
    )
    assert r.status_code in (201, 400)
    # If 400, user may exist if tests re-run quickly; continue to login either way

    # login
    r2 = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == email

    # oauth token endpoint
    r3 = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert r3.status_code == 200
    assert "access_token" in r3.json()
