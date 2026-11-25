# Import every model here so SQLAlchemy knows about all tables.
from app.models.user import User, UserRole  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.complaint import Complaint, CaseStatusHistory, PrivacyMode, ComplaintStatus  # noqa: F401
from app.models.complaint_identity import ComplaintIdentity  # noqa: F401
from app.models.evidence import Evidence  # noqa: F401
from app.models.adverse_event import AdverseEvent  # noqa: F401
