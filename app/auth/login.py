"""Flask-Login integration."""

from __future__ import annotations

from flask import Flask, flash, redirect, request, url_for

from app.extensions import login_manager
from app.repositories.user_repository import UserRepository


def init_login_manager(app: Flask) -> None:
    """Register the user loader and the unauthenticated handler."""

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return UserRepository.get(int(user_id))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        flash("Please sign in to access that page.", "warning")
        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))

    app.logger.debug("Login manager initialised")
