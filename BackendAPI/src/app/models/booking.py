from datetime import date
from typing import Optional

from sqlmodel import SQLModel, Field


class Booking(SQLModel, table=True):
    """Booking persistence model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: str = Field(index=True, description="Room identifier")
    guest_id: str = Field(index=True, description="Guest (user) id")
    check_in: date = Field(description="Check-in date")
    check_out: date = Field(description="Check-out date")
    status: str = Field(default="pending", description="Booking status")
