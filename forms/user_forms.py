from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp, ValidationError

from models.user import User
from utils.roles import Role

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE_REGEX = r"^\+?[\d\s\-()]{7,20}$"

ROLE_CHOICES = [
    (Role.MANAGER, Role.label(Role.MANAGER)),
    (Role.CASHIER, Role.label(Role.CASHIER)),
]


class UserForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Name is required."),
            Length(max=100),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Length(max=100),
            Regexp(EMAIL_REGEX, message="Enter a valid email address."),
        ],
    )
    phone = StringField(
        "Phone",
        validators=[
            Optional(),
            Length(max=20),
            Regexp(PHONE_REGEX, message="Enter a valid phone number."),
        ],
    )
    role = SelectField(
        "Role",
        choices=ROLE_CHOICES,
        validators=[DataRequired(message="Role is required.")],
    )

    def __init__(self, user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_email(self, field):
        email = field.data.strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != self.user_id:
            raise ValidationError("This email is already registered.")

    def validate_role(self, field):
        if Role.normalize(field.data) == Role.ADMIN:
            raise ValidationError("Cannot assign Administrator role.")


class PasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, max=128, message="Password must be 8–128 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm the password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
