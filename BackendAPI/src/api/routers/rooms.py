"""Rooms routes for listing available rooms.

Endpoints:
- GET /api/v1/rooms: Retrieve available rooms and details (JWT protected)

DB Expectations:
- rooms table example fields:
    id SERIAL PRIMARY KEY
    type TEXT NOT NULL
    price NUMERIC(10,2) NOT NULL
    availability BOOLEAN NOT NULL DEFAULT TRUE
"""

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.db import fetch_all
from src.api.security import oauth2_scheme

router = APIRouter()


class Room(BaseModel):
    """Room model aligned with Mobile OpenAPI."""
    id: int = Field(..., description="Room ID")
    type: str = Field(..., description="Room type/name")
    price: float = Field(..., description="Price per night")
    availability: bool = Field(..., description="Availability flag")


def _row_to_room(row: dict) -> Room:
    return Room(
        id=int(row["id"]),
        type=str(row["type"]),
        price=float(row["price"]),
        availability=bool(row["availability"]),
    )


# PUBLIC_INTERFACE
@router.get(
    "",
    tags=["bookings"],
    summary="Retrieve available rooms and details",
    description="Returns list of rooms including type, price, and availability.",
    response_model=List[Room],
    responses={200: {"description": "List of rooms"}},
)
async def list_rooms(token: str = Depends(oauth2_scheme)) -> List[Room]:
    """List rooms. JWT token is required; token is validated by dependency."""
    rows = await fetch_all(
        "SELECT id, type, price, availability FROM rooms ORDER BY id ASC"
    )
    return [_row_to_room(r) for r in rows]
