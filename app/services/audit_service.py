"""Audit trail service.

Every security- or data-relevant event funnels through :meth:`AuditService.record`
so the audit trail has one well-defined write path.
"""

from __future__ import annotations

from flask import has_request_context, request
from flask_login import current_user

from app.extensions import db
from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Create and read audit entries."""

    @staticmethod
    def _actor() -> tuple[int | None, str]:
        """Resolve the acting user, tolerating unauthenticated contexts.

        ``current_user`` is a request-bound proxy, so it raises outside a
        request (CLI commands, background seeding). Those events are still
        auditable -- they are simply attributed to "system".
        """
        if not has_request_context():
            return None, "system"
        if current_user and current_user.is_authenticated:
            return current_user.id, current_user.username
        return None, "anonymous"

    @staticmethod
    def _client_ip() -> str | None:
        if not has_request_context():
            return None
        # Fly.io terminates TLS at the edge and forwards the client IP.
        forwarded = request.headers.get("Fly-Client-IP") or request.headers.get(
            "X-Forwarded-For", ""
        )
        if forwarded:
            return forwarded.split(",")[0].strip()[:45]
        return request.remote_addr

    @staticmethod
    def record(
        *,
        action: AuditAction,
        entity_type: str | None = None,
        entity_id: str | int | None = None,
        detail: str | None = None,
        actor_id: int | None = None,
        actor_label: str | None = None,
        commit: bool = False,
    ) -> AuditLog:
        """Append one entry to the audit trail.

        ``commit`` is False by default so the audit row joins the same
        transaction as the change it describes -- if the change rolls back, so
        does its audit entry. Pass True for standalone events such as a failed
        login, which has no accompanying data change.
        """
        resolved_id, resolved_label = AuditService._actor()
        entry = AuditLog(
            action=action,
            actor_id=actor_id if actor_id is not None else resolved_id,
            actor_label=actor_label or resolved_label,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            detail=(detail or "")[:1000] or None,
            ip_address=AuditService._client_ip(),
        )
        AuditRepository.add(entry)
        if commit:
            db.session.commit()
        return entry

    @staticmethod
    def list_logs(**kwargs):
        return AuditRepository.list_logs(**kwargs)

    @staticmethod
    def recent(limit: int = 10):
        return AuditRepository.recent(limit)

    @staticmethod
    def count_all() -> int:
        return AuditRepository.count_all()
