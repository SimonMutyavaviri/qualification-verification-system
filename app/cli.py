"""Flask CLI commands for database setup and demo data.

Demo passwords are never hard-coded. ``seed-demo`` reads them from the
environment and, if they are absent, generates strong random ones and prints
them once so a developer can sign in locally. Nothing usable in production is
baked into the repository.
"""

from __future__ import annotations

import secrets
import string
from datetime import date, timedelta

import click
from flask import Flask

from app.extensions import db
from app.models.enums import QualificationStatus, Role
from app.models.institution import Institution
from app.models.qualification import Qualification
from app.models.user import User
from app.repositories.user_repository import InstitutionRepository, UserRepository

_PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*"


def generate_password(length: int = 16) -> str:
    """Generate a random password satisfying the default policy."""
    while True:
        candidate = "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))
        if (
            any(c.isupper() for c in candidate)
            and any(c.islower() for c in candidate)
            and any(c.isdigit() for c in candidate)
        ):
            return candidate


def _ensure_user(
    *, username: str, email: str, full_name: str, role: Role, password: str, institution_id=None
) -> tuple[User, bool]:
    existing = UserRepository.get_by_username(username)
    if existing is not None:
        return existing, False
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=role,
        institution_id=institution_id,
    )
    user.set_password(password)
    db.session.add(user)
    return user, True


def register_cli(app: Flask) -> None:
    """Attach the custom ``flask`` commands."""

    @app.cli.command("init-db")
    def init_db() -> None:
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-admin")
    @click.option("--username", required=True)
    @click.option("--email", required=True)
    @click.option("--full-name", required=True)
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Read from a prompt so it never appears in shell history.",
    )
    def create_admin(username: str, email: str, full_name: str, password: str) -> None:
        """Create an administrator account."""
        from app.utils.validators import validate_password

        validate_password(password, min_length=app.config["PASSWORD_MIN_LENGTH"])
        if UserRepository.get_by_username(username) is not None:
            raise click.ClickException(f"User {username} already exists.")
        user = User(username=username, email=email, full_name=full_name, role=Role.ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Administrator {username} created.")

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Populate demo institutions, users and qualifications.

        Intended for local development, the CI integration smoke check and the
        assessed demonstration. Safe to re-run: it is idempotent.
        """
        db.create_all()

        seeds = [
            ("Midlands State University", "MSU", "Zimbabwe", "registry@msu.ac.zw"),
            ("University of Zimbabwe", "UZ", "Zimbabwe", "registry@uz.ac.zw"),
            ("Institute of Chartered Accountants", "ICA", "Zimbabwe", "info@ica.org"),
        ]
        institutions: dict[str, Institution] = {}
        for name, code, country, contact in seeds:
            existing = InstitutionRepository.get_by_code(code)
            if existing is None:
                existing = Institution(name=name, code=code, country=country, contact_email=contact)
                db.session.add(existing)
            institutions[code] = existing
        db.session.flush()

        import os

        accounts = [
            (
                "admin",
                "admin@qvs.example.com",
                "System Administrator",
                Role.ADMIN,
                "SEED_ADMIN_PASSWORD",
            ),
            (
                "issuer",
                "issuer@qvs.example.com",
                "Registry Officer",
                Role.ISSUER,
                "SEED_ISSUER_PASSWORD",
            ),
            (
                "verifier",
                "verifier@qvs.example.com",
                "Employer Verifier",
                Role.VERIFIER,
                "SEED_VERIFIER_PASSWORD",
            ),
        ]
        created_credentials: list[tuple[str, str]] = []
        users: dict[str, User] = {}
        for username, email, full_name, role, env_var in accounts:
            password = os.environ.get(env_var) or generate_password()
            user, created = _ensure_user(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                password=password,
                institution_id=institutions["MSU"].id,
            )
            users[username] = user
            if created:
                created_credentials.append((username, password))
        db.session.flush()

        issuer = users["issuer"]
        today = date.today()
        demo_qualifications = [
            (
                "QVS-2023-DEMO01",
                "BSc Honours in Information Systems",
                "Degree",
                "Tinashe Moyo",
                "MSU",
                today - timedelta(days=800),
                None,
                QualificationStatus.ACTIVE,
                None,
            ),
            (
                "QVS-2022-DEMO02",
                "Certified Public Accountant",
                "Professional Certification",
                "Rudo Chikafu",
                "ICA",
                today - timedelta(days=1200),
                today - timedelta(days=30),
                QualificationStatus.ACTIVE,
                None,
            ),
            (
                "QVS-2021-DEMO03",
                "Diploma in Project Management",
                "Diploma",
                "Farai Ncube",
                "UZ",
                today - timedelta(days=1600),
                None,
                QualificationStatus.REVOKED,
                "Awarded in error following a records audit.",
            ),
        ]
        for (
            credential_id,
            title,
            qual_type,
            holder,
            inst_code,
            award,
            expiry,
            status,
            reason,
        ) in demo_qualifications:
            from app.repositories.qualification_repository import QualificationRepository

            if QualificationRepository.exists_credential_id(credential_id):
                continue
            db.session.add(
                Qualification(
                    credential_id=credential_id,
                    title=title,
                    qualification_type=qual_type,
                    holder_name=holder,
                    holder_email=f"{holder.split()[0].lower()}@example.com",
                    institution_id=institutions[inst_code].id,
                    award_date=award,
                    expiry_date=expiry,
                    status=status,
                    revocation_reason=reason,
                    issued_by_id=issuer.id,
                )
            )
        db.session.commit()

        click.echo("Demo data seeded.")
        click.echo(
            "  Credentials: QVS-2023-DEMO01 (valid), QVS-2022-DEMO02 (expired), "
            "QVS-2021-DEMO03 (revoked)"
        )
        if created_credentials:
            click.echo("\n  Generated sign-in credentials (shown once):")
            for username, password in created_credentials:
                click.echo(f"    {username}: {password}")
            click.echo(
                "\n  Set SEED_ADMIN_PASSWORD / SEED_ISSUER_PASSWORD / "
                "SEED_VERIFIER_PASSWORD to choose your own."
            )
        else:
            click.echo("  Accounts already existed; passwords unchanged.")
