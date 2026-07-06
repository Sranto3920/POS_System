"""
Platform authentication — /platform/login redirects to /owner/login.
"""

from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, logout_user

from models.platform_user import PlatformUser
from utils.i18n import t

platform_auth_bp = Blueprint("platform_auth", __name__, url_prefix="/platform")


@platform_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    return redirect(url_for("owner_auth.login", **request.args))


@platform_auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated and isinstance(current_user, PlatformUser):
        logout_user()
    flash(t("msg.logout_success"), "info")
    return redirect(url_for("owner_auth.login"))
