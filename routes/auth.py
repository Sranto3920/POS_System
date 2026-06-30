from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from forms.auth_forms import LoginForm
from models.platform_user import PlatformUser
from models.shop import Shop
from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if isinstance(current_user, PlatformUser):
            return redirect(url_for("platform.dashboard"))
        return redirect(url_for("dashboard.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form), 401

        if not user.is_active:
            flash(
                "Your account has been deactivated. Contact your shop administrator.",
                "warning",
            )
            return render_template("auth/login.html", form=form), 403

        shop = db.session.get(Shop, user.shop_id)
        if shop is None or not shop.is_active:
            flash(
                "Your shop account is inactive. Please contact the platform support.",
                "warning",
            )
            return render_template("auth/login.html", form=form), 403

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.full_name}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/") and not next_page.startswith("//"):
            if not next_page.startswith("/platform"):
                return redirect(next_page)

        return redirect(url_for("dashboard.dashboard"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
