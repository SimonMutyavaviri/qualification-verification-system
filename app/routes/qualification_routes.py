"""Qualification registration, search, detail, edit and revocation routes."""

from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.forms import (
    QualificationEditForm,
    QualificationForm,
    ReinstateForm,
    RevokeForm,
    SearchForm,
)
from app.models.enums import QualificationStatus, Role
from app.repositories.user_repository import InstitutionRepository
from app.services.qualification_service import QualificationService
from app.services.risk_service import RiskService
from app.utils.errors import DomainError, NotFoundError
from app.utils.security import issuer_required, roles_required

bp = Blueprint("qualifications", __name__, url_prefix="/qualifications")


def _parse_status(raw: str | None) -> QualificationStatus | None:
    if not raw:
        return None
    try:
        return QualificationStatus(raw)
    except ValueError:
        return None


@bp.route("/")
@login_required
@roles_required(Role.VERIFIER, Role.ISSUER)
def list_qualifications():
    """Paginated, filterable register of qualifications."""
    form = SearchForm(request.args, meta={"csrf": False})
    form.populate_institutions(InstitutionRepository.list_active())

    institution_id = form.institution_id.data or None
    page = request.args.get("page", 1, type=int)
    results = QualificationService.search(
        query=form.q.data or None,
        status=_parse_status(form.status.data),
        institution_id=int(institution_id) if institution_id else None,
        qualification_type=form.qualification_type.data or None,
        page=max(page, 1),
        per_page=current_app.config["ITEMS_PER_PAGE"],
    )
    return render_template("qualifications/list.html", form=form, results=results, page=page)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@issuer_required
def register():
    """Register a new qualification."""
    institutions = InstitutionRepository.list_active()
    form = QualificationForm()
    form.populate_institutions(institutions)

    if not institutions:
        flash(
            "No active institutions exist yet. An administrator must create one first.",
            "warning",
        )

    if form.validate_on_submit():
        try:
            qualification = QualificationService.register(
                actor=current_user,
                credential_id=form.credential_id.data or None,
                title=form.title.data,
                qualification_type=form.qualification_type.data,
                holder_name=form.holder_name.data,
                holder_email=form.holder_email.data,
                institution_id=form.institution_id.data,
                award_date=form.award_date.data,
                expiry_date=form.expiry_date.data,
            )
        except DomainError as exc:
            if exc.field and hasattr(form, exc.field):
                getattr(form, exc.field).errors.append(exc.message)
            else:
                flash(exc.message, "error")
        else:
            flash(
                f"Qualification registered with credential ID " f"{qualification.credential_id}.",
                "success",
            )
            return redirect(url_for("qualifications.detail", qualification_id=qualification.id))
    return render_template("qualifications/register.html", form=form)


@bp.route("/<int:qualification_id>")
@login_required
@roles_required(Role.VERIFIER, Role.ISSUER)
def detail(qualification_id: int):
    """Full record for one qualification, plus its review assessment."""
    try:
        qualification = QualificationService.get_or_404(qualification_id)
    except NotFoundError:
        abort(404)
    assessment = RiskService.assess(qualification) if current_user.is_issuer else None
    return render_template(
        "qualifications/detail.html",
        qualification=qualification,
        assessment=assessment,
        revoke_form=RevokeForm(),
        reinstate_form=ReinstateForm(),
    )


@bp.route("/<int:qualification_id>/edit", methods=["GET", "POST"])
@login_required
@issuer_required
def edit(qualification_id: int):
    """Edit the mutable fields of a qualification."""
    try:
        qualification = QualificationService.get_or_404(qualification_id)
    except NotFoundError:
        abort(404)

    form = QualificationEditForm(obj=qualification)
    if form.validate_on_submit():
        try:
            QualificationService.update(
                actor=current_user,
                qualification_id=qualification.id,
                title=form.title.data,
                qualification_type=form.qualification_type.data,
                holder_name=form.holder_name.data,
                holder_email=form.holder_email.data,
                expiry_date=form.expiry_date.data,
                clear_expiry=bool(form.clear_expiry.data),
            )
        except DomainError as exc:
            if exc.field and hasattr(form, exc.field):
                getattr(form, exc.field).errors.append(exc.message)
            else:
                flash(exc.message, "error")
        else:
            flash("Qualification updated.", "success")
            return redirect(url_for("qualifications.detail", qualification_id=qualification.id))
    return render_template("qualifications/edit.html", form=form, qualification=qualification)


@bp.route("/<int:qualification_id>/revoke", methods=["POST"])
@login_required
@issuer_required
def revoke(qualification_id: int):
    """Revoke a qualification with a recorded reason."""
    form = RevokeForm()
    if not form.validate_on_submit():
        flash("A revocation reason is required.", "error")
        return redirect(url_for("qualifications.detail", qualification_id=qualification_id))
    try:
        QualificationService.revoke(
            actor=current_user, qualification_id=qualification_id, reason=form.reason.data
        )
    except NotFoundError:
        abort(404)
    except DomainError as exc:
        flash(exc.message, "error")
    else:
        flash("Qualification revoked.", "success")
    return redirect(url_for("qualifications.detail", qualification_id=qualification_id))


@bp.route("/<int:qualification_id>/reinstate", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def reinstate(qualification_id: int):
    """Reverse a revocation (administrators only)."""
    form = ReinstateForm()
    if not form.validate_on_submit():
        flash("A reinstatement reason is required.", "error")
        return redirect(url_for("qualifications.detail", qualification_id=qualification_id))
    try:
        QualificationService.reinstate(
            actor=current_user, qualification_id=qualification_id, reason=form.reason.data
        )
    except NotFoundError:
        abort(404)
    except DomainError as exc:
        flash(exc.message, "error")
    else:
        flash("Qualification reinstated.", "success")
    return redirect(url_for("qualifications.detail", qualification_id=qualification_id))
