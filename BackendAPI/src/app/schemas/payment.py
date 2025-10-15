from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


PaymentMethod = Literal["stripe", "paypal", "wallet"]
PaymentStatus = Literal["pending", "succeeded", "failed"]


class PaymentRequest(BaseModel):
    """Request payload to process a payment for a booking."""
    booking_id: int = Field(..., description="Target booking identifier")
    amount: float = Field(..., gt=0, description="Amount to charge (currency units)")
    method: PaymentMethod = Field(..., description="Payment method to use")


class PaymentResponse(BaseModel):
    """Payment response data for a single payment."""
    id: int
    booking_id: int
    guest_id: str
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaymentListResponse(BaseModel):
    """Wrapper for listing multiple payments for a booking."""
    items: List[PaymentResponse]
