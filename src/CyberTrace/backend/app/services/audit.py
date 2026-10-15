"""Minimal audit-log writer, per PROJECT_PLAN.md section 11: "Audit log
for login, upload, export, and delete actions, viewable by admins."
Append-only -- callers only ever `db.add()` a new row, never update or
delete an existing one.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def record_audit_event(
    db: AsyncSession,
    *,
    user_id: str | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address,
        )
    )
