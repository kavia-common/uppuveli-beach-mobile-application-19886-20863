"""Admin Bookings CRUD routes.

These endpoints are for the Web Admin Panel and require an Admin OAuth JWT with 'admin' scope.

Endpoints:
- GET    /api/v1/bookings           : List bookings (paginated)
- POST   /api/v1/bookings           : Create a booking
- GET    /api/v1/bookings/{id}      : Retrieve a booking by ID
- PUT    /api/v1/bookings/{id}      : Update a booking by ID
- DELETE /api/v1/bookings/{id}      : Delete a booking by ID

DB Expectations:
- bookings table with UUID primary keys
- user_id and room_id reference users and rooms tables respectively
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.models import Booking as BookingORM, User as UserORM, Room as RoomORM, BookingStatus
from src.api.security import require_admin_scope

router = APIRouter()


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


def _orm_to_booking(booking: BookingORM) -> Booking:
    """Convert ORM Booking model to Pydantic response model."""
    # Convert UUIDs to integers for API compatibility (keeping spec alignment)
    # In production, you'd use proper UUID handling, but spec expects integers
    return Booking(
        id=int(str(booking.id).replace("-", "")[:8], 16),  # Hash UUID to int for compatibility
        userId=int(str(booking.user_id).replace("-", "")[:8], 16),
        roomId=int(str(booking.room_id).replace("-", "")[:8], 16),
        status=booking.status.value if isinstance(booking.status, BookingStatus) else str(booking.status),
        checkIn=booking.check_in,
        checkOut=booking.check_out,
    )


def _get_booking_or_404(db: Session, booking_id: int) -> BookingORM:
    """Get booking by pseudo-integer ID or raise 404."""
    # Since we're converting UUID to int, we need to query all and find match
    # This is inefficient but maintains API compatibility
    # In production, use UUID paths or proper ID mapping
    bookings = db.query(BookingORM).all()
    for booking in bookings:
        pseudo_id = int(str(booking.id).replace("-", "")[:8], 16)
        if pseudo_id == booking_id:
            return booking
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")


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
    _: Dict[str, Any] = Depends(require_admin_scope),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200, description="Max number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> List[Booking]:
    """List bookings with pagination."""
    bookings = db.query(BookingORM).order_by(BookingORM.created_at.desc()).limit(limit).offset(offset).all()
    return [_orm_to_booking(b) for b in bookings]


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
    _: Dict[str, Any] = Depends(require_admin_scope),
    db: Session = Depends(get_db),
) -> Booking:
    """Create a booking as admin."""
    if payload.checkOut <= payload.checkIn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="checkOut must be after checkIn")

    # Since API uses integer IDs but DB uses UUIDs, we need to look up by pseudo-ID
    # This is a workaround for API compatibility - in production use UUIDs end-to-end
    users = db.query(UserORM).all()
    user = None
    for u in users:
        if int(str(u.id).replace("-", "")[:8], 16) == payload.userId:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid userId")

    rooms = db.query(RoomORM).all()
    room = None
    for r in rooms:
        if int(str(r.id).replace("-", "")[:8], 16) == payload.roomId:
            room = r
            break
    
    if not room:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid roomId")

    # Parse status
    status_val = payload.status or "booked"
    try:
        booking_status = BookingStatus(status_val.lower())
    except ValueError:
        booking_status = BookingStatus.BOOKED

    # Create booking
    booking = BookingORM(
        user_id=user.id,
        room_id=room.id,
        check_in=payload.checkIn,
        check_out=payload.checkOut,
        status=booking_status,
        guests=1,  # Default
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return _orm_to_booking(booking)


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
    _: Dict[str, Any] = Depends(require_admin_scope),
    db: Session = Depends(get_db),
) -> Booking:
    """Retrieve a booking by ID."""
    booking = _get_booking_or_404(db, booking_id)
    return _orm_to_booking(booking)


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
    _: Dict[str, Any] = Depends(require_admin_scope),
    db: Session = Depends(get_db),
) -> Booking:
    """Update a booking by ID with provided fields."""
    booking = _get_booking_or_404(db, booking_id)

    # Validate date logic if both provided
    check_in = payload.checkIn if payload.checkIn is not None else booking.check_in
    check_out = payload.checkOut if payload.checkOut is not None else booking.check_out
    
    if check_out <= check_in:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="checkOut must be after checkIn")

    # Validate and resolve user_id if provided
    if payload.userId is not None:
        users = db.query(UserORM).all()
        user = None
        for u in users:
            if int(str(u.id).replace("-", "")[:8], 16) == payload.userId:
                user = u
                break
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid userId")
        booking.user_id = user.id

    # Validate and resolve room_id if provided
    if payload.roomId is not None:
        rooms = db.query(RoomORM).all()
        room = None
        for r in rooms:
            if int(str(r.id).replace("-", "")[:8], 16) == payload.roomId:
                room = r
                break
        if not room:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid roomId")
        booking.room_id = room.id

    # Update fields
    if payload.checkIn is not None:
        booking.check_in = payload.checkIn
    if payload.checkOut is not None:
        booking.check_out = payload.checkOut
    if payload.status is not None:
        try:
            booking.status = BookingStatus(payload.status.lower())
        except ValueError:
            pass  # Keep existing status if invalid

    db.commit()
    db.refresh(booking)
    
    return _orm_to_booking(booking)


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
    _: Dict[str, Any] = Depends(require_admin_scope),
    db: Session = Depends(get_db),
) -> None:
    """Delete a booking by ID."""
    booking = _get_booking_or_404(db, booking_id)
    db.delete(booking)
    db.commit()
    return None
