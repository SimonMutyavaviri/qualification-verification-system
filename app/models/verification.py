"""Verification model -- one row per verification attempt."""

from __future__ import annotations

from app.extensions import db
from app.models.enums import VerificationResult
from app.models.user import utcnow


class Verification(db.Model):
    """A record of a single credential verification attempt.

    ``qualification_id`` is nullable on purpose: an attempt against an unknown
    credential ID is still a real, auditable event worth keeping.
    """

    __tablename__ = "verifications"
    __table_args__ = (
        db.Index("ix_verification_credential_created", "credential_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(36), nullable=False, unique=True, index=True)
    credential_id = db.Column(db.String(32), nullable=False, index=True)
    qualification_id = db.Column(
        db.Integer, db.ForeignKey("qualifications.id", ondelete="CASCADE"), nullable=True
    )
    result = db.Column(db.Enum(VerificationResult, native_enum=False), nullable=False, index=True)
    performed_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    qualification = db.relationship("Qualification", back_populates="verifications")
    performed_by = db.relationship("User", back_populates="verifications")

    @property
    def is_successful(self) -> bool:
        return self.result == VerificationResult.VALID

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Verification {self.reference} {self.result.value}>"
