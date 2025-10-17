# Uppuveli Beach Platform

This monorepo includes multiple containers:
- MobileApplication (Flutter)
- BackendAPI (FastAPI)
- WebAdminPanel (React)

This document includes BackendAPI setup and pointers.

## BackendAPI

- API base path: /api/v1
- Health: GET /
- See BackendAPI/README.md for detailed run instructions and endpoint descriptions.
- Generate OpenAPI: python -m src.api.generate_openapi -> BackendAPI/interfaces/openapi.json
  - Or run: (cd BackendAPI && make openapi) if Makefile available

Cross-container integration checklist:
- BackendAPI CORS allows:
  - http://localhost:3000 (WebAdminPanel)
  - http://localhost:3001 (tools/local calls)
  - http://10.0.2.2 and http://10.0.2.2:3001 (Android emulator)
- Base URLs include /api/v1:
  - MobileApplication: API_BASE_URL in MobileApplication/.env (e.g., http://10.0.2.2:3001/api/v1)
  - WebAdminPanel: REACT_APP_API_BASE_URL in WebAdminPanel/.env (e.g., http://localhost:3001/api/v1)
- Health endpoint:
  - curl http://localhost:3001/ -> {"message":"Healthy"}

Database setup summary (PostgreSQL + SQLAlchemy + Alembic):
1) Copy BackendAPI/.env.example to BackendAPI/.env and fill DATABASE_URL and JWT settings
2) pip install -r BackendAPI/requirements.txt
3) Run migrations: (cd BackendAPI && alembic -c alembic.ini upgrade head)
4) Seed sample data: (cd BackendAPI && python -m src.db.seed)
5) Run server: (cd BackendAPI && uvicorn src.api.main:app --reload)

Project structure (BackendAPI relevant):
- src/db/models.py     -> SQLAlchemy models
- src/db/session.py    -> Engine/session and FastAPI dependency
- src/db/seed.py       -> Seed script
- alembic/             -> Migrations
- alembic.ini          -> Alembic config
- src/api/main.py      -> FastAPI app and routers
- src/api/routes/      -> Endpoint implementations
- src/core/security.py -> JWT and password hashing
- src/api/generate_openapi.py -> Exports OpenAPI schema
- interfaces/openapi.json     -> Generated API spec (run `make openapi` to refresh)