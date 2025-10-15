"""Bookings routes.

Endpoints:
- POST /api/v1/bookings: Create a new booking (JWT protected)

DB Expectations:
- bookings table:
    id SERIAL PRIMARY KEY
    user_id INTEGER NOT NULL REFERENCES users(id)
    room_id INTEGER NOT NULL REFERENCES rooms(id)
    check_in DATE NOT NULL
    check_out DATE NOT NULL
    status TEXT NOT NULL DEFAULT 'booked'
"""

from datetime import date
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.db import execute, fetch_one
from src.api.security import decode_access_token, oauth2_scheme

router = APIRouter()


class Booking(BaseModel):
    """Booking model aligned with Mobile OpenAPI schema."""
    id: int = Field(..., description="Booking ID")
    userId: int = Field(..., description="User ID")
    roomId: int = Field(..., description="Room ID")
    status: str = Field(..., description="Booking status")
    checkIn: date = Field(..., description="Check-in date")
    checkOut: date = Field(..., description="Check-out date")


class CreateBookingRequest(BaseModel):
    """Request body to create a booking."""
    roomId: int = Field(..., description="Room ID to book")
    checkIn: date = Field(..., description="Check-in date (YYYY-MM-DD)")
    checkOut: date = Field(..., description="Check-out date (YYYY-MM-DD)")


async def _get_user_id_from_token(token: str) -> int:
    payload = decode_access_token(token)
    # Prefer explicit claim user_id but fall back to sub
    uid = payload.get("user_id") or payload.get("sub")
    try:
        return int(uid)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc


def _row_to_booking(row: Dict[str, Any]) -> Booking:
    return Booking(
        id=int(row["id"]),
        userId=int(row["user_id"]),
        roomId=int(row["room_id"]),
        status=str(row["status"]),
        checkIn=row["check_in"],
        checkOut=row["check_out"],
    )


# PUBLIC_INTERFACE
@router.post(
    "",
    tags=["bookings"],
    summary="Create a new booking",
    description="Creates a booking for the authenticated user.",
    response_model=Booking,
    responses={
        201: {"description": "Booking created"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
    },
    status_code=201,
)
async def create_booking(payload: CreateBookingRequest, token: str = Depends(oauth2_scheme)) -> Booking:
    """Create a booking for the authenticated user."""
    user_id = await _get_user_id_from_token(token)

    if payload.checkOut <= payload.checkIn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="checkOut must be after checkIn")

    # Basic room existence check
    room = await fetch_one("SELECT id, availability FROM rooms WHERE id=$1", payload.roomId)
    if not room:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid roomId")

    # Create booking
    await execute(
        "INSERT INTO bookings (user_id, room_id, check_in, check_out, status) VALUES ($1, $2, $3, $4, 'booked')",
        user_id,
        payload.roomId,
        payload.checkIn,
        payload.checkOut,
    )

    created = await fetch_one(
        "SELECT id, user_id, room_id, status, check_in, check_out "
        "FROM bookings WHERE user_id=$1 AND room_id=$2 AND check_in=$3 AND check_out=$4 "
        "ORDER BY id DESC LIMIT 1",
        user_id,
        payload.roomId,
        payload.checkIn,
        payload.checkOut,
    )
    assert created is not None
    return _row_to_booking(created)
