import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.database import Base, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.complaint import CaseStatusHistory, Complaint
from app.models.complaint_identity import ComplaintIdentity
from app.models.user import User, UserRole
from app.schemas.complaint import ComplaintOut

PW = "StrongPass123"


@pytest.fixture()
def env():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
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
        s.add(Category(name="Test category"))
        s.commit()
    yield TestClient(app), Session
    app.dependency_overrides.clear()


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


def file_complaint(env, headers, mode="confidential"):
    client, _ = env
    r = client.post("/complaints", headers=headers, json={
        "category_id": 1, "privacy_mode": mode,
        "title": "Test complaint", "description": "Something happened at work."})
    assert r.status_code == 201, r.text
    return r.json()


def audit_actions(env):
    _, Session = env
    with Session() as s:
        return [(a.action, a.success) for a in s.scalars(select(AuditLog))]


# ---------- identity stays separate from case content ----------

def test_complaints_table_has_no_user_column():
    cols = {c.name for c in Complaint.__table__.columns}
    assert "user_id" not in cols
    assert not any("user" in c or "email" in c or "name" in c for c in cols)


def test_output_schema_has_no_user_fields():
    fields = set(ComplaintOut.model_fields)
    assert "user_id" not in fields and "email" not in fields


def test_identity_saved_in_separate_table(env):
    h = make_user(env, "emp@example.com")
    c = file_complaint(env, h)
    _, Session = env
    with Session() as s:
        link = s.scalar(select(ComplaintIdentity))
        emp = s.scalar(select(User).where(User.email == "emp@example.com"))
        assert str(link.complaint_id) == c["id"]
        assert link.user_id == emp.id


def test_create_response_leaks_no_identity(env):
    h = make_user(env, "emp@example.com")
    c = file_complaint(env, h)
    text = str(c)
    assert "emp@example.com" not in text and "user_id" not in c


def test_pseudonymous_gets_random_alias(env):
    h = make_user(env, "emp@example.com")
    c = file_complaint(env, h, "pseudonymous")
    assert c["pseudonym"].startswith("Reporter-")
    assert "emp" not in c["pseudonym"]
    assert file_complaint(env, h, "confidential")["pseudonym"] is None


# ---------- who can see which complaint ----------

def test_login_required(env):
    client, _ = env
    assert client.get("/complaints").status_code == 401


def test_employee_sees_only_own(env):
    a = make_user(env, "a@example.com")
    b = make_user(env, "b@example.com")
    ca = file_complaint(env, a)
    file_complaint(env, b)
    client, _ = env
    assert len(client.get("/complaints", headers=a).json()) == 1
    assert client.get(f"/complaints/{ca['id']}", headers=a).status_code == 200
    # other employee gets 404 and a denied row is logged
    assert client.get(f"/complaints/{ca['id']}", headers=b).status_code == 404
    assert ("complaint_access_denied", False) in audit_actions(env)


def test_reviewer_sees_all_cases_but_no_identity_in_content(env):
    a = make_user(env, "a@example.com")
    r = make_user(env, "rev@example.com", UserRole.reviewer)
    file_complaint(env, a)
    client, _ = env
    rows = client.get("/complaints", headers=r).json()
    assert len(rows) == 1
    assert "a@example.com" not in str(rows) and "user_id" not in rows[0]


# ---------- identity access is role-gated and logged ----------

def reveal(env, headers, cid, reason="reviewing this case now"):
    client, _ = env
    return client.get(f"/complaints/{cid}/identity", headers=headers,
                      params={"reason": reason})


def test_reviewer_cannot_see_confidential_identity(env):
    a = make_user(env, "a@example.com")
    r = make_user(env, "rev@example.com", UserRole.reviewer)
    c = file_complaint(env, a, "confidential")
    resp = reveal(env, r, c["id"])
    assert resp.status_code == 403
    assert "a@example.com" not in resp.text
    assert ("identity_access_denied", False) in audit_actions(env)


