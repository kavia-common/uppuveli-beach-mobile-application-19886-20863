from pydantic import BaseModel


# PUBLIC_INTERFACE
class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: float
    currency: str
    status: str
    method: str
    external_id: str | None = None
