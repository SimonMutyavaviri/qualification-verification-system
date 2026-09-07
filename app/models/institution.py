"""Institution model -- the awarding body behind a qualification."""

from __future__ import annotations

from app.extensions import db
from app.models.user import utcnow


class Institution(db.Model):
    """An awarding body authorised to issue qualifications."""

    __tablename__ = "institutions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    country = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    users = db.relationship("User", back_populates="institution")
    qualifications = db.relationship("Qualification", back_populates="institution")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Institution {self.code}>"
