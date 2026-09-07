"""Enforce append-only semantics on the audit log.

The assignment requires that audit records are "protected from ordinary
modification/deletion". A convention is not protection, so this module hooks
SQLAlchemy's flush events and raises when a persisted AuditLog row is updated
or deleted through the session.
"""

from __future__ import annotations

from sqlalchemy import event

from app.extensions import db
from app.models.audit import AuditLog
from app.utils.errors import ImmutableRecordError


def _block_update(mapper, connection, target):  # noqa: ARG001 - SQLAlchemy signature
    raise ImmutableRecordError("Audit log entries cannot be modified.")


def _block_delete(mapper, connection, target):  # noqa: ARG001 - SQLAlchemy signature
    raise ImmutableRecordError("Audit log entries cannot be deleted.")


def register_audit_guards() -> None:
    """Attach the immutability listeners (idempotent)."""
    if not event.contains(AuditLog, "before_update", _block_update):
        event.listen(AuditLog, "before_update", _block_update)
    if not event.contains(AuditLog, "before_delete", _block_delete):
        event.listen(AuditLog, "before_delete", _block_delete)


__all__ = ["register_audit_guards", "db"]
