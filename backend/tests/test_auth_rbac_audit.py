from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.user import User, UserRole

PASSWORD = "StrongPass123"


def register(client, email, name="Test User", password=PASSWORD):
    return client.post(
        "/auth/register",
        json={"email": email, "full_name": name, "password": password},
    )


def login_headers(client, email, password=PASSWORD):
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_admin(client, db, email):
    """Register a user, then promote them directly in the database."""
    register(client, email)
    user = db.scalar(select(User).where(User.email == email))
    user.role = UserRole.ic_admin
    db.commit()
    return login_headers(client, email)


def actions(db):
    return [row.action for row in db.scalars(select(AuditLog)).all()]


# ---------- Registration and login ----------

def test_register_creates_employee_without_password(client):
    r = register(client, "a@example.com")
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "employee"
    assert "password" not in body and "hashed_password" not in body


def test_duplicate_email_rejected(client):
    register(client, "a@example.com")
    assert register(client, "a@example.com").status_code == 400


def test_short_password_rejected(client):
    assert register(client, "a@example.com", password="abc").status_code == 422


def test_login_success_returns_token(client):
    register(client, "a@example.com")
    r = client.post("/auth/login", data={"username": "a@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password_rejected(client):
    register(client, "a@example.com")
    r = client.post("/auth/login", data={"username": "a@example.com", "password": "WrongPass999"})
    assert r.status_code == 401


# ---------- RBAC ----------

def test_no_token_gets_401(client):
    assert client.get("/users/me").status_code == 401


def test_bad_token_gets_401(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_employee_can_read_own_profile(client):
    register(client, "a@example.com")
    r = client.get("/users/me", headers=login_headers(client, "a@example.com"))
    assert r.status_code == 200
    assert r.json()["email"] == "a@example.com"


def test_employee_blocked_from_admin_endpoints(client):
    register(client, "a@example.com")
    h = login_headers(client, "a@example.com")
    assert client.get("/users/", headers=h).status_code == 403
    assert client.get("/audit/logs", headers=h).status_code == 403


def test_admin_can_list_users(client, db):
    h = make_admin(client, db, "boss@example.com")
    r = client.get("/users/", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_admin_can_change_role_but_not_own(client, db):
    h = make_admin(client, db, "boss@example.com")
    employee_id = register(client, "emp@example.com").json()["id"]

    r = client.patch(f"/users/{employee_id}/role", json={"role": "reviewer"}, headers=h)
    assert r.status_code == 200
    assert r.json()["role"] == "reviewer"

    admin_id = db.scalar(select(User).where(User.email == "boss@example.com")).id
    r = client.patch(f"/users/{admin_id}/role", json={"role": "employee"}, headers=h)
    assert r.status_code == 400


def test_role_change_takes_effect_with_old_token(client, db):
    register(client, "a@example.com")
    old_token = login_headers(client, "a@example.com")  # token issued as employee
    assert client.get("/users/", headers=old_token).status_code == 403

    user = db.scalar(select(User).where(User.email == "a@example.com"))
    user.role = UserRole.ic_admin
    db.commit()
    assert client.get("/users/", headers=old_token).status_code == 200


# ---------- Audit logging ----------

def test_audit_records_register_and_login(client, db):
    register(client, "a@example.com")
    login_headers(client, "a@example.com")
    assert "register" in actions(db)
    assert "login_success" in actions(db)


def test_audit_records_failed_login(client, db):
    register(client, "a@example.com")
    client.post("/auth/login", data={"username": "a@example.com", "password": "WrongPass999"})
    row = db.scalar(select(AuditLog).where(AuditLog.action == "login_failed"))
    assert row is not None and row.success is False


def test_audit_records_access_denied(client, db):
    register(client, "a@example.com")
    client.get("/users/", headers=login_headers(client, "a@example.com"))
    row = db.scalar(select(AuditLog).where(AuditLog.action == "access_denied"))
    assert row is not None and row.success is False


def test_audit_records_role_change(client, db):
    h = make_admin(client, db, "boss@example.com")
    emp_id = register(client, "emp@example.com").json()["id"]
    client.patch(f"/users/{emp_id}/role", json={"role": "reviewer"}, headers=h)
    row = db.scalar(select(AuditLog).where(AuditLog.action == "role_changed"))
    assert row.detail == "employee -> reviewer"


def test_audit_never_stores_passwords(client, db):
    register(client, "a@example.com")
    client.post("/auth/login", data={"username": "a@example.com", "password": "WrongPass999"})
    for row in db.scalars(select(AuditLog)).all():
        assert "WrongPass999" not in (row.detail or "")
        assert PASSWORD not in (row.detail or "")
