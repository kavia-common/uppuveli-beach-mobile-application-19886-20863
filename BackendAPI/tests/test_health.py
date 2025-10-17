from fastapi.testclient import TestClient
import os

from src.api.main import app

# Ensure DATABASE_URL is present for test environment
assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set for tests (e.g., to a local Postgres)."

client = TestClient(app)


def test_health():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Healthy"
