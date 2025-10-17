from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps.auth import get_current_user
from src.db.models import Booking, Payment, User
from src.db.session import get_db
from src.db.schemas import PaymentOut
from src.services.payments import process_payment_stub

router = APIRouter(prefix="/payments", tags=["Payments"])


class PaymentCreate(BaseModel):
    booking_id: int = Field(..., description="Related booking ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    method: str = Field(..., description="Payment method: stripe|paypal|wallet")


# PUBLIC_INTERFACE
@router.post(
    "",
    summary="Process payment (stub)",
    response_model=PaymentOut,
    status_code=201,
)
def process_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """Process a payment via a mocked gateway and persist the Payment."""
    booking = (
        db.execute(
            select(Booking).where(
                Booking.id == payload.booking_id,
                Booking.user_id == user.id,
            )
        )
        .scalar_one_or_none()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    external_id, status_str = process_payment_stub(
        amount=payload.amount,
        method=payload.method,
        booking_id=payload.booking_id,
        user_id=user.id,
    )

    payment = Payment(
        booking_id=booking.id,
        amount=payload.amount,
        currency="USD",
        status=status_str,
        method=payload.method,
        external_id=external_id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
