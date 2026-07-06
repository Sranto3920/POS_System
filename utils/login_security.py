from datetime import datetime, timedelta, timezone

from flask import request

from extensions import db
from models.login_attempt import LoginAttempt

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def count_recent_failures(email, login_type="shop"):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)
    return (
        LoginAttempt.query.filter(
            LoginAttempt.email == email.lower(),
            LoginAttempt.login_type == login_type,
            LoginAttempt.success.is_(False),
            LoginAttempt.attempted_at >= cutoff,
        ).count()
    )


def is_login_locked(email, login_type="shop"):
    return count_recent_failures(email, login_type) >= MAX_FAILED_ATTEMPTS


def log_login_attempt(email, success, login_type="shop"):
    attempt = LoginAttempt(
        email=email.lower(),
        ip_address=get_client_ip(),
        login_type=login_type,
        success=success,
    )
    db.session.add(attempt)
    db.session.commit()
