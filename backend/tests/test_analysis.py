"""Tests for the Phase 6W analysis endpoints.
No real model is loaded: the embedder and the category model are replaced by fast fakes.
The risk tests compare the API with calculate_risk called directly, so they check the
wiring (the right inputs reach the function), not the weights (test_risk.py does that)."""
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.database import Base, get_db
from app.main import app
from app.models.adverse_event import AdverseEvent
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.complaint import Complaint
from app.models.evidence import Evidence
from app.models.user import User, UserRole
from app.services import analysis as svc
from app.services import ml_bridge
from app.services import pattern_config as cfg
from app.services.risk import calculate_risk

REAL_SUGGEST = ml_bridge.suggest  # saved before the fake replaces it
PW = "Password123!"
CATEGORY = "Bullying / abuse of power"
SHOUT = "My manager shouts at me in front of everyone every single day."
TITLE_A, TITLE_B = "ZZTITLE alpha", "ZZTITLE beta"
DESC_A = "ZZDESC " + SHOUT
DESC_B = "ZZDESC " + SHOUT
OTHER = "The canteen coffee machine has been broken for two weeks now."

FAKE_SUGGEST = {
    "suggestions": [
        {"rank": 1, "category": "Verbal harassment", "score": 0.6},
        {"rank": 2, "category": "Bullying / abuse of power", "score": 0.2},
        {"rank": 3, "category": "Other", "score": 0.1},
    ],
    "notice": "SUGGESTION ONLY, for a human reviewer.",
    "message": "",
    "model": "fake",
}


def fake_embedder(texts):
    return [[1.0, 0.0] if "shout" in t.lower() else [0.0, 1.0] for t in texts]


@pytest.fixture(autouse=True)
def fast_fakes(monkeypatch):
    monkeypatch.setattr(svc, "EMBEDDER", fake_embedder)
    monkeypatch.setattr(ml_bridge, "suggest", lambda text: dict(FAKE_SUGGEST))


@pytest.fixture
def env():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with Session() as s:
        s.add(Category(name=CATEGORY))
        s.commit()
    yield TestClient(app), Session
    app.dependency_overrides.clear()


# ---------- helpers ----------

def make_user(env, email, role=UserRole.employee):
    client, Session = env
    r = client.post("/auth/register",
                    json={"email": email, "full_name": "Name " + email, "password": PW})
    assert r.status_code in (200, 201), r.text
    with Session() as s:
        u = s.scalar(select(User).where(User.email == email))
        u.role = role
        s.commit()
    r = client.post("/auth/login", data={"username": email, "password": PW})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def file_complaint(env, headers, title, desc, day):
    client, Session = env
    r = client.post("/complaints", headers=headers, json={
        "category_id": 1, "privacy_mode": "pseudonymous",
        "title": title, "description": desc})
    assert r.status_code == 201, r.text
    body = r.json()
    with Session() as s:  # fixed filing date, so the tests do not depend on the clock
        c = s.get(Complaint, uuid.UUID(body["id"]))
        c.created_at = datetime(2026, 11, day, 9, 0, tzinfo=timezone.utc)
        s.commit()
    return body


def two(env):
    """A staff reviewer, an employee, and two similar complaints (A filed 1 Nov, B filed 10 Nov)."""
    staff = make_user(env, "staff@example.com", UserRole.reviewer)
    emp = make_user(env, "emp@example.com")
    a = file_complaint(env, emp, TITLE_A, DESC_A, 1)
    b = file_complaint(env, emp, TITLE_B, DESC_B, 10)
    return {"staff": staff, "emp": emp, "a": a, "b": b}


def url(cid, tail):
    return "/analysis/complaints/" + str(cid) + "/" + tail


def audit_rows(env):
    _, Session = env
    with Session() as s:
        return [(a.action, a.success) for a in s.scalars(select(AuditLog))]


def add_event(env, staff, cid, kind, day):
    client, _ = env
    r = client.post(url(cid, "adverse-events"), headers=staff,
                    json={"event_type": kind, "event_date": day})
    assert r.status_code == 201, r.text
    return r.json()


