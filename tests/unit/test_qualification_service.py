"""Unit tests for qualification registration, update and revocation."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import AuditAction, QualificationStatus
from app.repositories.audit_repository import AuditRepository
from app.services.qualification_service import QualificationService
from app.utils.errors import (
    DuplicateCredentialError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

pytestmark = pytest.mark.unit


def _register(actor, institution, **overrides):
    payload = {
        "actor": actor,
        "title": "MSc Information Security",
        "qualification_type": "Degree",
        "holder_name": "Chipo Dube",
        "institution_id": institution.id,
        "award_date": date.today() - timedelta(days=365),
    }
    payload.update(overrides)
    return QualificationService.register(**payload)


class TestRegistration:
    def test_registers_with_generated_credential_id(self, db, issuer_user, institution):
        qualification = _register(issuer_user, institution)
        assert qualification.id is not None
        assert qualification.credential_id.startswith("QVS-")
        assert qualification.status == QualificationStatus.ACTIVE
        assert qualification.issued_by_id == issuer_user.id

    def test_registers_with_supplied_credential_id(self, db, issuer_user, institution):
        qualification = _register(issuer_user, institution, credential_id="qvs-2024-zzzzzz")
        assert qualification.credential_id == "QVS-2024-ZZZZZZ"

    def test_writes_an_audit_entry(self, db, issuer_user, institution):
        _register(issuer_user, institution)
        actions = [entry.action for entry in AuditRepository.recent(10)]
        assert AuditAction.QUALIFICATION_CREATED in actions

    def test_rejects_duplicate_credential_id(self, db, issuer_user, institution, qualification):
        with pytest.raises(DuplicateCredentialError):
            _register(issuer_user, institution, credential_id=qualification.credential_id)

    def test_duplicate_check_is_case_insensitive(self, db, issuer_user, institution, qualification):
        with pytest.raises(DuplicateCredentialError):
            _register(issuer_user, institution, credential_id=qualification.credential_id.lower())

    def test_rejects_verifier(self, db, verifier_user, institution):
        with pytest.raises(PermissionDeniedError):
            _register(verifier_user, institution)

    def test_admin_may_register(self, db, admin_user, institution):
        assert _register(admin_user, institution).id is not None

    def test_rejects_unknown_institution(self, db, issuer_user, institution):
        with pytest.raises(ValidationError, match="does not exist"):
            _register(issuer_user, institution, institution_id=9999)

    def test_rejects_inactive_institution(self, db, issuer_user, institution):
        institution.is_active = False
        db.session.commit()
        with pytest.raises(ValidationError, match="not active"):
            _register(issuer_user, institution)

    def test_rejects_blank_title(self, db, issuer_user, institution):
        with pytest.raises(ValidationError, match="title is required"):
            _register(issuer_user, institution, title="  ")

    def test_rejects_future_award_date(self, db, issuer_user, institution):
        with pytest.raises(ValidationError, match="future"):
            _register(issuer_user, institution, award_date=date.today() + timedelta(days=1))

    def test_rejects_expiry_before_award(self, db, issuer_user, institution):
        with pytest.raises(ValidationError, match="on or after"):
            _register(
                issuer_user,
                institution,
                award_date=date.today() - timedelta(days=10),
                expiry_date=date.today() - timedelta(days=20),
            )

    def test_rejects_unknown_qualification_type(self, db, issuer_user, institution):
        with pytest.raises(ValidationError, match="must be one of"):
            _register(issuer_user, institution, qualification_type="Honorary")


class TestGeneratedCredentialIds:
    def test_ids_are_unique_across_many_calls(self, db):
        generated = {QualificationService.generate_credential_id() for _ in range(50)}
        assert len(generated) == 50

    def test_id_matches_the_documented_format(self, db):
        from app.utils.validators import validate_credential_id

        candidate = QualificationService.generate_credential_id()
        assert validate_credential_id(candidate) == candidate

    def test_id_avoids_ambiguous_characters(self, db):
        for _ in range(20):
            suffix = QualificationService.generate_credential_id().split("-")[-1]
            assert not set(suffix) & {"O", "0", "I", "1"}


class TestUpdate:
    def test_updates_mutable_fields(self, db, issuer_user, qualification):
        updated = QualificationService.update(
            actor=issuer_user,
            qualification_id=qualification.id,
            title="BSc Honours in Software Engineering",
            holder_name="Tinashe R. Moyo",
        )
        assert updated.title == "BSc Honours in Software Engineering"
        assert updated.holder_name == "Tinashe R. Moyo"

    def test_records_an_audit_entry_describing_the_change(self, db, issuer_user, qualification):
        QualificationService.update(
            actor=issuer_user, qualification_id=qualification.id, title="New Title"
        )
        latest = AuditRepository.recent(1)[0]
        assert latest.action == AuditAction.QUALIFICATION_UPDATED
        assert "New Title" in latest.detail

    def test_no_change_writes_no_audit_entry(self, db, issuer_user, qualification):
        before = AuditRepository.count_all()
        QualificationService.update(
            actor=issuer_user, qualification_id=qualification.id, title=qualification.title
        )
        assert AuditRepository.count_all() == before

    def test_clear_expiry_removes_the_date(self, db, issuer_user, expired_qualification):
        updated = QualificationService.update(
            actor=issuer_user, qualification_id=expired_qualification.id, clear_expiry=True
        )
        assert updated.expiry_date is None

    def test_rejects_verifier(self, db, verifier_user, qualification):
        with pytest.raises(PermissionDeniedError):
            QualificationService.update(
                actor=verifier_user, qualification_id=qualification.id, title="x"
            )

    def test_rejects_unknown_qualification(self, db, issuer_user):
        with pytest.raises(NotFoundError):
            QualificationService.update(actor=issuer_user, qualification_id=9999, title="x")

    def test_rejects_editing_a_revoked_qualification(self, db, issuer_user, revoked_qualification):
        with pytest.raises(ValidationError, match="revoked qualification cannot be edited"):
            QualificationService.update(
                actor=issuer_user, qualification_id=revoked_qualification.id, title="x"
            )


class TestRevocation:
    def test_revokes_with_a_reason(self, db, issuer_user, qualification):
        revoked = QualificationService.revoke(
            actor=issuer_user, qualification_id=qualification.id, reason="Records audit"
        )
        assert revoked.status == QualificationStatus.REVOKED
        assert revoked.revocation_reason == "Records audit"

    def test_writes_an_audit_entry(self, db, issuer_user, qualification):
        QualificationService.revoke(
            actor=issuer_user, qualification_id=qualification.id, reason="Records audit"
        )
        assert AuditRepository.recent(1)[0].action == AuditAction.QUALIFICATION_REVOKED

    def test_requires_a_reason(self, db, issuer_user, qualification):
        with pytest.raises(ValidationError, match="reason is required"):
            QualificationService.revoke(
                actor=issuer_user, qualification_id=qualification.id, reason="  "
            )

    def test_rejects_double_revocation(self, db, issuer_user, revoked_qualification):
        with pytest.raises(ValidationError, match="already revoked"):
            QualificationService.revoke(
                actor=issuer_user, qualification_id=revoked_qualification.id, reason="again"
            )

    def test_rejects_verifier(self, db, verifier_user, qualification):
        with pytest.raises(PermissionDeniedError):
            QualificationService.revoke(
                actor=verifier_user, qualification_id=qualification.id, reason="no"
            )


class TestReinstatement:
    def test_admin_can_reinstate(self, db, admin_user, revoked_qualification):
        reinstated = QualificationService.reinstate(
            actor=admin_user,
            qualification_id=revoked_qualification.id,
            reason="Audit finding overturned",
        )
        assert reinstated.status == QualificationStatus.ACTIVE
        assert reinstated.revocation_reason is None

    def test_issuer_cannot_reinstate(self, db, issuer_user, revoked_qualification):
        with pytest.raises(PermissionDeniedError):
            QualificationService.reinstate(
                actor=issuer_user, qualification_id=revoked_qualification.id, reason="x"
            )

    def test_rejects_reinstating_an_active_qualification(self, db, admin_user, qualification):
        with pytest.raises(ValidationError, match="Only a revoked"):
            QualificationService.reinstate(
                actor=admin_user, qualification_id=qualification.id, reason="x"
            )


class TestSearch:
    def test_finds_by_partial_holder_name(self, db, qualification):
        results = QualificationService.search(query="Tinashe")
        assert qualification.id in [item.id for item in results.items]

    def test_finds_by_credential_id(self, db, qualification):
        results = QualificationService.search(query=qualification.credential_id)
        assert results.total == 1

    def test_filters_by_status(self, db, qualification, revoked_qualification):
        results = QualificationService.search(status=QualificationStatus.REVOKED)
        assert [item.id for item in results.items] == [revoked_qualification.id]

    def test_returns_nothing_for_an_unmatched_query(self, db, qualification):
        assert QualificationService.search(query="no-such-holder").total == 0

    def test_statistics_reflect_the_register(self, db, qualification, revoked_qualification):
        stats = QualificationService.statistics()
        assert stats["total"] == 2
        assert stats["active"] == 1
        assert stats["revoked"] == 1
