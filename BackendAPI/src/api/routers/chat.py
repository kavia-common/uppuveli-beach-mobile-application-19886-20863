"""Chat routes for chatbot/live chat.

Endpoints:
- POST /api/v1/chat: Send message to chatbot/live chat (JWT protected)

Behavior:
- Stub implementation returning deterministic response
- Could be extended to persist messages or call chatbot service
"""

from datetime import datetime, timezone
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.security import get_current_user

router = APIRouter()


class ChatMessageRequest(BaseModel):
    """Incoming chat message payload."""
    message: str = Field(..., description="Message content")


class ChatMessage(BaseModel):
    """Chat message aligned with Mobile OpenAPI."""
    id: int = Field(..., description="Message ID")
    userId: int = Field(..., description="User ID")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Creation timestamp")


def _uuid_to_int(uuid_val) -> int:
    """Convert UUID to int representation for API compatibility."""
    if isinstance(uuid_val, UUID):
        return int(uuid_val.hex, 16) % (10**18)
    return int(uuid_val)


# PUBLIC_INTERFACE
@router.post(
    "",
    tags=["chat"],
    summary="Send message to chatbot/live chat",
    description="Sends a message and returns the stored representation with timestamp.",
    response_model=ChatMessage,
    responses={200: {"description": "Chat message sent"}, 401: {"description": "Unauthorized"}},
    dependencies=[Depends(get_current_user)],
)
async def send_message(
    payload: ChatMessageRequest,
    current_user: Dict = Depends(get_current_user)
) -> ChatMessage:
    """Accepts a chat message and returns stub response. Future: persist to DB and integrate chatbot."""
    user_id_str = current_user.get("user_id") or current_user.get("sub")
    
    if not payload.message or not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="message is required"
        )

    # Stub response: return deterministic chat message
    # In production, persist to ChatMessage ORM and call chatbot service
    stub_id = abs(hash(payload.message)) % (10**9)
    
    return ChatMessage(
        id=stub_id,
        userId=_uuid_to_int(UUID(user_id_str)) if isinstance(user_id_str, str) else _uuid_to_int(user_id_str),
        message=payload.message.strip(),
        timestamp=datetime.now(timezone.utc)
    )
