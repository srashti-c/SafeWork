"""Logic behind the analysis endpoints (Phase 6W). No rules live here: the rules are in
risk.py, pattern.py and retaliation.py. This file only loads data and joins the pieces.
Nothing here changes a complaint's category, status or priority."""
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.adverse_event import AdverseEvent
from app.models.category import Category
from app.models.complaint import Complaint
from app.models.evidence import Evidence
from app.models.user import User
from app.services import ml_bridge
from app.services import pattern_config as cfg
from app.services.risk import calculate_risk
from app.services.risk_inputs import risk_inputs_for

# None = use the real sentence-transformer. Tests replace this with a fast fake.
EMBEDDER = None


def get_complaint(db: Session, complaint_id: uuid.UUID) -> Complaint | None:
    return db.get(Complaint, complaint_id)


def _text_of(c: Complaint) -> str:
    return ((c.title or "") + "\n" + (c.description or "")).strip()


def _category_names(db: Session) -> dict:
    return {c.id: c.name for c in db.scalars(select(Category))}


def _category_name(db: Session, c: Complaint) -> str:
    return _category_names(db).get(c.category_id, "")


def _cases(db: Session) -> list[dict]:
    names = _category_names(db)
    return [
        {"id": str(c.id), "title": c.title or "", "description": c.description or "",
         "category": names.get(c.category_id, ""), "created_at": c.created_at}
        for c in db.scalars(select(Complaint))
    ]


def _events_of(db: Session, complaint_id: uuid.UUID) -> list[dict]:
    rows = db.scalars(select(AdverseEvent).where(AdverseEvent.complaint_id == complaint_id))
    return [{"event_type": e.event_type, "event_date": e.event_date} for e in rows]


def suggest_for(c: Complaint) -> dict:
    """Ask the Phase 4 model for 3 suggestions. SUGGESTION ONLY; changes nothing."""
    return ml_bridge.suggest(_text_of(c))


def pattern_report(db: Session, c: Complaint) -> dict:
    r = risk_inputs_for(str(c.id), _cases(db), _events_of(db, c.id), embedder=EMBEDDER)
    return {"pattern": r["similar_cases"], "retaliation": r["retaliation"],
            "recurrence_count": r["inputs"]["recurrence_count"], "notice": r["notice"]}


def risk_report(db: Session, c: Complaint, frequency: str, power_imbalance: str) -> dict:
    r = risk_inputs_for(str(c.id), _cases(db), _events_of(db, c.id), embedder=EMBEDDER)
    evidence_count = db.scalar(
        select(func.count()).select_from(Evidence).where(Evidence.complaint_id == c.id)) or 0
    risk = calculate_risk(_category_name(db, c), _text_of(c), frequency=frequency,
                          power_imbalance=power_imbalance, evidence_count=evidence_count,
                          **r["inputs"])
    return {
        "risk": risk,
        "inputs_used": {"frequency": frequency, "power_imbalance": power_imbalance,
                        "retaliation_flag": r["inputs"]["retaliation_flag"],
                        "recurrence_count": r["inputs"]["recurrence_count"],
                        "evidence_count": evidence_count},
        "pattern": r["similar_cases"], "retaliation": r["retaliation"], "notice": r["notice"],
    }


def add_event(db: Session, user: User, c: Complaint, event_type: str, event_date: date) -> AdverseEvent:
    ev = AdverseEvent(complaint_id=c.id, event_type=event_type, event_date=event_date,
                      recorded_by_role=user.role.value)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def list_events(db: Session, c: Complaint) -> list[AdverseEvent]:
    return list(db.scalars(
        select(AdverseEvent).where(AdverseEvent.complaint_id == c.id)
        .order_by(AdverseEvent.event_date, AdverseEvent.created_at)))


EVENTS_NOTICE = cfg.RETALIATION_NOTICE