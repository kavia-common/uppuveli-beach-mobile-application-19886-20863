from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Payment(SQLModel, table=True):
    """Payment persistence model for booking payments."""

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(index=True, description="Associated booking id")
    guest_id: str = Field(index=True, description="Payer (user) id")
    amount: float = Field(description="Payment amount in currency units")
    method: str = Field(description="Payment method, e.g. stripe, paypal, wallet")
    status: str = Field(default="pending", description="Payment status: pending/succeeded/failed")
    reference: Optional[str] = Field(default=None, description="Gateway reference or simulated reference")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
