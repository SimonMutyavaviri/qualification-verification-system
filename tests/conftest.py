"""Shared pytest fixtures.

Each test gets a fresh application and an empty in-memory database, so tests
are order-independent and leave no state behind.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import create_app
from app.extensions import db as _db
from app.models.enums import QualificationStatus, Role
from app.models.institution import Institution
from app.models.qualification import Qualification
from app.models.user import User

# Passwords used only inside the test process; nothing here reaches an
# environment where it could grant access.
ADMIN_PASSWORD = "AdminPassw0rd!23"
ISSUER_PASSWORD = "IssuerPassw0rd!23"
VERIFIER_PASSWORD = "VerifyPassw0rd!23"


@pytest.fixture
def app():
    """A Flask app bound to a throwaway in-memory SQLite database."""
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    """The SQLAlchemy session/registry inside the app context."""
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def institution(db) -> Institution:
    record = Institution(
        name="Midlands State University",
        code="MSU",
        country="Zimbabwe",
        contact_email="registry@msu.ac.zw",
    )
    db.session.add(record)
    db.session.commit()
    return record


def _make_user(db, *, username: str, role: Role, password: str, institution=None) -> User:
    user = User(
        username=username,
        email=f"{username}@qvs.example.com",
        full_name=username.title(),
        role=role,
        institution_id=institution.id if institution else None,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db, institution) -> User:
    return _make_user(
        db, username="admin", role=Role.ADMIN, password=ADMIN_PASSWORD, institution=institution
    )


@pytest.fixture
def issuer_user(db, institution) -> User:
    return _make_user(
        db, username="issuer", role=Role.ISSUER, password=ISSUER_PASSWORD, institution=institution
    )


@pytest.fixture
def verifier_user(db, institution) -> User:
    return _make_user(
        db,
        username="verifier",
        role=Role.VERIFIER,
        password=VERIFIER_PASSWORD,
        institution=institution,
    )


@pytest.fixture
def qualification(db, institution, issuer_user) -> Qualification:
    """An active, non-expiring credential."""
    record = Qualification(
        credential_id="QVS-2023-AAAAAA",
        title="BSc Honours in Information Systems",
        qualification_type="Degree",
        holder_name="Tinashe Moyo",
        holder_email="tinashe@example.com",
        institution_id=institution.id,
        award_date=date.today() - timedelta(days=400),
        status=QualificationStatus.ACTIVE,
        issued_by_id=issuer_user.id,
    )
    db.session.add(record)
    db.session.commit()
    return record


@pytest.fixture
def expired_qualification(db, institution, issuer_user) -> Qualification:
    record = Qualification(
        credential_id="QVS-2020-BBBBBB",
        title="Certified Public Accountant",
        qualification_type="Professional Certification",
        holder_name="Rudo Chikafu",
        institution_id=institution.id,
        award_date=date.today() - timedelta(days=1200),
        expiry_date=date.today() - timedelta(days=10),
        status=QualificationStatus.ACTIVE,
        issued_by_id=issuer_user.id,
    )
    db.session.add(record)
    db.session.commit()
    return record


@pytest.fixture
def revoked_qualification(db, institution, issuer_user) -> Qualification:
    record = Qualification(
        credential_id="QVS-2021-CCCCCC",
        title="Diploma in Project Management",
        qualification_type="Diploma",
        holder_name="Farai Ncube",
        institution_id=institution.id,
        award_date=date.today() - timedelta(days=900),
        status=QualificationStatus.REVOKED,
        revocation_reason="Awarded in error following a records audit.",
        issued_by_id=issuer_user.id,
    )
    db.session.add(record)
    db.session.commit()
    return record


class AuthActions:
    """Helper for signing the test client in and out."""

    def __init__(self, client):
        self._client = client

    def login(self, identifier: str, password: str):
        return self._client.post(
            "/login",
            data={"identifier": identifier, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self._client.post("/logout", follow_redirects=True)


@pytest.fixture
def auth(client) -> AuthActions:
    return AuthActions(client)


@pytest.fixture
def logged_in_admin(auth, admin_user):
    auth.login("admin", ADMIN_PASSWORD)
    return admin_user


@pytest.fixture
def logged_in_issuer(auth, issuer_user):
    auth.login("issuer", ISSUER_PASSWORD)
    return issuer_user


@pytest.fixture
def logged_in_verifier(auth, verifier_user):
    auth.login("verifier", VERIFIER_PASSWORD)
    return verifier_user
