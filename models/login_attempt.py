from datetime import datetime, timezone

from extensions import db


class LoginAttempt(db.Model):
    __tablename__ = "LoginAttempts"

    id = db.Column("attempt_id", db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    login_type = db.Column(db.String(20), nullable=False, default="shop")
    success = db.Column(db.Boolean, nullable=False, default=False)
    attempted_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
