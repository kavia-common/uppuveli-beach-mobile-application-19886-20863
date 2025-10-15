"""Admin Bookings CRUD routes.

These endpoints are for the Web Admin Panel and require an Admin OAuth JWT with 'admin' scope.

Endpoints:
- GET    /api/v1/bookings           : List bookings (paginated)
- POST   /api/v1/bookings           : Create a booking
- GET    /api/v1/bookings/{id}      : Retrieve a booking by ID
- PUT    /api/v1/bookings/{id}      : Update a booking by ID
- DELETE /api/v1/bookings/{id}      : Delete a booking by ID

DB Expectations:
- bookings table with at least:
    id SERIAL PRIMARY KEY
    user_id INTEGER NOT NULL REFERENCES users(id)
    room_id INTEGER NOT NULL REFERENCES rooms(id)
    check_in DATE NOT NULL
    check_out DATE NOT NULL
    status TEXT NOT NULL DEFAULT 'booked'
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from src.api.db import execute, fetch_all, fetch_one
from src.api.security import decode_access_token, oauth2_scheme

router = APIRouter()


def _require_admin(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Ensure the provided bearer token has admin scope."""
    payload = decode_access_token(token)
    scope = str(payload.get("scope", ""))
    # Scope can contain space-separated scopes; ensure 'admin' present
    if "admin" not in scope.split():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin_scope_required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


class Booking(BaseModel):
    """Booking model reused for admin responses (aligned with mobile model)."""
    id: int = Field(..., description="Booking ID")
    userId: int = Field(..., description="User ID")
    roomId: int = Field(..., description="Room ID")
    status: str = Field(..., description="Booking status")
    checkIn: date = Field(..., description="Check-in date")
    checkOut: date = Field(..., description="Check-out date")


class CreateBookingRequest(BaseModel):
    """Request model to create a booking."""
    userId: int = Field(..., description="Guest user ID")
    roomId: int = Field(..., description="Room ID to book")
    checkIn: date = Field(..., description="Check-in date (YYYY-MM-DD)")
    checkOut: date = Field(..., description="Check-out date (YYYY-MM-DD)")
    status: Optional[str] = Field(default="booked", description="Initial status")


class UpdateBookingRequest(BaseModel):
    """Request model to update a booking."""
    userId: Optional[int] = Field(None, description="Guest user ID")
    roomId: Optional[int] = Field(None, description="Room ID to book")
    checkIn: Optional[date] = Field(None, description="Check-in date (YYYY-MM-DD)")
    checkOut: Optional[date] = Field(None, description="Check-out date (YYYY-MM-DD)")
    status: Optional[str] = Field(None, description="Booking status")


def _row_to_booking(row: Dict[str, Any]) -> Booking:
    """Map DB row to Booking model."""
    return Booking(
        id=int(row["id"]),
        userId=int(row["user_id"]),
        roomId=int(row["room_id"]),
        status=str(row["status"]),
        checkIn=row["check_in"],
        checkOut=row["check_out"],
    )


