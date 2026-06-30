from sqlalchemy import or_

from extensions import db
from models.category import Category
from models.product import Product
from utils.pagination import PER_PAGE_DEFAULT


class CategoryService:
    @staticmethod
    def list(shop_id, search="", page=1, per_page=PER_PAGE_DEFAULT):
        query = Category.query.filter_by(shop_id=shop_id)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Category.name.ilike(term),
                    Category.description.ilike(term),
                )
            )

        return query.order_by(Category.name.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get(shop_id, category_id):
        return Category.query.filter_by(shop_id=shop_id, id=category_id).first()

    @staticmethod
    def create(shop_id, form):
        category = Category(
            shop_id=shop_id,
            name=form.name.data.strip(),
            description=(form.description.data or "").strip() or None,
        )
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def update(category, form):
        category.name = form.name.data.strip()
        category.description = (form.description.data or "").strip() or None
        db.session.commit()
        return category

    @staticmethod
    def delete(category):
        if Product.query.filter_by(category_id=category.id).first():
            return False, "Cannot delete category with existing products."

        db.session.delete(category)
        db.session.commit()
        return True, f'Category "{category.name}" deleted successfully.'
