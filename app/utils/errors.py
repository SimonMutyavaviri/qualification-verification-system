"""Domain-level exceptions.

Routes translate these into HTTP responses; services raise them so the
business rules stay independent of Flask.
"""


class DomainError(Exception):
    """Base class for all expected business-rule failures."""

    status_code = 400

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class ValidationError(DomainError):
    """Input failed a validation rule."""

    status_code = 400


class DuplicateCredentialError(DomainError):
    """A qualification with this credential ID already exists."""

    status_code = 409


class NotFoundError(DomainError):
    """The requested entity does not exist."""

    status_code = 404


class PermissionDeniedError(DomainError):
    """The current user may not perform this action."""

    status_code = 403


class ImmutableRecordError(DomainError):
    """An attempt was made to alter an append-only record."""

    status_code = 403
