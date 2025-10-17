from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Plain password to hash")
    name: Optional[str] = Field(None, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class RoomOut(BaseModel):
    id: int
    room_number: str
    room_type: str
    price: float
    is_available: bool
    description: Optional[str] = None

    class Config:
        from_attributes = True


class BookingOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    status: str
    check_in: date
    check_out: date

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: float
    currency: str
    status: str
    method: str
    external_id: Optional[str] = None

    class Config:
        from_attributes = True


class LoyaltyAccountOut(BaseModel):
    id: int
    user_id: int
    points: int
    tier: str

    class Config:
        from_attributes = True


class LoyaltyHistoryOut(BaseModel):
    id: int
    account_id: int
    change: int
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class ReferralOut(BaseModel):
    id: int
    referrer_id: Optional[int] = None
    referee_id: Optional[int] = None
    code: str
    rewards: int

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    type: Optional[str] = None

    class Config:
        from_attributes = True


class ChatMessageOut(BaseModel):
    id: int
    user_id: int
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class BoutiqueItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    is_active: bool

    class Config:
        from_attributes = True
