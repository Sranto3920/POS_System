from datetime import datetime, timezone

from sqlalchemy import Computed

from extensions import db


PAYMENT_STATUS_PAID = "Paid"
PAYMENT_STATUS_PARTIAL = "Partially Paid"
PAYMENT_STATUS_DUE = "Due"
PAYMENT_STATUSES = (
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PARTIAL,
    PAYMENT_STATUS_DUE,
)


class Sale(db.Model):
    __tablename__ = "Sales"

    id = db.Column("sale_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("Customers.customer_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    sale_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    due_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    payment_status = db.Column(db.String(20), nullable=False, default=PAYMENT_STATUS_PAID)

    customer = db.relationship("Customer", backref="sales")
    user = db.relationship("User", backref="sales")
    details = db.relationship(
        "SaleDetail", backref="sale", cascade="all, delete-orphan", lazy="joined"
    )
    payments = db.relationship("Payment", backref="sale", lazy="dynamic")


class SaleDetail(db.Model):
    __tablename__ = "Sale_Details"

    id = db.Column("sale_detail_id", db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("Sales.sale_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("Products.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    subtotal = db.Column(
        db.Numeric(10, 2),
        Computed("((quantity * selling_price) - discount)", persisted=True),
    )

    product = db.relationship("Product", backref="sale_details")
