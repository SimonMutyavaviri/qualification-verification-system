"""End-to-end workflow tests through the HTTP layer.

These exercise the full stack -- routing, forms, services, repositories and
the database -- for the workflow the assignment specifies:

    login -> register -> retrieve -> verify -> verification record -> audit record
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import AuditAction, QualificationStatus, VerificationResult
from app.repositories.audit_repository import AuditRepository
from app.repositories.qualification_repository import QualificationRepository
from app.repositories.verification_repository import VerificationRepository
from tests.conftest import ADMIN_PASSWORD, ISSUER_PASSWORD, VERIFIER_PASSWORD

pytestmark = pytest.mark.integration


def _registration_payload(institution, **overrides):
    payload = {
        "credential_id": "",
        "title": "MSc Information Security",
        "qualification_type": "Degree",
        "holder_name": "Chipo Dube",
        "holder_email": "chipo@example.com",
        "institution_id": str(institution.id),
        "award_date": (date.today() - timedelta(days=200)).isoformat(),
        "expiry_date": "",
    }
    payload.update(overrides)
    return payload


class TestSignInFlow:
    def test_root_redirects_anonymous_users_to_login(self, client):
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Sign in" in response.data

    def test_valid_credentials_reach_the_dashboard(self, client, auth, issuer_user):
        response = auth.login("issuer", ISSUER_PASSWORD)
        assert response.status_code == 200
        assert b"Dashboard" in response.data

    def test_invalid_credentials_are_rejected(self, client, auth, issuer_user):
        response = auth.login("issuer", "WrongPassw0rd!23")
        assert b"Invalid username or password" in response.data

    def test_sign_out_ends_the_session(self, client, auth, issuer_user):
        auth.login("issuer", ISSUER_PASSWORD)
        auth.logout()
        assert client.get("/dashboard").status_code == 302

    def test_protected_page_redirects_when_signed_out(self, client):
        response = client.get("/qualifications/")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


class TestFullQualificationLifecycle:
    def test_register_retrieve_verify_and_audit(self, client, auth, issuer_user, institution, db):
        # 1. Sign in as an issuer.
        auth.login("issuer", ISSUER_PASSWORD)

        # 2. Register a qualification.
        response = client.post(
            "/qualifications/new",
            data=_registration_payload(institution),
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Qualification registered" in response.data

        qualification = QualificationRepository.search(query="Chipo Dube").items[0]
        credential_id = qualification.credential_id

        # 3. Retrieve it through search.
        listing = client.get(f"/qualifications/?q={credential_id}")
        assert credential_id.encode() in listing.data

        # 4. Retrieve the detail page.
        detail = client.get(f"/qualifications/{qualification.id}")
        assert b"Chipo Dube" in detail.data

        # 5. Verify it.
        verify = client.post(
            "/verify/", data={"credential_id": credential_id}, follow_redirects=True
        )
        assert b"VALID" in verify.data

        # 6. A verification record exists.
        record = VerificationRepository.history(credential_id=credential_id).items[0]
        assert record.result == VerificationResult.VALID
        assert record.performed_by_id == issuer_user.id

        # 7. Audit entries exist for both the registration and the verification.
        actions = [entry.action for entry in AuditRepository.recent(20)]
        assert AuditAction.QUALIFICATION_CREATED in actions
        assert AuditAction.VERIFICATION_PERFORMED in actions
        assert AuditAction.LOGIN_SUCCESS in actions

    def test_revocation_changes_the_verification_result(
        self, client, auth, issuer_user, qualification
    ):
        auth.login("issuer", ISSUER_PASSWORD)

        before = client.post(
            "/verify/", data={"credential_id": qualification.credential_id}, follow_redirects=True
        )
        assert b"VALID" in before.data

        client.post(
            f"/qualifications/{qualification.id}/revoke",
            data={"reason": "Awarded in error following a records audit."},
            follow_redirects=True,
        )

        after = client.post(
            "/verify/", data={"credential_id": qualification.credential_id}, follow_redirects=True
        )
        assert b"REVOKED" in after.data

    def test_expired_credential_verifies_as_expired(
        self, client, auth, verifier_user, expired_qualification
    ):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.post(
            "/verify/",
            data={"credential_id": expired_qualification.credential_id},
            follow_redirects=True,
        )
        assert b"EXPIRED" in response.data

    def test_unknown_credential_verifies_as_invalid(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.post(
            "/verify/", data={"credential_id": "QVS-2024-NOTREG"}, follow_redirects=True
        )
        assert b"INVALID" in response.data
        assert b"No credential matching" in response.data

    def test_duplicate_registration_is_rejected(
        self, client, auth, issuer_user, institution, qualification
    ):
        auth.login("issuer", ISSUER_PASSWORD)
        response = client.post(
            "/qualifications/new",
            data=_registration_payload(institution, credential_id=qualification.credential_id),
            follow_redirects=True,
        )
        assert b"already registered" in response.data
        assert QualificationRepository.count_all() == 1

    def test_invalid_registration_data_is_rejected(self, client, auth, issuer_user, institution):
        auth.login("issuer", ISSUER_PASSWORD)
        response = client.post(
            "/qualifications/new",
            data=_registration_payload(
                institution, award_date=(date.today() + timedelta(days=5)).isoformat()
            ),
            follow_redirects=True,
        )
        assert QualificationRepository.count_all() == 0
        assert b"future" in response.data

    def test_editing_updates_the_record(self, client, auth, issuer_user, qualification):
        auth.login("issuer", ISSUER_PASSWORD)
        response = client.post(
            f"/qualifications/{qualification.id}/edit",
            data={
                "title": "BSc Honours in Software Engineering",
                "qualification_type": "Degree",
                "holder_name": qualification.holder_name,
                "holder_email": qualification.holder_email or "",
                "expiry_date": "",
            },
            follow_redirects=True,
        )
        assert b"Qualification updated" in response.data
        assert qualification.title == "BSc Honours in Software Engineering"

    def test_revocation_requires_a_reason(self, client, auth, issuer_user, qualification):
        auth.login("issuer", ISSUER_PASSWORD)
        response = client.post(
            f"/qualifications/{qualification.id}/revoke",
            data={"reason": ""},
            follow_redirects=True,
        )
        assert b"reason is required" in response.data
        assert qualification.status == QualificationStatus.ACTIVE

    def test_unknown_qualification_returns_404(self, client, auth, issuer_user):
        auth.login("issuer", ISSUER_PASSWORD)
        assert client.get("/qualifications/9999").status_code == 404


class TestSearchAndFiltering:
    def test_filters_by_status(
        self, client, auth, verifier_user, qualification, revoked_qualification
    ):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.get("/qualifications/?status=revoked")
        assert revoked_qualification.credential_id.encode() in response.data
        assert qualification.credential_id.encode() not in response.data

    def test_search_by_holder_name(self, client, auth, verifier_user, qualification):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.get("/qualifications/?q=Tinashe")
        assert qualification.credential_id.encode() in response.data

    def test_empty_result_set_shows_an_empty_state(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.get("/qualifications/?q=nobody")
        assert b"No qualifications match" in response.data


class TestVerificationHistory:
    def test_verifier_sees_only_their_own_attempts(
        self, client, auth, verifier_user, issuer_user, qualification
    ):
        auth.login("issuer", ISSUER_PASSWORD)
        client.post("/verify/", data={"credential_id": qualification.credential_id})
        auth.logout()

        auth.login("verifier", VERIFIER_PASSWORD)
        client.post("/verify/", data={"credential_id": "QVS-2024-NOTREG"})
        response = client.get("/verify/history")
        assert b"QVS-2024-NOTREG" in response.data
        assert qualification.credential_id.encode() not in response.data

    def test_issuer_sees_all_attempts(
        self, client, auth, verifier_user, issuer_user, qualification
    ):
        auth.login("verifier", VERIFIER_PASSWORD)
        client.post("/verify/", data={"credential_id": qualification.credential_id})
        auth.logout()

        auth.login("issuer", ISSUER_PASSWORD)
        response = client.get("/verify/history")
        assert qualification.credential_id.encode() in response.data

    def test_receipt_page_is_reachable(self, client, auth, verifier_user, qualification):
        auth.login("verifier", VERIFIER_PASSWORD)
        client.post("/verify/", data={"credential_id": qualification.credential_id})
        reference = VerificationRepository.recent(1)[0].reference
        response = client.get(f"/verify/result/{reference}")
        assert response.status_code == 200
        assert reference.encode() in response.data

    def test_unknown_receipt_returns_404(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        assert client.get("/verify/result/does-not-exist").status_code == 404


class TestAdministrationWorkflows:
    def test_admin_creates_a_user(self, client, auth, admin_user, institution):
        auth.login("admin", ADMIN_PASSWORD)
        response = client.post(
            "/admin/users",
            data={
                "username": "newverifier",
                "full_name": "New Verifier",
                "email": "newverifier@qvs.example.com",
                "password": "ValidPassw0rd123",
                "role": "verifier",
                "institution_id": str(institution.id),
            },
            follow_redirects=True,
        )
        assert b"created" in response.data

    def test_admin_creates_an_institution(self, client, auth, admin_user):
        auth.login("admin", ADMIN_PASSWORD)
        response = client.post(
            "/admin/institutions",
            data={
                "name": "Chinhoyi University",
                "code": "CUT",
                "country": "Zimbabwe",
                "contact_email": "",
            },
            follow_redirects=True,
        )
        assert b"Institution created" in response.data

    def test_admin_views_the_audit_trail(self, client, auth, admin_user, qualification):
        auth.login("admin", ADMIN_PASSWORD)
        client.post("/verify/", data={"credential_id": qualification.credential_id})
        response = client.get("/admin/audit")
        assert b"verification.performed" in response.data

    def test_audit_trail_can_be_filtered(self, client, auth, admin_user):
        auth.login("admin", ADMIN_PASSWORD)
        response = client.get("/admin/audit?action=login.success")
        assert response.status_code == 200
        assert b"login.success" in response.data

    def test_admin_changes_a_user_role(self, client, auth, admin_user, verifier_user):
        auth.login("admin", ADMIN_PASSWORD)
        client.post(
            f"/admin/users/{verifier_user.id}/role",
            data={"role": "issuer"},
            follow_redirects=True,
        )
        assert verifier_user.role.value == "issuer"

    def test_admin_deactivates_a_user_who_then_cannot_sign_in(
        self, client, auth, admin_user, verifier_user
    ):
        auth.login("admin", ADMIN_PASSWORD)
        client.post(
            f"/admin/users/{verifier_user.id}/status",
            data={"action": "deactivate"},
            follow_redirects=True,
        )
        auth.logout()
        response = auth.login("verifier", VERIFIER_PASSWORD)
        assert b"deactivated" in response.data


class TestProfile:
    def test_user_changes_their_own_password(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.post(
            "/profile",
            data={"current_password": VERIFIER_PASSWORD, "new_password": "BrandNewPassw0rd"},
            follow_redirects=True,
        )
        assert b"password has been changed" in response.data
        auth.logout()
        assert b"Dashboard" in auth.login("verifier", "BrandNewPassw0rd").data


class TestOperationalEndpoints:
    def test_health_endpoint_reports_healthy(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "healthy"
        assert payload["checks"]["database"] == "ok"

    def test_health_endpoint_needs_no_authentication(self, client):
        assert client.get("/healthz").status_code == 200

    def test_metrics_endpoint_requires_authentication(self, client):
        assert client.get("/metrics").status_code == 302

    def test_metrics_endpoint_returns_counters(self, client, auth, admin_user, qualification):
        auth.login("admin", ADMIN_PASSWORD)
        payload = client.get("/metrics").get_json()
        assert payload["qualifications"]["total"] == 1
        assert "verifications" in payload


class TestErrorHandling:
    """The assignment asks for handling of specific HTTP statuses."""

    def test_404_renders_the_html_page_for_a_browser(self, client):
        response = client.get("/nosuchpage", headers={"Accept": "text/html"})
        assert response.status_code == 404
        assert b"Page not found" in response.data
        assert b"404" in response.data

    def test_wildcard_accept_still_gets_html(self, client):
        """curl and similar clients send */* and should get the readable page."""
        response = client.get("/nosuchpage", headers={"Accept": "*/*"})
        assert response.status_code == 404
        assert b"<!doctype html>" in response.data.lower()

    def test_404_returns_json_when_json_is_requested(self, client):
        response = client.get("/nosuchpage", headers={"Accept": "application/json"})
        assert response.status_code == 404
        assert response.get_json()["status"] == 404

    def test_405_is_handled(self, client, auth, admin_user):
        auth.login("admin", ADMIN_PASSWORD)
        response = client.get("/logout", headers={"Accept": "text/html"})
        assert response.status_code == 405
        assert b"Method not allowed" in response.data

    def test_403_renders_the_access_denied_page(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.get("/admin/users", headers={"Accept": "text/html"})
        assert response.status_code == 403
        assert b"Access denied" in response.data

    def test_error_pages_never_expose_the_secret_key(self, client, app):
        response = client.get("/nosuchpage", headers={"Accept": "text/html"})
        assert app.config["SECRET_KEY"].encode() not in response.data
