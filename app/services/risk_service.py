"""Qualification Review Assistant (bonus feature).

A rule-based assistant that scores a submitted qualification for signals that
warrant a human look: implausible dates, an unusually short-lived credential,
a holder with an unusual number of credentials, a burst of failed verification
attempts against the same reference, and so on.

Deliberately rule-based rather than model-based: an assistant that influences
whether a credential is trusted must be explainable and reproducible, and every
signal below can be pointed at a specific field in the record. The rules are
data, so a reviewer can read the thresholds without reading the code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import func, select

from app.extensions import db
from app.models.enums import QualificationStatus, VerificationResult
from app.models.qualification import Qualification
from app.models.verification import Verification

# Tunable thresholds, kept together so they can be reviewed and adjusted
# without touching the scoring logic.
THRESHOLDS = {
    "backdated_years": 60,  # award date implausibly far in the past
    "short_validity_days": 30,  # awarded and expiring almost immediately
    "holder_credential_count": 5,  # unusually many credentials for one holder
    "failed_attempt_count": 5,  # repeated failed lookups on this reference
    "recent_registration_days": 1,  # registered very recently
}

_LEVELS = ((70, "high"), (35, "medium"), (0, "low"))


@dataclass
class RiskSignal:
    """One triggered rule, with the weight it contributes."""

    code: str
    weight: int
    message: str


@dataclass
class RiskAssessment:
    """The overall outcome of a review."""

    score: int
    level: str
    signals: list[RiskSignal] = field(default_factory=list)

    @property
    def requires_review(self) -> bool:
        return self.level in {"medium", "high"}

    @property
    def tone(self) -> str:
        return {"high": "danger", "medium": "warning", "low": "success"}[self.level]


class RiskService:
    """Score a qualification against the review rules."""

    @staticmethod
    def _level_for(score: int) -> str:
        for threshold, level in _LEVELS:
            if score >= threshold:
                return level
        return "low"

    @staticmethod
    def assess(qualification: Qualification, *, today: date | None = None) -> RiskAssessment:
        """Return a :class:`RiskAssessment` for ``qualification``."""
        today = today or date.today()
        signals: list[RiskSignal] = []

        # 1. Implausibly old award date.
        age_years = (today - qualification.award_date).days / 365.25
        if age_years > THRESHOLDS["backdated_years"]:
            signals.append(
                RiskSignal(
                    "implausible_award_date",
                    30,
                    f"Award date is {int(age_years)} years ago, beyond the "
                    f"{THRESHOLDS['backdated_years']}-year plausibility window.",
                )
            )

        # 2. Credential that expires almost as soon as it is awarded.
        if qualification.expiry_date is not None:
            validity_days = (qualification.expiry_date - qualification.award_date).days
            if validity_days < THRESHOLDS["short_validity_days"]:
                signals.append(
                    RiskSignal(
                        "short_validity_window",
                        25,
                        f"Credential is valid for only {validity_days} day(s), "
                        "which is unusually short.",
                    )
                )

        # 3. Missing holder contact detail limits any follow-up.
        if not qualification.holder_email:
            signals.append(
                RiskSignal(
                    "incomplete_holder_contact",
                    10,
                    "No holder email address recorded, so the award cannot be "
                    "confirmed with the holder.",
                )
            )

        # 4. One holder name carrying an unusual number of credentials.
        holder_count = (
            db.session.scalar(
                select(func.count(Qualification.id)).where(
                    Qualification.holder_name == qualification.holder_name
                )
            )
            or 0
        )
        if holder_count > THRESHOLDS["holder_credential_count"]:
            signals.append(
                RiskSignal(
                    "high_holder_volume",
                    20,
                    f"{holder_count} credentials are registered to this holder name.",
                )
            )

        # 5. Repeated failed verification attempts against this reference.
        failed_attempts = (
            db.session.scalar(
                select(func.count(Verification.id)).where(
                    Verification.credential_id == qualification.credential_id,
                    Verification.result != VerificationResult.VALID,
                )
            )
            or 0
        )
        if failed_attempts >= THRESHOLDS["failed_attempt_count"]:
            signals.append(
                RiskSignal(
                    "repeated_failed_lookups",
                    20,
                    f"{failed_attempts} verification attempts on this reference "
                    "did not return VALID.",
                )
            )

        # 6. Already revoked -- always worth surfacing in a review queue.
        if qualification.status == QualificationStatus.REVOKED:
            signals.append(
                RiskSignal("revoked_credential", 40, "This credential has been revoked.")
            )

        score = min(100, sum(signal.weight for signal in signals))
        return RiskAssessment(score=score, level=RiskService._level_for(score), signals=signals)
