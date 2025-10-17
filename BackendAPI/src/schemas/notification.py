from pydantic import BaseModel


# PUBLIC_INTERFACE
class NotificationOut(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    type: str | None = None