def expected_risk(freq, power, flag, rec, ev):
    return calculate_risk(CATEGORY, (TITLE_B + "\n" + DESC_B).strip(), frequency=freq,
                          power_imbalance=power, retaliation_flag=flag,
                          recurrence_count=rec, evidence_count=ev)


ALL_CALLS = [
    ("POST", "suggest-category", None),
    ("POST", "risk", {}),
    ("GET", "patterns", None),
    ("POST", "adverse-events", {"event_type": "demotion", "event_date": "2026-11-20"}),
    ("GET", "adverse-events", None),
]


# ---------- who may use it ----------

def test_employee_gets_404_everywhere_and_it_is_logged(env):
    s = two(env)
    client, Session = env
    for method, tail, body in ALL_CALLS:
        r = client.request(method, url(s["b"]["id"], tail), headers=s["emp"], json=body)
        assert r.status_code == 404, (tail, r.status_code)
        assert r.json()["detail"] == "Not found"
    denied = [a for a in audit_rows(env) if a == ("analysis_access_denied", False)]
    assert len(denied) == len(ALL_CALLS)
    with Session() as db:
        assert db.scalar(select(AdverseEvent)) is None  # the employee's POST saved nothing


def test_no_login_gives_401(env):
    s = two(env)
    client, _ = env
    for method, tail, body in ALL_CALLS:
        r = client.request(method, url(s["b"]["id"], tail), json=body)
        assert r.status_code == 401, tail


def test_unknown_complaint_gives_404_for_staff(env):
    s = two(env)
    client, _ = env
    missing = uuid.uuid4()
    for method, tail, body in ALL_CALLS:
        r = client.request(method, url(missing, tail), headers=s["staff"], json=body)
        assert r.status_code == 404, tail


def test_reviewer_and_ic_admin_are_both_allowed(env):
    s = two(env)
    client, _ = env
    admin = make_user(env, "admin@example.com", UserRole.ic_admin)
    for headers in (s["staff"], admin):
        r = client.get(url(s["b"]["id"], "patterns"), headers=headers)
        assert r.status_code == 200, r.text


# ---------- category suggestion ----------

def test_suggestion_is_returned_with_notice_and_logged(env):
    s = two(env)
    client, _ = env
    r = client.post(url(s["b"]["id"], "suggest-category"), headers=s["staff"])
    assert r.status_code == 200, r.text
    j = r.json()
    assert len(j["suggestions"]) == 3
    assert "SUGGESTION ONLY" in j["notice"]
    assert ("category_suggested", True) in audit_rows(env)


def test_suggestion_does_not_change_the_complaint(env):
    s = two(env)
    client, _ = env
    before = client.get("/complaints/" + s["b"]["id"], headers=s["staff"]).json()
    client.post(url(s["b"]["id"], "suggest-category"), headers=s["staff"])
    after = client.get("/complaints/" + s["b"]["id"], headers=s["staff"]).json()
    assert before == after


def test_model_failure_gives_503_and_a_failed_audit_row(env, monkeypatch):
    s = two(env)
    client, _ = env

    def broken(text):
        raise ml_bridge.MlUnavailable("x")

    monkeypatch.setattr(ml_bridge, "suggest", broken)
    r = client.post(url(s["b"]["id"], "suggest-category"), headers=s["staff"])
    assert r.status_code == 503
    assert ("category_suggested", False) in audit_rows(env)


def test_bridge_reports_missing_model_code(monkeypatch):
    monkeypatch.setattr(ml_bridge, "_module", None)
    monkeypatch.setattr(ml_bridge, "PREDICT_FILE", Path("does_not_exist.py"))
    with pytest.raises(ml_bridge.MlUnavailable):
        REAL_SUGGEST("some text")


# ---------- pattern alerts + retaliation flag ----------

