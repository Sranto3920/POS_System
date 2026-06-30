from decimal import Decimal

from extensions import db
from models.product import Product
from models.purchase import Purchase, PurchaseDetail
from models.supplier import Supplier
from utils.pagination import PER_PAGE_DEFAULT


class PurchaseService:
    """Shop-scoped purchase operations."""

    def __init__(self, shop_id):
        self.shop_id = shop_id

    def create_purchase(self, shop_id, user_id, supplier_id, items):
        if not items:
            raise ValueError("At least one product line is required.")

        supplier = Supplier.query.filter_by(id=supplier_id, shop_id=shop_id).first()
        if supplier is None:
            raise ValueError("Supplier not found.")

        purchase = Purchase(
            shop_id=shop_id,
            supplier_id=supplier_id,
            user_id=user_id,
            total_amount=Decimal("0"),
        )
        db.session.add(purchase)

        total = Decimal("0")

        try:
            for item in items:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
                cost_price = Decimal(str(item["cost_price"]))

                if quantity <= 0:
                    raise ValueError("Quantity must be greater than zero.")
                if cost_price < 0:
                    raise ValueError("Cost price cannot be negative.")

                product = (
                    Product.query.filter_by(id=product_id, shop_id=shop_id)
                    .with_for_update()
                    .first()
                )
                if product is None:
                    raise ValueError(f"Product #{product_id} not found.")

                line_total = cost_price * quantity
                total += line_total

                detail = PurchaseDetail(
                    purchase=purchase,
                    product_id=product_id,
                    quantity=quantity,
                    cost_price=cost_price,
                )
                db.session.add(detail)

                product.stock_quantity = (product.stock_quantity or 0) + quantity
                product.cost_price = cost_price

            purchase.total_amount = total
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return purchase

    def list_purchases(self, page=1, per_page=PER_PAGE_DEFAULT, search=""):
        query = Purchase.query.filter_by(shop_id=self.shop_id).order_by(
            Purchase.purchase_date.desc(), Purchase.id.desc()
        )

        if search:
            like = f"%{search}%"
            query = query.join(Supplier).filter(Supplier.name.ilike(like))

        return query.paginate(page=page, per_page=per_page, error_out=False)

    def get_purchase(self, purchase_id):
        return Purchase.query.filter_by(id=purchase_id, shop_id=self.shop_id).first()
