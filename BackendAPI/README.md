# BackendAPI - FastAPI + SQLAlchemy + Alembic

This service powers the Uppuveli Beach platform backend.

## Quick start

1) Create .env
- cp .env.example .env
- Update DATABASE_URL and secrets

2) Install dependencies
- pip install -r requirements.txt

3) Run migrations
- alembic -c alembic.ini upgrade head

4) Seed data
- python -m src.db.seed

5) Run dev server
- uvicorn src.api.main:app --reload

## Common commands

- Create new migration (after model change):
  alembic -c alembic.ini revision --autogenerate -m "your message"

- Downgrade last migration:
  alembic -c alembic.ini downgrade -1

- Generate OpenAPI file:
  python -m src.api.generate_openapi

## Troubleshooting

- DATABASE_URL not set
  Ensure BackendAPI/.env contains DATABASE_URL and that your Postgres is reachable.

- psycopg2 build issues
  Use psycopg2-binary for local/dev (already in requirements.txt).

- Alembic can't find metadata
  Ensure imports in alembic/env.py reference src.db.models:Base correctly.

- Migrations vs. runtime
  Do not create tables at startup; always use Alembic.
