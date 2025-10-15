from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.user import User
from app.schemas.auth import GuestRegistrationRequest, AuthRequest, TokenResponse
from app.schemas.common import SuccessResponse
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()


@router.post(
    "/register",
    summary="Register new guest",
    response_model=SuccessResponse[dict],
    responses={
        400: {"description": "Bad Request"},
    },
)
# PUBLIC_INTERFACE
def register_guest(payload: GuestRegistrationRequest, session: Session = Depends(get_session)):
    """Register a new guest user. Returns standardized SuccessResponse."""
    # Check if user exists
    existing = session.exec(select(User).where(User.email == payload.email.lower())).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    user = User(
        email=payload.email.lower(),
        name=payload.name,
        phone=payload.phone,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return SuccessResponse(status="success", data={"id": str(user.id), "email": user.email, "name": user.name})


@router.post(
    "/login",
    summary="Authenticate guest",
    response_model=SuccessResponse[TokenResponse],
    responses={
        401: {"description": "Unauthorized"},
    },
)
# PUBLIC_INTERFACE
def login(payload: AuthRequest, session: Session = Depends(get_session)):
    """Authenticate user and return JWT token inside standardized SuccessResponse."""
    user = session.exec(select(User).where(User.email == payload.email.lower())).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=str(user.id))
    token = TokenResponse(access_token=access_token, token_type="bearer")

    return SuccessResponse(status="success", data=token)
