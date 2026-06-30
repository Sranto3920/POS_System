from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class CategoryForm(FlaskForm):
    name = StringField(
        "Category Name",
        validators=[
            DataRequired(message="Category name is required."),
            Length(max=100),
        ],
    )
    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=500)],
    )
