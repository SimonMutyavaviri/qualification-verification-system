"""Data access for the append-only audit log."""

from __future__ import annotations

from sqlalchemy import select

from app.extensions import db
from app.models.audit import AuditLog
from app.models.enums import AuditAction


class AuditRepository:
    """Read helpers plus the single sanctioned write path for audit rows."""

    @staticmethod
    def add(entry: AuditLog) -> AuditLog:
        db.session.add(entry)
        return entry

    @staticmethod
    def list_logs(
        *,
        action: AuditAction | None = None,
        actor_id: int | None = None,
        entity_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ):
        """Paginated audit trail, newest first."""
        stmt = select(AuditLog)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def count_all() -> int:
        return db.session.scalar(select(db.func.count(AuditLog.id))) or 0

    @staticmethod
    def recent(limit: int = 10) -> list[AuditLog]:
        stmt = (
            select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
        )
        return list(db.session.scalars(stmt))
