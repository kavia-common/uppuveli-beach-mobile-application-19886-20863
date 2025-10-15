# uppuveli-beach-mobile-application-19886-20863

This repository contains multiple containers: MobileApplication (Flutter), WebAdminPanel (React), BackendAPI (FastAPI), and Database (PostgreSQL).

BackendAPI bootstrap:
- Environment variables are read from BackendAPI/.env via python-dotenv.
- CORS is enabled for local web and mobile dev origins.
- Health endpoints:
  - GET / -> { "message": "Healthy" }
  - GET /api/v1/health -> detailed status payload

How to run BackendAPI locally:
1) Copy the example env and edit values as needed:
   cp BackendAPI/.env.example BackendAPI/.env

2) (Optional) Create a virtualenv and install dependencies:
   cd BackendAPI
   pip install -r requirements.txt

3) Start the server on port 3001:
   uvicorn src.api.main:app --host 0.0.0.0 --port 3001

CORS
- The default allowed origins include:
  http://localhost:3000, http://127.0.0.1:3000, capacitor://localhost, ionic://localhost
- To customize, set CORS_ORIGINS as a comma-separated list in BackendAPI/.env.

Configuration
- See BackendAPI/.env.example for all supported variables:
  DATABASE_URL, JWT_SECRET, JWT_EXPIRES_MIN, CORS_ORIGINS, ADMIN_OAUTH_CLIENTS, STRIPE_KEY, PAYPAL_KEY, FCM_KEY, APP_HOST, APP_PORT, APP_ENV.

OpenAPI
- Generate OpenAPI schema file:
  cd BackendAPI && python -m src.api.generate_openapi
  Output will be at BackendAPI/interfaces/openapi.json