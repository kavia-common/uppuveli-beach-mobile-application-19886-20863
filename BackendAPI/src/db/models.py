from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .session import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # relationships
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user")
    loyalty_account: Mapped[Optional["LoyaltyAccount"]] = relationship(
        "LoyaltyAccount", back_populates="user", uselist=False
    )
    referrals_sent: Mapped[list["Referral"]] = relationship(
        "Referral",
        back_populates="referrer",
        foreign_keys="Referral.referrer_id",
    )
    referrals_received: Mapped[list["Referral"]] = relationship(
        "Referral",
        back_populates="referee",
        foreign_keys="Referral.referee_id",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="user"
    )


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    room_type: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="room")


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="booked", nullable=False)
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint("check_out >= check_in", name="ck_booking_dates"),
        Index("ix_bookings_user_room", "user_id", "room_id"),
    )

    user: Mapped["User"] = relationship("User", back_populates="bookings")
    room: Mapped["Room"] = relationship("Room", back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="booking")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # stripe, paypal, wallet
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="payments")


class LoyaltyAccount(Base, TimestampMixin):
    __tablename__ = "loyalty_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tier: Mapped[str] = mapped_column(String(50), default="basic", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="loyalty_account")
    history: Mapped[list["LoyaltyHistory"]] = relationship(
        "LoyaltyHistory", back_populates="account", cascade="all, delete-orphan"
    )


class LoyaltyHistory(Base, TimestampMixin):
    __tablename__ = "loyalty_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False
    )
    change: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    account: Mapped["LoyaltyAccount"] = relationship("LoyaltyAccount", back_populates="history")


class Referral(Base, TimestampMixin):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("code", name="uq_referral_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    referrer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    referee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rewards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    referrer: Mapped[Optional["User"]] = relationship(
        "User", back_populates="referrals_sent", foreign_keys=[referrer_id]
    )
    referee: Mapped[Optional["User"]] = relationship(
        "User", back_populates="referrals_received", foreign_keys=[referee_id]
    )


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="chat_messages")


class BoutiqueItem(Base, TimestampMixin):
    __tablename__ = "boutique_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
