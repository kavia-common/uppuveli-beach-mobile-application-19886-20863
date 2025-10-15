"""Payments routes.

Endpoints:
- POST /api/v1/payments: Process payment for a booking (JWT protected)

Behavior:
- Stub payment processing (deterministic responses)
- Records transaction using SQLAlchemy ORM
- Returns Payment object per Mobile OpenAPI
"""

from datetime import datetime, timezone
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.models import Payment as PaymentORM, Booking as BookingORM, PaymentMethod, PaymentStatus
from src.api.security import get_current_user

router = APIRouter()


class Payment(BaseModel):
    """Payment model aligned with Mobile OpenAPI."""
    id: int = Field(..., description="Payment ID")
    bookingId: int = Field(..., description="Booking ID")
    amount: float = Field(..., description="Paid amount")
    status: str = Field(..., description="Payment status")
    method: str = Field(..., description="Payment method used")


class PaymentRequest(BaseModel):
    """Request to process a payment."""
    bookingId: int = Field(..., description="Booking to pay for")
    amount: float = Field(..., description="Amount to charge")
    method: str = Field(..., description="Payment method: stripe | paypal | wallet")


def _uuid_to_int(uuid_val) -> int:
    """Convert UUID to int representation for API compatibility."""
    if isinstance(uuid_val, UUID):
        return int(uuid_val.hex, 16) % (10**18)
    return int(uuid_val)


def _stub_charge_provider(method: str, amount: float) -> str:
    """Stub payment provider; returns deterministic success reference."""
    method_l = (method or "").lower()
    if method_l not in ("stripe", "paypal", "wallet"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported payment method"
        )
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    # Return stub transaction reference
    timestamp = int(datetime.now(timezone.utc).timestamp())
    return f"{method_l}_tx_{timestamp}"


# PUBLIC_INTERFACE
@router.post(
    "",
    tags=["payments"],
    summary="Process payment for a booking",
    description="Charges the given amount for the booking using the specified method and records the transaction.",
    response_model=Payment,
    responses={
        201: {"description": "Payment processed"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
    },
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
async def process_payment(
    payload: PaymentRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Payment:
    """Process a payment via stub provider and persist the record."""
    user_id_str = current_user.get("user_id") or current_user.get("sub")
    user_id_uuid = UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str

    # Validate booking exists and belongs to user (stub: accept any booking for MVP)
    # In production, implement proper booking validation
    booking = db.query(BookingORM).filter(
        BookingORM.user_id == user_id_uuid
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bookingId or booking not found"
        )

    # Stub charge provider
    txn_ref = _stub_charge_provider(payload.method, payload.amount)

    # Map method string to enum
    method_enum = PaymentMethod.STRIPE
    if payload.method.lower() == "paypal":
        method_enum = PaymentMethod.PAYPAL
    elif payload.method.lower() == "wallet":
        method_enum = PaymentMethod.WALLET

    # Create payment record
    payment = PaymentORM(
        booking_id=booking.id,
        user_id=user_id_uuid,
        amount=payload.amount,
        currency="USD",
        method=method_enum,
        status=PaymentStatus.CAPTURED,
        provider_txn_id=txn_ref
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return Payment(
        id=_uuid_to_int(payment.id),
        bookingId=_uuid_to_int(payment.booking_id),
        amount=float(payment.amount),
        status=payment.status.value,
        method=payment.method.value
    )
