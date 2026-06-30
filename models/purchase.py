from datetime import datetime, timezone

from sqlalchemy import Computed

from extensions import db


class Purchase(db.Model):
    __tablename__ = "Purchases"

    id = db.Column("purchase_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("Suppliers.supplier_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id"), nullable=False)
    purchase_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    supplier = db.relationship("Supplier", backref="purchases")
    user = db.relationship("User", backref="purchases")
    details = db.relationship(
        "PurchaseDetail", backref="purchase", cascade="all, delete-orphan", lazy="joined"
    )


class PurchaseDetail(db.Model):
    __tablename__ = "Purchase_Details"

    id = db.Column("purchase_detail_id", db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey("Purchases.purchase_id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("Products.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(
        db.Numeric(10, 2),
        Computed("(quantity * cost_price)", persisted=True),
    )

    product = db.relationship("Product", backref="purchase_details")
