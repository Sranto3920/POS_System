from datetime import datetime, timezone

from extensions import db


class DailyCash(db.Model):
    __tablename__ = "DailyCash"

    id = db.Column("daily_cash_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    cash_date = db.Column(db.Date, nullable=False)
    opening_cash = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    carry_forward_cash = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    supplier_payments = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    cash_withdrawals = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    actual_cash = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=True)
    recorded_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref="daily_cash_records")

    __table_args__ = (
        db.UniqueConstraint("shop_id", "cash_date", name="uq_daily_cash_shop_date"),
    )
