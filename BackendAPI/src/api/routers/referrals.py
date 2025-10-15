"""Referrals routes.

Endpoints:
- POST /api/v1/referrals: Submit referral code or generate new for current user (JWT protected)

Behavior:
- If 'code' provided: validate and credit rewards if applicable
- If no 'code': generate a unique code for the user and return it

DB Expectations:
- referrals table:
    id SERIAL PRIMARY KEY
    user_id INTEGER NOT NULL REFERENCES users(id)
    code TEXT UNIQUE NOT NULL
    rewards INTEGER NOT NULL DEFAULT 0

- referral_uses table (optional):
    id SERIAL PRIMARY KEY
    referrer_user_id INTEGER NOT NULL
    referee_user_id INTEGER NOT NULL
    code TEXT NOT NULL
    created_at TIMESTAMPTZ DEFAULT now()
"""

import secrets
import string
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.db import execute, fetch_one
from src.api.security import decode_access_token, oauth2_scheme

router = APIRouter()


class ReferralRequest(BaseModel):
    """Request to submit a referral code or generate new."""
    code: Optional[str] = Field(None, description="Referral code to submit; if omitted generates/refetches user's code")


class Referral(BaseModel):
    """Referral response aligned with Mobile OpenAPI."""
    userId: int = Field(..., description="User ID")
    code: str = Field(..., description="Referral code")
    rewards: int = Field(..., description="Accumulated rewards points")


async def _require_user_id(token: str) -> int:
    payload = decode_access_token(token)
    uid = payload.get("user_id") or payload.get("sub")
    try:
        return int(uid)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc


def _generate_code(length: int = 8) -> str:
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
)
async def submit_or_generate(payload: ReferralRequest, token: str = Depends(oauth2_scheme)) -> Referral:
    """Process referral: apply a code or generate the user's code."""
    user_id = await _require_user_id(token)

    # If code provided, attempt to redeem (referee is current user)
    if payload.code:
        ref = await fetch_one("SELECT user_id, code, rewards FROM referrals WHERE code=$1", payload.code.upper())
        if not ref:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
        referrer_id = int(ref["user_id"])
        if referrer_id == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot use own referral code")

        # Credit referrer rewards (+10 points for example) and record use (idempotency not enforced in stub)
        await execute("UPDATE referrals SET rewards = rewards + 10 WHERE code=$1", payload.code.upper())
        await execute(
            "INSERT INTO referral_uses (referrer_user_id, referee_user_id, code) VALUES ($1, $2, $3)",
            referrer_id,
            user_id,
            payload.code.upper(),
        )
        updated = await fetch_one("SELECT user_id, code, rewards FROM referrals WHERE code=$1", payload.code.upper())
        assert updated is not None
        return Referral(userId=int(updated["user_id"]), code=updated["code"], rewards=int(updated["rewards"]))

    # No code: ensure current user has a referral code, generate if missing
    existing = await fetch_one("SELECT user_id, code, rewards FROM referrals WHERE user_id=$1", user_id)
    if existing:
        return Referral(userId=user_id, code=existing["code"], rewards=int(existing["rewards"]))

    # Generate unique code; retry a few times on collision
    for _ in range(5):
        code = _generate_code()
        try:
            await execute("INSERT INTO referrals (user_id, code, rewards) VALUES ($1, $2, 0)", user_id, code)
            return Referral(userId=user_id, code=code, rewards=0)
        except Exception:
            continue

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not generate referral code")
