from datetime import datetime, timezone

from extensions import db


class DuePayment(db.Model):
    __tablename__ = "DuePayments"

    id = db.Column("due_payment_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey("Sales.sale_id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("Customers.customer_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False)
    collected_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    remarks = db.Column(db.String(255), nullable=True)

    sale = db.relationship("Sale", backref="due_payments")
    customer = db.relationship("Customer", backref="due_payments")
    user = db.relationship("User", backref="due_payments_collected")
