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

    @app.cli.command("seed-testdata")
    @click.option(
        "--reset",
        is_flag=True,
        help="Delete existing qualifications and verifications first.",
    )
    def seed_testdata(reset: bool) -> None:
        """Load the demonstration dataset: three universities and a varied register.

        Safe to re-run. Existing records are left alone unless --reset is given.
        Passwords come from the environment, or are generated and shown once.
        """
        import os

        from app.models.audit import AuditLog
        from app.models.verification import Verification
        from app.repositories.qualification_repository import QualificationRepository
        from app.services.verification_service import VerificationService
        from app.testdata import (
            BUSY_HOLDER,
            BUSY_HOLDER_CREDENTIALS,
            QUALIFICATIONS,
            UNIVERSITIES,
            UNIVERSITY_CODES,
            USERS,
            VERIFICATIONS,
            _days,
        )

        db.create_all()

        if reset:
            # Audit rows are append-only by design, so the guard has to be
            # bypassed explicitly here. This is a development command; the
            # application itself has no path that can do this.
            from sqlalchemy import event

            from app.utils.audit_guard import _block_delete, _block_update

            for target, hook in (
                ("before_delete", _block_delete),
                ("before_update", _block_update),
            ):
                if event.contains(AuditLog, target, hook):
                    event.remove(AuditLog, target, hook)
            Verification.query.delete()
            Qualification.query.delete()
            AuditLog.query.delete()
            db.session.commit()
            click.echo("Existing qualifications, verifications and audit entries removed.")

        # -- institutions --------------------------------------------------
        institutions: dict[str, Institution] = {}
        for spec in UNIVERSITIES:
            record = InstitutionRepository.get_by_code(spec["code"])
            if record is None:
                record = Institution(**spec)
                db.session.add(record)
            else:
                record.name = spec["name"]
                record.country = spec["country"]
                record.contact_email = spec["contact_email"]
                record.is_active = True
            institutions[spec["code"]] = record
        db.session.flush()

        # Anything that is not one of the three universities is deactivated
        # rather than deleted: credentials it already issued stay verifiable.
        deactivated = []
        for other in InstitutionRepository.list_all(page=1, per_page=100).items:
            if other.code not in UNIVERSITY_CODES and other.is_active:
                other.is_active = False
                deactivated.append(other.code)

        # -- users ---------------------------------------------------------
        users: dict[str, User] = {}
        created: list[tuple[str, str]] = []
        for username, full_name, role, code, env_var in USERS:
            password = os.environ.get(env_var) or generate_password()
            user, was_created = _ensure_user(
                username=username,
                email=f"{username.replace('.', '-')}@qvs.example.com",
                full_name=full_name,
                role=role,
                password=password,
                institution_id=institutions[code].id if code else None,
            )
            users[username] = user
            if was_created:
                created.append((username, password))
        db.session.flush()

        issuer_for = {
            "MSU": users["registry.msu"],
            "UZ": users["registry.uz"],
            "NUST": users["registry.nust"],
        }

        # -- qualifications ------------------------------------------------
        added = 0
        rows = list(QUALIFICATIONS)
        for cid, title, qtype, code, award_ago in BUSY_HOLDER_CREDENTIALS:
            rows.append(
                (
                    cid,
                    title,
                    qtype,
                    BUSY_HOLDER,
                    "tapiwa.chidziva@example.com",
                    code,
                    award_ago,
                    None,
                    QualificationStatus.ACTIVE,
                    None,
                )
            )

        for cid, title, qtype, holder, email, code, award_ago, expiry_ago, status, reason in rows:
            if QualificationRepository.exists_credential_id(cid):
                continue
            db.session.add(
                Qualification(
                    credential_id=cid,
                    title=title,
                    qualification_type=qtype,
                    holder_name=holder,
                    holder_email=email,
                    institution_id=institutions[code].id,
                    award_date=_days(award_ago),
                    expiry_date=_days(expiry_ago) if expiry_ago is not None else None,
                    status=status,
                    revocation_reason=reason,
                    issued_by_id=issuer_for[code].id,
                )
            )
            added += 1
        db.session.commit()

        # -- verification history -----------------------------------------
        checks = 0
        if Verification.query.count() == 0:
            for cid, username, _days_ago in VERIFICATIONS:
                VerificationService.verify(credential_id=cid, actor=users[username])
                checks += 1

        # -- summary --------------------------------------------------------
        click.echo("\nTest data loaded.")
        click.echo(f"  Universities        : {len(institutions)}")
        if deactivated:
            click.echo(f"  Deactivated (not a university): {', '.join(deactivated)}")
        click.echo(f"  Qualifications added: {added}")
        click.echo(f"  Total in register   : {QualificationRepository.count_all()}")
        click.echo(f"  Verifications run   : {checks}")

        if created:
            click.echo("\n  Sign-in details (shown once - record them now):")
            width = max(len(u) for u, _ in created)
            for username, password in created:
                click.echo(f"    {username.ljust(width)}  {password}")
        else:
            click.echo("\n  All accounts already existed; passwords unchanged.")
