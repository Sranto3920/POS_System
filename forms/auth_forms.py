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
