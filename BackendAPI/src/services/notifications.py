from typing import Optional


# PUBLIC_INTERFACE
def send_push_notification_stub(user_id: int, message: str, type_: Optional[str] = None) -> bool:
    """Mock notification sender; always returns True to indicate success."""
    return True
