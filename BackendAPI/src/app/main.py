import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings, openapi_tags
from app.schemas.common import ErrorResponse
from app.api.routes import auth as auth_routes
from app.api.routes import bookings as bookings_routes
from app.api.routes import payments as payments_routes
from app.db import create_db_and_tables, seed_demo_data


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title="Uppuveli Beach Mobile API",
        version="1.0.0",
        description=(
            "Comprehensive RESTful API for Uppuveli Beach Mobile Application, supporting guest registration, "
            "authentication, bookings, payments, loyalty, referrals, notifications, chat, guides, and boutique shopping. "
            "All endpoints require OAuth2/JWT authentication and return standardized JSON responses."
        ),
        openapi_tags=openapi_tags,
        servers=[{"url": "https://api.uppuvelibeach.com/api/v1"}],
    )

    # Permissive CORS for now (can be restricted later)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
    app.include_router(bookings_routes.router, prefix="/bookings", tags=["Bookings"])
    app.include_router(payments_routes.router, prefix="/payments", tags=["Payments"])

    # Health check
    @app.get("/", tags=["Health"], summary="Health Check")
    # PUBLIC_INTERFACE
    def health_check() -> dict:
        """Simple health check endpoint."""
        return {"message": "Healthy", "timestamp": datetime.utcnow().isoformat()}

    # Global exception handlers to standardize error response shape
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error_code=str(exc.status_code), message=exc.detail).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error_code="internal_error", message="Internal Server Error").model_dump(),
        )

    return app


app = create_app()


# Startup events: create tables and seed demo data if enabled
@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    if settings.SEED_DEMO:
        seed_demo_data()


# For uvicorn execution when needed:
if __name__ == "__main__":
    # Bind to port 3001 for the preview system
    import uvicorn

    port = int(os.getenv("PORT", "3001"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
