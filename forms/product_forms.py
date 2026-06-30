from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from models.category import Category
from models.supplier import Supplier


class ProductForm(FlaskForm):
    name = StringField(
        "Product Name",
        validators=[
            DataRequired(message="Product name is required."),
            Length(max=150),
        ],
    )
    barcode = StringField(
        "Barcode",
        validators=[Optional(), Length(max=50)],
    )
    sku = StringField(
        "SKU",
        validators=[Optional(), Length(max=50)],
    )
    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired(message="Category is required.")],
    )
    supplier_id = SelectField(
        "Supplier",
        coerce=int,
        validators=[DataRequired(message="Supplier is required.")],
    )
    cost_price = DecimalField(
        "Cost Price",
        places=2,
        validators=[
            DataRequired(message="Cost price is required."),
            NumberRange(min=0, message="Cost price cannot be negative."),
        ],
    )
    market_price = DecimalField(
        "Market Price",
        places=2,
        validators=[
            DataRequired(message="Market price is required."),
            NumberRange(min=0, message="Market price cannot be negative."),
        ],
    )
    minimum_selling_price = DecimalField(
        "Minimum Selling Price",
        places=2,
        validators=[
            Optional(),
            NumberRange(min=0, message="Minimum selling price cannot be negative."),
        ],
    )
    stock_quantity = IntegerField(
        "Stock Quantity",
        validators=[
            DataRequired(message="Stock quantity is required."),
            NumberRange(min=0, message="Stock quantity cannot be negative."),
        ],
        default=0,
    )
    expiry_date = DateField(
        "Expiry Date",
        validators=[Optional()],
        format="%Y-%m-%d",
    )

    def __init__(self, shop_id=None, show_minimum_price=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shop_id = shop_id
        self.show_minimum_price = show_minimum_price
        self.category_id.choices = [(0, "-- Select Category --")]
        self.supplier_id.choices = [(0, "-- Select Supplier --")]

        if shop_id:
            categories = (
                Category.query.filter_by(shop_id=shop_id)
                .order_by(Category.name.asc())
                .all()
            )
            suppliers = (
                Supplier.query.filter_by(shop_id=shop_id)
                .order_by(Supplier.name.asc())
                .all()
            )
            self.category_id.choices += [(c.id, c.name) for c in categories]
            self.supplier_id.choices += [(s.id, s.name) for s in suppliers]

    def validate_category_id(self, field):
        if not field.data:
            raise ValidationError("Please select a category.")

    def validate_supplier_id(self, field):
        if not field.data:
            raise ValidationError("Please select a supplier.")

    def validate_minimum_selling_price(self, field):
        if not self.show_minimum_price:
            return
        if field.data is None:
            raise ValidationError("Minimum selling price is required.")
        if self.market_price.data is not None and field.data > self.market_price.data:
            raise ValidationError(
                "Minimum selling price cannot be higher than market price."
            )
