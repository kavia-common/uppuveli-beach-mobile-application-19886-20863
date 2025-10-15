"""Payments routes.

Endpoints:
- POST /api/v1/payments: Process payment for a booking (JWT protected)

Behavior:
- Calls a stubbed payment provider based on 'method' (stripe, paypal, wallet)
- Records transaction in 'payments' table
- Returns Payment object per Mobile OpenAPI

DB Expectations:
- payments table:
    id SERIAL PRIMARY KEY
    booking_id INTEGER NOT NULL REFERENCES bookings(id)
    amount NUMERIC(10,2) NOT NULL
    status TEXT NOT NULL
    method TEXT NOT NULL
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.db import execute, fetch_one
from src.api.security import decode_access_token, oauth2_scheme
from src.api.payment_providers.base import get_payment_provider, ChargeResult

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


def _row_to_payment(row: Dict[str, Any]) -> Payment:
    return Payment(
        id=int(row["id"]),
        bookingId=int(row["booking_id"]),
        amount=float(row["amount"]),
        status=str(row["status"]),
        method=str(row["method"]),
    )


async def _require_user(token: str) -> int:
    payload = decode_access_token(token)
    uid = payload.get("user_id") or payload.get("sub")
    try:
        return int(uid)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc


async def _stub_charge_provider(method: str, amount: float) -> str:
    """Stub payment provider integration; returns a provider reference or raises HTTP 400."""
    method_l = (method or "").lower()
    if method_l not in ("stripe", "paypal", "wallet"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment method")
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")

    # Wallet is handled inline without external provider
    if method_l == "wallet":
        return f"wallet_tx_{int(datetime.now(timezone.utc).timestamp())}"

    # Use provider stubs for stripe/paypal
    try:
        provider = get_payment_provider(method_l)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment method")
    result: ChargeResult = provider.charge(amount)
    if not result.ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message)
    return result.reference


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
)
async def process_payment(payload: PaymentRequest, token: str = Depends(oauth2_scheme)) -> Payment:
    """Process a payment via stub provider and persist the record."""
    user_id = await _require_user(token)

    # Validate booking belongs to user
    booking = await fetch_one(
        "SELECT b.id, b.user_id FROM bookings b WHERE b.id=$1",
        payload.bookingId,
    )
    if not booking or int(booking["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bookingId")

    # Stub charge
    _ = await _stub_charge_provider(payload.method, payload.amount)

    # Persist payment
    await execute(
        "INSERT INTO payments (booking_id, amount, status, method) VALUES ($1, $2, 'paid', $3)",
        payload.bookingId,
        payload.amount,
        payload.method.lower(),
    )

    row = await fetch_one(
        "SELECT id, booking_id, amount, status, method FROM payments "
        "WHERE booking_id=$1 ORDER BY id DESC LIMIT 1",
        payload.bookingId,
    )
    assert row is not None
    return _row_to_payment(row)
