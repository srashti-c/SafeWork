import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.complaint import Complaint
from app.models.complaint_identity import ComplaintIdentity
from app.models.evidence import Evidence
from app.models.user import User, UserRole
from app.schemas.evidence import VerifyOut
from app.services.audit import log_event

MAX_BYTES = 10 * 1024 * 1024  # 10 MB
CHUNK = 1024 * 1024  # read 1 MB at a time

# allowed extension -> the only content type we accept for it
ALLOWED = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".txt": "text/plain",
}
# first bytes a real file of that type must start with (txt has none)
MAGIC = {
    ".pdf": b"%PDF-",
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
}


def _file_path(ev: Evidence) -> Path:
    return Path(settings.UPLOAD_DIR) / ev.stored_path


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def get_accessible_complaint(db: Session, user: User, complaint_id: uuid.UUID,
                             ip: str | None) -> Complaint:
    """Same rules as complaints: staff see all, an employee only their own.
    Everyone else gets 404 (so existence is not leaked) and an audit row."""
    complaint = db.get(Complaint, complaint_id)
    if complaint is not None:
        if user.role in (UserRole.reviewer, UserRole.ic_admin):
            return complaint
        owner_id = db.scalar(
            select(ComplaintIdentity.user_id).where(
                ComplaintIdentity.complaint_id == complaint_id
            )
        )
        if owner_id == user.id:
            return complaint
    log_event(
        db, "complaint_access_denied", user_id=user.id, resource_type="evidence",
        resource_id=str(complaint_id), detail="evidence access", ip_address=ip,
        success=False,
    )
    raise HTTPException(status_code=404, detail="Complaint not found")


def get_evidence(db: Session, complaint: Complaint, evidence_id: uuid.UUID) -> Evidence:
    ev = db.get(Evidence, evidence_id)
    if ev is None or ev.complaint_id != complaint.id:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev


def list_evidence(db: Session, complaint: Complaint) -> list[Evidence]:
    return list(db.scalars(
        select(Evidence).where(Evidence.complaint_id == complaint.id)
        .order_by(Evidence.uploaded_at)
    ))


def _reject(db: Session, user: User, complaint: Complaint, ip: str | None,
            code: int, reason: str):
    log_event(
        db, "evidence_upload_rejected", user_id=user.id, resource_type="complaint",
        resource_id=str(complaint.id), detail=reason, ip_address=ip, success=False,
    )
    raise HTTPException(status_code=code, detail=reason)


def save_upload(db: Session, user: User, complaint: Complaint, file: UploadFile,
                ip: str | None) -> Evidence:
    name = (file.filename or "").replace("\\", "/").split("/")[-1].strip()[:255]
    if not name:
        _reject(db, user, complaint, ip, 400, "File name is missing")
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED:
        _reject(db, user, complaint, ip, 415,
                "File type not allowed. Allowed: " + ", ".join(sorted(ALLOWED)))
    sent_type = (file.content_type or "").split(";")[0].strip().lower()
    if sent_type != ALLOWED[ext]:
        _reject(db, user, complaint, ip, 415, "File content type does not match its extension")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = uuid.uuid4().hex  # random; the original name is never used on disk
    stored = upload_dir / stored_name

    # Save and hash in the same pass (the server, not the client, makes the hash)
    h = hashlib.sha256()
    size = 0
    head = b""
    problem = None
    with open(stored, "wb") as out:
        while True:
            chunk = file.file.read(CHUNK)
            if not chunk:
                break
            if size == 0:
                head = chunk[:16]
            size += len(chunk)
            if size > MAX_BYTES:
                problem = (413, f"File is too large (maximum {MAX_BYTES // (1024 * 1024)} MB)")
                break
            h.update(chunk)
            out.write(chunk)
    if problem is None and size == 0:
        problem = (400, "File is empty")
    if problem is None and ext in MAGIC and not head.startswith(MAGIC[ext]):
        problem = (415, "File content does not look like its extension")
    if problem is not None:
        stored.unlink(missing_ok=True)
        _reject(db, user, complaint, ip, problem[0], problem[1])

    digest = h.hexdigest()
    ev = Evidence(
        complaint_id=complaint.id, original_filename=name, stored_path=stored_name,
        file_size=size, content_type=ALLOWED[ext], sha256=digest, uploaded_by=user.id,
    )
    try:
        db.add(ev)
        db.commit()
    except Exception:
        db.rollback()
        stored.unlink(missing_ok=True)
        raise
    db.refresh(ev)
    log_event(
        db, "evidence_uploaded", user_id=user.id, resource_type="evidence",
        resource_id=str(ev.id), detail=f"size={size} sha256={digest[:16]}", ip_address=ip,
    )
    return ev


def verify_evidence(db: Session, user: User, ev: Evidence, ip: str | None) -> VerifyOut:
    path = _file_path(ev)
    if not path.is_file():
        current, ok = None, False
        msg = "Stored file is missing, so integrity cannot be confirmed."
    else:
        current = sha256_of_file(path)
        ok = current == ev.sha256
        msg = ("Integrity matches: the file is the same as when it was uploaded."
               if ok else "File has changed since it was uploaded.")
    log_event(
        db, "evidence_verified", user_id=user.id, resource_type="evidence",
        resource_id=str(ev.id), detail=f"integrity_ok={ok}", ip_address=ip,
    )
    return VerifyOut(
        evidence_id=ev.id, integrity_ok=ok, message=msg, stored_sha256=ev.sha256,
        recalculated_sha256=current, verified_at=datetime.now(timezone.utc),
    )


def prepare_download(db: Session, user: User, ev: Evidence, ip: str | None) -> Path:
    path = _file_path(ev)
    if not path.is_file():
        log_event(
            db, "evidence_downloaded", user_id=user.id, resource_type="evidence",
            resource_id=str(ev.id), detail="stored file missing", ip_address=ip,
            success=False,
        )
        raise HTTPException(status_code=404, detail="Stored file is missing")
    log_event(
        db, "evidence_downloaded", user_id=user.id, resource_type="evidence",
        resource_id=str(ev.id), ip_address=ip,
    )
    return path