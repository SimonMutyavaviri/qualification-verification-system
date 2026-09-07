"""Unit tests for the validation rules (REQ-VAL-*)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.utils.errors import ValidationError
from app.utils.validators import (
    validate_award_and_expiry,
    validate_credential_id,
    validate_email,
    validate_password,
    validate_qualification_type,
    validate_required,
    validate_username,
)

pytestmark = pytest.mark.unit


class TestCredentialId:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("QVS-2024-A1B2C3", "QVS-2024-A1B2C3"),
            ("qvs-2024-a1b2c3", "QVS-2024-A1B2C3"),
            ("  QVS-2024-A1B2C3  ", "QVS-2024-A1B2C3"),
            ("AB-1999-ZZZZZZ", "AB-1999-ZZZZZZ"),
        ],
    )
    def test_accepts_and_normalises_valid_ids(self, raw, expected):
        assert validate_credential_id(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "   ",
            "QVS2024A1B2C3",  # missing separators
            "QVS-24-A1B2C3",  # year too short
            "QVS-2024-A1B2",  # suffix too short
            "QVS-2024-A1B2C3D",  # suffix too long
            "Q-2024-A1B2C3",  # prefix too short
            "QVSQVS-2024-A1B2C3",  # prefix too long
            "QVS-2024-A1B2C!",  # illegal character
        ],
    )
    def test_rejects_malformed_ids(self, raw):
        with pytest.raises(ValidationError) as exc:
            validate_credential_id(raw)
        assert exc.value.field == "credential_id"

    def test_rejects_none(self):
        with pytest.raises(ValidationError):
            validate_credential_id(None)


class TestRequiredText:
    def test_strips_surrounding_whitespace(self):
        assert validate_required("  BSc Computing  ", "title", "Title") == "BSc Computing"

    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_rejects_blank(self, value):
        with pytest.raises(ValidationError, match="Title is required"):
            validate_required(value, "title", "Title")

    def test_rejects_over_length(self):
        with pytest.raises(ValidationError, match="10 characters or fewer"):
            validate_required("x" * 11, "title", "Title", max_length=10)


class TestQualificationType:
    def test_accepts_known_type(self):
        assert validate_qualification_type("Degree") == "Degree"

    def test_rejects_unknown_type(self):
        with pytest.raises(ValidationError, match="must be one of"):
            validate_qualification_type("Honorary Doctorate")


class TestEmail:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Person@Example.COM", "person@example.com"),
            ("a.b+c@sub.domain.org", "a.b+c@sub.domain.org"),
        ],
    )
    def test_accepts_and_lowercases(self, raw, expected):
        assert validate_email(raw) == expected

    @pytest.mark.parametrize("raw", ["not-an-email", "missing@tld", "@example.com", "a b@c.com"])
    def test_rejects_malformed(self, raw):
        with pytest.raises(ValidationError):
            validate_email(raw)

    def test_optional_blank_returns_none(self):
        assert validate_email("", required=False) is None
        assert validate_email(None, required=False) is None

    def test_required_blank_raises(self):
        with pytest.raises(ValidationError, match="required"):
            validate_email("")


class TestUsername:
    def test_lowercases_valid_username(self):
        assert validate_username("Reg.Officer-1") == "reg.officer-1"

    @pytest.mark.parametrize("raw", ["ab", "has space", "has/slash", "x" * 65])
    def test_rejects_invalid(self, raw):
        with pytest.raises(ValidationError):
            validate_username(raw)


class TestPasswordPolicy:
    def test_accepts_compliant_password(self):
        assert validate_password("StrongPass123") == "StrongPass123"

    @pytest.mark.parametrize(
        "raw,expected_message",
        [
            ("Short1a", "at least 12 characters"),
            ("alllowercase123", "uppercase letter"),
            ("ALLUPPERCASE123", "lowercase letter"),
            ("NoDigitsInHere", "one digit"),
        ],
    )
    def test_rejects_weak_passwords(self, raw, expected_message):
        with pytest.raises(ValidationError, match=expected_message):
            validate_password(raw)

    def test_rejects_empty(self):
        with pytest.raises(ValidationError, match="required"):
            validate_password("")

    def test_honours_custom_minimum_length(self):
        with pytest.raises(ValidationError, match="at least 20 characters"):
            validate_password("StrongPass123", min_length=20)


class TestAwardAndExpiryDates:
    def test_accepts_award_without_expiry(self):
        award = date(2020, 6, 1)
        assert validate_award_and_expiry(award, None) == (award, None)

    def test_accepts_expiry_after_award(self):
        award, expiry = date(2020, 6, 1), date(2025, 6, 1)
        assert validate_award_and_expiry(award, expiry) == (award, expiry)

    def test_accepts_expiry_equal_to_award(self):
        same = date(2020, 6, 1)
        assert validate_award_and_expiry(same, same) == (same, same)

    def test_rejects_missing_award_date(self):
        with pytest.raises(ValidationError, match="Award date is required"):
            validate_award_and_expiry(None, None)

    def test_rejects_future_award_date(self):
        future = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError, match="cannot be in the future"):
            validate_award_and_expiry(future, None)

    def test_rejects_implausibly_old_award_date(self):
        with pytest.raises(ValidationError, match="earlier than 1900"):
            validate_award_and_expiry(date(1899, 12, 31), None)

    def test_rejects_expiry_before_award(self):
        with pytest.raises(ValidationError, match="on or after the award date"):
            validate_award_and_expiry(date(2020, 6, 1), date(2019, 6, 1))
