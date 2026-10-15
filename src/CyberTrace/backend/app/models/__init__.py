"""Import all models here so Base.metadata is fully populated for
create_all() (dev/test) and for Alembic's autogenerate to see them."""
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.case import Case  # noqa: F401
from app.models.evidence import EvidenceFile  # noqa: F401
from app.models.log_record import LogRecord  # noqa: F401
from app.models.parse_error import ParseError, ParsingGap  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.user import User  # noqa: F401
