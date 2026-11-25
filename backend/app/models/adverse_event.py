import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdverseEvent(Base):
    """A work-related event (for example a demotion) recorded by staff for one complaint.
    It stores only the ROLE of the person who recorded it, never their user id
    (the user id goes into the audit log). Used only to prompt a human review of
    possible retaliation. It never proves retaliation."""
    __tablename__ = "adverse_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("complaints.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(30))
    event_date: Mapped[date] = mapped_column(Date)
    recorded_by_role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )