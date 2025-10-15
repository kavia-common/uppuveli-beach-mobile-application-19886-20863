"""Security utilities for password hashing and JWT token management.

Provides:
- Password hashing and verification using passlib[bcrypt]
- JWT creation and verification using PyJWT
- FastAPI OAuth2PasswordBearer dependency for protecting routes
- Admin scope verification helpers

Environment:
- JWT_SECRET and JWT_EXPIRES_MIN are read from src.api.config.get_settings()

Notes:
- This module does not perform database access; it only handles crypto and token concerns.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt  # PyJWT
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends

from passlib.context import CryptContext

from src.api.config import get_settings

# Configure password hashing context (bcrypt)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 bearer token dependency to protect future routes
# PUBLIC_INTERFACE
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT",
    description="Include the Bearer token obtained from /api/v1/auth/login",
)


# PUBLIC_INTERFACE
def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt via passlib."""
    return _pwd_context.hash(plain_password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return _pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False


# PUBLIC_INTERFACE
def create_access_token(subject: Dict[str, Any], expires_minutes_override: Optional[int] = None) -> str:
    """Create a signed JWT access token.

    subject: dict payload that at minimum should include a 'sub' or 'user_id' claim.
    expires_minutes_override: optional expiration in minutes overriding settings.
    """
    settings = get_settings()
    expires_in_min = expires_minutes_override if expires_minutes_override is not None else settings.jwt_expires_min
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_in_min)

    payload = {
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        **subject,
    }
    token = jwt.encode(payload, settings.jwt_secret or "insecure-dev-secret", algorithm="HS256")
    return token


# PUBLIC_INTERFACE
def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token, raising HTTP 401 on errors."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret or "insecure-dev-secret", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# PUBLIC_INTERFACE
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """FastAPI dependency to extract and validate the current user from JWT token.
    
    This dependency can be used in any route that requires authentication:
    
    Example:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            user_id = current_user.get("user_id")
            return {"message": f"Hello user {user_id}"}
    
    Returns:
        Dict containing the decoded JWT payload with user claims (user_id, sub, etc.)
    
    Raises:
        HTTPException: 401 if token is invalid, expired, or missing
    """
    return decode_access_token(token)


# PUBLIC_INTERFACE
async def require_admin_scope(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """FastAPI dependency to ensure the provided bearer token has admin scope.
    
    This dependency validates that the JWT token contains 'admin' in the scope claim.
    Use this to protect admin-only endpoints.
    
    Example:
        @router.get("/admin/bookings")
        async def list_bookings(admin: dict = Depends(require_admin_scope)):
            # Only accessible with admin scope token
            return {"bookings": [...]}
    
    Returns:
        Dict containing the decoded JWT payload with admin claims
    
    Raises:
        HTTPException: 401 if token is missing, invalid, expired, or lacks admin scope
    """
    payload = decode_access_token(token)
    scope = str(payload.get("scope", ""))
    # Scope can contain space-separated scopes; ensure 'admin' present
    if "admin" not in scope.split():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin_scope_required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
