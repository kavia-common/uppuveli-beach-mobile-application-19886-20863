"""Notifications providers stubs.

This module exposes simple stub functions to "send" notifications. They do not
integrate with real services; instead, they return canned responses suitable for
development and testing.

Environment variables (via src.api.config.get_settings()):
- FCM_KEY: optional Firebase Cloud Messaging server key for future real impl.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.api.config import get_settings


@dataclass
class SendResult:
    """Represents a result from sending a notification."""
    ok: bool
    provider: str
    reference: str
    message: str = "sent"


def _ts_ref(prefix: str) -> str:
    return f"{prefix}_{int(datetime.now(timezone.utc).timestamp())}"


# PUBLIC_INTERFACE
def send_push_notification(user_id: int, message: str, title: Optional[str] = None) -> SendResult:
    """Send a push notification via FCM stub.

    Returns a SendResult with a stub reference. Does not perform real network I/O.
    """
    _ = get_settings().fcm_key  # read for potential future conditions; not required for stub
    ref = _ts_ref("fcm_stub")
    return SendResult(ok=True, provider="fcm", reference=ref, message="sent")


# PUBLIC_INTERFACE
def send_email(recipient: str, subject: str, body: str) -> SendResult:
    """Send an email via stub provider. Always succeeds in stub mode."""
    ref = _ts_ref("email_stub")
    return SendResult(ok=True, provider="email", reference=ref, message="queued")


# PUBLIC_INTERFACE
def send_sms(phone_number: str, body: str) -> SendResult:
    """Send an SMS via stub provider. Always succeeds in stub mode."""
    ref = _ts_ref("sms_stub")
    return SendResult(ok=True, provider="sms", reference=ref, message="queued")
