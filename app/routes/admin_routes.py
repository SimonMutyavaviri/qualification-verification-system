"""Administrator routes: user management, institutions and the audit trail."""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.forms import InstitutionForm, UserForm
from app.models.enums import AuditAction, Role
from app.repositories.user_repository import InstitutionRepository, UserRepository
from app.services.audit_service import AuditService
from app.services.user_service import InstitutionService, UserService
from app.utils.errors import DomainError
from app.utils.security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/users", methods=["GET", "POST"])
@login_required
@admin_required
def users():
    """List users and create new accounts."""
    institutions = InstitutionRepository.list_active()
    form = UserForm()
    form.populate_institutions(institutions)

    if form.validate_on_submit():
        try:
            UserService.create_user(
                actor=current_user,
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                password=form.password.data,
                role=Role(form.role.data),
                institution_id=int(form.institution_id.data) if form.institution_id.data else None,
            )
        except DomainError as exc:
            if exc.field and hasattr(form, exc.field):
                getattr(form, exc.field).errors.append(exc.message)
            else:
                flash(exc.message, "error")
        else:
            flash(f"User {form.username.data} created.", "success")
            return redirect(url_for("admin.users"))

    page = request.args.get("page", 1, type=int)
    listing = UserRepository.list_all(
        page=max(page, 1), per_page=current_app.config["ITEMS_PER_PAGE"]
    )
    return render_template("admin/users.html", form=form, listing=listing, roles=list(Role))


@bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_role(user_id: int):
    """Change a user's role."""
    try:
        role = Role(request.form.get("role", ""))
    except ValueError:
        flash("Unknown role.", "error")
        return redirect(url_for("admin.users"))
    try:
        UserService.set_role(actor=current_user, user_id=user_id, role=role)
    except DomainError as exc:
        flash(exc.message, "error")
    else:
        flash("Role updated.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:user_id>/status", methods=["POST"])
@login_required
@admin_required
def change_status(user_id: int):
    """Activate or deactivate a user account."""
    activate = request.form.get("action") == "activate"
    try:
        UserService.set_active(actor=current_user, user_id=user_id, is_active=activate)
    except DomainError as exc:
        flash(exc.message, "error")
    else:
        flash("Account activated." if activate else "Account deactivated.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/institutions", methods=["GET", "POST"])
@login_required
@admin_required
def institutions():
    """List institutions and create new ones."""
    form = InstitutionForm()
    if form.validate_on_submit():
        try:
            InstitutionService.create(
                actor=current_user,
                name=form.name.data,
                code=form.code.data,
                country=form.country.data,
                contact_email=form.contact_email.data,
            )
        except DomainError as exc:
            if exc.field and hasattr(form, exc.field):
                getattr(form, exc.field).errors.append(exc.message)
            else:
                flash(exc.message, "error")
        else:
            flash("Institution created.", "success")
            return redirect(url_for("admin.institutions"))

    page = request.args.get("page", 1, type=int)
    listing = InstitutionRepository.list_all(
        page=max(page, 1), per_page=current_app.config["ITEMS_PER_PAGE"]
    )
    return render_template("admin/institutions.html", form=form, listing=listing)


@bp.route("/institutions/<int:institution_id>/status", methods=["POST"])
@login_required
@admin_required
def institution_status(institution_id: int):
    activate = request.form.get("action") == "activate"
    try:
        InstitutionService.set_active(
            actor=current_user, institution_id=institution_id, is_active=activate
        )
    except DomainError as exc:
        flash(exc.message, "error")
    else:
        flash("Institution updated.", "success")
    return redirect(url_for("admin.institutions"))


@bp.route("/audit")
@login_required
@admin_required
def audit():
    """Browse the append-only audit trail."""
    action_filter = request.args.get("action") or None
    parsed_action = None
    if action_filter:
        try:
            parsed_action = AuditAction(action_filter)
        except ValueError:
            parsed_action = None

    page = request.args.get("page", 1, type=int)
    listing = AuditService.list_logs(
        action=parsed_action,
        page=max(page, 1),
        per_page=current_app.config["ITEMS_PER_PAGE"] * 2,
    )
    return render_template(
        "admin/audit.html",
        listing=listing,
        actions=list(AuditAction),
        selected_action=action_filter or "",
    )
