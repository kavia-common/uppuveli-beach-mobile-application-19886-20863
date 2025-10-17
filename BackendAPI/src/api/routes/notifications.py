from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps.auth import get_current_user
from src.db.models import Notification, User
from src.db.session import get_db
from src.db.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# PUBLIC_INTERFACE
@router.get("", summary="List user notifications", response_model=List[NotificationOut])
def list_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationOut]:
    """Return notifications for the current user."""
    items = db.execute(select(Notification).where(Notification.user_id == user.id)).scalars().all()
    return items
