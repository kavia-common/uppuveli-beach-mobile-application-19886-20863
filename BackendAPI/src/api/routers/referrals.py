"""Referrals routes.

Endpoints:
- POST /api/v1/referrals: Submit referral code or generate new for current user (JWT protected)

Behavior:
- If 'code' provided: validate and credit rewards
- If no 'code': generate a unique code for the user and return it
"""

import secrets
import string
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.api.db import get_db
from src.api.models import Referral as ReferralORM, ReferralStatus
from src.api.security import get_current_user

router = APIRouter()


class ReferralRequest(BaseModel):
    """Request to submit a referral code or generate new."""
    code: Optional[str] = Field(None, description="Referral code to submit; if omitted generates/refetches user's code")


class Referral(BaseModel):
    """Referral response aligned with Mobile OpenAPI."""
    userId: int = Field(..., description="User ID")
    code: str = Field(..., description="Referral code")
    rewards: int = Field(..., description="Accumulated rewards points")


def _uuid_to_int(uuid_val) -> int:
    """Convert UUID to int representation for API compatibility."""
    if isinstance(uuid_val, UUID):
        return int(uuid_val.hex, 16) % (10**18)
    return int(uuid_val)


def _generate_code(length: int = 8) -> str:
    """Generate a random alphanumeric referral code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# PUBLIC_INTERFACE
@router.post(
    "",
    tags=["loyalty"],
    summary="Submit referral code or generate new",
    description="Submits a referral code for credit or generates a new code for the current user.",
    response_model=Referral,
    responses={
        200: {"description": "Referral processed"},
        400: {"description": "Invalid code"},
        401: {"description": "Unauthorized"},
    },
    dependencies=[Depends(get_current_user)],
)
async def submit_or_generate(
    payload: ReferralRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Referral:
    """Process referral: apply a code or generate the user's code."""
    user_id_str = current_user.get("user_id") or current_user.get("sub")
    user_id_uuid = UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str

    # If code provided, attempt to redeem
    if payload.code:
        ref = db.query(ReferralORM).filter(
            ReferralORM.code == payload.code.upper()
        ).first()
        
        if not ref:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code"
            )
        
        if ref.user_id == user_id_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use own referral code"
            )

        # Credit referrer rewards (+10 points)
        ref.rewards += 10
        ref.status = ReferralStatus.USED
        db.commit()
        db.refresh(ref)

        return Referral(
            userId=_uuid_to_int(ref.user_id),
            code=ref.code,
            rewards=ref.rewards
        )

    # No code: ensure current user has a referral code, generate if missing
    existing = db.query(ReferralORM).filter(
        ReferralORM.user_id == user_id_uuid
    ).first()
    
    if existing:
        return Referral(
            userId=_uuid_to_int(user_id_uuid),
            code=existing.code,
            rewards=existing.rewards
        )

    # Generate unique code with retry logic
    for _ in range(5):
        code = _generate_code()
        try:
            referral = ReferralORM(
                user_id=user_id_uuid,
                code=code,
                status=ReferralStatus.GENERATED,
                rewards=0
            )
            db.add(referral)
            db.commit()
            db.refresh(referral)
            
            return Referral(
                userId=_uuid_to_int(user_id_uuid),
                code=code,
                rewards=0
            )
        except IntegrityError:
            db.rollback()
            continue

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not generate referral code"
    )
