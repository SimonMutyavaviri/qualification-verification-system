"""Qualification model -- the credential record being verified."""

from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models.enums import QualificationStatus
from app.models.user import utcnow


class Qualification(db.Model):
    """A qualification or certification awarded to a named holder.

    ``credential_id`` is the public reference a verifier quotes; it is unique
    across the whole system so a credential can never be registered twice.
    """

    __tablename__ = "qualifications"
    __table_args__ = (
        db.UniqueConstraint("credential_id", name="uq_qualification_credential_id"),
        db.Index("ix_qualification_holder_institution", "holder_name", "institution_id"),
        db.CheckConstraint(
            "expiry_date IS NULL OR expiry_date >= award_date",
            name="ck_qualification_expiry_after_award",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.String(32), nullable=False, unique=True, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    qualification_type = db.Column(db.String(64), nullable=False)
    holder_name = db.Column(db.String(255), nullable=False, index=True)
    holder_email = db.Column(db.String(255), nullable=True)
    institution_id = db.Column(
        db.Integer, db.ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False
    )
    award_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    status = db.Column(
        db.Enum(QualificationStatus, native_enum=False),
        nullable=False,
        default=QualificationStatus.ACTIVE,
        index=True,
    )
    revocation_reason = db.Column(db.String(500), nullable=True)
    issued_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    institution = db.relationship("Institution", back_populates="qualifications")
    issued_by = db.relationship(
        "User", back_populates="issued_qualifications", foreign_keys=[issued_by_id]
    )
    verifications = db.relationship(
        "Verification", back_populates="qualification", cascade="all, delete-orphan"
    )

    def is_expired(self, on_date: date | None = None) -> bool:
        """True when an expiry date exists and has passed."""
        if self.expiry_date is None:
            return False
        return self.expiry_date < (on_date or date.today())

    @property
    def effective_status(self) -> QualificationStatus:
        """Stored status, upgraded to EXPIRED when the expiry date has passed.

        Revocation always wins: a revoked credential stays revoked even after
        its expiry date, because that is the more serious signal.
        """
        if self.status == QualificationStatus.REVOKED:
            return QualificationStatus.REVOKED
        if self.is_expired():
            return QualificationStatus.EXPIRED
        return self.status

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Qualification {self.credential_id}>"
