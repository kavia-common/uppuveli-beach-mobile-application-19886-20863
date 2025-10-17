from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps.auth import get_current_user
from src.db.models import LoyaltyAccount, LoyaltyHistory, User
from src.db.session import get_db
from src.db.schemas import LoyaltyAccountOut, LoyaltyHistoryOut

router = APIRouter(prefix="/loyalty", tags=["Loyalty"])


class LoyaltyResponse(LoyaltyAccountOut):
    history: List[LoyaltyHistoryOut] = []


# PUBLIC_INTERFACE
@router.get("", summary="Get current user's loyalty", response_model=LoyaltyResponse)
def get_loyalty(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Return loyalty account summary and history for current user."""
    account = (
        db.execute(
            select(LoyaltyAccount).where(LoyaltyAccount.user_id == user.id)
        )
        .scalar_one_or_none()
    )
    if not account:
        # return zeroed account info when none exists
        empty = LoyaltyResponse(
            id=0,
            user_id=user.id,
            points=0,
            tier="basic",
            history=[],
        )
        return empty
    history = (
        db.execute(
            select(LoyaltyHistory).where(
                LoyaltyHistory.account_id == account.id
            )
        )
        .scalars()
        .all()
    )
    base = LoyaltyAccountOut.model_validate(account).model_dump()
    return LoyaltyResponse.model_validate({**base, "history": history})
