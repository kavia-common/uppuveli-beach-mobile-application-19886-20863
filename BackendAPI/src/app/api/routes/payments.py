from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session, select

from app.core.security import get_current_user_id
from app.db import get_session
from app.models.booking import Booking
from app.models.payment import Payment
from app.schemas.payment import PaymentListResponse, PaymentRequest, PaymentResponse
from app.schemas.common import SuccessResponse

router = APIRouter()


def _simulate_gateway_status(booking_id: int, amount: float, method: str) -> tuple[str, str]:
    """
    Deterministic payment simulation:
    - Fail if amount <= 0 (already validated elsewhere)
    - Fail if booking_id % 5 == 0
    - Otherwise succeed
    Reference is a reproducible string.
    """
    if booking_id % 5 == 0:
        return "failed", f"SIM-{method.upper()}-{booking_id}-AMT{int(amount*100)}-FAIL"
    return "succeeded", f"SIM-{method.upper()}-{booking_id}-AMT{int(amount*100)}-OK"


@router.post(
    "",
    summary="Process payment for a booking",
    response_model=SuccessResponse[PaymentResponse],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Booking Not Found"},
    },
)
# PUBLIC_INTERFACE
def create_payment(
    payload: PaymentRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Process a payment for a booking for the authenticated user.

    Parameters:
    - payload: PaymentRequest containing booking_id, amount, and method

    Returns:
    - SuccessResponse[PaymentResponse] with processed payment details
    """
    # Validate booking existence and ownership
    booking = session.exec(select(Booking).where(Booking.id == payload.booking_id)).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if str(booking.guest_id) != str(user_id):
        # Protect against paying for someone else's booking
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if payload.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")

    # Simulate gateway processing deterministically
    status_str, reference = _simulate_gateway_status(payload.booking_id, payload.amount, payload.method)

    payment = Payment(
        booking_id=payload.booking_id,
        guest_id=str(user_id),
        amount=float(payload.amount),
        method=payload.method,
        status=status_str,
        reference=reference,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)

    resp = PaymentResponse(
        id=payment.id,
        booking_id=payment.booking_id,
        guest_id=payment.guest_id,
        amount=payment.amount,
        method=payment.method,  # type: ignore[assignment]
        status=payment.status,  # type: ignore[assignment]
        reference=payment.reference,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )
    return SuccessResponse(status="success", data=resp)


@router.get(
    "/{booking_id}",
    summary="List payments by booking id",
    response_model=SuccessResponse[PaymentListResponse],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Booking Not Found"},
    },
)
# PUBLIC_INTERFACE
def list_payments_for_booking(
    booking_id: int = Path(..., ge=1, description="Booking identifier"),
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Retrieve all payments for a specific booking, restricted to the booking owner.

    Parameters:
    - booking_id: integer id of the booking

    Returns:
    - SuccessResponse[PaymentListResponse] listing payments
    """
    booking = session.exec(select(Booking).where(Booking.id == booking_id)).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if str(booking.guest_id) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    payments: List[Payment] = session.exec(select(Payment).where(Payment.booking_id == booking_id)).all()
    items = [
        PaymentResponse(
            id=p.id,
            booking_id=p.booking_id,
            guest_id=p.guest_id,
            amount=p.amount,
            method=p.method,  # type: ignore[assignment]
            status=p.status,  # type: ignore[assignment]
            reference=p.reference,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in payments
    ]

    return SuccessResponse(status="success", data=PaymentListResponse(items=items))
