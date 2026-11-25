"""Request and reply shapes for the analysis endpoints (Phase 6W).
Every reply has a fixed shape, so nothing else (pseudonym, identity, user id) can leak.
Every result keeps the notice that the existing code produced."""
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.services import pattern_config as cfg

Number = int | float


# ---- category suggestion ----
class SuggestionItem(BaseModel):
    rank: int
    category: str
    score: float


class SuggestOut(BaseModel):
    suggestions: list[SuggestionItem]
    notice: str
    message: str | None = None
    model: str | None = None


# ---- pattern alerts and retaliation flag ----
class PatternMatchOut(BaseModel):
    case_id: str
    category: str
    filed_on: str
    similarity: float


class PatternOut(BaseModel):
    case_id: str
    matches: list[PatternMatchOut]
    threshold: float
    message: str
    notice: str


class RetaliationMatchOut(BaseModel):
    event_type: str
    event_date: str
    days_after: int


class RetaliationOut(BaseModel):
    retaliation_flag: bool
    window_days: int
    events_checked: int
    matches: list[RetaliationMatchOut]
    notice: str
    message: str


class PatternReportOut(BaseModel):
    pattern: PatternOut
    retaliation: RetaliationOut
    recurrence_count: int
    notice: str


# ---- risk score ----
class RiskRequest(BaseModel):
    frequency: Literal["unknown", "once", "a_few", "repeated"] = "unknown"
    power_imbalance: Literal["unknown", "none", "senior", "direct_manager"] = "unknown"


class ReasonOut(BaseModel):
    factor: str
    points: Number
    max_points: Number
    reason: str


class RiskOut(BaseModel):
    score: Number
    max_score: Number
    level: str
    reasons: list[ReasonOut]
    notice: str


class InputsUsedOut(BaseModel):
    frequency: str
    power_imbalance: str
    retaliation_flag: bool
    recurrence_count: int
    evidence_count: int


class RiskReportOut(BaseModel):
    risk: RiskOut
    inputs_used: InputsUsedOut
    pattern: PatternOut
    retaliation: RetaliationOut
    notice: str


# ---- adverse events ----
class AdverseEventCreate(BaseModel):
    event_type: str
    event_date: date

    @field_validator("event_type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in cfg.ADVERSE_EVENT_TYPES:
            raise ValueError("event_type must be one of: " + ", ".join(cfg.ADVERSE_EVENT_TYPES))
        return v


class AdverseEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    complaint_id: uuid.UUID
    event_type: str
    event_date: date
    recorded_by_role: str
    created_at: datetime


class AdverseEventResult(BaseModel):
    event: AdverseEventOut
    notice: str


class AdverseEventList(BaseModel):
    events: list[AdverseEventOut]
    notice: str