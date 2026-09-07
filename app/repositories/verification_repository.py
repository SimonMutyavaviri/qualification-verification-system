"""Data access for verification records."""

from __future__ import annotations

from sqlalchemy import select

from app.extensions import db
from app.models.enums import VerificationResult
from app.models.verification import Verification


class VerificationRepository:
    """Query and persistence helpers for the Verification model."""

    @staticmethod
    def add(verification: Verification) -> Verification:
        db.session.add(verification)
        return verification

    @staticmethod
    def get_by_reference(reference: str) -> Verification | None:
        stmt = select(Verification).where(Verification.reference == reference)
        return db.session.scalars(stmt).first()

    @staticmethod
    def history(
        *,
        credential_id: str | None = None,
        result: VerificationResult | None = None,
        performed_by_id: int | None = None,
        page: int = 1,
        per_page: int = 10,
    ):
        """Paginated verification history, newest first."""
        stmt = select(Verification)
        if credential_id:
            stmt = stmt.where(
                Verification.credential_id.ilike(f"%{credential_id.strip().upper()}%")
            )
        if result is not None:
            stmt = stmt.where(Verification.result == result)
        if performed_by_id:
            stmt = stmt.where(Verification.performed_by_id == performed_by_id)
        stmt = stmt.order_by(Verification.created_at.desc())
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def count_by_result(result: VerificationResult) -> int:
        stmt = select(db.func.count(Verification.id)).where(Verification.result == result)
        return db.session.scalar(stmt) or 0

    @staticmethod
    def count_all() -> int:
        return db.session.scalar(select(db.func.count(Verification.id))) or 0

    @staticmethod
    def recent(limit: int = 5) -> list[Verification]:
        stmt = select(Verification).order_by(Verification.created_at.desc()).limit(limit)
        return list(db.session.scalars(stmt))
