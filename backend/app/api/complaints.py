import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.category import Category
from app.models.complaint import CaseStatusHistory, Complaint
from app.models.complaint_identity import ComplaintIdentity
from app.models.user import User
from app.schemas.complaint import (
    CategoryOut, ComplaintCreate, ComplaintOut, IdentityOut,
    StatusHistoryOut, StatusUpdate,
)
from app.services import complaints as svc
from app.services.audit import log_event

router = APIRouter(prefix="/complaints", tags=["complaints"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def staff_user(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    """Only reviewer or ic_admin. A refusal is written to the audit log."""
    if user.role not in svc.STAFF_ROLES:
        log_event(db, "access_denied", user_id=user.id,
                  detail=f"{request.method} {request.url.path}",
                  ip_address=_ip(request), success=False)
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "You do not have permission to do this")
    return user


@categories_router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    return list(db.scalars(select(Category).order_by(Category.name)))


@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(data: ComplaintCreate, request: Request,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    return svc.create_complaint(db, user, data, _ip(request))


@router.get("", response_model=list[ComplaintOut])
def list_complaints(db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    return svc.list_complaints(db, user)


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: uuid.UUID, request: Request,
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    return svc.get_complaint_for_user(db, user, complaint_id, _ip(request))


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(complaint_id: uuid.UUID, data: StatusUpdate, request: Request,
                  db: Session = Depends(get_db),
                  user: User = Depends(staff_user)):
    complaint = svc.get_complaint_for_user(db, user, complaint_id, _ip(request))
    return svc.change_status(db, user, complaint, data.new_status, data.note, _ip(request))


@router.get("/{complaint_id}/history", response_model=list[StatusHistoryOut])
def status_history(complaint_id: uuid.UUID, request: Request,
                   db: Session = Depends(get_db),
                   user: User = Depends(staff_user)):
    svc.get_complaint_for_user(db, user, complaint_id, _ip(request))
    return list(db.scalars(
        select(CaseStatusHistory)
        .where(CaseStatusHistory.complaint_id == complaint_id)
        .order_by(CaseStatusHistory.id)
    ))


@router.get("/{complaint_id}/identity", response_model=IdentityOut)
def reveal_identity(
    complaint_id: uuid.UUID, request: Request,
    reason: str = Query(min_length=10, max_length=300),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """The ONLY way to see who filed a complaint. Always audit-logged."""
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")

    if not svc.can_view_identity(user.role, complaint.privacy_mode):
        log_event(db, "identity_access_denied", user_id=user.id,
                  resource_type="complaint", resource_id=str(complaint_id),
                  detail=f"reason given: {reason}"[:500],
                  ip_address=_ip(request), success=False)
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "You are not allowed to see the identity for this complaint")

    link = db.scalar(select(ComplaintIdentity).where(
        ComplaintIdentity.complaint_id == complaint_id))
    person = db.get(User, link.user_id)

    log_event(db, "identity_viewed", user_id=user.id, resource_type="complaint",
              resource_id=str(complaint_id), detail=f"reason: {reason}"[:500],
              ip_address=_ip(request))
    return IdentityOut(
        complaint_id=complaint_id, user_id=person.id, email=person.email,
        full_name=person.full_name, privacy_mode=complaint.privacy_mode,
        notice="This access has been logged. SafeWork reduces who can see "
               "identity, but it does not promise absolute anonymity.",
    )