import hashlib
from pathlib import Path

import pytest
from sqlalchemy import select

import app.services.evidence as ev_svc
from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.evidence import Evidence
from app.models.user import User, UserRole
from app.schemas.evidence import EvidenceOut, EvidenceUploadOut, VerifyOut

# Reuse the helpers and the in-memory database fixture from test_complaints.py
try:
    from tests.test_complaints import env, make_user, file_complaint  # noqa: F401
except ImportError:
    from test_complaints import env, make_user, file_complaint  # noqa: F401


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Every test saves files in its own temporary folder."""
    d = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(d))
    return d


def new_case(env, headers, mode="confidential"):
    res = file_complaint(env, headers, mode)
    if hasattr(res, "json"):
        res = res.json()
    return res if isinstance(res, str) else res["id"]


def upload(env, headers, cid, name="report.txt", data=b"hello evidence",
           ctype="text/plain"):
    client, _ = env
    return client.post(f"/complaints/{cid}/evidence", headers=headers,
                       files={"file": (name, data, ctype)})


def audit_rows(env, action):
    _, Session = env
    with Session() as s:
        return list(s.scalars(select(AuditLog).where(AuditLog.action == action)))


def user_id(env, email):
    _, Session = env
    with Session() as s:
        return s.scalar(select(User.id).where(User.email == email))


# ---------- hash ----------
def test_hash_is_correct(env):
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    data = b"hello evidence"
    r = upload(env, h, cid, data=data)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["sha256"] == hashlib.sha256(data).hexdigest()
    assert body["file_size"] == len(data)
    assert body["original_filename"] == "report.txt"
    assert body["content_type"] == "text/plain"


def test_file_saved_with_random_name(env, upload_dir):
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    upload(env, h, cid)
    upload(env, h, cid)
    names = [p.name for p in upload_dir.iterdir()]
    assert len(names) == 2 and names[0] != names[1]
    for n in names:
        assert "report" not in n and "." not in n and len(n) == 32


def test_reply_has_no_identity_fields(env):
    fields = (set(EvidenceUploadOut.model_fields) | set(EvidenceOut.model_fields)
              | set(VerifyOut.model_fields))
    for bad in ("uploaded_by", "user_id", "stored_path", "email", "full_name"):
        assert bad not in fields
    h = make_user(env, "a@x.com")
    r = upload(env, h, new_case(env, h))
    assert set(r.json()) == set(EvidenceUploadOut.model_fields)
    assert "admissib" in r.json()["notice"].lower()


# ---------- verify ----------
def test_verify_unchanged_file(env):
    client, _ = env
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    eid = upload(env, h, cid).json()["id"]
    r = client.post(f"/complaints/{cid}/evidence/{eid}/verify", headers=h)
    assert r.status_code == 200
    b = r.json()
    assert b["integrity_ok"] is True
    assert "matches" in b["message"].lower()
    assert b["stored_sha256"] == b["recalculated_sha256"]
    assert "admissib" in b["notice"].lower()


def test_verify_detects_changed_file(env, upload_dir):
    client, _ = env
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    first = upload(env, h, cid).json()
    (upload_dir / next(upload_dir.iterdir()).name).write_bytes(b"secretly edited")
    r = client.post(f"/complaints/{cid}/evidence/{first['id']}/verify", headers=h)
    b = r.json()
    assert b["integrity_ok"] is False
    assert "changed" in b["message"].lower()
    assert b["stored_sha256"] == first["sha256"]
    assert b["recalculated_sha256"] == hashlib.sha256(b"secretly edited").hexdigest()


def test_verify_missing_file(env, upload_dir):
    client, _ = env
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    eid = upload(env, h, cid).json()["id"]
    next(upload_dir.iterdir()).unlink()
    b = client.post(f"/complaints/{cid}/evidence/{eid}/verify", headers=h).json()
    assert b["integrity_ok"] is False
    assert "missing" in b["message"].lower()
    assert b["recalculated_sha256"] is None


# ---------- limits ----------
def test_size_limit(env, upload_dir, monkeypatch):
    monkeypatch.setattr(ev_svc, "MAX_BYTES", 10)
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    r = upload(env, h, cid, data=b"x" * 11)
    assert r.status_code == 413
    assert list(upload_dir.iterdir()) == []          # half-saved file removed
    rows = audit_rows(env, "evidence_upload_rejected")
    assert len(rows) == 1 and rows[0].success is False
    assert upload(env, h, cid, data=b"x" * 10).status_code == 201   # exactly at the limit


def test_type_limits(env, upload_dir):
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    assert upload(env, h, cid, "virus.exe", b"MZ....", "application/x-msdownload").status_code == 415
    assert upload(env, h, cid, "a.txt", b"hi", "application/x-msdownload").status_code == 415
    assert upload(env, h, cid, "fake.png", b"not really a png", "image/png").status_code == 415
    assert list(upload_dir.iterdir()) == []
    assert len(audit_rows(env, "evidence_upload_rejected")) == 3
    good_png = b"\x89PNG\r\n\x1a\n" + b"0" * 20
    assert upload(env, h, cid, "photo.png", good_png, "image/png").status_code == 201


def test_empty_file_rejected(env):
    h = make_user(env, "a@x.com")
    assert upload(env, h, new_case(env, h), data=b"").status_code == 400


# ---------- access ----------
def test_owner_and_staff_access(env):
    client, _ = env
    owner = make_user(env, "a@x.com")
    reviewer = make_user(env, "rev@x.com", UserRole.reviewer)
    admin = make_user(env, "adm@x.com", UserRole.ic_admin)
    cid = new_case(env, owner)
    eid = upload(env, owner, cid).json()["id"]
    assert len(client.get(f"/complaints/{cid}/evidence", headers=owner).json()) == 1
    assert len(client.get(f"/complaints/{cid}/evidence", headers=reviewer).json()) == 1
    assert client.get(f"/complaints/{cid}/evidence/{eid}/download", headers=reviewer).status_code == 200
    assert client.post(f"/complaints/{cid}/evidence/{eid}/verify", headers=admin).status_code == 200


def test_other_employee_denied_and_logged(env, upload_dir):
    client, _ = env
    owner = make_user(env, "a@x.com")
    other = make_user(env, "b@x.com")
    cid = new_case(env, owner)
    eid = upload(env, owner, cid).json()["id"]
    base = f"/complaints/{cid}/evidence"
    assert upload(env, other, cid).status_code == 404
    assert client.get(base, headers=other).status_code == 404
    assert client.post(f"{base}/{eid}/verify", headers=other).status_code == 404
    assert client.get(f"{base}/{eid}/download", headers=other).status_code == 404
    assert len(list(upload_dir.iterdir())) == 1      # the denied upload saved nothing
    denied = [r for r in audit_rows(env, "complaint_access_denied")
              if r.user_id == user_id(env, "b@x.com")]
    assert len(denied) == 4 and all(r.success is False for r in denied)


def test_evidence_must_belong_to_that_complaint(env):
    client, _ = env
    h = make_user(env, "a@x.com")
    c1, c2 = new_case(env, h), new_case(env, h)
    eid = upload(env, h, c1).json()["id"]
    r = client.post(f"/complaints/{c2}/evidence/{eid}/verify", headers=h)
    assert r.status_code == 404


def test_login_required(env):
    client, _ = env
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    r = client.post(f"/complaints/{cid}/evidence", files={"file": ("a.txt", b"x", "text/plain")})
    assert r.status_code == 401
    assert client.get(f"/complaints/{cid}/evidence").status_code == 401


# ---------- download ----------
def test_download_returns_same_bytes(env):
    client, _ = env
    h = make_user(env, "a@x.com")
    cid = new_case(env, h)
    data = b"exact content 123"
    eid = upload(env, h, cid, data=data).json()["id"]
    r = client.get(f"/complaints/{cid}/evidence/{eid}/download", headers=h)
    assert r.status_code == 200 and r.content == data
    assert "attachment" in r.headers["content-disposition"]
    assert r.headers["x-content-type-options"] == "nosniff"


# ---------- audit + privacy ----------
def test_audit_rows_for_upload_verify_download(env):
    client, _ = env
    h = make_user(env, "a@x.com")
    uid = user_id(env, "a@x.com")
    cid = new_case(env, h)
    eid = upload(env, h, cid).json()["id"]
    client.post(f"/complaints/{cid}/evidence/{eid}/verify", headers=h)
    client.get(f"/complaints/{cid}/evidence/{eid}/download", headers=h)
    for action in ("evidence_uploaded", "evidence_verified", "evidence_downloaded"):
        rows = audit_rows(env, action)
        assert len(rows) == 1, action
        assert rows[0].user_id == uid and rows[0].success is True
        assert rows[0].resource_id == eid


def test_no_identity_leak_for_pseudonymous_case(env):
    client, Session = env
    email = "leaky.person@x.com"
    h = make_user(env, email)
    cid = new_case(env, h, "pseudonymous")
    r1 = upload(env, h, cid)
    eid = r1.json()["id"]
    r2 = client.get(f"/complaints/{cid}/evidence", headers=h)
    r3 = client.post(f"/complaints/{cid}/evidence/{eid}/verify", headers=h)
    r4 = client.get(f"/complaints/{cid}/evidence/{eid}/download", headers=h)
    for r in (r1, r2, r3):
        assert email not in r.text and "uploaded_by" not in r.text and "user_id" not in r.text
    assert email not in str(r4.headers)
    for row in audit_rows(env, "evidence_uploaded") + audit_rows(env, "evidence_verified"):
        assert email not in (row.detail or "")
    # the uploader id exists only inside the database table, never in a reply
    with Session() as s:
        row = s.scalars(select(Evidence)).all()[0]
        assert row.uploaded_by == user_id(env, email)