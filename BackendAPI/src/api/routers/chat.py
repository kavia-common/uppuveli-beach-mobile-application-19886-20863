"""Chat routes for chatbot/live chat.

Endpoints:
- POST /api/v1/chat: Send message to chatbot/live chat (JWT protected)

Behavior:
- Stores the message in 'chat_messages' table (if exists)
- Returns the message with timestamp; could be extended to call 3rd-party chatbot
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.db import execute, fetch_one
from src.api.security import decode_access_token, oauth2_scheme

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


async def _require_user_id(token: str) -> int:
    payload = decode_access_token(token)
    uid = payload.get("user_id") or payload.get("sub")
    try:
        return int(uid)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc


def _row_to_chat_message(row: Dict[str, Any]) -> ChatMessage:
    return ChatMessage(
        id=int(row["id"]),
        userId=int(row["user_id"]),
        message=str(row["message"]),
        timestamp=row["created_at"],
    )


# PUBLIC_INTERFACE
@router.post(
    "",
    tags=["chat"],
    summary="Send message to chatbot/live chat",
    description="Sends a message and returns the stored representation with timestamp.",
    response_model=ChatMessage,
    responses={200: {"description": "Chat message sent"}, 401: {"description": "Unauthorized"}},
)
async def send_message(payload: ChatMessageRequest, token: str = Depends(oauth2_scheme)) -> ChatMessage:
    """Accepts a chat message, persists it, and echoes it back."""
    user_id = await _require_user_id(token)
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message is required")

    # Persist message
    await execute(
        "INSERT INTO chat_messages (user_id, message) VALUES ($1, $2)",
        user_id,
        payload.message.strip(),
    )
    row = await fetch_one(
        "SELECT id, user_id, message, created_at FROM chat_messages WHERE user_id=$1 ORDER BY id DESC LIMIT 1",
        user_id,
    )
    assert row is not None
    return _row_to_chat_message(row)
