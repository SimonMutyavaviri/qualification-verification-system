"""Authorisation decorators and HTTP security headers."""

from __future__ import annotations

import contextlib
from functools import wraps

from flask import Response, abort, request
from flask_login import current_user

from app.models.enums import AuditAction, Role


def _record_denial(reason: str) -> None:
    """Write an ACCESS_DENIED audit entry, never blocking the 403 itself.

    Committed immediately: the request is about to abort with a 403, so there
    is no later commit to ride along with and the entry would otherwise be
    discarded when the session is torn down.
    """
    from app.services.audit_service import AuditService

    # Auditing must never turn a clean 403 into a 500.
    with contextlib.suppress(Exception):  # pragma: no cover - defensive
        AuditService.record(
            action=AuditAction.ACCESS_DENIED,
            entity_type="route",
            entity_id=request.endpoint,
            detail=reason,
            commit=True,
        )


def roles_required(*roles: Role):
    """Restrict a view to the given roles (administrators always pass)."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role(*roles):
                _record_denial(
                    f"{current_user.username} lacks role(s) " f"{', '.join(r.value for r in roles)}"
                )
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


admin_required = roles_required(Role.ADMIN)
issuer_required = roles_required(Role.ISSUER)


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    # Tailwind is loaded from the CDN in development; 'unsafe-inline' is needed
    # for its runtime-generated styles. Documented in docs/security.md.
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
}


def apply_security_headers(response: Response) -> Response:
    """Attach hardening headers to every response."""
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    if request.is_secure:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response
