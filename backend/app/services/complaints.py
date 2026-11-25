import secrets
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.complaint import (
    CaseStatusHistory, Complaint, ComplaintStatus, PrivacyMode,
)
from app.models.complaint_identity import ComplaintIdentity
from app.models.user import User, UserRole
from app.schemas.complaint import ComplaintCreate
from app.services.audit import log_event

STAFF_ROLES = {UserRole.reviewer, UserRole.ic_admin}

# Which status can move to which. "closed" is final.
ALLOWED_TRANSITIONS = {
    ComplaintStatus.submitted: {ComplaintStatus.under_review},
    ComplaintStatus.under_review: {ComplaintStatus.escalated_to_ic, ComplaintStatus.closed},
    ComplaintStatus.escalated_to_ic: {ComplaintStatus.closed},
    ComplaintStatus.closed: set(),
}


def can_view_identity(role: UserRole, mode: PrivacyMode) -> bool:
    """ic_admin: always. reviewer: only when the person chose 'identified'."""
    if role == UserRole.ic_admin:
        return True
    if role == UserRole.reviewer and mode == PrivacyMode.identified:
        return True
    return False


def create_complaint(db: Session, user: User, data: ComplaintCreate, ip: str | None) -> Complaint:
    if db.get(Category, data.category_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category")

    pseudonym = None
    if data.privacy_mode == PrivacyMode.pseudonymous:
        pseudonym = "Reporter-" + secrets.token_hex(3)  # random alias, not the name

    complaint = Complaint(
        category_id=data.category_id,
        privacy_mode=data.privacy_mode,
        pseudonym=pseudonym,
        title=data.title,
        description=data.description,
        incident_date=data.incident_date,
        status=ComplaintStatus.submitted,
    )
    db.add(complaint)
    db.flush()  # gives the complaint its id

    # The ONLY place that links the case to the person
    db.add(ComplaintIdentity(complaint_id=complaint.id, user_id=user.id))
    db.add(CaseStatusHistory(
        complaint_id=complaint.id, old_status=None,
        new_status=ComplaintStatus.submitted.value, changed_by=user.id,
        note="Complaint submitted",
    ))
    db.commit()
    db.refresh(complaint)

    log_event(db, "complaint_created", user_id=user.id, resource_type="complaint",
              resource_id=str(complaint.id), detail=f"privacy_mode={data.privacy_mode.value}",
              ip_address=ip)
    return complaint


def list_complaints(db: Session, user: User) -> list[Complaint]:
    query = select(Complaint).order_by(Complaint.created_at.desc())
    if user.role not in STAFF_ROLES:
        # employees: only their own, found through the identity table
        query = query.join(
            ComplaintIdentity, ComplaintIdentity.complaint_id == Complaint.id
        ).where(ComplaintIdentity.user_id == user.id)
    return list(db.scalars(query))


def get_complaint_for_user(db: Session, user: User, complaint_id: uuid.UUID,
                           ip: str | None) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    if user.role not in STAFF_ROLES:
        owner = db.scalar(select(ComplaintIdentity).where(
            ComplaintIdentity.complaint_id == complaint_id,
            ComplaintIdentity.user_id == user.id,
        ))
        if owner is None:
            log_event(db, "complaint_access_denied", user_id=user.id,
                      resource_type="complaint", resource_id=str(complaint_id),
                      ip_address=ip, success=False)
            # 404, not 403, so outsiders cannot learn that the case exists
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    return complaint


def change_status(db: Session, user: User, complaint: Complaint,
                  new_status: ComplaintStatus, note: str | None, ip: str | None) -> Complaint:
    old = complaint.status
    if new_status not in ALLOWED_TRANSITIONS[old]:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot move from {old.value} to {new_status.value}",
        )
    complaint.status = new_status
    complaint.updated_at = datetime.now(timezone.utc)
    db.add(CaseStatusHistory(
        complaint_id=complaint.id, old_status=old.value,
        new_status=new_status.value, changed_by=user.id, note=note,
    ))
    db.commit()
    db.refresh(complaint)
    log_event(db, "complaint_status_changed", user_id=user.id, resource_type="complaint",
              resource_id=str(complaint.id), detail=f"{old.value} -> {new_status.value}",
              ip_address=ip)
    return complaint