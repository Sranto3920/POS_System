from functools import wraps

from flask import abort, redirect, request, url_for
from flask_login import current_user

from models.platform_user import PlatformUser
from utils.roles import Role


def role_required(*roles):
    """Restrict a shop view to one or more roles. User must be a shop user."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if isinstance(current_user, PlatformUser):
                abort(403)
            if not Role.matches(current_user.role, *roles):
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def platform_required(view_func):
    """
    Restrict a view to authenticated platform owners only.
    Shop users and anonymous visitors are denied.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("platform_auth.login", next=request.url))
        if not isinstance(current_user, PlatformUser):
            abort(403)
        if not current_user.is_active:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def shop_user_required(view_func):
    """Ensure the current user is a shop staff member, not a platform owner."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.url))
        if isinstance(current_user, PlatformUser):
            return redirect(url_for("platform.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped
