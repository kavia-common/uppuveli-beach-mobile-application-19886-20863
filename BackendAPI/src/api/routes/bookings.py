from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps.auth import get_current_user
from src.db.models import Booking, Room, User
from src.db.session import get_db
from src.db.schemas import BookingOut

router = APIRouter(prefix="/bookings", tags=["Bookings"])


class BookingCreate(BaseModel):
    room_id: int = Field(..., description="Room ID to book")
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")


# PUBLIC_INTERFACE
@router.post("", summary="Create booking", response_model=BookingOut, status_code=201)
def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a booking for the current user."""
    if payload.check_out < payload.check_in:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date range")
    room = db.execute(select(Room).where(Room.id == payload.room_id)).scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    booking = Booking(
        user_id=current_user.id,
        room_id=room.id,
        status="booked",
        check_in=payload.check_in,
        check_out=payload.check_out,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
