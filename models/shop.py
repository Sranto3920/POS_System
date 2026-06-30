"""
Shop model — one tenant in the multi-tenant POS system.

Each shop is a paying customer. All business data (products, sales, etc.)
is scoped by shop_id. Platform owner creates and manages shops.
"""

from datetime import datetime, timezone

from extensions import db


class Shop(db.Model):
    __tablename__ = "Shops"

    id = db.Column("shop_id", db.Integer, primary_key=True)
    shop_name = db.Column(db.String(150), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    address = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=True
    )

    @property
    def status_label(self):
        return "Active" if self.is_active else "Inactive"

    @property
    def status_badge_class(self):
        return "success" if self.is_active else "secondary"

    def __repr__(self):
        return f"<Shop {self.shop_name} ({self.email})>"
