from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from extensions import db
from models.product import Product
from utils.formatters import LOW_STOCK_THRESHOLD
from utils.pagination import PER_PAGE_DEFAULT


class ProductService:
    @staticmethod
    def list(
        shop_id,
        search="",
        category_id=None,
        stock_filter="all",
        page=1,
        per_page=PER_PAGE_DEFAULT,
    ):
        query = (
            Product.query.filter_by(shop_id=shop_id)
            .options(joinedload(Product.category), joinedload(Product.supplier))
        )

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.barcode.ilike(term),
                    Product.sku.ilike(term),
                )
            )

        if category_id:
            query = query.filter(Product.category_id == category_id)

        if stock_filter == "out":
            query = query.filter(Product.stock_quantity <= 0)
        elif stock_filter == "low":
            query = query.filter(
                Product.stock_quantity > 0,
                Product.stock_quantity <= LOW_STOCK_THRESHOLD,
            )
        elif stock_filter == "in_stock":
            query = query.filter(Product.stock_quantity > LOW_STOCK_THRESHOLD)

        return query.order_by(Product.name.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def search_for_sale(shop_id, query_text, limit=15):
        if not query_text or not query_text.strip():
            return []

        term = f"%{query_text.strip()}%"
        return (
            Product.query.filter_by(shop_id=shop_id)
            .filter(
                or_(
                    Product.name.ilike(term),
                    Product.barcode.ilike(term),
                    Product.sku.ilike(term),
                )
            )
            .filter(Product.stock_quantity > 0)
            .order_by(Product.name.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get(shop_id, product_id):
        return (
            Product.query.filter_by(shop_id=shop_id, id=product_id)
            .options(joinedload(Product.category), joinedload(Product.supplier))
            .first()
        )

    @staticmethod
    def create(shop_id, form, can_edit_minimum=False):
        market_price = form.market_price.data
        minimum_price = (
            form.minimum_selling_price.data
            if can_edit_minimum and form.minimum_selling_price.data is not None
            else form.cost_price.data
        )

        product = Product(
            shop_id=shop_id,
            category_id=form.category_id.data,
            supplier_id=form.supplier_id.data,
            name=form.name.data.strip(),
            barcode=(form.barcode.data or "").strip() or None,
            sku=(form.sku.data or "").strip() or None,
            cost_price=form.cost_price.data,
            default_selling_price=market_price,
            market_price=market_price,
            minimum_selling_price=minimum_price,
            stock_quantity=form.stock_quantity.data or 0,
            expiry_date=form.expiry_date.data,
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update(product, form, can_edit_minimum=False):
        market_price = form.market_price.data
        product.category_id = form.category_id.data
        product.supplier_id = form.supplier_id.data
        product.name = form.name.data.strip()
        product.barcode = (form.barcode.data or "").strip() or None
        product.sku = (form.sku.data or "").strip() or None
        product.cost_price = form.cost_price.data
        product.market_price = market_price
        product.default_selling_price = market_price
        if can_edit_minimum and form.minimum_selling_price.data is not None:
            product.minimum_selling_price = form.minimum_selling_price.data
        product.stock_quantity = form.stock_quantity.data or 0
        product.expiry_date = form.expiry_date.data
        db.session.commit()
        return product

    @staticmethod
    def delete(product):
        name = product.name
        db.session.delete(product)
        db.session.commit()
        return True, f'Product "{name}" deleted successfully.'
