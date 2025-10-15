from typing import Optional

from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """User persistence model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    phone: Optional[str] = None
    hashed_password: str
    is_active: bool = True
