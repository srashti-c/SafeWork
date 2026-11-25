import sys

import app.models  # noqa: F401
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.services.audit import log_event

if len(sys.argv) != 2:
    print("Usage: python promote_admin.py email@example.com")
    sys.exit(1)

with SessionLocal() as db:
    user = db.scalar(select(User).where(User.email == sys.argv[1].lower()))
    if user is None:
        print("No user with that email.")
        sys.exit(1)
    user.role = UserRole.ic_admin
    db.commit()
    log_event(db, "admin_promoted_via_script", user_id=user.id,
              resource_type="user", resource_id=str(user.id),
              detail="role set to ic_admin by command-line script")
    print(f"{user.email} is now ic_admin")
