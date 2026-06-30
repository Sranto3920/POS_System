from datetime import datetime, timezone

from extensions import db


class CustomerLedger(db.Model):
    __tablename__ = "Customer_Ledger"

    id = db.Column("ledger_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("Customers.customer_id"), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey("Sales.sale_id"))
    transaction_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    debit = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    credit = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    remarks = db.Column(db.Text)

    customer = db.relationship("Customer", backref="ledger_entries")
    sale = db.relationship("Sale", backref="ledger_entries")
