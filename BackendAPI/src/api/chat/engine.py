"""Chat engine stub.

Provides a minimal chatbot engine that returns either a canned response for
common greetings or echoes the message back with a friendly prefix.

Intended for local development; no external AI services are called.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ChatEngineResponse:
    """Represents a reply from the chat engine."""
    text: str
    created_at: float  # epoch seconds


_GREETINGS = {"hi", "hello", "hey", "good morning", "good evening", "ayubowan", "vanakkam"}


# PUBLIC_INTERFACE
def generate_reply(user_message: str) -> ChatEngineResponse:
    """Return a canned response or echo message as a reply."""
    msg = (user_message or "").strip()
    now = datetime.now(timezone.utc).timestamp()
    if not msg:
        return ChatEngineResponse(text="I'm here to help. Please type your message.", created_at=now)

    if msg.lower() in _GREETINGS:
        return ChatEngineResponse(
            text="Hello! Welcome to Uppuveli Beach by DSK. How can I assist with your stay?",
            created_at=now,
        )

    return ChatEngineResponse(text=f"You said: {msg}", created_at=now)
