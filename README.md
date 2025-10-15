# uppuveli-beach-mobile-application-19886-20863

This repository contains multiple containers: MobileApplication (Flutter), WebAdminPanel (React), BackendAPI (FastAPI), and Database (PostgreSQL).

BackendAPI bootstrap:
- Environment variables are read from BackendAPI/.env via python-dotenv.
- CORS is enabled for local web and mobile dev origins.
- Health endpoints:
  - GET / -> { "message": "Healthy" }
  - GET /api/v1/health -> detailed status payload

Admin OAuth2 (Mock) for Web Admin Panel:
- Endpoints (mounted under /api/v1):
  - GET /oauth/authorize
    - Query: response_type=code, client_id, redirect_uri, scope=admin (default), state (optional)
    - Validates client_id and redirect_uri against ADMIN_OAUTH_CLIENTS.
    - Redirects to redirect_uri with ?code=...&state=...
  - POST /oauth/token
    - Body: { grant_type: "authorization_code", code, redirect_uri, client_id, client_secret? }
    - Exchanges code for a JWT bearer access_token with scope "admin".
  - GET /admin/me
    - Requires Authorization: Bearer <token>.
    - Returns the token claims (mock admin identity).
- This is a mock for local/dev integration with the Web Admin Panel. Not for production.
- Configure clients via ADMIN_OAUTH_CLIENTS env var (JSON array). Example:
  ADMIN_OAUTH_CLIENTS='[{"provider":"mock","client_id":"admin-web","client_secret":"dev-secret"}]'

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

Mobile API endpoints (JWT protected)
- GET /api/v1/rooms
- POST /api/v1/bookings
- POST /api/v1/payments
- GET /api/v1/loyalty
- POST /api/v1/referrals
- GET /api/v1/notifications
- POST /api/v1/chat