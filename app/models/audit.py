"""Append-only audit log model."""

from __future__ import annotations

from app.extensions import db
from app.models.enums import AuditAction
from app.models.user import utcnow


class AuditLog(db.Model):
    """An immutable record of a security- or data-relevant event.

    Immutability is enforced at the ORM layer (see ``app.utils.audit_guard``)
    rather than only by convention, so an accidental update or delete raises
    instead of silently rewriting history.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (db.Index("ix_audit_action_created", "action", "created_at"),)

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.Enum(AuditAction, native_enum=False), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_label = db.Column(db.String(128), nullable=False, default="anonymous")
    entity_type = db.Column(db.String(64), nullable=True)
    entity_id = db.Column(db.String(64), nullable=True)
    detail = db.Column(db.String(1000), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    actor = db.relationship("User")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AuditLog {self.action.value} {self.created_at}>"
