"""
ShopService — business logic for platform owner shop management.

Handles shop creation (with first Admin user), updates, and status toggling.
All writes are wrapped in database transactions.
"""

from datetime import datetime, timezone

from sqlalchemy import desc, func

from extensions import db
from models.shop import Shop
from models.user import User
from utils.roles import Role


class ShopService:
    @staticmethod
    def get_all_shops():
        """Return all shops ordered by newest first."""
        return Shop.query.order_by(desc(Shop.created_at), desc(Shop.id)).all()

    @staticmethod
    def get_shop(shop_id):
        return db.session.get(Shop, shop_id)

    @staticmethod
    def get_shop_admin(shop_id):
        """Return the primary Admin user for a shop."""
        return (
            User.query.filter_by(shop_id=shop_id)
            .filter(func.lower(User.role) == Role.ADMIN)
            .order_by(User.id.asc())
            .first()
        )

    @staticmethod
    def create_shop_with_admin(form):
        """
        Create a new shop and its first Admin user in a single transaction.

        Returns the created Shop on success.
        Raises ValueError on duplicate email (safety net beyond form validation).
        """
        shop_email = form.email.data.strip().lower()
        admin_email = form.admin_email.data.strip().lower()

        if Shop.query.filter_by(email=shop_email).first():
            raise ValueError("A shop with this email already exists.")

        if User.query.filter_by(email=admin_email).first():
            raise ValueError("This admin email is already registered.")

        try:
            shop = Shop(
                shop_name=form.shop_name.data.strip(),
                owner_name=form.owner_name.data.strip(),
                phone=form.phone.data.strip(),
                email=shop_email,
                address=form.address.data.strip(),
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(shop)
            db.session.flush()

            admin = User(
                shop_id=shop.id,
                full_name=form.admin_name.data.strip(),
                email=admin_email,
                role=Role.ADMIN,
                phone=form.phone.data.strip(),
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            admin.set_password(form.admin_password.data)
            db.session.add(admin)

            db.session.commit()
            return shop

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_shop(shop, form):
        """Update shop profile fields."""
        shop.shop_name = form.shop_name.data.strip()
        shop.owner_name = form.owner_name.data.strip()
        shop.phone = form.phone.data.strip()
        shop.email = form.email.data.strip().lower()
        shop.address = form.address.data.strip()
        db.session.commit()
        return shop

    @staticmethod
    def toggle_status(shop):
        """Activate or deactivate a shop."""
        shop.is_active = not shop.is_active
        db.session.commit()
        return shop

    @staticmethod
    def count_shops():
        return Shop.query.count()

    @staticmethod
    def count_active_shops():
        return Shop.query.filter_by(is_active=True).count()

    @staticmethod
    def reset_shop_admin_password(shop_id, password):
        admin = ShopService.get_shop_admin(shop_id)
        if admin is None:
            raise ValueError("No shop admin account found for this shop.")
        admin.set_password(password)
        db.session.commit()
        return admin

    @staticmethod
    def get_shop_credentials():
        """Shop admin login details for platform owner profile."""
        rows = []
        for shop in ShopService.get_all_shops():
            admin = ShopService.get_shop_admin(shop.id)
            rows.append(
                {
                    "shop": shop,
                    "admin": admin,
                    "login_email": admin.email if admin else None,
                    "login_password": admin.shop_login_password if admin else None,
                }
            )
        return rows
