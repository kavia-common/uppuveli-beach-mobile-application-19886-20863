from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.api.config import get_settings
from src.api.db import init_db_pool, close_db_pool

# Initialize settings
settings = get_settings()

# FastAPI application with metadata and tags
app = FastAPI(
    title="Uppuveli Beach API",
    description="Backend API for Uppuveli Beach mobile app and admin panel.",
    version="0.1.0",
    contact={"name": "Uppuveli Beach by DSK", "url": "https://uppuvelibeach.com"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {"name": "health", "description": "Service health and diagnostics"},
        {"name": "auth", "description": "Authentication and token management"},
        {"name": "bookings", "description": "Bookings operations"},
        {"name": "payments", "description": "Payments processing"},
        {"name": "loyalty", "description": "Loyalty and referrals"},
        {"name": "notifications", "description": "Notifications and messaging"},
        {"name": "chat", "description": "Chat and chatbot"},
        {"name": "admin", "description": "Admin operations for Web Admin Panel"},
    ],
)

# Configure CORS using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup/shutdown hooks to manage database connection pool
@app.on_event("startup")
async def _on_startup() -> None:
    """Initialize resources like the database connection pool."""
    await init_db_pool()


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    """Cleanly release resources such as the database pool."""
    await close_db_pool()


# Routers
from src.api.routers import auth  # type: ignore
from src.api.routers import admin_oauth  # type: ignore
from src.api.routers import rooms, bookings, payments, loyalty, referrals, notifications, chat  # type: ignore
from src.api.routers import admin_bookings  # type: ignore

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# Admin OAuth2 mock flow (authorization, token) and admin profile endpoint
app.include_router(admin_oauth.router, prefix="/api/v1", tags=["auth"])

# Mobile endpoints
app.include_router(rooms.router, prefix="/api/v1/rooms", tags=["bookings"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
# Admin endpoints (require admin OAuth token scope='admin'); same resource path space for CRUD by admins
app.include_router(admin_bookings.router, prefix="/api/v1/bookings", tags=["admin"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(loyalty.router, prefix="/api/v1/loyalty", tags=["loyalty"])
app.include_router(referrals.router, prefix="/api/v1/referrals", tags=["loyalty"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Returns service status to indicate the API is running.",
    responses={200: {"description": "Service is healthy"}},
)
def health_check() -> Dict[str, str]:
    """Health check endpoint returning a simple status message."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/api/v1/health",
    tags=["health"],
    summary="Detailed health status",
    description="Returns detailed service health including environment and allowed origins.",
    responses={
        200: {
            "description": "Detailed health",
            "content": {"application/json": {}},
        }
    },
)
def detailed_health() -> JSONResponse:
    """Detailed health endpoint with minimal env info (non-sensitive)."""
    payload = {
        "status": "ok",
        "env": settings.app_env,
        "cors_origins": settings.cors_origins,
        "port": settings.app_port,
    }
    return JSONResponse(payload)


# Entrypoint note:
# Run with: uvicorn src.api.main:app --host 0.0.0.0 --port 3001
# The default port is governed by APP_PORT in .env, but uvicorn CLI overrides apply.
