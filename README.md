# Uppuveli Beach Platform

This monorepo includes multiple containers:
- MobileApplication (Flutter)
- BackendAPI (FastAPI)
- WebAdminPanel (React)

This document includes BackendAPI database setup instructions.

## BackendAPI - Database Setup (PostgreSQL + SQLAlchemy + Alembic)

1) Create and configure a .env file
- Copy BackendAPI/.env.example to BackendAPI/.env
- Update DATABASE_URL and secrets as appropriate

Env variables required:
- DATABASE_URL
- JWT_SECRET
- JWT_ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES
- OAUTH_CLIENT_ID
- OAUTH_CLIENT_SECRET
- STRIPE_API_KEY
- PAYPAL_CLIENT_ID
- PAYPAL_CLIENT_SECRET
- FCM_SERVER_KEY

2) Install dependencies (within BackendAPI directory)
- pip install -r requirements.txt

3) Initialize the database via Alembic
- Ensure your DATABASE_URL points to a reachable Postgres instance
- Run:
  alembic -c alembic.ini upgrade head

4) Seed initial data
- Run:
  python -m src.db.seed
This will create one admin user and a few sample rooms.

5) Run the API
- uvicorn src.api.main:app --reload

Notes:
- The application uses synchronous SQLAlchemy with psycopg2.
- Migrations manage schema. Do not create tables at startup.
- DB session dependency is available as src.db.session.get_db for route handlers.

Project structure (BackendAPI relevant):
- src/db/models.py     -> SQLAlchemy models
- src/db/session.py    -> Engine/session and FastAPI dependency
- src/db/seed.py       -> Seed script
- alembic/             -> Migrations
- alembic.ini          -> Alembic config
- src/api/main.py      -> FastAPI app
- src/api/generate_openapi.py -> Script to export OpenAPI schema to interfaces/openapi.json
- interfaces/openapi.json     -> Generated API spec (run `make openapi` to refresh)