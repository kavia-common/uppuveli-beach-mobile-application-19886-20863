from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.db.session import init_engine_and_session, get_db, Base
from src.api.settings import get_settings

# Routers
from src.api.routes.auth import router as auth_router
from src.api.routes.rooms import router as rooms_router
from src.api.routes.bookings import router as bookings_router
from src.api.routes.payments import router as payments_router
from src.api.routes.loyalty import router as loyalty_router
from src.api.routes.referrals import router as referrals_router
from src.api.routes.notifications import router as notifications_router
from src.api.routes.chat import router as chat_router


# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This sets up CORS, initializes the database engine and session factory
    using the DATABASE_URL from environment variables (loaded via dotenv),
    and ensures metadata is available for migrations and runtime operations.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Uppuveli Beach Backend API",
        description="FastAPI backend for Uppuveli Beach platform",
        version="1.0.0",
        openapi_tags=[
            {"name": "Health", "description": "Service health endpoints"},
            {"name": "Auth", "description": "User registration and authentication"},
            {"name": "Rooms", "description": "Rooms listing and details"},
            {"name": "Bookings", "description": "Bookings management"},
            {"name": "Payments", "description": "Payments processing (stubbed)"},
            {"name": "Loyalty", "description": "Loyalty points and history"},
            {"name": "Referrals", "description": "Referral program operations"},
            {"name": "Notifications", "description": "User notifications"},
            {"name": "Chat", "description": "Chatbot/live chat"},
            {"name": "Admin", "description": "Administrative operations (scaffold)"},
        ],
    )

    settings = get_settings()
    # Access a field to avoid unused-variable lint while ensuring settings are loaded
    _ = settings.JWT_ALGORITHM
    # CORS allow localhost and dev hosts
    allowed_origins = [
        # Web Admin Panel (React dev server)
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Backend local direct calls (some tools)
        "http://localhost",
        "http://127.0.0.1",
        # Android emulator loopback to host machine
        "http://10.0.2.2",
        "http://10.0.2.2:3000",
        "http://10.0.2.2:3001",
        # Common alternate ports for backend during dev
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        # Initialize DB engine and session factory
        init_engine_and_session()
        # Note: We don't create tables here; Alembic manages schema via migrations.

    @app.get("/", summary="Health check", tags=["Health"])
    def health_check():
        """Return simple health status for liveness probes."""
        return {"message": "Healthy"}

    # Mount versioned API with prefix /api/v1
    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(rooms_router, prefix=api_prefix)
    app.include_router(bookings_router, prefix=api_prefix)
    app.include_router(payments_router, prefix=api_prefix)
    app.include_router(loyalty_router, prefix=api_prefix)
    app.include_router(referrals_router, prefix=api_prefix)
    app.include_router(notifications_router, prefix=api_prefix)
    app.include_router(chat_router, prefix=api_prefix)

    # override openapi to ensure stable schema file generation
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[assignment]

    return app


# Instantiate the app for ASGI servers and OpenAPI generation
app = create_app()

# Re-export get_db for routers to depend on
__all__ = ["app", "get_db", "Base", "create_app"]
