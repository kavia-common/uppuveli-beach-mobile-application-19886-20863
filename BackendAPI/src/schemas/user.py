from pydantic import BaseModel, EmailStr


# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """User public schema."""
    id: int
    email: EmailStr
    name: str | None = None
    phone: str | None = None
    is_active: bool
