"""
UserService — shop-scoped staff user management.

Admins can create and manage Managers and Cashiers within their shop.
"""

from datetime import datetime, timezone

from extensions import db
from models.user import User
from utils.roles import Role


class UserService:
    @staticmethod
    def list_users(shop_id):
        return (
            User.query.filter_by(shop_id=shop_id)
            .order_by(User.created_at.desc(), User.id.desc())
            .all()
        )

    @staticmethod
    def get_user(shop_id, user_id):
        return User.query.filter_by(shop_id=shop_id, id=user_id).first()

    @staticmethod
    def create_user(shop_id, form, password):
        role = Role.normalize(form.role.data)
        if role == Role.ADMIN:
            raise ValueError("Cannot create an Administrator account.")

        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            raise ValueError("This email is already registered.")

        user = User(
            shop_id=shop_id,
            full_name=form.full_name.data.strip(),
            email=email,
            phone=(form.phone.data or "").strip() or None,
            role=role,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user(shop_id, user_id, form):
        user = UserService.get_user(shop_id, user_id)
        if user is None:
            raise ValueError("User not found.")

        if Role.normalize(user.role) == Role.ADMIN:
            raise ValueError("Administrator accounts cannot be edited here.")

        role = Role.normalize(form.role.data)
        if role == Role.ADMIN:
            raise ValueError("Cannot assign Administrator role.")

        email = form.email.data.strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            raise ValueError("This email is already registered.")

        user.full_name = form.full_name.data.strip()
        user.email = email
        user.phone = (form.phone.data or "").strip() or None
        user.role = role
        db.session.commit()
        return user

    @staticmethod
    def delete_user(shop_id, user_id, current_user_id):
        if user_id == current_user_id:
            raise ValueError("You cannot delete your own account.")

        user = UserService.get_user(shop_id, user_id)
        if user is None:
            raise ValueError("User not found.")

        if Role.normalize(user.role) == Role.ADMIN:
            raise ValueError("Administrator accounts cannot be deleted.")

        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def toggle_active(shop_id, user_id, current_user_id):
        if user_id == current_user_id:
            raise ValueError("You cannot deactivate your own account.")

        user = UserService.get_user(shop_id, user_id)
        if user is None:
            raise ValueError("User not found.")

        if Role.normalize(user.role) == Role.ADMIN:
            raise ValueError("Administrator status cannot be toggled.")

        user.is_active = not user.is_active
        db.session.commit()
        return user

    @staticmethod
    def reset_password(shop_id, user_id, password):
        user = UserService.get_user(shop_id, user_id)
        if user is None:
            raise ValueError("User not found.")

        user.set_password(password)
        db.session.commit()
        return user
