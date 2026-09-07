"""Qualification lifecycle business rules.

The service owns validation, duplicate prevention, authorisation and audit
writing. Routes stay thin; repositories stay dumb.
"""

from __future__ import annotations

import secrets
from datetime import date

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.enums import AuditAction, QualificationStatus, Role
from app.models.qualification import Qualification
from app.models.user import User
from app.repositories.qualification_repository import QualificationRepository
from app.repositories.user_repository import InstitutionRepository
from app.services.audit_service import AuditService
from app.utils.errors import (
    DuplicateCredentialError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.utils.validators import (
    validate_award_and_expiry,
    validate_credential_id,
    validate_email,
    validate_qualification_type,
    validate_required,
)

# Ambiguity-free alphabet: no O/0 or I/1, so a credential ID read aloud or
# copied off a printed certificate does not turn into a different ID.
_ID_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class QualificationService:
    """Create, update, search and revoke qualifications."""

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def generate_credential_id(prefix: str = "QVS", year: int | None = None) -> str:
        """Generate an unused credential ID of the form ``QVS-2024-A1B2C3``."""
        year = year or date.today().year
        for _ in range(20):
            suffix = "".join(secrets.choice(_ID_ALPHABET) for _ in range(6))
            candidate = f"{prefix.upper()}-{year}-{suffix}"
            if not QualificationRepository.exists_credential_id(candidate):
                return candidate
        raise ValidationError("Could not allocate a unique credential ID. Please try again.")

    @staticmethod
    def _assert_can_issue(user: User) -> None:
        if not user.has_role(Role.ISSUER):
            raise PermissionDeniedError(
                "Only issuers and administrators may manage qualifications."
            )

    # -- commands ----------------------------------------------------------
    @staticmethod
    def register(
        *,
        actor: User,
        title: str,
        qualification_type: str,
        holder_name: str,
        institution_id: int,
        award_date: date | None,
        expiry_date: date | None = None,
        holder_email: str | None = None,
        credential_id: str | None = None,
    ) -> Qualification:
        """Register a new qualification after validating every field."""
        QualificationService._assert_can_issue(actor)

        title = validate_required(title, "title", "Qualification title")
        qualification_type = validate_qualification_type(qualification_type)
        holder_name = validate_required(holder_name, "holder_name", "Holder name")
        holder_email = validate_email(holder_email, field="holder_email", required=False)
        award_date, expiry_date = validate_award_and_expiry(award_date, expiry_date)

        if not institution_id:
            raise ValidationError("Institution is required.", field="institution_id")
        institution = InstitutionRepository.get(int(institution_id))
        if institution is None:
            raise ValidationError("Selected institution does not exist.", field="institution_id")
        if not institution.is_active:
            raise ValidationError("Selected institution is not active.", field="institution_id")

        if credential_id:
            credential_id = validate_credential_id(credential_id)
            if QualificationRepository.exists_credential_id(credential_id):
                raise DuplicateCredentialError(
                    f"Credential ID {credential_id} is already registered.",
                    field="credential_id",
                )
        else:
            credential_id = QualificationService.generate_credential_id()

        qualification = Qualification(
            credential_id=credential_id,
            title=title,
            qualification_type=qualification_type,
            holder_name=holder_name,
            holder_email=holder_email,
            institution_id=institution.id,
            award_date=award_date,
            expiry_date=expiry_date,
            status=QualificationStatus.ACTIVE,
            issued_by_id=actor.id,
        )
        QualificationRepository.add(qualification)
        AuditService.record(
            action=AuditAction.QUALIFICATION_CREATED,
            entity_type="qualification",
            entity_id=credential_id,
            detail=f"Registered '{title}' for {holder_name} at {institution.name}",
        )
        try:
            db.session.commit()
        except IntegrityError as exc:
            # Guards against a race between the existence check and the insert.
            db.session.rollback()
            raise DuplicateCredentialError(
                f"Credential ID {credential_id} is already registered.",
                field="credential_id",
            ) from exc
        return qualification

    @staticmethod
    def update(
        *,
        actor: User,
        qualification_id: int,
        title: str | None = None,
        qualification_type: str | None = None,
        holder_name: str | None = None,
        holder_email: str | None = None,
        expiry_date: date | None = None,
        clear_expiry: bool = False,
    ) -> Qualification:
        """Update the mutable fields of an existing qualification.

        The credential ID, award date, institution and issuer are deliberately
        immutable: changing them would rewrite the meaning of a credential that
        third parties may already have verified.
        """
        QualificationService._assert_can_issue(actor)
        qualification = QualificationRepository.get(qualification_id)
        if qualification is None:
            raise NotFoundError("Qualification not found.")
        if qualification.status == QualificationStatus.REVOKED:
            raise ValidationError("A revoked qualification cannot be edited.")

        changes: list[str] = []
        if title is not None:
            new_title = validate_required(title, "title", "Qualification title")
            if new_title != qualification.title:
                changes.append(f"title: '{qualification.title}' -> '{new_title}'")
                qualification.title = new_title
        if qualification_type is not None:
            new_type = validate_qualification_type(qualification_type)
            if new_type != qualification.qualification_type:
                changes.append(f"type: '{qualification.qualification_type}' -> '{new_type}'")
                qualification.qualification_type = new_type
        if holder_name is not None:
            new_holder = validate_required(holder_name, "holder_name", "Holder name")
            if new_holder != qualification.holder_name:
                changes.append(f"holder: '{qualification.holder_name}' -> '{new_holder}'")
                qualification.holder_name = new_holder
        if holder_email is not None:
            new_email = validate_email(holder_email, field="holder_email", required=False)
            if new_email != qualification.holder_email:
                changes.append("holder_email updated")
                qualification.holder_email = new_email
        if clear_expiry:
            if qualification.expiry_date is not None:
                changes.append("expiry cleared")
            qualification.expiry_date = None
        elif expiry_date is not None:
            validate_award_and_expiry(qualification.award_date, expiry_date)
            if expiry_date != qualification.expiry_date:
                changes.append(f"expiry -> {expiry_date.isoformat()}")
            qualification.expiry_date = expiry_date

        if not changes:
            return qualification

        AuditService.record(
            action=AuditAction.QUALIFICATION_UPDATED,
            entity_type="qualification",
            entity_id=qualification.credential_id,
            detail="; ".join(changes),
        )
        db.session.commit()
        return qualification

    @staticmethod
    def revoke(*, actor: User, qualification_id: int, reason: str) -> Qualification:
        """Revoke a qualification, recording who did it and why."""
        QualificationService._assert_can_issue(actor)
        qualification = QualificationRepository.get(qualification_id)
        if qualification is None:
            raise NotFoundError("Qualification not found.")
        if qualification.status == QualificationStatus.REVOKED:
            raise ValidationError("Qualification is already revoked.")
        reason = validate_required(reason, "reason", "Revocation reason", max_length=500)

        qualification.status = QualificationStatus.REVOKED
        qualification.revocation_reason = reason
        AuditService.record(
            action=AuditAction.QUALIFICATION_REVOKED,
            entity_type="qualification",
            entity_id=qualification.credential_id,
            detail=f"Revoked: {reason}",
        )
        db.session.commit()
        return qualification

    @staticmethod
    def reinstate(*, actor: User, qualification_id: int, reason: str) -> Qualification:
        """Reverse a revocation. Administrators only -- it re-validates a credential."""
        if not actor.is_admin:
            raise PermissionDeniedError("Only administrators may reinstate a qualification.")
        qualification = QualificationRepository.get(qualification_id)
        if qualification is None:
            raise NotFoundError("Qualification not found.")
        if qualification.status != QualificationStatus.REVOKED:
            raise ValidationError("Only a revoked qualification can be reinstated.")
        reason = validate_required(reason, "reason", "Reinstatement reason", max_length=500)

        qualification.status = QualificationStatus.ACTIVE
        qualification.revocation_reason = None
        AuditService.record(
            action=AuditAction.QUALIFICATION_REINSTATED,
            entity_type="qualification",
            entity_id=qualification.credential_id,
            detail=f"Reinstated: {reason}",
        )
        db.session.commit()
        return qualification

    # -- queries -----------------------------------------------------------
    @staticmethod
    def get_or_404(qualification_id: int) -> Qualification:
        qualification = QualificationRepository.get(qualification_id)
        if qualification is None:
            raise NotFoundError("Qualification not found.")
        return qualification

    @staticmethod
    def search(**kwargs):
        return QualificationRepository.search(**kwargs)

    @staticmethod
    def statistics() -> dict[str, int]:
        """Counts used by the dashboard tiles."""
        return {
            "total": QualificationRepository.count_all(),
            "active": QualificationRepository.count_by_status(QualificationStatus.ACTIVE),
            "revoked": QualificationRepository.count_by_status(QualificationStatus.REVOKED),
        }
