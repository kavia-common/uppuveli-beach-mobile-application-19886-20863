from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.deps.auth import get_current_user
from src.db.models import ChatMessage, User
from src.db.session import get_db
from src.db.schemas import ChatMessageOut

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message text")


# PUBLIC_INTERFACE
@router.post("", summary="Send chat message", response_model=ChatMessageOut)
def send_chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Echo back the provided message and store it as a ChatMessage."""
    msg = ChatMessage(
        user_id=user.id,
        message=payload.message,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
