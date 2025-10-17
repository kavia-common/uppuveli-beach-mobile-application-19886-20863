# DATABASE_URL Guide

The BackendAPI uses SQLAlchemy with the psycopg2 driver. Set the DATABASE_URL in BackendAPI/.env.

Examples:
- Local Postgres:
  DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/uppuveli_db
- Docker Compose service:
  DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/uppuveli_db
- Cloud provider (render.com, railway, etc.):
  DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require

Common issues:
- Missing driver: ensure psycopg2-binary is installed (already in requirements.txt).
- Wrong driver prefix: use postgresql+psycopg2 not postgres://
- SSL requirements: add ?sslmode=require if your provider mandates SSL.
- Network/hostnames: if running via Docker, use the container name (e.g., db) rather than localhost.

Commands:
- Apply migrations: alembic -c alembic.ini upgrade head
- Seed data: python -m src.db.seed
