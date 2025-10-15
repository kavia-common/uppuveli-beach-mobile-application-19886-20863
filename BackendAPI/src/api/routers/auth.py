"""Authentication routes for guest users.

Endpoints:
- POST /api/v1/auth/register: Register a new guest
- POST /api/v1/auth/login: Authenticate via email/password and receive JWT

Both endpoints align with the Mobile OpenAPI expectations.

Database:
- Requires a 'users' table with at least columns:
    id SERIAL PRIMARY KEY
    email TEXT UNIQUE NOT NULL
    name TEXT NOT NULL
    password_hash TEXT NOT NULL
    phone TEXT NULL
    loyalty_points INTEGER NOT NULL DEFAULT 0
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr

from src.api.db import fetch_one, execute
from src.api.models import (
    AuthRequest,
    GuestRegistrationRequest,
    LoginResponse,
    SuccessUserResponse,
    User,
)
from src.api.security import create_access_token, hash_password, verify_password

router = APIRouter()


async def _get_user_by_email(email: EmailStr) -> Optional[Dict[str, Any]]:
    """Fetch user record by email."""
    return await fetch_one(
        "SELECT id, email, name, password_hash, COALESCE(loyalty_points, 0) AS loyalty_points "
        "FROM users WHERE lower(email)=lower($1)",
        str(email),
    )


async def _create_user(data: GuestRegistrationRequest) -> Dict[str, Any]:
    """Insert a new user and return the row."""
    pw_hash = hash_password(data.password)
    # Try insert; rely on DB unique constraint for duplicate detection.
    await execute(
        "INSERT INTO users (email, name, password_hash, phone, loyalty_points) "
        "VALUES ($1, $2, $3, $4, $5)",
        str(data.email),
        data.name,
        pw_hash,
        data.phone,
        0,
    )
    # Return the newly created user
    created = await fetch_one(
        "SELECT id, email, name, COALESCE(loyalty_points, 0) AS loyalty_points "
        "FROM users WHERE lower(email)=lower($1)",
        str(data.email),
    )
    assert created is not None
    return created


def _row_to_user(row: Dict[str, Any]) -> User:
    """Convert DB row to API User model."""
    return User(
        id=int(row["id"]),
        email=row["email"],
        name=row["name"],
        loyaltyPoints=int(row.get("loyalty_points", 0)),
    )


# PUBLIC_INTERFACE
@router.post(
    "/register",
    tags=["auth"],
    summary="Register new guest",
    description="Creates a new guest user account. Returns the created user.",
    response_model=SuccessUserResponse,
    responses={
        200: {"description": "Success"},
        400: {"description": "Invalid input or duplicate email"},
    },
)
async def register(payload: GuestRegistrationRequest) -> SuccessUserResponse:
    """Register a new guest with email, password and name.

    Errors:
    - 400 if the email is already registered.
    """
    existing = await _get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    try:
        created = await _create_user(payload)
    except Exception as exc:
        # Likely duplicate or DB issue
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user",
        ) from exc

    user = _row_to_user(created)
    return SuccessUserResponse(status="success", data=user)


# PUBLIC_INTERFACE
@router.post(
    "/login",
    tags=["auth"],
    summary="Authenticate guest",
    description="Authenticates a guest via email/password and returns a JWT token with user info.",
    response_model=LoginResponse,
    responses={
        200: {"description": "JWT issued"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(payload: AuthRequest) -> LoginResponse:
    """Login endpoint issuing a JWT that includes user_id claim.

    Errors:
    - 401 if email not found or password mismatch.
    """
    row = await _get_user_by_email(payload.email)
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = _row_to_user(row)
    token = create_access_token({"user_id": user.id, "sub": str(user.id)})
    return LoginResponse(token=token, user=user)
