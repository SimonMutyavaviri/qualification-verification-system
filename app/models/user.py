"""User account model with role-based access helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.enums import Role


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp (``datetime.utcnow`` is deprecated)."""
    return datetime.now(UTC)


class User(UserMixin, db.Model):
    """An authenticated actor: administrator, issuer or verifier."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role, native_enum=False), nullable=False, default=Role.VERIFIER)
    institution_id = db.Column(
        db.Integer, db.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    institution = db.relationship("Institution", back_populates="users")
    issued_qualifications = db.relationship(
        "Qualification", back_populates="issued_by", foreign_keys="Qualification.issued_by_id"
    )
    verifications = db.relationship("Verification", back_populates="performed_by")

    # -- password handling -------------------------------------------------
    def set_password(self, password: str) -> None:
        """Hash and store ``password`` (PBKDF2-SHA256 via Werkzeug)."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Constant-time comparison of ``password`` against the stored hash."""
        return check_password_hash(self.password_hash, password)

    # -- authorisation helpers --------------------------------------------
    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_issuer(self) -> bool:
        return self.role in (Role.ISSUER, Role.ADMIN)

    def has_role(self, *roles: Role) -> bool:
        """True when the user holds any of ``roles`` (admin is a superset)."""
        return self.role == Role.ADMIN or self.role in roles

    # Flask-Login uses ``is_active`` to block disabled accounts.
    def get_id(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User {self.username} ({self.role.value})>"
