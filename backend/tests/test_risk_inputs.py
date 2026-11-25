from datetime import datetime, timedelta, timezone

import pytest

from app.services import pattern_config as cfg
from app.services import risk_inputs
from app.services.risk import calculate_risk

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
TABLE = {"x1": [1.0, 0.0], "x2": [1.0, 0.0], "far": [0.0, 1.0]}


def emb(texts):
    return [TABLE[t] for t in texts]


def case(cid, text, days=0):
    return {"id": cid, "title": "", "description": text, "category": "Other",
            "created_at": T0 + timedelta(days=days)}


CASES = [case("old", "x1", -30), case("target", "x2", 0), case("other", "far", -5)]


def ev(days, kind="transfer"):
    return {"event_type": kind, "event_date": (T0 + timedelta(days=days)).date()}


def run(events, **kw):
    return risk_inputs.risk_inputs_for("target", CASES, events, emb, 0.9, **kw)


def test_inputs_have_exactly_the_two_phase5_names():
    r = run([ev(10)])
    assert set(r["inputs"]) == {"retaliation_flag", "recurrence_count"}
    assert r["inputs"]["retaliation_flag"] is True
    assert r["inputs"]["recurrence_count"] == 1 and type(r["inputs"]["recurrence_count"]) is int


def test_no_event_and_no_similar_case_gives_off_and_zero():
    r = risk_inputs.risk_inputs_for("old", CASES, [], emb, 0.9)
    assert r["inputs"] == {"retaliation_flag": False, "recurrence_count": 0}


def test_phase5_risk_score_accepts_the_inputs():
    r = run([ev(10)])
    with_inputs = calculate_risk("Other", "text", **r["inputs"])["score"]
    assert with_inputs == calculate_risk("Other", "text", retaliation_flag=True,
                                         recurrence_count=1)["score"]
    assert with_inputs > calculate_risk("Other", "text")["score"]


def test_event_outside_window_does_not_raise_flag():
    assert run([ev(91)])["inputs"]["retaliation_flag"] is False
    assert run([ev(91)], window_days=100)["inputs"]["retaliation_flag"] is True


def test_notices_are_present_everywhere():
    r = run([ev(10)])
    assert set(r) == {"inputs", "retaliation", "similar_cases", "notice"}
    assert cfg.PATTERN_NOTICE in r["notice"] and cfg.RETALIATION_NOTICE in r["notice"]
    assert r["retaliation"]["notice"] == cfg.RETALIATION_NOTICE
    assert r["similar_cases"]["notice"] == cfg.PATTERN_NOTICE


def test_unknown_case_raises():
    with pytest.raises(ValueError):
        risk_inputs.risk_inputs_for("nope", CASES, [], emb, 0.9)