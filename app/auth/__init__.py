"""Authentication helpers.

Flask-Login wiring lives in :mod:`app.auth.login`; the authorisation
decorators live in :mod:`app.utils.security`.
"""

from app.auth.login import init_login_manager

__all__ = ["init_login_manager"]
