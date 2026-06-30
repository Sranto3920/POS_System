from datetime import date

from extensions import db
from utils.formatters import LOW_STOCK_THRESHOLD


class Product(db.Model):
    __tablename__ = "Products"

    id = db.Column("product_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("Categories.category_id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("Suppliers.supplier_id"), nullable=False)
    name = db.Column("product_name", db.String(150), nullable=False)
    barcode = db.Column(db.String(50))
    sku = db.Column(db.String(50))
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    default_selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_selling_price = db.Column(db.Numeric(10, 2))
    market_price = db.Column(db.Numeric(10, 2))
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.Date)

    supplier = db.relationship("Supplier", backref="products")

    @property
    def effective_market_price(self):
        if self.market_price is not None:
            return self.market_price
        return self.default_selling_price

    @property
    def effective_minimum_price(self):
        if self.minimum_selling_price is not None:
            return self.minimum_selling_price
        return self.cost_price

    @property
    def is_low_stock(self):
        return (self.stock_quantity or 0) <= LOW_STOCK_THRESHOLD

    @property
    def stock_status(self):
        qty = self.stock_quantity or 0
        if qty <= 0:
            return "Out of Stock"
        if qty <= LOW_STOCK_THRESHOLD:
            return "Low Stock"
        return "In Stock"

    @property
    def stock_badge_class(self):
        qty = self.stock_quantity or 0
        if qty <= 0:
            return "danger"
        if qty <= LOW_STOCK_THRESHOLD:
            return "warning"
        return "success"

    def __repr__(self):
        return f"<Product {self.name}>"
