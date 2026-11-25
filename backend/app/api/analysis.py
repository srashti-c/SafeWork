"""Analysis endpoints (Phase 6W): suggestions, risk score, pattern alerts, adverse events.
Reviewer / ic_admin only. Everyone else gets 404. Every call is audit-logged.
Nothing here changes a complaint, and nothing names or accuses anyone."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analysis import (
    AdverseEventCreate, AdverseEventList, AdverseEventResult, PatternReportOut,
    RiskReportOut, RiskRequest, SuggestOut,
)
from app.services import analysis as svc
from app.services import ml_bridge
from app.services.audit import log_event
from app.services.complaints import STAFF_ROLES

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def analysis_staff(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    """Staff only. Anyone else gets a plain 404 and an audit row."""
    if user.role not in STAFF_ROLES:
        log_event(db, "analysis_access_denied", user_id=user.id,
                  detail=f"{request.method} {request.url.path}",
                  ip_address=_ip(request), success=False)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return user


def _complaint(db: Session, complaint_id: uuid.UUID):
    c = svc.get_complaint(db, complaint_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    return c


@router.post("/complaints/{complaint_id}/suggest-category", response_model=SuggestOut)
def suggest_category(complaint_id: uuid.UUID, request: Request,
                     db: Session = Depends(get_db), user: User = Depends(analysis_staff)):
    c = _complaint(db, complaint_id)
    try:
        result = svc.suggest_for(c)
    except ml_bridge.MlUnavailable:
        log_event(db, "category_suggested", user_id=user.id, resource_type="complaint",
                  resource_id=str(c.id), detail="model unavailable",
                  ip_address=_ip(request), success=False)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Category suggestion is not available right now")
    log_event(db, "category_suggested", user_id=user.id, resource_type="complaint",
              resource_id=str(c.id), detail=f"suggestions={len(result.get('suggestions', []))}",
              ip_address=_ip(request))
    return result


@router.post("/complaints/{complaint_id}/risk", response_model=RiskReportOut)
def risk(complaint_id: uuid.UUID, body: RiskRequest, request: Request,
         db: Session = Depends(get_db), user: User = Depends(analysis_staff)):
    c = _complaint(db, complaint_id)
    try:
        result = svc.risk_report(db, c, body.frequency, body.power_imbalance)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid risk input")
    log_event(db, "risk_calculated", user_id=user.id, resource_type="complaint",
              resource_id=str(c.id), detail=f"level={result['risk']['level']}",
              ip_address=_ip(request))
    return result


@router.get("/complaints/{complaint_id}/patterns", response_model=PatternReportOut)
def patterns(complaint_id: uuid.UUID, request: Request,
             db: Session = Depends(get_db), user: User = Depends(analysis_staff)):
    c = _complaint(db, complaint_id)
    result = svc.pattern_report(db, c)
    log_event(db, "patterns_checked", user_id=user.id, resource_type="complaint",
              resource_id=str(c.id),
              detail=f"similar={len(result['pattern']['matches'])}, "
                     f"retaliation_flag={result['retaliation']['retaliation_flag']}",
              ip_address=_ip(request))
    return result


@router.post("/complaints/{complaint_id}/adverse-events",
             response_model=AdverseEventResult, status_code=status.HTTP_201_CREATED)
def add_adverse_event(complaint_id: uuid.UUID, body: AdverseEventCreate, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(analysis_staff)):
    c = _complaint(db, complaint_id)
    ev = svc.add_event(db, user, c, body.event_type, body.event_date)
    log_event(db, "adverse_event_added", user_id=user.id, resource_type="complaint",
              resource_id=str(c.id), detail=f"type={ev.event_type}", ip_address=_ip(request))
    return {"event": ev, "notice": svc.EVENTS_NOTICE}


@router.get("/complaints/{complaint_id}/adverse-events", response_model=AdverseEventList)
def list_adverse_events(complaint_id: uuid.UUID, request: Request,
                        db: Session = Depends(get_db), user: User = Depends(analysis_staff)):
    c = _complaint(db, complaint_id)
    events = svc.list_events(db, c)
    log_event(db, "adverse_events_listed", user_id=user.id, resource_type="complaint",
              resource_id=str(c.id), detail=f"count={len(events)}", ip_address=_ip(request))
    return {"events": events, "notice": svc.EVENTS_NOTICE}