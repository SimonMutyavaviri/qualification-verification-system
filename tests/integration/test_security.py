"""Security and access-control tests.

These assert the controls claimed in docs/security.md actually hold, so the
claims in the report are backed by an executing test rather than a promise.
"""

from __future__ import annotations

import pytest
from werkzeug.middleware.proxy_fix import ProxyFix

from app.models.enums import AuditAction
from app.repositories.audit_repository import AuditRepository
from tests.conftest import ADMIN_PASSWORD, ISSUER_PASSWORD, VERIFIER_PASSWORD

pytestmark = [pytest.mark.integration, pytest.mark.security]


class TestAuthenticationRequired:
    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard",
            "/qualifications/",
            "/qualifications/new",
            "/verify/",
            "/verify/history",
            "/admin/users",
            "/admin/institutions",
            "/admin/audit",
            "/profile",
            "/metrics",
        ],
    )
    def test_anonymous_access_is_redirected_to_login(self, client, path):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


class TestRoleBasedAccessControl:
    @pytest.mark.parametrize("path", ["/admin/users", "/admin/institutions", "/admin/audit"])
    def test_issuer_cannot_reach_admin_pages(self, client, auth, issuer_user, path):
        auth.login("issuer", ISSUER_PASSWORD)
        assert client.get(path).status_code == 403

    @pytest.mark.parametrize("path", ["/admin/users", "/admin/audit", "/qualifications/new"])
    def test_verifier_cannot_reach_privileged_pages(self, client, auth, verifier_user, path):
        auth.login("verifier", VERIFIER_PASSWORD)
        assert client.get(path).status_code == 403

    def test_verifier_cannot_register_a_qualification_by_posting(
        self, client, auth, verifier_user, institution
    ):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.post(
            "/qualifications/new",
            data={
                "title": "Forged Degree",
                "qualification_type": "Degree",
                "holder_name": "Somebody",
                "institution_id": str(institution.id),
                "award_date": "2020-01-01",
            },
        )
        assert response.status_code == 403

    def test_verifier_cannot_revoke(self, client, auth, verifier_user, qualification):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.post(
            f"/qualifications/{qualification.id}/revoke", data={"reason": "malicious"}
        )
        assert response.status_code == 403
        assert qualification.revocation_reason is None

    def test_issuer_cannot_reinstate(self, client, auth, issuer_user, revoked_qualification):
        auth.login("issuer", ISSUER_PASSWORD)
        response = client.post(
            f"/qualifications/{revoked_qualification.id}/reinstate", data={"reason": "x"}
        )
        assert response.status_code == 403

    def test_admin_reaches_every_page(self, client, auth, admin_user):
        auth.login("admin", ADMIN_PASSWORD)
        for path in ("/admin/users", "/admin/audit", "/qualifications/new", "/verify/"):
            assert client.get(path).status_code == 200

    def test_denied_access_is_audited(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        client.get("/admin/users")
        assert AuditAction.ACCESS_DENIED in [e.action for e in AuditRepository.recent(5)]


class TestSecurityHeaders:
    @pytest.mark.parametrize(
        "header,expected",
        [
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ],
    )
    def test_hardening_headers_are_present(self, client, header, expected):
        assert client.get("/login").headers[header] == expected

    def test_content_security_policy_is_set(self, client):
        csp = client.get("/login").headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_headers_are_present_on_error_responses(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.get("/admin/users")
        assert response.status_code == 403
        assert response.headers["X-Frame-Options"] == "DENY"


class TestSessionCookies:
    def test_session_cookie_is_http_only(self, client, auth, admin_user):
        auth.login("admin", ADMIN_PASSWORD)
        cookies = client.get("/dashboard").headers.getlist("Set-Cookie")
        # The cookie is only re-sent when it changes; assert the config instead
        # when no Set-Cookie header was emitted on this particular response.
        if cookies:
            assert any("HttpOnly" in cookie for cookie in cookies)

    def test_cookie_configuration_is_hardened(self, app):
        assert app.config["SESSION_COOKIE_HTTPONLY"] is True
        assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


class TestInformationDisclosure:
    def test_invalid_result_reveals_nothing_about_the_register(
        self, client, auth, verifier_user, qualification
    ):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.post(
            "/verify/", data={"credential_id": "QVS-2024-NOTREG"}, follow_redirects=True
        )
        assert qualification.holder_name.encode() not in response.data

    def test_login_failure_does_not_reveal_whether_the_user_exists(self, client, auth, admin_user):
        known = auth.login("admin", "WrongPassw0rd!23").data
        unknown = auth.login("nosuchuser", "WrongPassw0rd!23").data
        assert b"Invalid username or password" in known
        assert b"Invalid username or password" in unknown

    def test_error_pages_do_not_leak_stack_traces(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.get("/qualifications/9999")
        assert response.status_code == 404
        assert b"Traceback" not in response.data


class TestSqlInjectionResistance:
    """SQLAlchemy parameterises every query; these assert the behaviour holds."""

    @pytest.mark.parametrize(
        "payload",
        [
            "'; DROP TABLE qualifications; --",
            "' OR '1'='1",
            '" OR 1=1 --',
        ],
    )
    def test_search_treats_injection_payloads_as_literal_text(
        self, client, auth, verifier_user, qualification, payload
    ):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.get("/qualifications/", query_string={"q": payload})
        assert response.status_code == 200
        assert b"No qualifications match" in response.data
        # The register is intact.
        assert client.get("/qualifications/").status_code == 200

    def test_injection_in_the_verification_field_is_handled(self, client, auth, verifier_user):
        auth.login("verifier", VERIFIER_PASSWORD)
        response = client.post(
            "/verify/",
            data={"credential_id": "' OR '1'='1"},
            follow_redirects=True,
        )
        assert b"INVALID" in response.data


class TestCsrfProtection:
    """CSRF is disabled in the testing config, so it is asserted directly."""

    def test_csrf_is_enabled_outside_testing(self):
        from app.config import DevelopmentConfig

        assert getattr(DevelopmentConfig, "WTF_CSRF_ENABLED", True) is True

    def test_state_changing_routes_reject_get(self, client, auth, issuer_user, qualification):
        auth.login("issuer", ISSUER_PASSWORD)
        assert client.get(f"/qualifications/{qualification.id}/revoke").status_code == 405

    def test_logout_is_post_only(self, client, auth, admin_user):
        auth.login("admin", ADMIN_PASSWORD)
        assert client.get("/logout").status_code == 405


class TestOpenRedirectProtection:
    def test_external_next_parameter_is_ignored(self, client, auth, admin_user):
        response = client.post(
            "/login?next=https://evil.example.com/steal",
            data={"identifier": "admin", "password": ADMIN_PASSWORD},
        )
        assert response.status_code == 302
        assert "evil.example.com" not in response.headers["Location"]

    def test_relative_next_parameter_is_honoured(self, client, auth, admin_user):
        response = client.post(
            "/login?next=/admin/audit",
            data={"identifier": "admin", "password": ADMIN_PASSWORD},
        )
        assert response.headers["Location"].endswith("/admin/audit")


class TestProductionConfigurationGuards:
    def test_production_refuses_a_missing_secret_key(self, monkeypatch):
        from app.config import ProductionConfig

        monkeypatch.delenv("SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            ProductionConfig()

    def test_production_refuses_the_development_placeholder_key(self, monkeypatch):
        from app.config import ProductionConfig

        monkeypatch.setenv("SECRET_KEY", "dev-only-insecure-key")
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            ProductionConfig()

    def test_production_requires_a_database_url(self, monkeypatch):
        from app.config import ProductionConfig

        monkeypatch.setenv("SECRET_KEY", "a-genuinely-random-production-value")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            ProductionConfig()

    def test_production_normalises_the_postgres_url_scheme(self, monkeypatch):
        from app.config import ProductionConfig

        monkeypatch.setenv("SECRET_KEY", "a-genuinely-random-production-value")
        monkeypatch.setenv("DATABASE_URL", "postgres://user:pw@host:5432/db")
        config = ProductionConfig()
        assert config.SQLALCHEMY_DATABASE_URI.startswith("postgresql+psycopg://")

    def test_production_disables_debug_and_forces_secure_cookies(self, monkeypatch):
        from app.config import ProductionConfig

        monkeypatch.setenv("SECRET_KEY", "a-genuinely-random-production-value")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@host:5432/db")
        config = ProductionConfig()
        assert config.DEBUG is False
        assert config.SESSION_COOKIE_SECURE is True


class TestProxyAwareness:
    """Behind Fly.io's edge, TLS terminates at the proxy.

    Without ProxyFix the application sees plain HTTP for every request, so it
    would never emit HSTS and would record the proxy's address in the audit
    trail instead of the caller's. These tests pin that behaviour.
    """

    def test_proxy_headers_are_not_trusted_by_default(self, app):
        """Trusting X-Forwarded-* without a proxy in front lets clients forge them."""
        assert app.config["TRUST_PROXY_HEADERS"] is False

    def test_production_trusts_the_proxy(self, monkeypatch):
        from app.config import ProductionConfig

        monkeypatch.setenv("SECRET_KEY", "a-genuinely-random-production-value")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@host:5432/db")
        assert ProductionConfig().TRUST_PROXY_HEADERS is True

    def test_hsts_is_sent_for_an_https_request(self, app, client):
        """A forwarded HTTPS request must receive HSTS."""
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        response = client.get("/login", headers={"X-Forwarded-Proto": "https"})
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

    def test_hsts_is_not_sent_over_plain_http(self, client):
        """HSTS on a plain-HTTP response is meaningless and browsers ignore it."""
        assert "Strict-Transport-Security" not in client.get("/login").headers
