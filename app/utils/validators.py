"""Reusable validation rules.

These are plain functions with no Flask dependency so they can be unit tested
directly and reused by both the web forms and the service layer.
"""

from __future__ import annotations

import re
from datetime import date

from app.utils.errors import ValidationError

CREDENTIAL_ID_PATTERN = re.compile(r"^[A-Z]{2,5}-\d{4}-[A-Z0-9]{6}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{3,64}$")

# Types accepted by the registration form. Kept here so the form, the service
# layer and the tests all agree on one list.
QUALIFICATION_TYPES = (
    "Degree",
    "Diploma",
    "Certificate",
    "Professional Certification",
    "Short Course",
    "Licence",
)

MIN_AWARD_YEAR = 1900


def validate_credential_id(value: str) -> str:
    """Normalise and validate a credential reference (``QVS-2024-A1B2C3``)."""
    if not value or not value.strip():
        raise ValidationError("Credential ID is required.", field="credential_id")
    normalised = value.strip().upper()
    if not CREDENTIAL_ID_PATTERN.match(normalised):
        raise ValidationError(
            "Credential ID must look like PREFIX-YYYY-XXXXXX (e.g. QVS-2024-A1B2C3).",
            field="credential_id",
        )
    return normalised


def validate_required(value: str | None, field: str, label: str, max_length: int = 255) -> str:
    """Ensure a text field is present and within ``max_length``."""
    if value is None or not str(value).strip():
        raise ValidationError(f"{label} is required.", field=field)
    cleaned = str(value).strip()
    if len(cleaned) > max_length:
        raise ValidationError(f"{label} must be {max_length} characters or fewer.", field=field)
    return cleaned


def validate_qualification_type(value: str | None) -> str:
    """Ensure the qualification type is one of the supported values."""
    cleaned = validate_required(value, "qualification_type", "Qualification type", 64)
    if cleaned not in QUALIFICATION_TYPES:
        raise ValidationError(
            f"Qualification type must be one of: {', '.join(QUALIFICATION_TYPES)}.",
            field="qualification_type",
        )
    return cleaned


def validate_email(value: str | None, *, field: str = "email", required: bool = True) -> str | None:
    """Validate an email address; returns ``None`` when optional and blank."""
    if value is None or not str(value).strip():
        if required:
            raise ValidationError("Email address is required.", field=field)
        return None
    cleaned = str(value).strip().lower()
    if not EMAIL_PATTERN.match(cleaned) or len(cleaned) > 255:
        raise ValidationError("Enter a valid email address.", field=field)
    return cleaned


def validate_username(value: str | None) -> str:
    """Validate a username: 3-64 chars of letters, digits, dot, dash, underscore."""
    cleaned = validate_required(value, "username", "Username", 64)
    if not USERNAME_PATTERN.match(cleaned):
        raise ValidationError(
            "Username may only contain letters, numbers, dots, dashes and "
            "underscores (3-64 characters).",
            field="username",
        )
    return cleaned.lower()


def validate_password(value: str | None, min_length: int = 12) -> str:
    """Enforce the password policy: length plus three character classes.

    Requiring upper, lower and digit (rather than every class) keeps the policy
    usable while still ruling out the trivially guessable passwords that a
    length check alone lets through.
    """
    if not value:
        raise ValidationError("Password is required.", field="password")
    if len(value) < min_length:
        raise ValidationError(
            f"Password must be at least {min_length} characters long.", field="password"
        )
    if not re.search(r"[A-Z]", value):
        raise ValidationError(
            "Password must contain at least one uppercase letter.", field="password"
        )
    if not re.search(r"[a-z]", value):
        raise ValidationError(
            "Password must contain at least one lowercase letter.", field="password"
        )
    if not re.search(r"\d", value):
        raise ValidationError("Password must contain at least one digit.", field="password")
    return value


def validate_award_and_expiry(
    award_date: date | None, expiry_date: date | None, *, today: date | None = None
) -> tuple[date, date | None]:
    """Validate the award/expiry date pair.

    Rules: an award date is required, may not be in the future, and may not
    predate ``MIN_AWARD_YEAR``; an expiry date, when given, must fall on or
    after the award date.
    """
    today = today or date.today()
    if award_date is None:
        raise ValidationError("Award date is required.", field="award_date")
    if award_date > today:
        raise ValidationError("Award date cannot be in the future.", field="award_date")
    if award_date.year < MIN_AWARD_YEAR:
        raise ValidationError(
            f"Award date cannot be earlier than {MIN_AWARD_YEAR}.", field="award_date"
        )
    if expiry_date is not None and expiry_date < award_date:
        raise ValidationError(
            "Expiry date must be on or after the award date.", field="expiry_date"
        )
    return award_date, expiry_date
