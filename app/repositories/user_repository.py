"""Data access for users and institutions."""

from __future__ import annotations

from sqlalchemy import func, or_, select

from app.extensions import db
from app.models.institution import Institution
from app.models.user import User


class UserRepository:
    """Query and persistence helpers for the User model."""

    @staticmethod
    def add(user: User) -> User:
        db.session.add(user)
        return user

    @staticmethod
    def get(user_id: int) -> User | None:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_username(username: str) -> User | None:
        stmt = select(User).where(func.lower(User.username) == username.strip().lower())
        return db.session.scalars(stmt).first()

    @staticmethod
    def get_by_email(email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        return db.session.scalars(stmt).first()

    @staticmethod
    def get_by_identifier(identifier: str) -> User | None:
        """Look up by username or email so sign-in accepts either."""
        cleaned = identifier.strip().lower()
        stmt = select(User).where(
            or_(func.lower(User.username) == cleaned, func.lower(User.email) == cleaned)
        )
        return db.session.scalars(stmt).first()

    @staticmethod
    def list_all(page: int = 1, per_page: int = 10):
        stmt = select(User).order_by(User.created_at.desc())
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def count_all() -> int:
        return db.session.scalar(select(func.count(User.id))) or 0


class InstitutionRepository:
    """Query and persistence helpers for the Institution model."""

    @staticmethod
    def add(institution: Institution) -> Institution:
        db.session.add(institution)
        return institution

    @staticmethod
    def get(institution_id: int) -> Institution | None:
        return db.session.get(Institution, institution_id)

    @staticmethod
    def get_by_code(code: str) -> Institution | None:
        stmt = select(Institution).where(func.lower(Institution.code) == code.strip().lower())
        return db.session.scalars(stmt).first()

    @staticmethod
    def get_by_name(name: str) -> Institution | None:
        stmt = select(Institution).where(func.lower(Institution.name) == name.strip().lower())
        return db.session.scalars(stmt).first()

    @staticmethod
    def list_active() -> list[Institution]:
        stmt = select(Institution).where(Institution.is_active.is_(True)).order_by(Institution.name)
        return list(db.session.scalars(stmt))

    @staticmethod
    def list_all(page: int = 1, per_page: int = 10):
        stmt = select(Institution).order_by(Institution.name)
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def count_all() -> int:
        return db.session.scalar(select(func.count(Institution.id))) or 0