async def _get_booking_or_404(booking_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        "SELECT id, user_id, room_id, status, check_in, check_out FROM bookings WHERE id=$1",
        booking_id,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return row


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="List all bookings",
    description="Returns a paginated list of bookings. Requires admin scope.",
    tags=["admin"],
    response_model=List[Booking],
    responses={200: {"description": "List of bookings"}, 401: {"description": "Unauthorized"}},
)
async def list_bookings(
    _: Dict[str, Any] = Depends(_require_admin),
    limit: int = Query(20, ge=1, le=200, description="Max number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> List[Booking]:
    """List bookings with pagination."""
    rows = await fetch_all(
        "SELECT id, user_id, room_id, status, check_in, check_out "
        "FROM bookings ORDER BY id DESC LIMIT $1 OFFSET $2",
        limit,
        offset,
    )
    return [_row_to_booking(r) for r in rows]


# PUBLIC_INTERFACE
@router.post(
    "",
    summary="Create a new booking (admin)",
    description="Creates a booking for a specified user and room. Requires admin scope.",
    tags=["admin"],
    response_model=Booking,
    status_code=201,
    responses={
        201: {"description": "Booking created"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
    },
)
async def create_booking_admin(
    payload: CreateBookingRequest,
    _: Dict[str, Any] = Depends(_require_admin),
) -> Booking:
    """Create a booking as admin."""
    if payload.checkOut <= payload.checkIn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="checkOut must be after checkIn")

    # Validate user and room existence
    user = await fetch_one("SELECT id FROM users WHERE id=$1", payload.userId)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid userId")

    room = await fetch_one("SELECT id FROM rooms WHERE id=$1", payload.roomId)
    if not room:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid roomId")

    status_val = (payload.status or "booked").strip() or "booked"

    await execute(
        "INSERT INTO bookings (user_id, room_id, check_in, check_out, status) VALUES ($1, $2, $3, $4, $5)",
        payload.userId,
        payload.roomId,
        payload.checkIn,
        payload.checkOut,
        status_val,
    )
    created = await fetch_one(
        "SELECT id, user_id, room_id, status, check_in, check_out FROM bookings "
        "WHERE user_id=$1 AND room_id=$2 AND check_in=$3 AND check_out=$4 "
        "ORDER BY id DESC LIMIT 1",
        payload.userId,
        payload.roomId,
        payload.checkIn,
        payload.checkOut,
    )
    assert created is not None
    return _row_to_booking(created)


# PUBLIC_INTERFACE
@router.get(
    "/{booking_id}",
    summary="Get booking by ID (admin)",
    description="Returns the details of a booking by ID. Requires admin scope.",
    tags=["admin"],
    response_model=Booking,
    responses={200: {"description": "Booking details"}, 401: {"description": "Unauthorized"}, 404: {"description": "Not found"}},
)
async def get_booking_admin(
    booking_id: int = Path(..., ge=1),
    _: Dict[str, Any] = Depends(_require_admin),
) -> Booking:
    """Retrieve a booking by ID."""
    row = await _get_booking_or_404(booking_id)
    return _row_to_booking(row)


# PUBLIC_INTERFACE
@router.put(
    "/{booking_id}",
    summary="Update booking by ID (admin)",
    description="Updates fields of a booking. Requires admin scope.",
    tags=["admin"],
    response_model=Booking,
    responses={200: {"description": "Booking updated"}, 400: {"description": "Invalid input"}, 401: {"description": "Unauthorized"}, 404: {"description": "Not found"}},
)
async def update_booking_admin(
    payload: UpdateBookingRequest,
    booking_id: int = Path(..., ge=1),
    _: Dict[str, Any] = Depends(_require_admin),
) -> Booking:
    """Update a booking by ID with provided fields."""
    # Ensure exists
    _ = await _get_booking_or_404(booking_id)

    # Validate date logic if both provided
    if payload.checkIn and payload.checkOut and payload.checkOut <= payload.checkIn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="checkOut must be after checkIn")

    # Validate foreign keys if provided
    if payload.userId is not None:
        u = await fetch_one("SELECT id FROM users WHERE id=$1", payload.userId)
        if not u:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid userId")
    if payload.roomId is not None:
        r = await fetch_one("SELECT id FROM rooms WHERE id=$1", payload.roomId)
        if not r:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid roomId")

    # Build dynamic update
    sets: List[str] = []
    params: List[Any] = []
    if payload.userId is not None:
        sets.append(f"user_id=${len(params)+1}")
        params.append(payload.userId)
    if payload.roomId is not None:
        sets.append(f"room_id=${len(params)+1}")
        params.append(payload.roomId)
    if payload.checkIn is not None:
        sets.append(f"check_in=${len(params)+1}")
        params.append(payload.checkIn)
    if payload.checkOut is not None:
        sets.append(f"check_out=${len(params)+1}")
        params.append(payload.checkOut)
    if payload.status is not None:
        sets.append(f"status=${len(params)+1}")
        params.append(payload.status)

    if not sets:
        # Nothing to update; return current record
        current = await _get_booking_or_404(booking_id)
        return _row_to_booking(current)

    # Append booking_id as final param
    params.append(booking_id)
    set_clause = ", ".join(sets)
    sql = f"UPDATE bookings SET {set_clause} WHERE id=${len(params)}"
    await execute(sql, *params)

    updated = await _get_booking_or_404(booking_id)
    return _row_to_booking(updated)


# PUBLIC_INTERFACE
@router.delete(
    "/{booking_id}",
    summary="Delete booking by ID (admin)",
    description="Deletes a booking by ID. Requires admin scope.",
    tags=["admin"],
    status_code=204,
    responses={204: {"description": "Booking deleted"}, 401: {"description": "Unauthorized"}, 404: {"description": "Not found"}},
)
async def delete_booking_admin(
    booking_id: int = Path(..., ge=1),
    _: Dict[str, Any] = Depends(_require_admin),
) -> None:
    """Delete a booking by ID."""
    # Ensure exists
    _ = await _get_booking_or_404(booking_id)
    await execute("DELETE FROM bookings WHERE id=$1", booking_id)
    return None
