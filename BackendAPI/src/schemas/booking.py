from datetime import date
from pydantic import BaseModel


# PUBLIC_INTERFACE
class BookingOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    status: str
    check_in: date
    check_out: date
