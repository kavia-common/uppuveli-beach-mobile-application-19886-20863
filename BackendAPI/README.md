# BackendAPI - FastAPI + SQLAlchemy + Alembic

This service powers the Uppuveli Beach platform backend.

## Quick start

1) Create .env
- cp .env.example .env
- Update DATABASE_URL and secrets (JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES, etc.)

2) Install dependencies
- pip install -r requirements.txt

3) Run migrations
- alembic -c alembic.ini upgrade head

4) Seed data
- python -m src.db.seed

5) Run dev server
- uvicorn src.api.main:app --reload

### Create an Admin User (CLI)
Use the management script to create or update an admin user (idempotent). It reads DATABASE_URL and JWT settings from BackendAPI/.env.

Options:
- --email: admin email (required)
- --password: plain password (required)
- --name: display name (optional, default "Administrator")
- --superuser: mark as superuser (optional)
- --print-token: also print a JWT containing {"admin": true} (optional)

Run directly:
- python -m src.scripts.create_admin --email admin@uppuveli.com --password 'CHANGEME' --superuser --print-token

Or via Makefile:
- make create-admin EMAIL=admin@uppuveli.com PASSWORD='CHANGEME' SUPERUSER=1 PRINT_TOKEN=1

Security notes:
- Do not commit credentials to the repo.
- Ensure BackendAPI/.env contains DATABASE_URL and JWT_SECRET.
- The script is safe to run multiple times; it will update the password if the admin already exists.

6) Generate OpenAPI JSON
- python -m src.api.generate_openapi
- The file is written to interfaces/openapi.json
- Alternatively: make openapi

CORS:
- Ensure the backend allows development origins:
  - http://localhost:3000 (WebAdminPanel)
  - http://localhost:3001 (direct calls)
  - http://10.0.2.2 and http://10.0.2.2:3001 (Android emulator to host)

Health:
- GET / -> {"message": "Healthy"}
- Use this to verify the service is running before mobile/web integration

## API Overview (prefix /api/v1)

- Health:
  - GET / -> {"message": "Healthy"}

- Auth:
  - POST /api/v1/auth/register -> Create a user (201)
  - POST /api/v1/auth/login -> JWT and user data (200)
  - POST /api/v1/auth/token -> OAuth2 password token (200), for Swagger Authorize

- Rooms (auth required):
  - GET /api/v1/rooms -> List rooms (200)

- Bookings (auth required):
  - POST /api/v1/bookings -> Create a booking (201)

- Payments (auth required, stubbed):
  - POST /api/v1/payments -> Process payment and persist Payment (201)

- Loyalty (auth required):
  - GET /api/v1/loyalty -> Current user's loyalty and history (200)

- Referrals (auth required):
  - POST /api/v1/referrals -> Redeem referral code (200)

- Notifications (auth required):
  - GET /api/v1/notifications -> List user notifications (200)

- Chat (auth required):
  - POST /api/v1/chat -> Echo message and persist chat entry (200)

- Admin (scaffold):
  - Use admin JWTs with "admin": true claim (future admin endpoints will require it).

Security:
- OAuth2 password flow supported via /api/v1/auth/token
- Bearer JWT required for protected endpoints

CORS:
- Allowed origins include http://localhost:3000 and common mobile dev hosts.

## Running tests

- Ensure DATABASE_URL points to a reachable Postgres with the schema migrated.
- Run: pytest

Tests included:
- tests/test_health.py
- tests/test_auth.py
- tests/test_rooms.py

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
