from sqlalchemy import or_

from extensions import db
from models.product import Product
from models.supplier import Supplier
from utils.pagination import PER_PAGE_DEFAULT


class SupplierService:
    @staticmethod
    def list(shop_id, search="", page=1, per_page=PER_PAGE_DEFAULT):
        query = Supplier.query.filter_by(shop_id=shop_id)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Supplier.name.ilike(term),
                    Supplier.phone.ilike(term),
                    Supplier.email.ilike(term),
                    Supplier.address.ilike(term),
                )
            )

        return query.order_by(Supplier.name.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get(shop_id, supplier_id):
        return Supplier.query.filter_by(shop_id=shop_id, id=supplier_id).first()

    @staticmethod
    def create(shop_id, form):
        supplier = Supplier(
            shop_id=shop_id,
            name=form.name.data.strip(),
            phone=(form.phone.data or "").strip() or None,
            email=(form.email.data or "").strip().lower() or None,
            address=(form.address.data or "").strip() or None,
        )
        db.session.add(supplier)
        db.session.commit()
        return supplier

    @staticmethod
    def update(supplier, form):
        supplier.name = form.name.data.strip()
        supplier.phone = (form.phone.data or "").strip() or None
        supplier.email = (form.email.data or "").strip().lower() or None
        supplier.address = (form.address.data or "").strip() or None
        db.session.commit()
        return supplier

    @staticmethod
    def delete(supplier):
        if Product.query.filter_by(supplier_id=supplier.id).first():
            return False, "Cannot delete supplier with existing products."

        db.session.delete(supplier)
        db.session.commit()
        return True, f'Supplier "{supplier.name}" deleted successfully.'
