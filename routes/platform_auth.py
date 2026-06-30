"""
Platform authentication routes — login and logout for the software owner.

URL prefix: /platform
Shop staff use /login instead.
"""

from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from extensions import db
from forms.platform_forms import PlatformLoginForm
from models.platform_user import PlatformUser

platform_auth_bp = Blueprint("platform_auth", __name__, url_prefix="/platform")


@platform_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and isinstance(current_user, PlatformUser):
        return redirect(url_for("platform.dashboard"))

    form = PlatformLoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = PlatformUser.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("platform/login.html", form=form), 401

        if not user.is_active:
            flash("Your platform account has been deactivated.", "warning")
            return render_template("platform/login.html", form=form), 403

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome, {user.full_name}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/platform"):
            return redirect(next_page)

        return redirect(url_for("platform.dashboard"))

    return render_template("platform/login.html", form=form)


@platform_auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated and isinstance(current_user, PlatformUser):
        logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("platform_auth.login"))
