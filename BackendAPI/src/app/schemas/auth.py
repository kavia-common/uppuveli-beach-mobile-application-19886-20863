from pydantic import BaseModel, EmailStr, Field


class GuestRegistrationRequest(BaseModel):
    """Guest registration payload."""

    email: EmailStr = Field(..., description="Guest email address")
    password: str = Field(..., min_length=6, description="Account password")
    name: str = Field(..., description="Full name")
    phone: str | None = Field(None, description="Phone number")


class AuthRequest(BaseModel):
    """Authentication request payload."""

    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=6, description="Password")


class TokenResponse(BaseModel):
    """JWT token response structure."""

    access_token: str
    token_type: str = "bearer"
