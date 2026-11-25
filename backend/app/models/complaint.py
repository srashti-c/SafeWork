import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrivacyMode(str, enum.Enum):
    identified = "identified"
    confidential = "confidential"
    pseudonymous = "pseudonymous"


class ComplaintStatus(str, enum.Enum):
    submitted = "submitted"
    under_review = "under_review"
    escalated_to_ic = "escalated_to_ic"
    closed = "closed"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Complaint(Base):
    """Case content only. There is NO user_id here on purpose.
    Who filed it lives in the separate complaint_identities table."""
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    privacy_mode: Mapped[PrivacyMode] = mapped_column(Enum(PrivacyMode, name="privacymode"))
    pseudonym: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaintstatus"), default=ComplaintStatus.submitted
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CaseStatusHistory(Base):
    """One row for every status change. Never edited, only added."""
    __tablename__ = "case_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("complaints.id"), index=True)
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30))
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)