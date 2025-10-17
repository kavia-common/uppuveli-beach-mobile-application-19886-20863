from pydantic import BaseModel


# PUBLIC_INTERFACE
class RoomOut(BaseModel):
    id: int
    room_number: str
    room_type: str
    price: float
    is_available: bool
    description: str | None = None
