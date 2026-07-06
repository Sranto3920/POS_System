from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from utils.roles import Role


class User(UserMixin, db.Model):
    """Shop staff user — Admin, Manager, or Cashier within one shop."""

    __tablename__ = "Users"

    id = db.Column("user_id", db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("Shops.shop_id"), nullable=False)
    full_name = db.Column("name", db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column("password", db.String(255), nullable=False)
    login_password = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False, default=Role.CASHIER)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    preferred_language = db.Column(db.String(5), nullable=False, default="bn")
    created_at = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)

    shop = db.relationship("Shop", backref=db.backref("users", lazy="dynamic"))

    def get_id(self):
        """Prefix shop user IDs so Flask-Login can distinguish from platform users."""
        return f"s:{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.login_password = password

    @property
    def shop_login_password(self):
        """Recoverable login password (shop owner / platform owner support)."""
        return self.login_password

    def check_password(self, password):
        stored = self.password_hash or ""

        if stored.startswith(("pbkdf2:", "scrypt:")):
            return check_password_hash(stored, password)

        # Upgrade legacy plaintext passwords on successful login.
        if stored == password:
            self.set_password(password)
            db.session.commit()
            return True

        return False

    def has_role(self, *roles):
        return Role.matches(self.role, *roles)

    @property
    def is_platform_user(self):
        return False

    @property
    def role_label(self):
        return Role.label(self.role)

    @property
    def normalized_role(self):
        return Role.normalize(self.role)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
