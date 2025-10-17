from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.session import init_engine_and_session, get_db, Base


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
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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

    return app


# Instantiate the app for ASGI servers and OpenAPI generation
app = create_app()

# Re-export get_db for routers to depend on
__all__ = ["app", "get_db", "Base", "create_app"]
