import json
import logging
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError
from pydantic import field_validator  # pydantic v2
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class OAuthClient(BaseModel):
    """Represents an Admin OAuth client configuration."""
    provider: str = Field(..., description="OAuth provider name, e.g., google, azuread")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    app_host: str = Field(default=os.getenv("APP_HOST", "0.0.0.0"), description="Host interface to bind")
    app_port: int = Field(default=int(os.getenv("APP_PORT", "3001")), description="Port to listen on")
    app_env: str = Field(default=os.getenv("APP_ENV", "development"), description="Environment name")

    database_url: str = Field(default=os.getenv("DATABASE_URL", ""), description="Database connection URL")

    jwt_secret: str = Field(default=os.getenv("JWT_SECRET", ""), description="JWT signing secret")
    jwt_expires_min: int = Field(default=int(os.getenv("JWT_EXPIRES_MIN", "60")), description="JWT expiration in minutes")

    cors_origins: List[str] = Field(default=None, description="List of allowed CORS origins")

    # Raw JSON string for admin OAuth clients
    admin_oauth_clients_raw: str = Field(default=os.getenv("ADMIN_OAUTH_CLIENTS", "[]"))
    admin_oauth_clients: List[OAuthClient] = Field(default_factory=list, description="Parsed admin OAuth clients")

    stripe_key: Optional[str] = Field(default=os.getenv("STRIPE_KEY"), description="Stripe API secret key")
    paypal_key: Optional[str] = Field(default=os.getenv("PAYPAL_KEY"), description="PayPal client secret")
    fcm_key: Optional[str] = Field(default=os.getenv("FCM_KEY"), description="Firebase Cloud Messaging server key")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        # Accept already-parsed list
        if isinstance(v, list) and v:
            return v
        # If None or empty, get from environment
        raw = os.getenv("CORS_ORIGINS", "")
        if not raw:
            # Reasonable defaults for local dev (web and mobile)
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "capacitor://localhost",
                "ionic://localhost",
            ]
        return [item.strip() for item in raw.split(",") if item.strip()]

    def __init__(self, **data):
        # Ensure .env is loaded before initializing
        load_dotenv()
        super().__init__(**data)

    @field_validator("admin_oauth_clients", mode="before")
    @classmethod
    def parse_admin_oauth_clients(cls, v):
        if isinstance(v, list):
            return v
        raw = os.getenv("ADMIN_OAUTH_CLIENTS", "[]")
        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("ADMIN_OAUTH_CLIENTS must be a JSON array")
            return data
        except json.JSONDecodeError as e:
            logging.warning("Failed to parse ADMIN_OAUTH_CLIENTS JSON: %s", e)
            return []

    @field_validator("database_url")
    @classmethod
    def require_database_url(cls, v):
        # Database URL may be empty at bootstrap; do not enforce hard requirement yet.
        return v

    @field_validator("jwt_secret")
    @classmethod
    def warn_if_empty_jwt_secret(cls, v):
        if not v:
            logging.warning("JWT_SECRET is not set. Do not use this in production.")
        return v


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return cached application settings loaded from environment variables."""
    return _cached_settings()


@lru_cache()
def _cached_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        # Log and re-raise to fail fast on invalid configuration
        logging.error("Configuration validation error: %s", e)
        raise
