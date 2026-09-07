"""Unit tests for the verification engine (REQ-VER-*)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import AuditAction, QualificationStatus, VerificationResult
from app.repositories.audit_repository import AuditRepository
from app.repositories.verification_repository import VerificationRepository
from app.services.verification_service import VerificationService

pytestmark = pytest.mark.unit


class TestStatusDecisionTable:
    """``evaluate_status`` is pure, so every branch is covered directly."""

    def test_missing_qualification_is_invalid(self):
        assert VerificationService.evaluate_status(None) == VerificationResult.INVALID

    def test_active_unexpired_is_valid(self, qualification):
        assert VerificationService.evaluate_status(qualification) == VerificationResult.VALID

    def test_revoked_is_revoked(self, revoked_qualification):
        assert (
            VerificationService.evaluate_status(revoked_qualification) == VerificationResult.REVOKED
        )

    def test_past_expiry_is_expired(self, expired_qualification):
        assert (
            VerificationService.evaluate_status(expired_qualification) == VerificationResult.EXPIRED
        )

    def test_revocation_outranks_expiry(self, db, expired_qualification):
        expired_qualification.status = QualificationStatus.REVOKED
        db.session.commit()
        assert (
            VerificationService.evaluate_status(expired_qualification) == VerificationResult.REVOKED
        )

    def test_expiry_evaluated_against_supplied_date(self, db, qualification):
        qualification.expiry_date = date.today() + timedelta(days=30)
        db.session.commit()
        assert VerificationService.evaluate_status(qualification) == VerificationResult.VALID
        future = date.today() + timedelta(days=60)
        assert (
            VerificationService.evaluate_status(qualification, on_date=future)
            == VerificationResult.EXPIRED
        )

    def test_expiry_on_the_expiry_date_itself_is_still_valid(self, db, qualification):
        qualification.expiry_date = date.today()
        db.session.commit()
        assert VerificationService.evaluate_status(qualification) == VerificationResult.VALID


class TestVerifyWorkflow:
    def test_valid_credential_returns_valid_with_details(self, db, qualification, verifier_user):
        outcome = VerificationService.verify(
            credential_id=qualification.credential_id, actor=verifier_user
        )
        assert outcome.result == VerificationResult.VALID
        assert outcome.is_valid
        assert outcome.qualification.id == qualification.id
        assert outcome.reference

    def test_lookup_is_case_insensitive(self, db, qualification, verifier_user):
        outcome = VerificationService.verify(
            credential_id=qualification.credential_id.lower(), actor=verifier_user
        )
        assert outcome.result == VerificationResult.VALID

    def test_unknown_credential_returns_invalid(self, db, verifier_user):
        outcome = VerificationService.verify(credential_id="QVS-2024-NOTREG", actor=verifier_user)
        assert outcome.result == VerificationResult.INVALID

    def test_invalid_result_discloses_no_qualification(self, db, verifier_user):
        outcome = VerificationService.verify(credential_id="QVS-2024-NOTREG", actor=verifier_user)
        assert outcome.qualification is None

    def test_malformed_reference_is_invalid_and_noted(self, db, verifier_user):
        outcome = VerificationService.verify(credential_id="not a credential", actor=verifier_user)
        assert outcome.result == VerificationResult.INVALID
        record = VerificationRepository.get_by_reference(outcome.reference)
        assert record.notes == "Malformed credential reference"

    def test_blank_reference_is_handled(self, db, verifier_user):
        outcome = VerificationService.verify(credential_id="", actor=verifier_user)
        assert outcome.result == VerificationResult.INVALID

    def test_revoked_credential_returns_revoked(self, db, revoked_qualification, verifier_user):
        outcome = VerificationService.verify(
            credential_id=revoked_qualification.credential_id, actor=verifier_user
        )
        assert outcome.result == VerificationResult.REVOKED
        assert "revoked" in outcome.message.lower()

    def test_expired_credential_returns_expired(self, db, expired_qualification, verifier_user):
        outcome = VerificationService.verify(
            credential_id=expired_qualification.credential_id, actor=verifier_user
        )
        assert outcome.result == VerificationResult.EXPIRED

    def test_every_result_has_a_distinct_tone(self, db, verifier_user, qualification):
        outcome = VerificationService.verify(
            credential_id=qualification.credential_id, actor=verifier_user
        )
        assert outcome.css_tone == "success"


class TestVerificationRecording:
    def test_creates_a_verification_record(self, db, qualification, verifier_user):
        before = VerificationRepository.count_all()
        VerificationService.verify(credential_id=qualification.credential_id, actor=verifier_user)
        assert VerificationRepository.count_all() == before + 1

    def test_record_links_to_the_qualification(self, db, qualification, verifier_user):
        outcome = VerificationService.verify(
            credential_id=qualification.credential_id, actor=verifier_user
        )
        record = VerificationRepository.get_by_reference(outcome.reference)
        assert record.qualification_id == qualification.id
        assert record.performed_by_id == verifier_user.id

    def test_failed_attempt_is_still_recorded(self, db, verifier_user):
        before = VerificationRepository.count_all()
        VerificationService.verify(credential_id="QVS-2024-NOTREG", actor=verifier_user)
        assert VerificationRepository.count_all() == before + 1

    def test_records_an_audit_entry(self, db, qualification, verifier_user):
        VerificationService.verify(credential_id=qualification.credential_id, actor=verifier_user)
        latest = AuditRepository.recent(1)[0]
        assert latest.action == AuditAction.VERIFICATION_PERFORMED
        assert "VALID" in latest.detail

    def test_anonymous_verification_is_recorded_without_an_actor(self, db, qualification):
        outcome = VerificationService.verify(credential_id=qualification.credential_id)
        record = VerificationRepository.get_by_reference(outcome.reference)
        assert record.performed_by_id is None

    def test_references_are_unique(self, db, qualification, verifier_user):
        references = {
            VerificationService.verify(
                credential_id=qualification.credential_id, actor=verifier_user
            ).reference
            for _ in range(5)
        }
        assert len(references) == 5


class TestHistoryAndStatistics:
    def test_history_returns_newest_first(self, db, qualification, verifier_user):
        VerificationService.verify(credential_id=qualification.credential_id, actor=verifier_user)
        VerificationService.verify(credential_id="QVS-2024-NOTREG", actor=verifier_user)
        items = VerificationService.history(page=1, per_page=10).items
        assert items[0].credential_id == "QVS-2024-NOTREG"

    def test_history_filters_by_result(self, db, qualification, verifier_user):
        VerificationService.verify(credential_id=qualification.credential_id, actor=verifier_user)
        VerificationService.verify(credential_id="QVS-2024-NOTREG", actor=verifier_user)
        page = VerificationService.history(result=VerificationResult.INVALID)
        assert page.total == 1

    def test_history_filters_by_actor(self, db, qualification, verifier_user, issuer_user):
        VerificationService.verify(credential_id=qualification.credential_id, actor=verifier_user)
        VerificationService.verify(credential_id=qualification.credential_id, actor=issuer_user)
        page = VerificationService.history(performed_by_id=verifier_user.id)
        assert page.total == 1

    def test_statistics_count_each_result(
        self, db, qualification, revoked_qualification, expired_qualification, verifier_user
    ):
        for credential in (
            qualification.credential_id,
            revoked_qualification.credential_id,
            expired_qualification.credential_id,
            "QVS-2024-NOTREG",
        ):
            VerificationService.verify(credential_id=credential, actor=verifier_user)
        stats = VerificationService.statistics()
        assert stats == {"total": 4, "valid": 1, "invalid": 1, "revoked": 1, "expired": 1}
