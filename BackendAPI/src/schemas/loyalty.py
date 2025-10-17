from pydantic import BaseModel


# PUBLIC_INTERFACE
class LoyaltyAccountOut(BaseModel):
    id: int
    user_id: int
    points: int
    tier: str
