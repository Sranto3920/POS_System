from datetime import datetime, timezone

from extensions import db

PAYMENT_METHODS = ("Cash", "Card", "Mobile Banking", "Bank Transfer", "Credit")


class Payment(db.Model):
    __tablename__ = "Payments"

    id = db.Column("payment_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("Sales.sale_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=True)
    payment_method = db.Column(db.String(30), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_type = db.Column(db.String(20), nullable=False, default="sale")
    payment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref="payments_collected")

    @property
    def sale_ref(self):
        return self.sale