def test_pattern_finds_the_similar_case_and_returns_every_notice(env):
    s = two(env)
    client, _ = env
    r = client.get(url(s["b"]["id"], "patterns"), headers=s["staff"])
    assert r.status_code == 200, r.text
    j = r.json()
    assert [m["case_id"] for m in j["pattern"]["matches"]] == [s["a"]["id"]]
    m = j["pattern"]["matches"][0]
    assert set(m) == {"case_id", "category", "filed_on", "similarity"}
    assert m["similarity"] >= cfg.SIMILARITY_THRESHOLD
    assert m["filed_on"] == "2026-11-01"
    assert j["recurrence_count"] == 1
    assert cfg.PATTERN_NOTICE in j["pattern"]["notice"]
    assert cfg.RETALIATION_NOTICE in j["retaliation"]["notice"]
    assert cfg.PATTERN_NOTICE in j["notice"] and cfg.RETALIATION_NOTICE in j["notice"]
    assert ("patterns_checked", True) in audit_rows(env)


def test_earlier_case_lists_the_later_one_but_has_no_recurrence(env):
    s = two(env)
    client, _ = env
    j = client.get(url(s["a"]["id"], "patterns"), headers=s["staff"]).json()
    assert [m["case_id"] for m in j["pattern"]["matches"]] == [s["b"]["id"]]
    assert j["recurrence_count"] == 0


def test_a_different_complaint_has_no_matches(env):
    s = two(env)
    client, _ = env
    c = file_complaint(env, s["emp"], "ZZTITLE gamma", "ZZDESC " + OTHER, 12)
    j = client.get(url(c["id"], "patterns"), headers=s["staff"]).json()
    assert j["pattern"]["matches"] == []
    assert j["recurrence_count"] == 0


@pytest.mark.parametrize("day,flag", [
    ("2026-11-20", True),    # 10 days after filing
    ("2026-11-10", True),    # same day counts
    ("2026-11-05", False),   # before filing never counts
    ("2027-06-01", False),   # outside the 90-day window
])
def test_retaliation_flag_follows_the_window(env, day, flag):
    s = two(env)
    client, _ = env
    add_event(env, s["staff"], s["b"]["id"], "demotion", day)
    j = client.get(url(s["b"]["id"], "patterns"), headers=s["staff"]).json()
    assert j["retaliation"]["retaliation_flag"] is flag
    assert j["retaliation"]["events_checked"] == 1


def test_retaliation_match_shows_days_after(env):
    s = two(env)
    client, _ = env
    add_event(env, s["staff"], s["b"]["id"], "demotion", "2026-11-20")
    j = client.get(url(s["b"]["id"], "patterns"), headers=s["staff"]).json()
    assert j["retaliation"]["matches"] == [
        {"event_type": "demotion", "event_date": "2026-11-20", "days_after": 10}]


# ---------- risk score ----------

def test_risk_with_empty_body_uses_unknown_and_matches_the_function(env):
    s = two(env)
    client, _ = env
    r = client.post(url(s["b"]["id"], "risk"), headers=s["staff"], json={})
    assert r.status_code == 200, r.text
    j = r.json()
    exp = expected_risk("unknown", "unknown", False, 1, 0)
    assert j["inputs_used"] == {"frequency": "unknown", "power_imbalance": "unknown",
                                "retaliation_flag": False, "recurrence_count": 1,
                                "evidence_count": 0}
    for key in ("score", "max_score", "level", "reasons", "notice"):
        assert j["risk"][key] == exp[key], key
    assert sum(x["points"] for x in j["risk"]["reasons"]) == j["risk"]["score"]
    assert cfg.PATTERN_NOTICE in j["notice"] and cfg.RETALIATION_NOTICE in j["notice"]
    assert ("risk_calculated", True) in audit_rows(env)


def test_risk_uses_body_events_and_evidence(env):
    s = two(env)
    client, Session = env
    add_event(env, s["staff"], s["b"]["id"], "demotion", "2026-11-20")
    with Session() as db:
        staff_id = db.scalar(select(User.id).where(User.email == "staff@example.com"))
        db.add(Evidence(complaint_id=uuid.UUID(s["b"]["id"]), original_filename="a.txt",
                        stored_path="x", file_size=1, content_type="text/plain",
                        sha256="0" * 64, uploaded_by=staff_id))
        db.commit()
    body = {"frequency": "a_few", "power_imbalance": "direct_manager"}
    j = client.post(url(s["b"]["id"], "risk"), headers=s["staff"], json=body).json()
    exp = expected_risk("a_few", "direct_manager", True, 1, 1)
    assert j["inputs_used"] == {"frequency": "a_few", "power_imbalance": "direct_manager",
                                "retaliation_flag": True, "recurrence_count": 1,
                                "evidence_count": 1}
    assert j["risk"]["score"] == exp["score"]
    assert j["risk"]["level"] == exp["level"]
    assert j["risk"]["reasons"] == exp["reasons"]
    assert j["retaliation"]["retaliation_flag"] is True


