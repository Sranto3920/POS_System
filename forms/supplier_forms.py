from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from forms.shop_forms import EMAIL_REGEX, PHONE_REGEX


class SupplierForm(FlaskForm):
    name = StringField(
        "Supplier Name",
        validators=[
            DataRequired(message="Supplier name is required."),
            Length(max=150),
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
    email = StringField(
        "Email",
        validators=[
            Optional(),
            Length(max=100),
            Regexp(EMAIL_REGEX, message="Enter a valid email address."),
        ],
    )
    address = TextAreaField(
        "Address",
        validators=[Optional(), Length(max=500)],
    )
