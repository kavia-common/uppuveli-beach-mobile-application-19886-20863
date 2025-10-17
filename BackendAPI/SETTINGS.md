# BackendAPI Settings

Configuration is provided via environment variables loaded from `.env` using python-dotenv.

Primary variables:
- DATABASE_URL
- JWT_SECRET
- JWT_ALGORITHM (default HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES (default 60)
- OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET (optional)
- STRIPE_API_KEY, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET (optional)
- FCM_SERVER_KEY (optional)

Access settings in code:
- from src.api.settings import get_settings
- settings = get_settings()
- Use settings.DATABASE_URL, settings.JWT_SECRET, etc.

Notes:
- Do not commit actual secrets. Use .env locally and CI secret managers in deployment.
- The DB schema is managed by Alembic migrations; the app does not auto-create tables.
