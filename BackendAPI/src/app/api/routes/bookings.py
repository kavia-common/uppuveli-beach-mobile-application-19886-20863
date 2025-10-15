from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.security import get_current_user_id
from app.db import get_session
from app.models.booking import Booking
from app.schemas.booking import BookingSchema
from app.schemas.common import SuccessResponse

router = APIRouter()


@router.get(
    "",
    summary="List bookings",
    response_model=SuccessResponse[List[BookingSchema]],
)
# PUBLIC_INTERFACE
def list_bookings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """Return a paginated list of bookings for the authenticated user."""
    statement = (
        select(Booking)
        .where(Booking.guest_id == user_id)
        .order_by(Booking.check_in)
        .offset(offset)
        .limit(limit)
    )
    bookings = session.exec(statement).all()

    # Build BookingSchema instances explicitly to avoid passing SQLModel to Pydantic v2
    serialized: List[dict] = []
    for b in bookings:
        schema = BookingSchema(
            id=b.id,
            room_id=b.room_id,
            guest_id=b.guest_id,
            check_in=b.check_in,
            check_out=b.check_out,
            status=b.status,
        )
        serialized.append(schema.model_dump())

    return SuccessResponse(status="success", data=serialized)


@router.post(
    "",
    summary="Create booking",
    response_model=SuccessResponse[BookingSchema],
)
# PUBLIC_INTERFACE
def create_booking(
    payload: BookingSchema,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new booking record for the authenticated user."""
    # Simple validation
    if payload.check_in >= payload.check_out:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="check_out must be after check_in")

    # Create model instance (force guest_id to current user)
    booking = Booking(
        room_id=payload.room_id,
        guest_id=user_id,
        check_in=payload.check_in,
        check_out=payload.check_out,
        status=payload.status or "pending",
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)

    # Build BookingSchema using explicit fields, then return its data
    data_schema = BookingSchema(
        id=booking.id,
        room_id=booking.room_id,
        guest_id=booking.guest_id,
        check_in=booking.check_in,
        check_out=booking.check_out,
        status=booking.status,
    )

    return SuccessResponse(status="success", data=data_schema)