def test_risk_bad_values_give_422(env):
    s = two(env)
    client, _ = env
    for body in ({"frequency": "weekly"}, {"power_imbalance": "boss"}):
        r = client.post(url(s["b"]["id"], "risk"), headers=s["staff"], json=body)
        assert r.status_code == 422


def test_every_allowed_schema_value_is_accepted_by_the_risk_function():
    for f in ("unknown", "once", "a_few", "repeated"):
        calculate_risk("Other", frequency=f)
    for p in ("unknown", "none", "senior", "direct_manager"):
        calculate_risk("Other", power_imbalance=p)


# ---------- adverse events ----------

def test_add_and_list_adverse_event(env):
    s = two(env)
    client, _ = env
    r = client.post(url(s["b"]["id"], "adverse-events"), headers=s["staff"],
                    json={"event_type": "  Demotion ", "event_date": "2026-11-20"})
    assert r.status_code == 201, r.text
    body = r.json()
    ev = body["event"]
    assert ev["event_type"] == "demotion"
    assert ev["recorded_by_role"] == "reviewer"
    assert set(ev) == {"id", "complaint_id", "event_type", "event_date",
                       "recorded_by_role", "created_at"}
    assert body["notice"] == cfg.RETALIATION_NOTICE
    r2 = client.get(url(s["b"]["id"], "adverse-events"), headers=s["staff"])
    assert r2.status_code == 200
    assert [e["id"] for e in r2.json()["events"]] == [ev["id"]]
    assert r2.json()["notice"] == cfg.RETALIATION_NOTICE
    actions = audit_rows(env)
    assert ("adverse_event_added", True) in actions
    assert ("adverse_events_listed", True) in actions


def test_unknown_event_type_and_missing_date_give_422(env):
    s = two(env)
    client, _ = env
    for body in ({"event_type": "fired_unfairly", "event_date": "2026-11-20"},
                 {"event_type": "demotion"},
                 {"event_type": "demotion", "event_date": "not-a-date"}):
        r = client.post(url(s["b"]["id"], "adverse-events"), headers=s["staff"], json=body)
        assert r.status_code == 422, body


def test_every_configured_event_type_is_accepted(env):
    s = two(env)
    for kind in cfg.ADVERSE_EVENT_TYPES:
        add_event(env, s["staff"], s["b"]["id"], kind, "2026-11-20")


def test_adverse_events_table_has_no_user_column():
    cols = {c.name for c in AdverseEvent.__table__.columns}
    assert "user_id" not in cols
    assert not any("email" in c for c in cols)
    assert "recorded_by_role" in cols


# ---------- nothing names or accuses anyone ----------

def test_no_reply_or_audit_row_leaks_names_text_or_identity(env):
    s = two(env)
    client, _ = env
    add_event(env, s["staff"], s["b"]["id"], "demotion", "2026-11-20")
    texts = []
    for method, tail, body in ALL_CALLS:
        r = client.request(method, url(s["b"]["id"], tail), headers=s["staff"], json=body)
        assert r.status_code in (200, 201), (tail, r.text)
        texts.append(r.text)
    pseudonym = s["b"].get("pseudonym")
    assert pseudonym, "test setup: the pseudonymous complaint should have an alias"
    banned = [pseudonym, s["a"].get("pseudonym") or "none-given", "ZZTITLE", "ZZDESC",
              "emp@example.com", "staff@example.com", "user_id"]
    for text in texts:
        for word in banned:
            assert word not in text, word
    _, Session = client, env[1]
    with env[1]() as db:
        for row in db.scalars(select(AuditLog)):
            blob = (row.detail or "") + (row.resource_id or "")
            assert "ZZTITLE" not in blob and "ZZDESC" not in blob
            assert "emp@example.com" not in blob