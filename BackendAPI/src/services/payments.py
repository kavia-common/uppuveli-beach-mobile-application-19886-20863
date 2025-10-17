import uuid
from typing import Tuple


# PUBLIC_INTERFACE
def process_payment_stub(
    amount: float,
    method: str,
    booking_id: int,
    user_id: int,
) -> Tuple[str, str]:
    """Mock payment processing; returns (external_id, status)."""
    if method not in {"stripe", "paypal", "wallet"}:
        # mark as failed to emulate gateway validation
        return (f"mock_{uuid.uuid4().hex}", "failed")
    external = f"mock_{method}_{uuid.uuid4().hex}"
    return (external, "succeeded")
