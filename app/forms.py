"""WTForms definitions.

Forms handle presentation-level validation and CSRF. The authoritative rules
live in :mod:`app.utils.validators` and are re-applied in the service layer, so
a request that bypasses the form still cannot write invalid data.
"""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional

from app.models.enums import QualificationStatus, Role, VerificationResult
from app.utils.validators import QUALIFICATION_TYPES

# Deliverability does a live DNS lookup, which makes form validation depend on
# the network and fails in CI and offline. Format checking is what a form should
# assert; whether the mailbox actually exists is not knowable here.
EMAIL_FORMAT = Email(check_deliverability=False)


class LoginForm(FlaskForm):
    identifier = StringField("Username or email", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Keep me signed in")
    submit = SubmitField("Sign in")


class QualificationForm(FlaskForm):
    """Register or edit a qualification."""

    credential_id = StringField(
        "Credential ID",
        validators=[Optional(), Length(max=32)],
        description="Leave blank to generate one automatically.",
    )
    title = StringField("Qualification title", validators=[DataRequired(), Length(max=255)])
    qualification_type = SelectField(
        "Qualification type",
        choices=[(t, t) for t in QUALIFICATION_TYPES],
        validators=[DataRequired()],
    )
    holder_name = StringField("Holder full name", validators=[DataRequired(), Length(max=255)])
    holder_email = StringField(
        "Holder email", validators=[Optional(), EMAIL_FORMAT, Length(max=255)]
    )
    institution_id = SelectField("Institution", coerce=int, validators=[DataRequired()])
    award_date = DateField("Award date", validators=[DataRequired()])
    expiry_date = DateField("Expiry date", validators=[Optional()])
    submit = SubmitField("Save qualification")

    def populate_institutions(self, institutions) -> None:
        """Fill the institution dropdown from the active institution list."""
        self.institution_id.choices = [(i.id, f"{i.name} ({i.code})") for i in institutions]


class QualificationEditForm(FlaskForm):
    """Edit the mutable subset of a qualification."""

    title = StringField("Qualification title", validators=[DataRequired(), Length(max=255)])
    qualification_type = SelectField(
        "Qualification type",
        choices=[(t, t) for t in QUALIFICATION_TYPES],
        validators=[DataRequired()],
    )
    holder_name = StringField("Holder full name", validators=[DataRequired(), Length(max=255)])
    holder_email = StringField(
        "Holder email", validators=[Optional(), EMAIL_FORMAT, Length(max=255)]
    )
    expiry_date = DateField("Expiry date", validators=[Optional()])
    clear_expiry = BooleanField("Remove expiry date (credential does not expire)")
    submit = SubmitField("Save changes")


class RevokeForm(FlaskForm):
    reason = TextAreaField("Reason for revocation", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Revoke qualification")


class ReinstateForm(FlaskForm):
    reason = TextAreaField("Reason for reinstatement", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Reinstate qualification")


class SearchForm(FlaskForm):
    """Search and filter the qualification register."""

    class Meta:
        csrf = False  # GET-only filter form; no state change to protect.

    q = StringField("Search", validators=[Optional(), Length(max=255)])
    status = SelectField(
        "Status",
        choices=[("", "Any status")] + [(s.value, s.label) for s in QualificationStatus],
        validators=[Optional()],
    )
    qualification_type = SelectField(
        "Type",
        choices=[("", "Any type")] + [(t, t) for t in QUALIFICATION_TYPES],
        validators=[Optional()],
    )
    institution_id = SelectField("Institution", validators=[Optional()])
    submit = SubmitField("Search")

    def populate_institutions(self, institutions) -> None:
        self.institution_id.choices = [("", "Any institution")] + [
            (str(i.id), i.name) for i in institutions
        ]


class VerificationForm(FlaskForm):
    credential_id = StringField(
        "Credential ID",
        validators=[DataRequired(), Length(max=32)],
        description="For example QVS-2024-A1B2C3",
    )
    submit = SubmitField("Verify credential")


class VerificationHistoryForm(FlaskForm):
    class Meta:
        csrf = False

    credential_id = StringField("Credential ID", validators=[Optional(), Length(max=32)])
    result = SelectField(
        "Result",
        choices=[("", "Any result")] + [(r.value, r.value.title()) for r in VerificationResult],
        validators=[Optional()],
    )
    submit = SubmitField("Filter")


class UserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), EMAIL_FORMAT, Length(max=255)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Temporary password", validators=[DataRequired()])
    role = SelectField(
        "Role", choices=[(r.value, r.label) for r in Role], validators=[DataRequired()]
    )
    institution_id = SelectField("Institution", validators=[Optional()])
    submit = SubmitField("Create user")

    def populate_institutions(self, institutions) -> None:
        self.institution_id.choices = [("", "No institution")] + [
            (str(i.id), i.name) for i in institutions
        ]


class InstitutionForm(FlaskForm):
    name = StringField("Institution name", validators=[DataRequired(), Length(max=255)])
    code = StringField("Code", validators=[DataRequired(), Length(max=16)])
    country = StringField("Country", validators=[Optional(), Length(max=100)])
    contact_email = StringField(
        "Contact email", validators=[Optional(), EMAIL_FORMAT, Length(max=255)]
    )
    submit = SubmitField("Create institution")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired()])
    submit = SubmitField("Change password")
