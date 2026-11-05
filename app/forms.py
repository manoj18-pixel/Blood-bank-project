"""WTForms definitions with server-side validation."""

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DateTimeLocalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from app.constants import (
    BLOOD_GROUP_CHOICES,
    GENDER_CHOICES,
    URGENCY_CHOICES,
)
from app.utils.time import utcnow

PHONE_REGEX = r"^[0-9+\-\s()]{7,20}$"
PINCODE_REGEX = r"^[0-9]{4,10}$"


def strong_password(form, field):
    value = field.data or ""
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not any(char.isalpha() for char in value) or not any(
        char.isdigit() for char in value
    ):
        raise ValidationError("Password must contain at least one letter and one number.")


class RegisterForm(FlaskForm):
    full_name = StringField(
        "Full name", validators=[DataRequired(), Length(min=2, max=80)]
    )
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField(
        "Phone number",
        validators=[DataRequired(), Regexp(PHONE_REGEX, message="Enter a valid phone number.")],
    )
    blood_group = SelectField(
        "Blood group", choices=BLOOD_GROUP_CHOICES, validators=[DataRequired()]
    )
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=80)])
    area = StringField("Area / locality", validators=[Optional(), Length(max=120)])
    pincode = StringField(
        "Pincode",
        validators=[Optional(), Regexp(PINCODE_REGEX, message="Enter a valid pincode.")],
    )
    password = PasswordField("Password", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    # Only DataRequired here: sign-in must accept any address that already
    # exists in the database, even one that the stricter registration
    # validator would reject (e.g. the seeded admin@bloodlink.local account).
    email = StringField("Email address", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Keep me signed in")
    submit = SubmitField("Sign in")


class ForgotForm(FlaskForm):
    # Same reasoning as LoginForm: the route responds generically and the
    # address only needs to match a stored account, not pass format checks.
    email = StringField("Email address", validators=[DataRequired()])
    submit = SubmitField("Send reset link")


class ResetForm(FlaskForm):
    password = PasswordField("New password", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Update password")


class ProfileForm(FlaskForm):
    full_name = StringField(
        "Full name", validators=[DataRequired(), Length(min=2, max=80)]
    )
    phone = StringField(
        "Phone number",
        validators=[DataRequired(), Regexp(PHONE_REGEX, message="Enter a valid phone number.")],
    )
    blood_group = SelectField(
        "Blood group", choices=BLOOD_GROUP_CHOICES, validators=[DataRequired()]
    )
    date_of_birth = DateField("Date of birth", validators=[Optional()])
    gender = SelectField("Gender", choices=GENDER_CHOICES, validators=[Optional()])
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=80)])
    area = StringField("Area / locality", validators=[Optional(), Length(max=120)])
    pincode = StringField(
        "Pincode",
        validators=[Optional(), Regexp(PINCODE_REGEX, message="Enter a valid pincode.")],
    )
    last_donation_date = DateField("Last donation date", validators=[Optional()])
    is_donor = BooleanField("I want to donate blood")
    is_available = BooleanField("Available to donate now")
    submit = SubmitField("Save profile")

    def validate_date_of_birth(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Date of birth cannot be in the future.")

    def validate_last_donation_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Last donation date cannot be in the future.")


class PasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change password")


class RequestForm(FlaskForm):
    patient_name = StringField(
        "Patient name", validators=[DataRequired(), Length(min=2, max=80)]
    )
    patient_age = IntegerField(
        "Patient age", validators=[Optional(), NumberRange(min=0, max=120)]
    )
    blood_group = SelectField(
        "Blood group needed", choices=BLOOD_GROUP_CHOICES, validators=[DataRequired()]
    )
    units_needed = IntegerField(
        "Units needed", validators=[DataRequired(), NumberRange(min=1, max=10)]
    )
    hospital_name = StringField(
        "Hospital / blood bank", validators=[DataRequired(), Length(min=2, max=160)]
    )
    address = StringField(
        "Hospital address", validators=[DataRequired(), Length(min=3, max=255)]
    )
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=80)])
    pincode = StringField(
        "Pincode",
        validators=[Optional(), Regexp(PINCODE_REGEX, message="Enter a valid pincode.")],
    )
    urgency = SelectField(
        "Urgency", choices=URGENCY_CHOICES, validators=[DataRequired()]
    )
    needed_by = DateTimeLocalField(
        "Needed by", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    contact_phone = StringField(
        "Contact number",
        validators=[DataRequired(), Regexp(PHONE_REGEX, message="Enter a valid phone number.")],
    )
    notes = TextAreaField("Additional notes", validators=[Optional(), Length(max=1000)])
    accept_terms = BooleanField(
        "I understand this is a community matching service, not a medical provider.",
        validators=[DataRequired(message="Please accept the disclaimer to continue.")],
    )
    submit = SubmitField("Post request")

    def validate_needed_by(self, field):
        if field.data and field.data < utcnow():
            raise ValidationError("The needed-by time must be in the future.")


class OfferForm(FlaskForm):
    message = TextAreaField(
        "Message to the requester", validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField("I can help")


class FulfillForm(FlaskForm):
    donated_on = DateField("Donation date", validators=[DataRequired()], default=date.today)
    units = IntegerField("Units donated", validators=[DataRequired(), NumberRange(min=1, max=4)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Mark as fulfilled")

    def validate_donated_on(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Donation date cannot be in the future.")
