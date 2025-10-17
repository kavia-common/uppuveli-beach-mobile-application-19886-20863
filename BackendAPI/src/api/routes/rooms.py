from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.api.deps.auth import get_current_user
from src.db.models import Room, User
from src.db.session import get_db
from src.db.schemas import RoomOut

router = APIRouter(prefix="/rooms", tags=["Rooms"])


# PUBLIC_INTERFACE
@router.get("", summary="List available rooms", response_model=List[RoomOut])
def list_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RoomOut]:
    """Return the list of rooms (authentication required)."""
    rooms = db.execute(select(Room)).scalars().all()
    return rooms
