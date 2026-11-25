import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.evidence import EvidenceOut, EvidenceUploadOut, VerifyOut
from app.services import evidence as svc

router = APIRouter(prefix="/complaints/{complaint_id}/evidence", tags=["evidence"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=EvidenceUploadOut, status_code=201)
def upload_evidence(
    complaint_id: uuid.UUID, request: Request, file: UploadFile = File(...),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    complaint = svc.get_accessible_complaint(db, user, complaint_id, _ip(request))
    return svc.save_upload(db, user, complaint, file, _ip(request))


@router.get("", response_model=list[EvidenceOut])
def list_evidence(
    complaint_id: uuid.UUID, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    complaint = svc.get_accessible_complaint(db, user, complaint_id, _ip(request))
    return svc.list_evidence(db, complaint)


@router.post("/{evidence_id}/verify", response_model=VerifyOut)
def verify_evidence(
    complaint_id: uuid.UUID, evidence_id: uuid.UUID, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    complaint = svc.get_accessible_complaint(db, user, complaint_id, _ip(request))
    ev = svc.get_evidence(db, complaint, evidence_id)
    return svc.verify_evidence(db, user, ev, _ip(request))


@router.get("/{evidence_id}/download")
def download_evidence(
    complaint_id: uuid.UUID, evidence_id: uuid.UUID, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    complaint = svc.get_accessible_complaint(db, user, complaint_id, _ip(request))
    ev = svc.get_evidence(db, complaint, evidence_id)
    path = svc.prepare_download(db, user, ev, _ip(request))
    return FileResponse(
        path, media_type=ev.content_type, filename=ev.original_filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )