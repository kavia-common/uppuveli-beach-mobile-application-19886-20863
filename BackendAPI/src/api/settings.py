"""Application settings loader.

Loads environment variables from .env (via python-dotenv) and exposes
typed accessors for configuration commonly needed across the BackendAPI.

Note: Do not hardcode secrets. Ensure a .env file is provided in BackendAPI/.
"""

from functools import lru_cache
import os
from typing import Optional

from dotenv import load_dotenv

# Eagerly load .env when the module is imported
load_dotenv()


class Settings:
    """Runtime settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # JWT / Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # OAuth
    OAUTH_CLIENT_ID: Optional[str]
    OAUTH_CLIENT_SECRET: Optional[str]

    # Payments
    STRIPE_API_KEY: Optional[str]
    PAYPAL_CLIENT_ID: Optional[str]
    PAYPAL_CLIENT_SECRET: Optional[str]

    # Push notifications
    FCM_SERVER_KEY: Optional[str]

    def __init__(self) -> None:
        self.DATABASE_URL = self._require("DATABASE_URL")

        self.JWT_SECRET = self._require("JWT_SECRET")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

        self.OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
        self.OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

        self.STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
        self.PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
        self.PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

        self.FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")

    @staticmethod
    def _require(key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return value


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance loaded from environment variables."""
    return Settings()
