"""Rooms routes for listing available rooms.

Endpoints:
- GET /api/v1/rooms: Retrieve available rooms and details (JWT protected)

DB Expectations:
- Room ORM model with fields: id, type, price, availability
"""

from typing import Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.models import Room as RoomORM
from src.api.security import get_current_user

router = APIRouter()


class Room(BaseModel):
    """Room model aligned with Mobile OpenAPI."""
    id: int = Field(..., description="Room ID")
    type: str = Field(..., description="Room type/name")
    price: float = Field(..., description="Price per night")
    availability: bool = Field(..., description="Availability flag")


# PUBLIC_INTERFACE
@router.get(
    "",
    tags=["bookings"],
    summary="Retrieve available rooms and details",
    description="Returns list of rooms including type, price, and availability.",
    response_model=List[Room],
    responses={200: {"description": "List of rooms"}},
    dependencies=[Depends(get_current_user)],
)
async def list_rooms(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Room]:
    """List rooms. JWT token is required; token is validated by get_current_user dependency."""
    rooms = db.query(RoomORM).order_by(RoomORM.id).all()
    return [
        Room(
            id=int(str(room.id)) if hasattr(room.id, 'hex') else int(room.id),
            type=room.type,
            price=float(room.price),
            availability=room.availability
        )
        for room in rooms
    ]
