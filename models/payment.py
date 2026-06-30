from datetime import datetime, timezone

from extensions import db

PAYMENT_METHODS = ("Cash", "Card", "Mobile Banking", "Bank Transfer", "Credit")


class Payment(db.Model):
    __tablename__ = "Payments"

    id = db.Column("payment_id", db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("Sales.sale_id"), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def sale_ref(self):
        return self.sale
