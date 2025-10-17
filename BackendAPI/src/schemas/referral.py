from pydantic import BaseModel


# PUBLIC_INTERFACE
class ReferralOut(BaseModel):
    id: int
    referrer_id: int | None = None
    referee_id: int | None = None
    code: str
    rewards: int
