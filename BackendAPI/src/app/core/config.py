import os
from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env if present
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    JWT_SECRET: str = Field(default=os.getenv("JWT_SECRET", "dev-insecure-secret"))
    JWT_ALGORITHM: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./app.db"))
    SEED_DEMO: bool = Field(default=(os.getenv("SEED_DEMO", "true").lower() == "true"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

openapi_tags = [
    {"name": "Auth", "description": "Authentication and user onboarding."},
    {"name": "Bookings", "description": "Manage room bookings."},
    {"name": "Payments", "description": "Process and view booking payments."},
    {"name": "Health", "description": "Health and diagnostics."},
]
