"""Application factory for the Qualification Verification System."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import get_config
from app.extensions import csrf, db, limiter, login_manager, migrate

__version__ = "1.0.0"


def _configure_logging(app: Flask) -> None:
    """Log to stdout (captured by Docker/Fly) and, locally, to a rotating file."""
    level = logging.DEBUG if app.debug else logging.INFO
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    stream.setLevel(level)

    app.logger.handlers.clear()
    app.logger.addHandler(stream)
    app.logger.setLevel(level)

    if not app.testing and os.environ.get("LOG_TO_FILE", "").lower() in {"1", "true"}:
        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler("logs/qvs.log", maxBytes=1_048_576, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        app.logger.addHandler(file_handler)


def create_app(config_name: str | None = None) -> Flask:
    """Build and configure a Flask application instance.

    The factory pattern keeps global state out of the module import path, which
    is what lets the test suite build a fresh app and database per test.
    """
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    app.config["APP_VERSION"] = __version__

    # Behind a trusted reverse proxy (Fly.io), the real scheme and client
    # address arrive in X-Forwarded-*. Without this the app treats every
    # request as plain HTTP: HSTS would never be sent and audit entries would
    # record the proxy's address rather than the caller's.
    if app.config.get("TRUST_PROXY_HEADERS"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # -- extensions --------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.enabled = app.config.get("RATELIMIT_ENABLED", True)
    limiter.init_app(app)

    # Importing the models registers them with SQLAlchemy's metadata before
    # create_all/migrations run.
    from app import models  # noqa: F401
    from app.auth import init_login_manager
    from app.cli import register_cli
    from app.errors import register_error_handlers
    from app.routes import ALL_BLUEPRINTS
    from app.utils.audit_guard import register_audit_guards
    from app.utils.security import apply_security_headers

    init_login_manager(app)
    register_audit_guards()
    register_error_handlers(app)
    register_cli(app)

    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)

    app.after_request(apply_security_headers)
    _configure_logging(app)

    # -- template helpers --------------------------------------------------
    from app.models.enums import QualificationStatus, Role, VerificationResult

    @app.context_processor
    def inject_globals():
        return {
            "app_version": __version__,
            "Role": Role,
            "QualificationStatus": QualificationStatus,
            "VerificationResult": VerificationResult,
        }

    @app.template_filter("datetime")
    def format_datetime(value, fmt: str = "%d %b %Y %H:%M") -> str:
        return value.strftime(fmt) if value else "-"

    @app.template_filter("date")
    def format_date(value, fmt: str = "%d %b %Y") -> str:
        return value.strftime(fmt) if value else "-"

    app.logger.info("Qualification Verification System %s initialised", __version__)
    return app
