from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.services.audit import log_event

# Tells Swagger where to log in; also makes the "Authorize" button appear
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Read the token, then load the user FROM THE DATABASE."""
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise error
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise error

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise error
    return user


def require_roles(*allowed_roles: UserRole):
    """Build a dependency that only lets the listed roles through."""
    def checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Role comes from the database, not the token, so changes apply at once
        if current_user.role not in allowed_roles:
            log_event(
                db, "access_denied", user_id=current_user.id,
                detail=f"{request.method} {request.url.path}",
                ip_address=request.client.host if request.client else None,
                success=False,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to do this",
            )
        return current_user
    return checker
