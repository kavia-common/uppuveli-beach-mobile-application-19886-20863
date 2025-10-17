# BackendAPI Database Checklist

Use this checklist to verify the DB setup for the BackendAPI.

- [ ] Environment
  - [ ] Copy .env.example to .env
  - [ ] Set DATABASE_URL to a reachable Postgres instance (e.g., postgresql+psycopg2://user:pass@localhost:5432/db)
  - [ ] Set JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

- [ ] Dependencies
  - [ ] pip install -r requirements.txt
  - [ ] psycopg2-binary installed for local development

- [ ] Migrations (Alembic)
  - [ ] alembic -c alembic.ini upgrade head runs without errors
  - [ ] Tables created: users, admin_users, rooms, bookings, payments, loyalty_accounts, loyalty_history, referrals, notifications, chat_messages, boutique_items

- [ ] Seed data
  - [ ] python -m src.db.seed
  - [ ] Confirm admin user exists (email from SEED_ADMIN_EMAIL)
  - [ ] Confirm sample rooms inserted (101, 102, 201)

- [ ] Runtime
  - [ ] uvicorn src.api.main:app --reload
  - [ ] GET / returns {"message": "Healthy"}

- [ ] Project references
  - [ ] Use src.db.session.get_db in routes for DB sessions
  - [ ] Do not create tables at startup; use Alembic migrations

Troubleshooting:
- If alembic cannot import src modules, ensure BackendAPI/src is on PYTHONPATH or run commands from BackendAPI directory.
- Verify DATABASE_URL matches installed driver (psycopg2 for sync).
