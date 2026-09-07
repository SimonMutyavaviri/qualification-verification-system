"""Authentication routes: sign in, sign out, profile."""

from __future__ import annotations

from urllib.parse import urlparse

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import limiter
from app.forms import ChangePasswordForm, LoginForm
from app.services.user_service import AuthService, UserService
from app.utils.errors import DomainError

bp = Blueprint("auth", __name__)


def _safe_next(target: str | None) -> str:
    """Only follow a ``next`` parameter that stays on this host.

    Without this check the login redirect is an open redirect that can be used
    to make a phishing link look like it came from the application.
    """
    if not target:
        return url_for("main.dashboard")
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return url_for("main.dashboard")
    if not target.startswith("/"):
        return url_for("main.dashboard")
    return target


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit(
    lambda: current_app.config.get("RATELIMIT_LOGIN", "10 per minute"),
    methods=["POST"],
)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = AuthService.authenticate(form.identifier.data, form.password.data)
        except DomainError as exc:
            flash(exc.message, "error")
        else:
            login_user(user, remember=bool(form.remember_me.data))
            flash(f"Welcome back, {user.full_name}.", "success")
            return redirect(_safe_next(request.args.get("next")))
    return render_template("login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    AuthService.record_logout(current_user)
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            UserService.change_password(
                user=current_user,
                current_password=form.current_password.data,
                new_password=form.new_password.data,
            )
        except DomainError as exc:
            flash(exc.message, "error")
        else:
            flash("Your password has been changed.", "success")
            return redirect(url_for("auth.profile"))
    return render_template("profile.html", form=form)
