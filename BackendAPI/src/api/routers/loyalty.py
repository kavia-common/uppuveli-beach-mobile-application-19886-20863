"""Loyalty routes.

Endpoints:
- GET /api/v1/loyalty: Get loyalty points and history (JWT protected)

DB Expectations:
- users.loyalty_points INTEGER
- loyalty_history table:
    id SERIAL PRIMARY KEY
    user_id INTEGER NOT NULL REFERENCES users(id)
    change INTEGER NOT NULL
    reason TEXT NOT NULL
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.db import fetch_all, fetch_one
from src.api.security import decode_access_token, oauth2_scheme

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


async def _require_user_id(token: str) -> int:
    payload = decode_access_token(token)
    uid = payload.get("user_id") or payload.get("sub")
    try:
        return int(uid)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc


# PUBLIC_INTERFACE
@router.get(
    "",
    tags=["loyalty"],
    summary="Get loyalty points and history",
    description="Returns current loyalty points and recent history for the authenticated user.",
    response_model=Loyalty,
    responses={200: {"description": "Loyalty info"}, 401: {"description": "Unauthorized"}},
)
async def get_loyalty(token: str = Depends(oauth2_scheme)) -> Loyalty:
    """Get loyalty info for current user."""
    user_id = await _require_user_id(token)
    user = await fetch_one("SELECT id, COALESCE(loyalty_points,0) AS points FROM users WHERE id=$1", user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    rows = await fetch_all(
        "SELECT change, reason, created_at FROM loyalty_history WHERE user_id=$1 ORDER BY created_at DESC LIMIT 100",
        user_id,
    )
    history = [
        LoyaltyHistoryItem(date=r["created_at"], change=int(r["change"]), reason=str(r["reason"])) for r in rows
    ]
    return Loyalty(userId=user_id, points=int(user["points"]), history=history)
