"""Notifications routes.

Endpoints:
- GET /api/v1/notifications: Fetch user notifications (JWT protected)

DB Expectations:
- Notification ORM model with relationship to User
"""

from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.models import Notification as NotificationORM
from src.api.security import get_current_user

router = APIRouter()


class Notification(BaseModel):
    """Notification model aligned with Mobile OpenAPI."""
    id: int = Field(..., description="Notification ID")
    userId: int = Field(..., description="User ID")
    message: str = Field(..., description="Notification message")
    read: bool = Field(..., description="Read status")


def _uuid_to_int(uuid_val) -> int:
    """Convert UUID to int representation for API compatibility."""
    if isinstance(uuid_val, UUID):
        return int(uuid_val.hex, 16) % (10**18)
    return int(uuid_val)


# PUBLIC_INTERFACE
@router.get(
    "",
    tags=["notifications"],
    summary="Fetch user notifications",
    description="Returns notifications for the authenticated user.",
    response_model=List[Notification],
    responses={200: {"description": "List of notifications"}, 401: {"description": "Unauthorized"}},
    dependencies=[Depends(get_current_user)],
)
async def list_notifications(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Notification]:
    """Fetch notifications for the current user."""
    user_id_str = current_user.get("user_id") or current_user.get("sub")
    user_id_uuid = UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str

    notifications = db.query(NotificationORM).filter(
        NotificationORM.user_id == user_id_uuid
    ).order_by(NotificationORM.created_at.desc()).all()

    return [
        Notification(
            id=_uuid_to_int(notif.id),
            userId=_uuid_to_int(notif.user_id),
            message=notif.message,
            read=notif.is_read
        )
        for notif in notifications
    ]
