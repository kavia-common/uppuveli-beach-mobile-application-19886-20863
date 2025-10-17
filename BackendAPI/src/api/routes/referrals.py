from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps.auth import get_current_user
from src.db.models import Referral, User
from src.db.session import get_db
from src.db.schemas import ReferralOut

router = APIRouter(prefix="/referrals", tags=["Referrals"])


class ReferralRequest(BaseModel):
    code: str = Field(..., description="Referral code to redeem")


# PUBLIC_INTERFACE
@router.post("", summary="Redeem referral code", response_model=ReferralOut)
def redeem_referral(
    payload: ReferralRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """Redeem a referral code and attribute rewards (simple increments)."""
    referral = (
        db.execute(select(Referral).where(Referral.code == payload.code))
        .scalar_one_or_none()
    )
    if not referral:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid referral code")
    # prevent self-refer
    if referral.referrer_id == user.id:
        raise HTTPException(
            status_code=400, detail="Cannot use your own referral code"
        )

    # attribute referee if not set and increment rewards
    if referral.referee_id is None:
        referral.referee_id = user.id
        referral.rewards = (referral.rewards or 0) + 10
        db.add(referral)
        db.commit()
        db.refresh(referral)
    return referral
