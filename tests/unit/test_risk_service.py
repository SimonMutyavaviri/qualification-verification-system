"""Unit tests for the rule-based Qualification Review Assistant (bonus)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import QualificationStatus, VerificationResult
from app.models.qualification import Qualification
from app.models.verification import Verification
from app.services.risk_service import THRESHOLDS, RiskService

pytestmark = pytest.mark.unit


def _codes(assessment) -> set[str]:
    return {signal.code for signal in assessment.signals}


class TestRiskSignals:
    def test_clean_record_scores_low(self, db, qualification):
        assessment = RiskService.assess(qualification)
        assert assessment.level == "low"
        assert not assessment.requires_review

    def test_missing_holder_email_is_flagged(self, db, qualification):
        qualification.holder_email = None
        db.session.commit()
        assert "incomplete_holder_contact" in _codes(RiskService.assess(qualification))

    def test_implausibly_old_award_date_is_flagged(self, db, qualification):
        qualification.award_date = date.today() - timedelta(days=365 * 70)
        db.session.commit()
        assert "implausible_award_date" in _codes(RiskService.assess(qualification))

    def test_very_short_validity_window_is_flagged(self, db, qualification):
        qualification.award_date = date.today() - timedelta(days=10)
        qualification.expiry_date = date.today() - timedelta(days=5)
        db.session.commit()
        assert "short_validity_window" in _codes(RiskService.assess(qualification))

    def test_normal_validity_window_is_not_flagged(self, db, qualification):
        qualification.expiry_date = qualification.award_date + timedelta(days=365)
        db.session.commit()
        assert "short_validity_window" not in _codes(RiskService.assess(qualification))

    def test_revoked_credential_is_flagged(self, db, revoked_qualification):
        assessment = RiskService.assess(revoked_qualification)
        assert "revoked_credential" in _codes(assessment)
        assert assessment.requires_review

    def test_many_credentials_for_one_holder_are_flagged(
        self, db, qualification, institution, issuer_user
    ):
        for index in range(THRESHOLDS["holder_credential_count"]):
            db.session.add(
                Qualification(
                    credential_id=f"QVS-2024-DUP{index:03d}",
                    title="Short Course in Ethics",
                    qualification_type="Short Course",
                    holder_name=qualification.holder_name,
                    institution_id=institution.id,
                    award_date=date.today() - timedelta(days=100),
                    status=QualificationStatus.ACTIVE,
                    issued_by_id=issuer_user.id,
                )
            )
        db.session.commit()
        assert "high_holder_volume" in _codes(RiskService.assess(qualification))

    def test_repeated_failed_lookups_are_flagged(self, db, qualification):
        for index in range(THRESHOLDS["failed_attempt_count"]):
            db.session.add(
                Verification(
                    reference=f"ref-{index}",
                    credential_id=qualification.credential_id,
                    qualification_id=qualification.id,
                    result=VerificationResult.INVALID,
                )
            )
        db.session.commit()
        assert "repeated_failed_lookups" in _codes(RiskService.assess(qualification))

    def test_successful_lookups_do_not_trigger_the_failure_rule(self, db, qualification):
        for index in range(THRESHOLDS["failed_attempt_count"] + 2):
            db.session.add(
                Verification(
                    reference=f"ok-{index}",
                    credential_id=qualification.credential_id,
                    qualification_id=qualification.id,
                    result=VerificationResult.VALID,
                )
            )
        db.session.commit()
        assert "repeated_failed_lookups" not in _codes(RiskService.assess(qualification))


class TestRiskScoring:
    def test_score_is_capped_at_100(self, db, revoked_qualification):
        revoked_qualification.holder_email = None
        revoked_qualification.award_date = date.today() - timedelta(days=365 * 70)
        revoked_qualification.expiry_date = revoked_qualification.award_date + timedelta(days=1)
        db.session.commit()
        assert RiskService.assess(revoked_qualification).score <= 100

    @pytest.mark.parametrize(
        "score,expected", [(0, "low"), (34, "low"), (35, "medium"), (69, "medium"), (70, "high")]
    )
    def test_level_boundaries(self, score, expected):
        assert RiskService._level_for(score) == expected

    def test_tone_matches_the_level(self, db, revoked_qualification):
        assert RiskService.assess(revoked_qualification).tone in {"success", "warning", "danger"}

    def test_signals_carry_an_explanation(self, db, revoked_qualification):
        for signal in RiskService.assess(revoked_qualification).signals:
            assert signal.message
            assert signal.weight > 0
