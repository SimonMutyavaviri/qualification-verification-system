"""Data access for qualifications.

Keeping queries here means the service layer expresses business rules and the
routes never touch SQLAlchemy directly.
"""

from __future__ import annotations

from sqlalchemy import or_, select

from app.extensions import db
from app.models.enums import QualificationStatus
from app.models.institution import Institution
from app.models.qualification import Qualification


class QualificationRepository:
    """Query and persistence helpers for the Qualification model."""

    @staticmethod
    def add(qualification: Qualification) -> Qualification:
        db.session.add(qualification)
        return qualification

    @staticmethod
    def get(qualification_id: int) -> Qualification | None:
        return db.session.get(Qualification, qualification_id)

    @staticmethod
    def get_by_credential_id(credential_id: str) -> Qualification | None:
        """Look up a qualification by its public credential reference."""
        stmt = select(Qualification).where(
            Qualification.credential_id == credential_id.strip().upper()
        )
        return db.session.scalars(stmt).first()

    @staticmethod
    def exists_credential_id(credential_id: str) -> bool:
        return QualificationRepository.get_by_credential_id(credential_id) is not None

    @staticmethod
    def search(
        *,
        query: str | None = None,
        status: QualificationStatus | None = None,
        institution_id: int | None = None,
        qualification_type: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ):
        """Paginated search across credential ID, holder name and title."""
        stmt = select(Qualification).join(Institution)
        if query:
            like = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Qualification.credential_id.ilike(like),
                    Qualification.holder_name.ilike(like),
                    Qualification.title.ilike(like),
                )
            )
        if status is not None:
            stmt = stmt.where(Qualification.status == status)
        if institution_id:
            stmt = stmt.where(Qualification.institution_id == institution_id)
        if qualification_type:
            stmt = stmt.where(Qualification.qualification_type == qualification_type)
        stmt = stmt.order_by(Qualification.created_at.desc())
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def count_by_status(status: QualificationStatus) -> int:
        stmt = select(db.func.count(Qualification.id)).where(Qualification.status == status)
        return db.session.scalar(stmt) or 0

    @staticmethod
    def count_all() -> int:
        return db.session.scalar(select(db.func.count(Qualification.id))) or 0

    @staticmethod
    def recent(limit: int = 5) -> list[Qualification]:
        stmt = select(Qualification).order_by(Qualification.created_at.desc()).limit(limit)
        return list(db.session.scalars(stmt))
