"""Dashboard, landing page and operational health endpoints."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import text

from app.extensions import db
from app.repositories.user_repository import InstitutionRepository, UserRepository
from app.services.audit_service import AuditService
from app.services.qualification_service import QualificationService
from app.services.verification_service import VerificationService

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@bp.route("/dashboard")
@login_required
def dashboard():
    """Role-aware overview of register size, verification mix and recent activity."""
    qualification_stats = QualificationService.statistics()
    verification_stats = VerificationService.statistics()
    context = {
        "qualification_stats": qualification_stats,
        "verification_stats": verification_stats,
        "recent_verifications": VerificationService.history(page=1, per_page=5).items,
    }
    if current_user.is_issuer:
        from app.repositories.qualification_repository import QualificationRepository

        context["recent_qualifications"] = QualificationRepository.recent(5)
    if current_user.is_admin:
        context["recent_audit"] = AuditService.recent(8)
        context["user_count"] = UserRepository.count_all()
        context["institution_count"] = InstitutionRepository.count_all()
        context["audit_count"] = AuditService.count_all()
    return render_template("dashboard.html", **context)


@bp.route("/healthz")
def healthz():
    """Liveness/readiness probe used by Docker and Fly.io.

    Returns 503 rather than 200 when the database is unreachable, so a broken
    deployment fails its health check instead of taking traffic.
    """
    checks = {"application": "ok"}
    status_code = 200
    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # pragma: no cover - exercised only on real outage
        checks["database"] = "error"
        checks["error"] = type(exc).__name__
        status_code = 503
    payload = {
        "status": "healthy" if status_code == 200 else "unhealthy",
        "checks": checks,
        "version": current_app.config.get("APP_VERSION", "1.0.0"),
    }
    return jsonify(payload), status_code


@bp.route("/metrics")
@login_required
def metrics():
    """Lightweight JSON metrics feeding the monitoring panel on the dashboard."""
    return jsonify(
        {
            "qualifications": QualificationService.statistics(),
            "verifications": VerificationService.statistics(),
            "audit_entries": AuditService.count_all(),
            "users": UserRepository.count_all(),
            "institutions": InstitutionRepository.count_all(),
        }
    )
