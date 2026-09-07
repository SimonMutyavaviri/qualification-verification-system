"""Unit tests for authentication, user administration and audit integrity."""

from __future__ import annotations

import pytest

from app.models.audit import AuditLog
from app.models.enums import AuditAction, Role
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.user_service import AuthService, InstitutionService, UserService
from app.utils.errors import (
    ImmutableRecordError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from tests.conftest import ADMIN_PASSWORD, VERIFIER_PASSWORD

pytestmark = pytest.mark.unit


class TestPasswordHashing:
    def test_password_is_not_stored_in_plaintext(self, admin_user):
        assert ADMIN_PASSWORD not in admin_user.password_hash

    def test_check_password_accepts_the_correct_password(self, admin_user):
        assert admin_user.check_password(ADMIN_PASSWORD)

    def test_check_password_rejects_a_wrong_password(self, admin_user):
        assert not admin_user.check_password("WrongPassw0rd!23")

    def test_the_same_password_hashes_differently_each_time(self, db, admin_user):
        first = admin_user.password_hash
        admin_user.set_password(ADMIN_PASSWORD)
        assert admin_user.password_hash != first  # salted


class TestAuthentication:
    def test_authenticates_by_username(self, db, admin_user):
        assert AuthService.authenticate("admin", ADMIN_PASSWORD).id == admin_user.id

    def test_authenticates_by_email(self, db, admin_user):
        assert AuthService.authenticate(admin_user.email, ADMIN_PASSWORD).id == admin_user.id

    def test_username_match_is_case_insensitive(self, db, admin_user):
        assert AuthService.authenticate("ADMIN", ADMIN_PASSWORD).id == admin_user.id

    def test_rejects_a_wrong_password(self, db, admin_user):
        with pytest.raises(ValidationError, match="Invalid username or password"):
            AuthService.authenticate("admin", "WrongPassw0rd!23")

    def test_unknown_user_gets_the_same_message_as_a_wrong_password(self, db, admin_user):
        with pytest.raises(ValidationError, match="Invalid username or password"):
            AuthService.authenticate("nosuchuser", "WrongPassw0rd!23")

    def test_rejects_a_deactivated_account(self, db, admin_user):
        admin_user.is_active = False
        db.session.commit()
        with pytest.raises(ValidationError, match="deactivated"):
            AuthService.authenticate("admin", ADMIN_PASSWORD)

    def test_successful_sign_in_is_audited(self, db, admin_user):
        AuthService.authenticate("admin", ADMIN_PASSWORD)
        assert AuditRepository.recent(1)[0].action == AuditAction.LOGIN_SUCCESS

    def test_failed_sign_in_is_audited(self, db, admin_user):
        with pytest.raises(ValidationError):
            AuthService.authenticate("admin", "WrongPassw0rd!23")
        assert AuditAction.LOGIN_FAILURE in [e.action for e in AuditRepository.recent(5)]

    def test_failed_attempts_are_counted(self, db, admin_user):
        for _ in range(3):
            with pytest.raises(ValidationError):
                AuthService.authenticate("admin", "WrongPassw0rd!23")
        assert admin_user.failed_login_count == 3

    def test_successful_sign_in_resets_the_failure_counter(self, db, admin_user):
        with pytest.raises(ValidationError):
            AuthService.authenticate("admin", "WrongPassw0rd!23")
        AuthService.authenticate("admin", ADMIN_PASSWORD)
        assert admin_user.failed_login_count == 0

    def test_sign_in_records_the_timestamp(self, db, admin_user):
        assert admin_user.last_login_at is None
        AuthService.authenticate("admin", ADMIN_PASSWORD)
        assert admin_user.last_login_at is not None

    @pytest.mark.parametrize("identifier,password", [("", "x"), ("admin", ""), ("", "")])
    def test_rejects_blank_credentials(self, db, admin_user, identifier, password):
        with pytest.raises(ValidationError):
            AuthService.authenticate(identifier, password)


class TestRoleModel:
    def test_admin_satisfies_every_role_check(self, admin_user):
        assert admin_user.has_role(Role.VERIFIER)
        assert admin_user.has_role(Role.ISSUER)
        assert admin_user.is_issuer

    def test_issuer_is_not_an_admin(self, issuer_user):
        assert issuer_user.is_issuer
        assert not issuer_user.is_admin

    def test_verifier_holds_only_the_verifier_role(self, verifier_user):
        assert verifier_user.has_role(Role.VERIFIER)
        assert not verifier_user.has_role(Role.ISSUER)
        assert not verifier_user.is_issuer


class TestUserAdministration:
    def test_admin_creates_a_user(self, db, admin_user, institution):
        user = UserService.create_user(
            actor=admin_user,
            username="newissuer",
            email="new@qvs.example.com",
            full_name="New Issuer",
            password="ValidPassw0rd123",
            role=Role.ISSUER,
            institution_id=institution.id,
        )
        assert user.id is not None
        assert user.role == Role.ISSUER

    def test_non_admin_cannot_create_a_user(self, db, issuer_user):
        with pytest.raises(PermissionDeniedError):
            UserService.create_user(
                actor=issuer_user,
                username="x1234",
                email="x@qvs.example.com",
                full_name="X",
                password="ValidPassw0rd123",
                role=Role.VERIFIER,
            )

    def test_rejects_a_duplicate_username(self, db, admin_user):
        with pytest.raises(ValidationError, match="username is already taken"):
            UserService.create_user(
                actor=admin_user,
                username="admin",
                email="other@qvs.example.com",
                full_name="Other",
                password="ValidPassw0rd123",
                role=Role.VERIFIER,
            )

    def test_rejects_a_duplicate_email(self, db, admin_user):
        with pytest.raises(ValidationError, match="email address is already registered"):
            UserService.create_user(
                actor=admin_user,
                username="otheruser",
                email=admin_user.email,
                full_name="Other",
                password="ValidPassw0rd123",
                role=Role.VERIFIER,
            )

    def test_rejects_a_weak_password(self, db, admin_user):
        with pytest.raises(ValidationError, match="at least 12 characters"):
            UserService.create_user(
                actor=admin_user,
                username="weakuser",
                email="weak@qvs.example.com",
                full_name="Weak",
                password="short1A",
                role=Role.VERIFIER,
            )

    def test_changes_a_role(self, db, admin_user, verifier_user):
        updated = UserService.set_role(actor=admin_user, user_id=verifier_user.id, role=Role.ISSUER)
        assert updated.role == Role.ISSUER

    def test_admin_cannot_demote_themselves(self, db, admin_user):
        with pytest.raises(ValidationError, match="your own administrator role"):
            UserService.set_role(actor=admin_user, user_id=admin_user.id, role=Role.VERIFIER)

    def test_admin_cannot_deactivate_themselves(self, db, admin_user):
        with pytest.raises(ValidationError, match="your own account"):
            UserService.set_active(actor=admin_user, user_id=admin_user.id, is_active=False)

    def test_deactivates_another_user(self, db, admin_user, verifier_user):
        updated = UserService.set_active(
            actor=admin_user, user_id=verifier_user.id, is_active=False
        )
        assert updated.is_active is False

    def test_unknown_user_raises_not_found(self, db, admin_user):
        with pytest.raises(NotFoundError):
            UserService.set_role(actor=admin_user, user_id=9999, role=Role.ISSUER)


class TestPasswordChange:
    def test_changes_the_password(self, db, verifier_user):
        UserService.change_password(
            user=verifier_user,
            current_password=VERIFIER_PASSWORD,
            new_password="BrandNewPassw0rd",
        )
        assert verifier_user.check_password("BrandNewPassw0rd")

    def test_rejects_a_wrong_current_password(self, db, verifier_user):
        with pytest.raises(ValidationError, match="current password is incorrect"):
            UserService.change_password(
                user=verifier_user, current_password="Wrong", new_password="BrandNewPassw0rd"
            )

    def test_rejects_reusing_the_current_password(self, db, verifier_user):
        with pytest.raises(ValidationError, match="must differ"):
            UserService.change_password(
                user=verifier_user,
                current_password=VERIFIER_PASSWORD,
                new_password=VERIFIER_PASSWORD,
            )

    def test_enforces_the_password_policy(self, db, verifier_user):
        with pytest.raises(ValidationError, match="at least 12 characters"):
            UserService.change_password(
                user=verifier_user, current_password=VERIFIER_PASSWORD, new_password="Short1a"
            )


class TestInstitutionAdministration:
    def test_admin_creates_an_institution(self, db, admin_user):
        created = InstitutionService.create(
            actor=admin_user, name="Chinhoyi University", code="cut", country="Zimbabwe"
        )
        assert created.code == "CUT"

    def test_non_admin_cannot_create_an_institution(self, db, issuer_user):
        with pytest.raises(PermissionDeniedError):
            InstitutionService.create(actor=issuer_user, name="X University", code="XU")

    def test_rejects_a_duplicate_code(self, db, admin_user, institution):
        with pytest.raises(ValidationError, match="code is already in use"):
            InstitutionService.create(actor=admin_user, name="Another", code=institution.code)

    def test_rejects_a_duplicate_name(self, db, admin_user, institution):
        with pytest.raises(ValidationError, match="name already exists"):
            InstitutionService.create(actor=admin_user, name=institution.name, code="ZZZ")

    def test_deactivates_an_institution(self, db, admin_user, institution):
        updated = InstitutionService.set_active(
            actor=admin_user, institution_id=institution.id, is_active=False
        )
        assert updated.is_active is False


class TestAuditImmutability:
    """The audit trail must be append-only, enforced rather than assumed."""

    def test_entries_can_be_appended(self, db, admin_user):
        before = AuditRepository.count_all()
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, detail="test", commit=True)
        assert AuditRepository.count_all() == before + 1

    def test_updating_an_entry_raises(self, db, admin_user):
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, detail="original", commit=True)
        entry = AuditRepository.recent(1)[0]
        entry.detail = "tampered"
        with pytest.raises(ImmutableRecordError):
            db.session.commit()
        db.session.rollback()

    def test_deleting_an_entry_raises(self, db, admin_user):
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, detail="keep me", commit=True)
        entry = AuditRepository.recent(1)[0]
        db.session.delete(entry)
        with pytest.raises(ImmutableRecordError):
            db.session.commit()
        db.session.rollback()

    def test_entry_survives_a_blocked_deletion(self, db, admin_user):
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, detail="keep me", commit=True)
        count = AuditRepository.count_all()
        entry = AuditRepository.recent(1)[0]
        db.session.delete(entry)
        with pytest.raises(ImmutableRecordError):
            db.session.commit()
        db.session.rollback()
        assert AuditRepository.count_all() == count


