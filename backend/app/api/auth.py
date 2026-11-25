from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import Token, UserCreate, UserOut
from app.services.audit import log_event

router = APIRouter(prefix="/auth", tags=["auth"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, request: Request, db: Session = Depends(get_db)):
    email = data.email.lower()

    if db.scalar(select(User).where(User.email == email)):
        log_event(db, "register_failed", detail=f"duplicate email: {email}",
                  ip_address=client_ip(request), success=False)
        raise HTTPException(status_code=400, detail="Email already registered")

    # Public registration ALWAYS creates an employee
    user = User(
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=UserRole.employee,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(db, "register", user_id=user.id, resource_type="user",
              resource_id=str(user.id), ip_address=client_ip(request))
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form.username.lower()
    user = db.scalar(select(User).where(User.email == email))

    if not user or not verify_password(form.password, user.hashed_password):
        log_event(db, "login_failed", user_id=user.id if user else None,
                  detail=f"email: {email}", ip_address=client_ip(request), success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        log_event(db, "login_blocked", user_id=user.id, detail="account disabled",
                  ip_address=client_ip(request), success=False)
        raise HTTPException(status_code=403, detail="Account is disabled")

    log_event(db, "login_success", user_id=user.id, ip_address=client_ip(request))
    return Token(access_token=create_access_token(user.id, user.role.value))
