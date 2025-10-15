"""API models and schemas for BackendAPI.

Contains:
- Auth request/response models for guest registration and login
- Minimal User model for public API responses from auth endpoints
"""
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    """Represents a guest user returned to clients."""
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    name: str = Field(..., description="Full name")
    loyaltyPoints: int = Field(0, description="Current loyalty points")


# PUBLIC_INTERFACE
class GuestRegistrationRequest(BaseModel):
    """Request body to register a new guest user."""
    email: EmailStr = Field(..., description="Guest email")
    password: str = Field(..., description="Guest password (plaintext; will be hashed)")
    name: str = Field(..., description="Guest full name")
    phone: Optional[str] = Field(default=None, description="Phone number")


# PUBLIC_INTERFACE
class AuthRequest(BaseModel):
    """Request body to authenticate a guest user via email/password."""
    email: EmailStr = Field(..., description="Guest email")
    password: str = Field(..., description="Guest plaintext password")


# PUBLIC_INTERFACE
class LoginResponse(BaseModel):
    """Response for successful login: returns token and user."""
    token: str = Field(..., description="JWT bearer token")
    user: User = Field(..., description="Authenticated user info")


# PUBLIC_INTERFACE
class SuccessUserResponse(BaseModel):
    """Generic success response that returns the user object."""
    status: str = Field("success", description="Status indicator", const=True)
    data: User = Field(..., description="User object")