def test_reviewer_cannot_see_pseudonymous_identity(env):
    a = make_user(env, "a@example.com")
    r = make_user(env, "rev@example.com", UserRole.reviewer)
    c = file_complaint(env, a, "pseudonymous")
    assert reveal(env, r, c["id"]).status_code == 403


def test_reviewer_can_see_identified_and_it_is_logged(env):
    a = make_user(env, "a@example.com")
    r = make_user(env, "rev@example.com", UserRole.reviewer)
    c = file_complaint(env, a, "identified")
    resp = reveal(env, r, c["id"])
    assert resp.status_code == 200
    assert resp.json()["email"] == "a@example.com"
    assert ("identity_viewed", True) in audit_actions(env)


def test_admin_can_see_confidential_and_it_is_logged(env):
    a = make_user(env, "a@example.com")
    ad = make_user(env, "adm@example.com", UserRole.ic_admin)
    c = file_complaint(env, a, "confidential")
    resp = reveal(env, ad, c["id"])
    assert resp.status_code == 200
    assert "not promise absolute anonymity" in resp.json()["notice"]
    assert audit_actions(env).count(("identity_viewed", True)) == 1


def test_employee_cannot_use_identity_endpoint_even_for_own(env):
    a = make_user(env, "a@example.com")
    c = file_complaint(env, a, "identified")
    assert reveal(env, a, c["id"]).status_code == 403
    assert ("identity_access_denied", False) in audit_actions(env)


def test_identity_needs_a_reason(env):
    a = make_user(env, "a@example.com")
    ad = make_user(env, "adm@example.com", UserRole.ic_admin)
    c = file_complaint(env, a)
    assert reveal(env, ad, c["id"], reason="short").status_code == 422


def test_every_identity_attempt_is_logged(env):
    a = make_user(env, "a@example.com")
    r = make_user(env, "rev@example.com", UserRole.reviewer)
    ad = make_user(env, "adm@example.com", UserRole.ic_admin)
    c = file_complaint(env, a, "confidential")
    reveal(env, r, c["id"])
    reveal(env, ad, c["id"])
    acts = [x[0] for x in audit_actions(env)]
    assert acts.count("identity_access_denied") == 1
    assert acts.count("identity_viewed") == 1


# ---------- status updates and history ----------

def patch_status(env, headers, cid, new):
    client, _ = env
    return client.patch(f"/complaints/{cid}/status", headers=headers,
                        json={"new_status": new, "note": "test"})


def test_employee_cannot_change_status(env):
    a = make_user(env, "a@example.com")
    c = file_complaint(env, a)
    assert patch_status(env, a, c["id"], "under_review").status_code == 403
    assert ("access_denied", False) in audit_actions(env)


def test_reviewer_status_flow_and_history(env):
    a = make_user(env, "a@example.com")
    r = make_user(env, "rev@example.com", UserRole.reviewer)
    c = file_complaint(env, a)
    assert patch_status(env, r, c["id"], "under_review").status_code == 200
    assert patch_status(env, r, c["id"], "closed").status_code == 200
    _, Session = env
    with Session() as s:
        rows = list(s.scalars(select(CaseStatusHistory).order_by(CaseStatusHistory.id)))
    assert [x.new_status for x in rows] == ["submitted", "under_review", "closed"]
    assert rows[1].old_status == "submitted"


def test_invalid_status_jump_rejected(env):
    a = make_user(env, "a@example.com")
    r = make_user(env, "rev@example.com", UserRole.reviewer)
    c = file_complaint(env, a)
    assert patch_status(env, r, c["id"], "closed").status_code == 400
    patch_status(env, r, c["id"], "under_review")
    patch_status(env, r, c["id"], "closed")
    assert patch_status(env, r, c["id"], "under_review").status_code == 400


def test_unknown_category_rejected(env):
    a = make_user(env, "a@example.com")
    client, _ = env
    r = client.post("/complaints", headers=a, json={
        "category_id": 999, "privacy_mode": "identified",
        "title": "Test complaint", "description": "Something happened."})
    assert r.status_code == 400