class TestAuditQueries:
    def test_filters_by_action(self, db, admin_user):
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, commit=True)
        AuditService.record(action=AuditAction.LOGOUT, commit=True)
        page = AuditService.list_logs(action=AuditAction.LOGOUT)
        assert page.total == 1

    def test_filters_by_entity_type(self, db, admin_user):
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, entity_type="user", commit=True)
        AuditService.record(
            action=AuditAction.VERIFICATION_PERFORMED, entity_type="verification", commit=True
        )
        assert AuditService.list_logs(entity_type="verification").total == 1

    def test_detail_is_truncated_to_the_column_width(self, db, admin_user):
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, detail="x" * 2000, commit=True)
        assert len(AuditRepository.recent(1)[0].detail) == 1000

    def test_entry_is_attributed_to_system_outside_a_request(self, db):
        """CLI and seeding events have no request; they are still auditable."""
        AuditService.record(action=AuditAction.LOGIN_FAILURE, commit=True)
        assert AuditRepository.recent(1)[0].actor_label == "system"

    def test_entry_is_attributed_to_anonymous_for_a_signed_out_request(self, app, db):
        with app.test_request_context("/login"):
            AuditService.record(action=AuditAction.LOGIN_FAILURE, commit=True)
        assert AuditRepository.recent(1)[0].actor_label == "anonymous"

    def test_audit_log_model_repr_is_readable(self, db, admin_user):
        AuditService.record(action=AuditAction.LOGIN_SUCCESS, commit=True)
        entry = AuditRepository.recent(1)[0]
        assert isinstance(entry, AuditLog)
        assert "login.success" in repr(entry)
