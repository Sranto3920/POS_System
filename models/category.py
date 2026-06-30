from extensions import db


class Category(db.Model):
    __tablename__ = "Categories"

    id = db.Column("category_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    name = db.Column("category_name", db.String(100), nullable=False)
    description = db.Column(db.Text)

    products = db.relationship("Product", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"
