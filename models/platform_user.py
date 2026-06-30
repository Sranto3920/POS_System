"""
PlatformUser model — represents the software owner (you).

Stored in Platform_Users, separate from shop staff in Users.
Only platform users can access /platform/* routes.
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class PlatformUser(UserMixin, db.Model):
    __tablename__ = "Platform_Users"

    id = db.Column("platform_user_id", db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_login = db.Column(db.DateTime)

    def get_id(self):
        """Prefix platform IDs so Flask-Login can distinguish from shop users."""
        return f"p:{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_platform_user(self):
        return True

    def __repr__(self):
        return f"<PlatformUser {self.email}>"
