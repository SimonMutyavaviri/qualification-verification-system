"""Verification routes: run a check, show the result, browse the history."""

from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    request,
)
from flask_login import current_user, login_required

from app.extensions import limiter
from app.forms import VerificationForm, VerificationHistoryForm
from app.models.enums import Role, VerificationResult
from app.services.verification_service import VerificationService
from app.utils.security import roles_required

bp = Blueprint("verification", __name__, url_prefix="/verify")


@bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required(Role.VERIFIER, Role.ISSUER)
@limiter.limit(
    lambda: current_app.config.get("RATELIMIT_VERIFY", "30 per minute"),
    methods=["POST"],
)
def verify():
    """Verify a credential reference and display the outcome."""
    form = VerificationForm()
    outcome = None
    if form.validate_on_submit():
        outcome = VerificationService.verify(
            credential_id=form.credential_id.data, actor=current_user
        )
    return render_template("verification/verify.html", form=form, outcome=outcome)


@bp.route("/result/<reference>")
@login_required
@roles_required(Role.VERIFIER, Role.ISSUER)
def result(reference: str):
    """Permalink to a previously issued verification receipt."""
    record = VerificationService.get_by_reference(reference)
    if record is None:
        abort(404)
    return render_template("verification/result.html", record=record)


@bp.route("/history")
@login_required
@roles_required(Role.VERIFIER, Role.ISSUER)
def history():
    """Verification history.

    Verifiers see only their own attempts; issuers and administrators see the
    whole trail, which is what makes the history useful for oversight.
    """
    form = VerificationHistoryForm(request.args, meta={"csrf": False})
    result_filter = None
    if form.result.data:
        try:
            result_filter = VerificationResult(form.result.data)
        except ValueError:
            result_filter = None

    page = request.args.get("page", 1, type=int)
    records = VerificationService.history(
        credential_id=form.credential_id.data or None,
        result=result_filter,
        performed_by_id=None if current_user.is_issuer else current_user.id,
        page=max(page, 1),
        per_page=current_app.config["ITEMS_PER_PAGE"],
    )
    return render_template("verification/history.html", form=form, records=records)
