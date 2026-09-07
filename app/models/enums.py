"""Domain enumerations shared across models, services and templates."""

from enum import Enum


class Role(str, Enum):
    """Application roles, ordered from least to most privileged."""

    VERIFIER = "verifier"
    ISSUER = "issuer"
    ADMIN = "admin"

    @property
    def label(self) -> str:
        return {
            Role.VERIFIER: "Verifier",
            Role.ISSUER: "Qualification Issuer",
            Role.ADMIN: "Administrator",
        }[self]


class QualificationStatus(str, Enum):
    """Lifecycle state of a registered qualification."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"

    @property
    def label(self) -> str:
        return self.value.capitalize()


class VerificationResult(str, Enum):
    """Outcome of a verification attempt."""

    VALID = "VALID"
    INVALID = "INVALID"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class AuditAction(str, Enum):
    """Auditable actions recorded in the immutable audit trail."""

    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILURE = "login.failure"
    LOGOUT = "logout"
    QUALIFICATION_CREATED = "qualification.created"
    QUALIFICATION_UPDATED = "qualification.updated"
    QUALIFICATION_REVOKED = "qualification.revoked"
    QUALIFICATION_REINSTATED = "qualification.reinstated"
    VERIFICATION_PERFORMED = "verification.performed"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DEACTIVATED = "user.deactivated"
    INSTITUTION_CREATED = "institution.created"
    INSTITUTION_UPDATED = "institution.updated"
    ACCESS_DENIED = "access.denied"
