"""Authentication and user/institution administration."""

from __future__ import annotations

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.enums import AuditAction, Role
from app.models.institution import Institution
from app.models.user import User, utcnow
from app.repositories.user_repository import InstitutionRepository, UserRepository
from app.services.audit_service import AuditService
from app.utils.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.utils.validators import (
    validate_email,
    validate_password,
    validate_required,
    validate_username,
)


class AuthService:
    """Credential checking and login/logout auditing."""

    @staticmethod
    def authenticate(identifier: str, password: str) -> User:
        """Return the user for valid credentials, else raise ValidationError.

        The same message is returned whether the username or the password was
        wrong, so the response cannot be used to enumerate accounts.
        """
        generic = "Invalid username or password."
        if not identifier or not password:
            raise ValidationError(generic)

        user = UserRepository.get_by_identifier(identifier)
        if user is None or not user.check_password(password):
            AuditService.record(
                action=AuditAction.LOGIN_FAILURE,
                entity_type="user",
                entity_id=identifier[:64],
                detail="Failed sign-in attempt",
                actor_label=identifier[:64] or "anonymous",
                commit=True,
            )
            if user is not None:
                user.failed_login_count = (user.failed_login_count or 0) + 1
                db.session.commit()
            raise ValidationError(generic)

        if not user.is_active:
            AuditService.record(
                action=AuditAction.LOGIN_FAILURE,
                entity_type="user",
                entity_id=user.username,
                detail="Sign-in attempt on a deactivated account",
                actor_id=user.id,
                actor_label=user.username,
                commit=True,
            )
            raise ValidationError("This account has been deactivated. Contact an administrator.")

        user.failed_login_count = 0
        user.last_login_at = utcnow()
        AuditService.record(
            action=AuditAction.LOGIN_SUCCESS,
            entity_type="user",
            entity_id=user.username,
            detail=f"Signed in as {user.role.value}",
            actor_id=user.id,
            actor_label=user.username,
        )
        db.session.commit()
        return user

    @staticmethod
    def record_logout(user: User) -> None:
        AuditService.record(
            action=AuditAction.LOGOUT,
            entity_type="user",
            entity_id=user.username,
            detail="Signed out",
            actor_id=user.id,
            actor_label=user.username,
            commit=True,
        )


class UserService:
    """User administration -- administrators only."""

    @staticmethod
    def _assert_admin(actor: User) -> None:
        if not actor.is_admin:
            raise PermissionDeniedError("Only administrators may manage users.")

    @staticmethod
    def create_user(
        *,
        actor: User,
        username: str,
        email: str,
        full_name: str,
        password: str,
        role: Role,
        institution_id: int | None = None,
    ) -> User:
        """Create a user account after validating every field."""
        UserService._assert_admin(actor)
        username = validate_username(username)
        email = validate_email(email)
        full_name = validate_required(full_name, "full_name", "Full name")
        min_length = current_app.config.get("PASSWORD_MIN_LENGTH", 12)
        validate_password(password, min_length=min_length)
        if not isinstance(role, Role):
            raise ValidationError("A valid role must be selected.", field="role")

        if UserRepository.get_by_username(username) is not None:
            raise ValidationError("That username is already taken.", field="username")
        if UserRepository.get_by_email(email) is not None:
            raise ValidationError("That email address is already registered.", field="email")
        if institution_id and InstitutionRepository.get(int(institution_id)) is None:
            raise ValidationError("Selected institution does not exist.", field="institution_id")

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            institution_id=int(institution_id) if institution_id else None,
        )
        user.set_password(password)
        UserRepository.add(user)
        AuditService.record(
            action=AuditAction.USER_CREATED,
            entity_type="user",
            entity_id=username,
            detail=f"Created {role.value} account for {full_name}",
        )
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise ValidationError("That username or email is already registered.") from exc
        return user

    @staticmethod
    def set_role(*, actor: User, user_id: int, role: Role) -> User:
        """Change a user's role, refusing self-demotion of the last admin path."""
        UserService._assert_admin(actor)
        user = UserRepository.get(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        if user.id == actor.id and role != Role.ADMIN:
            raise ValidationError("You cannot remove your own administrator role.")
        previous = user.role
        if previous == role:
            return user
        user.role = role
        AuditService.record(
            action=AuditAction.USER_UPDATED,
            entity_type="user",
            entity_id=user.username,
            detail=f"Role changed {previous.value} -> {role.value}",
        )
        db.session.commit()
        return user

    @staticmethod
    def set_active(*, actor: User, user_id: int, is_active: bool) -> User:
        """Activate or deactivate an account (deactivation blocks sign-in)."""
        UserService._assert_admin(actor)
        user = UserRepository.get(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        if user.id == actor.id and not is_active:
            raise ValidationError("You cannot deactivate your own account.")
        if user.is_active == is_active:
            return user
        user.is_active = is_active
        AuditService.record(
            action=AuditAction.USER_UPDATED if is_active else AuditAction.USER_DEACTIVATED,
            entity_type="user",
            entity_id=user.username,
            detail="Account activated" if is_active else "Account deactivated",
        )
        db.session.commit()
        return user

    @staticmethod
    def change_password(*, user: User, current_password: str, new_password: str) -> User:
        """Let a signed-in user rotate their own password."""
        if not user.check_password(current_password):
            raise ValidationError("Your current password is incorrect.", field="current_password")
        min_length = current_app.config.get("PASSWORD_MIN_LENGTH", 12)
        validate_password(new_password, min_length=min_length)
        if user.check_password(new_password):
            raise ValidationError(
                "The new password must differ from the current one.", field="new_password"
            )
        user.set_password(new_password)
        AuditService.record(
            action=AuditAction.USER_UPDATED,
            entity_type="user",
            entity_id=user.username,
            detail="Password changed",
            actor_id=user.id,
            actor_label=user.username,
        )
        db.session.commit()
        return user


class InstitutionService:
    """Institution administration -- administrators only."""

    @staticmethod
    def create(
        *,
        actor: User,
        name: str,
        code: str,
        country: str | None = None,
        contact_email: str | None = None,
    ) -> Institution:
        if not actor.is_admin:
            raise PermissionDeniedError("Only administrators may manage institutions.")
        name = validate_required(name, "name", "Institution name")
        code = validate_required(code, "code", "Institution code", max_length=16).upper()
        contact_email = validate_email(contact_email, field="contact_email", required=False)
        if InstitutionRepository.get_by_code(code) is not None:
            raise ValidationError("That institution code is already in use.", field="code")
        if InstitutionRepository.get_by_name(name) is not None:
            raise ValidationError("That institution name already exists.", field="name")

        institution = Institution(
            name=name,
            code=code,
            country=(country or "").strip() or None,
            contact_email=contact_email,
        )
        InstitutionRepository.add(institution)
        AuditService.record(
            action=AuditAction.INSTITUTION_CREATED,
            entity_type="institution",
            entity_id=code,
            detail=f"Created institution {name}",
        )
        db.session.commit()
        return institution

    @staticmethod
    def set_active(*, actor: User, institution_id: int, is_active: bool) -> Institution:
        if not actor.is_admin:
            raise PermissionDeniedError("Only administrators may manage institutions.")
        institution = InstitutionRepository.get(institution_id)
        if institution is None:
            raise NotFoundError("Institution not found.")
        institution.is_active = is_active
        AuditService.record(
            action=AuditAction.INSTITUTION_UPDATED,
            entity_type="institution",
            entity_id=institution.code,
            detail="Activated" if is_active else "Deactivated",
        )
        db.session.commit()
        return institution
