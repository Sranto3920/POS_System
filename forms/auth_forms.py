from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Length, Regexp


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Length(max=120),
            Regexp(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                message="Enter a valid email address.",
            ),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, max=128, message="Password must be 6–128 characters."),
        ],
    )
    remember_me = BooleanField("Remember Me")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired(), Length(min=6, max=128)],
    )
    new_password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )

    def validate_confirm_password(self, field):
        if field.data != self.new_password.data:
            from wtforms.validators import ValidationError
            raise ValidationError("Passwords must match.")
