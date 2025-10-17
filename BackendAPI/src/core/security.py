from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from src.api.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a stored hash."""
    return pwd_context.verify(plain_password, password_hash)


# PUBLIC_INTERFACE
def create_access_token(
    subject: str | int,
    expires_minutes: Optional[int] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: user id or unique identifier
        expires_minutes: optional minutes to expire; defaults from settings
        extra_claims: additional claims to embed

    Returns:
        Signed JWT string.
    """
    settings = get_settings()
    if expires_minutes is None:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=int(expires_minutes))
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


# PUBLIC_INTERFACE
def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising on invalid tokens."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
