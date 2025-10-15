"""Loyalty routes.

Endpoints:
- GET /api/v1/loyalty: Get loyalty points and history (JWT protected)

DB Expectations:
- LoyaltyAccount ORM model with relationship to LoyaltyHistory
"""

from datetime import datetime
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.models import LoyaltyAccount as LoyaltyAccountORM, LoyaltyHistory as LoyaltyHistoryORM
from src.api.security import get_current_user

router = APIRouter()


class LoyaltyHistoryItem(BaseModel):
    """Individual loyalty history record."""
    date: datetime = Field(..., description="Event timestamp")
    change: int = Field(..., description="Points change (+/-)")
    reason: str = Field(..., description="Reason for change")


class Loyalty(BaseModel):
    """Loyalty response aligned with Mobile OpenAPI."""
    userId: int = Field(..., description="User ID")
    points: int = Field(..., description="Current points balance")
    history: List[LoyaltyHistoryItem] = Field(default_factory=list, description="Points change history")


def _uuid_to_int(uuid_val) -> int:
    """Convert UUID to int representation for API compatibility."""
    if isinstance(uuid_val, UUID):
        return int(uuid_val.hex, 16) % (10**18)
    return int(uuid_val)


# PUBLIC_INTERFACE
@router.get(
    "",
    tags=["loyalty"],
    summary="Get loyalty points and history",
    description="Returns current loyalty points and recent history for the authenticated user.",
    response_model=Loyalty,
    responses={200: {"description": "Loyalty info"}, 401: {"description": "Unauthorized"}},
    dependencies=[Depends(get_current_user)],
)
async def get_loyalty(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Loyalty:
    """Get loyalty info for current user."""
    user_id_str = current_user.get("user_id") or current_user.get("sub")
    user_id_uuid = UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str

    # Query loyalty account
    loyalty_account = db.query(LoyaltyAccountORM).filter(
        LoyaltyAccountORM.user_id == user_id_uuid
    ).first()

    if not loyalty_account:
        # Create default loyalty account if not exists
        loyalty_account = LoyaltyAccountORM(
            user_id=user_id_uuid,
            points=0,
            tier="basic"
        )
        db.add(loyalty_account)
        db.commit()
        db.refresh(loyalty_account)

    # Query history
    history_records = db.query(LoyaltyHistoryORM).filter(
        LoyaltyHistoryORM.user_id == user_id_uuid
    ).order_by(LoyaltyHistoryORM.created_at.desc()).limit(100).all()

    history = [
        LoyaltyHistoryItem(
            date=record.created_at,
            change=record.change,
            reason=record.reason.value
        )
        for record in history_records
    ]

    return Loyalty(
        userId=_uuid_to_int(user_id_uuid),
        points=loyalty_account.points,
        history=history
    )
