from datetime import date
from pydantic import BaseModel, Field


class BookingSchema(BaseModel):
    """Booking schema for API request/response."""

    id: int | None = Field(default=None)
    room_id: str = Field(..., description="Room identifier")
    guest_id: str | None = Field(default=None, description="Guest id (ignored on create; set by server)")
    check_in: date = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: date = Field(..., description="Check-out date (YYYY-MM-DD)")
    status: str | None = Field(default="pending", description="Booking status")
