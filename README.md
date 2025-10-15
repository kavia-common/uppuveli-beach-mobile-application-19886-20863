# Uppuveli Beach Mobile Application

This repository contains the BackendAPI (FastAPI) service powering the Uppuveli Beach mobile app.

How to run BackendAPI locally:
1. cd BackendAPI
2. Create a virtualenv and install requirements:
   - python -m venv .venv && source .venv/bin/activate
   - pip install -r requirements.txt
3. Copy environment example:
   - cp .env.example .env
4. Start the API:
   - uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload --app-dir src

OpenAPI Docs (when running):
- http://localhost:3001/docs
- http://localhost:3001/openapi.json

Implemented endpoints:
- POST /auth/register
- POST /auth/login
- GET /bookings?limit=20&offset=0 (requires Bearer token)
- POST /bookings (requires Bearer token)
- POST /payments (requires Bearer token) — process a payment for a booking
- GET /payments/{booking_id} (requires Bearer token) — list payments for a booking

Auth
- JWT Bearer tokens with OAuth2 password flow (token issued by /auth/login)
- Provide Authorization: Bearer <token> header for protected routes

Standardized responses:
- SuccessResponse: {"status": "success", "data": ...}
- ErrorResponse: {"error_code": "...", "message": "...", "details": {...?}}

Notes:
- SQLite used via SQLModel; demo seed user: demo@uppuveli.com / password123 (if SEED_DEMO=true)
- CORS is permissive for now.

Tests
- Run test suite:
  - cd BackendAPI
  - CI=true pytest -q --maxfail=1 --disable-warnings
- Tests use an in-memory SQLite database and do not touch production data.
- Env overrides during tests: TESTING=true and SEED_DEMO=false; JWT secret and expiry set to test-safe values.
