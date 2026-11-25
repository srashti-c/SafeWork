import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

INTEGRITY_NOTICE = (
    "This proves only that the file is unchanged since it was uploaded to this system. "
    "It does NOT prove who created the file, that its content is true, or that it is "
    "legally admissible."
)


class EvidenceOut(BaseModel):
    """What anyone may see about a file. No user fields and no server path, on purpose."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_id: uuid.UUID
    original_filename: str
    file_size: int
    content_type: str
    sha256: str
    uploaded_at: datetime


class EvidenceUploadOut(EvidenceOut):
    notice: str = INTEGRITY_NOTICE


class VerifyOut(BaseModel):
    evidence_id: uuid.UUID
    integrity_ok: bool
    message: str
    stored_sha256: str
    recalculated_sha256: str | None
    verified_at: datetime
    notice: str = INTEGRITY_NOTICE