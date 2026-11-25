from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import RoleUpdate, UserOut
from app.services.audit import log_event

router = APIRouter(prefix="/users", tags=["users"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    """Any logged-in user can see their own profile."""
    return current_user


@router.get("/", response_model=list[UserOut])
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ic_admin)),
):
    """Only ic_admin can list all users. Viewing the list is logged."""
    log_event(db, "user_list_viewed", user_id=admin.id, resource_type="user",
              ip_address=client_ip(request))
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/{user_id}/role", response_model=UserOut)
def change_role(
    user_id: int,
    data: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ic_admin)),
):
    """Only ic_admin can change someone's role."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")
    old_role = user.role.value
    user.role = data.role
    db.commit()
    db.refresh(user)
    log_event(db, "role_changed", user_id=admin.id, resource_type="user",
              resource_id=str(user.id), detail=f"{old_role} -> {data.role.value}",
              ip_address=client_ip(request))
    return user
