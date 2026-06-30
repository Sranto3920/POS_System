"""
Shop management forms — used by the platform owner to create and edit shops.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

from models.shop import Shop
from models.user import User

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE_REGEX = r"^\+?[\d\s\-()]{7,20}$"


class CreateShopForm(FlaskForm):
    """Collects shop details and the first Admin user for a new tenant."""

    shop_name = StringField(
        "Shop Name",
        validators=[
            DataRequired(message="Shop name is required."),
            Length(max=150),
        ],
    )
    owner_name = StringField(
        "Owner Name",
        validators=[
            DataRequired(message="Owner name is required."),
            Length(max=100),
        ],
    )
    phone = StringField(
        "Phone",
        validators=[
            DataRequired(message="Phone is required."),
            Length(max=20),
            Regexp(PHONE_REGEX, message="Enter a valid phone number."),
        ],
    )
    email = StringField(
        "Shop Email",
        validators=[
            DataRequired(message="Shop email is required."),
            Length(max=100),
            Regexp(EMAIL_REGEX, message="Enter a valid email address."),
        ],
    )
    address = TextAreaField(
        "Address",
        validators=[
            DataRequired(message="Address is required."),
            Length(max=500),
        ],
    )
    admin_name = StringField(
        "Admin Name",
        validators=[
            DataRequired(message="Admin name is required."),
            Length(max=100),
        ],
    )
    admin_email = StringField(
        "Admin Email",
        validators=[
            DataRequired(message="Admin email is required."),
            Length(max=100),
            Regexp(EMAIL_REGEX, message="Enter a valid email address."),
        ],
    )
    admin_password = PasswordField(
        "Temporary Password",
        validators=[
            DataRequired(message="Temporary password is required."),
            Length(min=8, max=128, message="Password must be at least 8 characters."),
        ],
    )

    def validate_email(self, field):
        email = field.data.strip().lower()
        if Shop.query.filter_by(email=email).first():
            raise ValidationError("A shop with this email already exists.")

    def validate_admin_email(self, field):
        email = field.data.strip().lower()
        if User.query.filter_by(email=email).first():
            raise ValidationError("This admin email is already registered.")


class EditShopForm(FlaskForm):
    """Edit shop profile fields. Does not change the admin password."""

    shop_name = StringField(
        "Shop Name",
        validators=[DataRequired(), Length(max=150)],
    )
    owner_name = StringField(
        "Owner Name",
        validators=[DataRequired(), Length(max=100)],
    )
    phone = StringField(
        "Phone",
        validators=[
            DataRequired(),
            Length(max=20),
            Regexp(PHONE_REGEX, message="Enter a valid phone number."),
        ],
    )
    email = StringField(
        "Shop Email",
        validators=[
            DataRequired(),
            Length(max=100),
            Regexp(EMAIL_REGEX, message="Enter a valid email address."),
        ],
    )
    address = TextAreaField(
        "Address",
        validators=[DataRequired(), Length(max=500)],
    )

    def __init__(self, shop_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shop_id = shop_id

    def validate_email(self, field):
        email = field.data.strip().lower()
        existing = Shop.query.filter_by(email=email).first()
        if existing and existing.id != self.shop_id:
            raise ValidationError("A shop with this email already exists.")
