from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import hash_password, verify_password, create_access_token
from src.db.models import User
from src.db.session import get_db
from src.db.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Plain password")
    name: Optional[str] = Field(None, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Plain password")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(
        "bearer",
        description="Token type",
    )
    user: UserOut


# PUBLIC_INTERFACE
@router.post("/register", summary="Register new user", response_model=UserOut, status_code=201)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> Any:
    """Register a user by email and password.

    Returns:
        UserOut: created user.
    """
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        phone=payload.phone,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# PUBLIC_INTERFACE
@router.post("/login", summary="Authenticate user (email/password)", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """Authenticate with email/password and return JWT and user details."""
    user = (
        db.execute(select(User).where(User.email == payload.email))
        .scalar_one_or_none()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type="bearer", user=user)


# PUBLIC_INTERFACE
@router.post(
    "/token",
    summary="OAuth2 password token",
    description="Standard OAuth2 password flow token endpoint for Swagger 'Authorize'.",
    response_model=TokenResponse,
)
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Any:
    """Issue JWT for OAuth2 password flow using username as email."""
    user = (
        db.execute(select(User).where(User.email == form_data.username))
        .scalar_one_or_none()
    )
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type="bearer", user=user)
