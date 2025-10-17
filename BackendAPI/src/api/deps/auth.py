from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import decode_token
from src.db.models import User, AdminUser
from src.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# PUBLIC_INTERFACE
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Return the current authenticated user based on Bearer token."""
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    user = db.execute(select(User).where(User.id == int(sub))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user"
        )
    return user


# PUBLIC_INTERFACE
def get_current_admin(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> AdminUser:
    """Return the current admin user based on Bearer token. Requires admin claim."""
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if not payload.get("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    sub = payload.get("sub")
    admin = (
        db.execute(select(AdminUser).where(AdminUser.id == int(sub)))
        .scalar_one_or_none()
    )
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found"
        )
    return admin
