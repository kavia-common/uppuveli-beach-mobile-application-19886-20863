"""Notifications routes.

Endpoints:
- GET /api/v1/notifications: Fetch user notifications (JWT protected)

DB Expectations:
- notifications table:
    id SERIAL PRIMARY KEY
    user_id INTEGER NOT NULL REFERENCES users(id)
    message TEXT NOT NULL
    read BOOLEAN NOT NULL DEFAULT FALSE
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.db import fetch_all
from src.api.security import decode_access_token, oauth2_scheme

router = APIRouter()


class Notification(BaseModel):
    """Notification model aligned with Mobile OpenAPI."""
    id: int = Field(..., description="Notification ID")
    userId: int = Field(..., description="User ID")
    message: str = Field(..., description="Notification message")
    read: bool = Field(..., description="Read status")
    # created_at omitted from OpenAPI but available if needed


async def _require_user_id(token: str) -> int:
    payload = decode_access_token(token)
    uid = payload.get("user_id") or payload.get("sub")
    try:
        return int(uid)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc


def _row_to_notification(row: dict) -> Notification:
    return Notification(
        id=int(row["id"]),
        userId=int(row["user_id"]),
        message=str(row["message"]),
        read=bool(row["read"]),
    )


# PUBLIC_INTERFACE
@router.get(
    "",
    tags=["notifications"],
    summary="Fetch user notifications",
    description="Returns notifications for the authenticated user.",
    response_model=List[Notification],
    responses={200: {"description": "List of notifications"}, 401: {"description": "Unauthorized"}},
)
async def list_notifications(token: str = Depends(oauth2_scheme)) -> List[Notification]:
    """Fetch notifications for the current user."""
    user_id = await _require_user_id(token)
    rows = await fetch_all(
        "SELECT id, user_id, message, read FROM notifications WHERE user_id=$1 ORDER BY id DESC",
        user_id,
    )
    return [_row_to_notification(r) for r in rows]
