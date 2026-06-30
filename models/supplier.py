from extensions import db


class Supplier(db.Model):
    __tablename__ = "Suppliers"

    id = db.Column("supplier_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    name = db.Column("supplier_name", db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)

    def __repr__(self):
        return f"<Supplier {self.name}>"
