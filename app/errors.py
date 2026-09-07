"""Centralised HTTP and domain error handling.

Handlers content-negotiate: API-style clients get JSON, browsers get a styled
page. Stack traces never reach the client -- they go to the application log.
"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from app.extensions import db
from app.utils.errors import DomainError

# Titles and copy for the pages the assignment asks for by number.
ERROR_COPY = {
    400: ("Bad request", "The request could not be understood. Please check and try again."),
    401: ("Sign-in required", "You need to sign in before viewing that page."),
    403: ("Access denied", "Your role does not permit access to that page."),
    404: ("Page not found", "The page or record you asked for does not exist."),
    405: ("Method not allowed", "That action is not supported on this address."),
    429: ("Too many requests", "You have made too many requests. Please wait and try again."),
    500: ("Something went wrong", "An unexpected error occurred and has been logged."),
}


def _wants_json() -> bool:
    """True when the client explicitly prefers JSON over HTML.

    A strict preference is required so that a wildcard ``Accept: */*`` -- sent
    by curl and by many HTTP clients -- still gets the readable HTML page.
    Only a client that actually asks for JSON receives JSON.
    """
    if request.path.startswith(("/healthz", "/metrics")):
        return True
    accept = request.accept_mimetypes
    return accept["application/json"] > accept["text/html"]


def _render(code: int, message: str | None = None):
    title, description = ERROR_COPY.get(code, ERROR_COPY[500])
    description = message or description
    if _wants_json():
        return jsonify({"error": title, "message": description, "status": code}), code
    template = f"errors/{code}.html"
    try:
        return render_template(template, title=title, description=description), code
    except Exception:
        # Not every status has a bespoke template; fall back to the generic one.
        return (
            render_template("errors/generic.html", code=code, title=title, description=description),
            code,
        )


def register_error_handlers(app: Flask) -> None:
    """Attach handlers for domain errors and the standard HTTP statuses."""

    @app.errorhandler(DomainError)
    def handle_domain_error(exc: DomainError):
        return _render(exc.status_code, exc.message)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        code = exc.code or 500
        # exc.description is Werkzeug's own copy; ours is friendlier for the
        # statuses we have written copy for.
        message = None if code in ERROR_COPY else exc.description
        return _render(code, message)

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        # Roll back so a half-applied transaction cannot leak into the next
        # request on this connection.
        db.session.rollback()
        app.logger.exception("Unhandled exception on %s: %s", request.path, exc)
        return _render(500)
