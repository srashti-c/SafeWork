from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_event(
    db: Session,
    action: str,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    success: bool = True,
) -> None:
    """Write one row to audit_logs. NEVER put passwords or tokens in detail."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail[:500] if detail else None,
        ip_address=ip_address,
        success=success,
    )
    db.add(entry)
    db.commit()
