"""The verification engine.

Workflow implemented here:

    credential ID -> input validation -> database lookup -> status evaluation
    -> result -> verification record -> audit record

A verification is always recorded, including failed and malformed attempts,
because "who tried to verify what, and when" is exactly the auditable history
the system exists to provide.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from flask import has_request_context, request

from app.extensions import db
from app.models.enums import (
    AuditAction,
    QualificationStatus,
    VerificationResult,
)
from app.models.qualification import Qualification
from app.models.user import User
from app.models.verification import Verification
from app.repositories.qualification_repository import QualificationRepository
from app.repositories.verification_repository import VerificationRepository
from app.services.audit_service import AuditService
from app.utils.errors import ValidationError
from app.utils.validators import validate_credential_id

# Messages shown to the verifier. They state the outcome without leaking
# details of a credential that failed to verify.
RESULT_MESSAGES = {
    VerificationResult.VALID: "This credential is valid and currently in good standing.",
    VerificationResult.INVALID: (
        "No credential matching that reference could be found. "
        "Check the reference and try again."
    ),
    VerificationResult.REVOKED: (
        "This credential has been revoked by the issuing institution and is no longer valid."
    ),
    VerificationResult.EXPIRED: (
        "This credential was validly issued but has passed its expiry date."
    ),
}


@dataclass(frozen=True)
class VerificationOutcome:
    """What the verification produced, ready for rendering."""

    result: VerificationResult
    reference: str
    credential_id: str
    message: str
    qualification: Qualification | None = None

    @property
    def is_valid(self) -> bool:
        return self.result == VerificationResult.VALID

    @property
    def css_tone(self) -> str:
        """Tailwind tone key used by the result template."""
        return {
            VerificationResult.VALID: "success",
            VerificationResult.INVALID: "danger",
            VerificationResult.REVOKED: "danger",
            VerificationResult.EXPIRED: "warning",
        }[self.result]


class VerificationService:
    """Evaluate credentials and record every attempt."""

    @staticmethod
    def evaluate_status(
        qualification: Qualification | None, *, on_date: date | None = None
    ) -> VerificationResult:
        """Map a qualification (or its absence) to a verification result.

        Pure function -- no database or request access -- so the decision table
        can be unit tested exhaustively.
        """
        if qualification is None:
            return VerificationResult.INVALID
        if qualification.status == QualificationStatus.REVOKED:
            return VerificationResult.REVOKED
        if qualification.is_expired(on_date):
            return VerificationResult.EXPIRED
        if qualification.status == QualificationStatus.EXPIRED:
            return VerificationResult.EXPIRED
        return VerificationResult.VALID

    @staticmethod
    def _request_metadata() -> tuple[str | None, str | None]:
        if not has_request_context():
            return None, None
        ip = request.headers.get("Fly-Client-IP") or request.headers.get("X-Forwarded-For", "")
        ip = ip.split(",")[0].strip() if ip else request.remote_addr
        agent = (request.headers.get("User-Agent") or "")[:255] or None
        return (ip[:45] if ip else None), agent

    @staticmethod
    def verify(*, credential_id: str, actor: User | None = None) -> VerificationOutcome:
        """Run the full verification workflow for ``credential_id``.

        A malformed reference is treated as INVALID rather than an error: the
        attempt is real and must be auditable, and telling an attacker which
        references are even well-formed is needless information.
        """
        raw = (credential_id or "").strip().upper()
        try:
            normalised = validate_credential_id(raw)
            malformed = False
        except ValidationError:
            normalised = raw[:32] or "(blank)"
            malformed = True

        qualification = (
            None if malformed else QualificationRepository.get_by_credential_id(normalised)
        )
        result = VerificationService.evaluate_status(qualification)

        ip_address, user_agent = VerificationService._request_metadata()
        reference = str(uuid.uuid4())
        record = Verification(
            reference=reference,
            credential_id=normalised,
            qualification_id=qualification.id if qualification else None,
            result=result,
            performed_by_id=actor.id if actor else None,
            ip_address=ip_address,
            user_agent=user_agent,
            notes="Malformed credential reference" if malformed else None,
        )
        VerificationRepository.add(record)
        AuditService.record(
            action=AuditAction.VERIFICATION_PERFORMED,
            entity_type="verification",
            entity_id=reference,
            detail=f"{normalised} -> {result.value}",
        )
        db.session.commit()

        return VerificationOutcome(
            result=result,
            reference=reference,
            credential_id=normalised,
            message=RESULT_MESSAGES[result],
            # Details are only exposed for a credential that actually verified.
            qualification=qualification if result != VerificationResult.INVALID else None,
        )

    # -- queries -----------------------------------------------------------
    @staticmethod
    def history(**kwargs):
        return VerificationRepository.history(**kwargs)

    @staticmethod
    def get_by_reference(reference: str) -> Verification | None:
        return VerificationRepository.get_by_reference(reference)

    @staticmethod
    def statistics() -> dict[str, int]:
        """Counts used by the dashboard tiles."""
        return {
            "total": VerificationRepository.count_all(),
            "valid": VerificationRepository.count_by_result(VerificationResult.VALID),
            "invalid": VerificationRepository.count_by_result(VerificationResult.INVALID),
            "revoked": VerificationRepository.count_by_result(VerificationResult.REVOKED),
            "expired": VerificationRepository.count_by_result(VerificationResult.EXPIRED),
        }
