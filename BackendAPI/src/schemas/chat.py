from datetime import datetime
from pydantic import BaseModel


# PUBLIC_INTERFACE
class ChatMessageOut(BaseModel):
    id: int
    user_id: int
    message: str
    timestamp: datetime
