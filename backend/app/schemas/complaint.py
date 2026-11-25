import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.complaint import ComplaintStatus, PrivacyMode


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None = None


class ComplaintCreate(BaseModel):
    category_id: int
    privacy_mode: PrivacyMode
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    incident_date: date | None = None


class ComplaintOut(BaseModel):
    """Case content only. There is no user field on purpose."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    category_id: int
    privacy_mode: PrivacyMode
    pseudonym: str | None = None
    title: str
    description: str
    incident_date: date | None = None
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime


class StatusUpdate(BaseModel):
    new_status: ComplaintStatus
    note: str | None = Field(default=None, max_length=500)


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    complaint_id: uuid.UUID
    old_status: str | None = None
    new_status: str
    changed_by: int
    note: str | None = None
    created_at: datetime


class IdentityOut(BaseModel):
    complaint_id: uuid.UUID
    user_id: int
    email: str
    full_name: str
    privacy_mode: PrivacyMode
    notice: str