"""ORM models and API schemas for BackendAPI.

This module contains:
- SQLAlchemy ORM models matching the database schema (users, rooms, bookings, etc.)
- Pydantic models for API request/response schemas
- Relationship mappings between entities

Database schema alignment:
- All ORM models use UUID primary keys
- Enums are mapped to PostgreSQL enum types
- Relationships use lazy='select' by default for simplicity
"""

from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, Text, Date, DateTime,
    ForeignKey, CheckConstraint, Index, CHAR
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, EmailStr
import uuid

from src.api.db import Base


# ============================================================================
# PostgreSQL Enum Types (matching schema.sql)
# ============================================================================

class BookingStatus(str, PyEnum):
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"
    VOIDED = "voided"


class NotificationStatus(str, PyEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class NotificationType(str, PyEnum):
    SYSTEM = "system"
    PROMOTION = "promotion"
    BOOKING = "booking"
    LOYALTY = "loyalty"
    PAYMENT = "payment"
    CHAT = "chat"


class PaymentMethod(str, PyEnum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    WALLET = "wallet"
    CASH = "cash"
    CARD = "card"


class LoyaltyReason(str, PyEnum):
    BOOKING = "booking"
    PURCHASE = "purchase"
    REFERRAL_REWARD = "referral_reward"
    ADJUSTMENT = "adjustment"
    REVERSAL = "reversal"


class ReferralStatus(str, PyEnum):
    GENERATED = "generated"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================

class User(Base):
    """Guest user model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    loyalty_account = relationship("LoyaltyAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    loyalty_history = relationship("LoyaltyHistory", back_populates="user", cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="user", foreign_keys="[Referral.user_id]", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", foreign_keys="[ChatMessage.user_id]")


class AdminUser(Base):
    """Admin user model for staff access."""
    __tablename__ = "admin_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    role = Column(Text, nullable=False, default="admin")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chat_messages = relationship("ChatMessage", back_populates="admin", foreign_keys="[ChatMessage.admin_id]")


class Room(Base):
    """Hotel room model."""
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(Text, unique=True, nullable=True)
    type = Column(Text, nullable=False, index=True)
    price = Column(Numeric(12, 2), nullable=False)
    availability = Column(Boolean, nullable=False, default=True, index=True)
    description = Column(Text, nullable=True)
    max_occupancy = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("price >= 0", name="rooms_price_check"),
        CheckConstraint("max_occupancy > 0", name="rooms_max_occupancy_check"),
    )
    
    # Relationships
    bookings = relationship("Booking", back_populates="room")


class Booking(Base):
    """Booking model."""
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(ENUM(BookingStatus, name="booking_status"), nullable=False, default=BookingStatus.BOOKED, index=True)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    guests = Column(Integer, nullable=False, default=1)
    special_requests = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("guests > 0", name="bookings_guests_check"),
        CheckConstraint("check_out > check_in", name="bookings_dates_valid"),
        Index("idx_bookings_checkin_checkout", "check_in", "check_out"),
    )
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")


class Payment(Base):
    """Payment model."""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(CHAR(3), nullable=False, default="USD")
    method = Column(ENUM(PaymentMethod, name="payment_method"), nullable=False)
    status = Column(ENUM(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.PENDING, index=True)
    provider_txn_id = Column(Text, nullable=True)
    meta_data = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("amount >= 0", name="payments_amount_check"),
    )
    
    # Relationships
    booking = relationship("Booking", back_populates="payments")
    user = relationship("User", back_populates="payments")


class LoyaltyAccount(Base):
    """Loyalty account model (one per user)."""
    __tablename__ = "loyalty_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    points = Column(Integer, nullable=False, default=0)
    tier = Column(Text, nullable=False, default="basic")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="loyalty_account")
    history = relationship("LoyaltyHistory", back_populates="account", cascade="all, delete-orphan")


class LoyaltyHistory(Base):
    """Loyalty points history model."""
    __tablename__ = "loyalty_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    change = Column(Integer, nullable=False)
    reason = Column(ENUM(LoyaltyReason, name="loyalty_reason"), nullable=False, index=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    account = relationship("LoyaltyAccount", back_populates="history")
    user = relationship("User", back_populates="loyalty_history")


class Referral(Base):
    """Referral code model."""
    __tablename__ = "referrals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(Text, unique=True, nullable=False, index=True)
    status = Column(ENUM(ReferralStatus, name="referral_status"), nullable=False, default=ReferralStatus.GENERATED, index=True)
    rewards = Column(Integer, nullable=False, default=0)
    referred_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="referrals", foreign_keys=[user_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])


class Notification(Base):
    """Notification model."""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(ENUM(NotificationType, name="notification_type"), nullable=False, default=NotificationType.SYSTEM)
    message = Column(Text, nullable=False)
    status = Column(ENUM(NotificationStatus, name="notification_status"), nullable=False, default=NotificationStatus.QUEUED, index=True)
    is_read = Column(Boolean, nullable=False, default=False)
    meta_data = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")


class ChatMessage(Base):
    """Chat message model."""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True)
    message = Column(Text, nullable=False)
    direction = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint("direction IN ('inbound', 'outbound')", name="chat_messages_direction_check"),
    )
    
    # Relationships
    user = relationship("User", back_populates="chat_messages", foreign_keys=[user_id])
    admin = relationship("AdminUser", back_populates="chat_messages", foreign_keys=[admin_id])


class BoutiqueItem(Base):
    """Boutique item model."""
    __tablename__ = "boutique_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    sku = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("price >= 0", name="boutique_items_price_check"),
        CheckConstraint("stock >= 0", name="boutique_items_stock_check"),
    )


# ============================================================================
# Pydantic API Schemas (kept from original models.py for backward compatibility)
# ============================================================================

class UserResponse(BaseModel):
    """Represents a guest user returned to clients."""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    name: str = Field(..., description="Full name")
    loyaltyPoints: int = Field(0, description="Current loyalty points")


# PUBLIC_INTERFACE
class GuestRegistrationRequest(BaseModel):
    """Request body to register a new guest user."""
    email: EmailStr = Field(..., description="Guest email")
    password: str = Field(..., description="Guest password (plaintext; will be hashed)")
    name: str = Field(..., description="Guest full name")
    phone: Optional[str] = Field(default=None, description="Phone number")


# PUBLIC_INTERFACE
class AuthRequest(BaseModel):
    """Request body to authenticate a guest user via email/password."""
    email: EmailStr = Field(..., description="Guest email")
    password: str = Field(..., description="Guest plaintext password")


# PUBLIC_INTERFACE
class LoginResponse(BaseModel):
    """Response for successful login: returns token and user."""
    token: str = Field(..., description="JWT bearer token")
    user: UserResponse = Field(..., description="Authenticated user info")


# PUBLIC_INTERFACE
class SuccessUserResponse(BaseModel):
    """Generic success response that returns the user object."""
    status: str = Field("success", description="Status indicator")
    data: UserResponse = Field(..., description="User object")
