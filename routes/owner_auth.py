"""Platform / software owner login at /owner/login."""

from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from extensions import db
from forms.platform_forms import PlatformLoginForm
from models.platform_user import PlatformUser
from utils.i18n import t
from utils.login_security import is_login_locked, log_login_attempt

owner_auth_bp = Blueprint("owner_auth", __name__, url_prefix="/owner")


@owner_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and isinstance(current_user, PlatformUser):
        return redirect(url_for("platform.dashboard"))

    form = PlatformLoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if is_login_locked(email, login_type="owner"):
            flash(t("msg.login_locked"), "danger")
            log_login_attempt(email, False, login_type="owner")
            return render_template("auth/owner_login.html", form=form, login_error=True), 429

        user = PlatformUser.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            log_login_attempt(email, False, login_type="owner")
            flash(t("msg.login_failed_retry"), "danger")
            return render_template("auth/owner_login.html", form=form, login_error=True), 401

        if not user.is_active:
            log_login_attempt(email, False, login_type="owner")
            flash(t("msg.account_deactivated"), "warning")
            return render_template("auth/owner_login.html", form=form), 403

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        log_login_attempt(email, True, login_type="owner")
        login_user(user, remember=form.remember_me.data)
        flash(t("msg.welcome", name=user.full_name), "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/platform"):
            return redirect(next_page)

        return redirect(url_for("platform.dashboard"))

    return render_template("auth/owner_login.html", form=form)


@owner_auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated and isinstance(current_user, PlatformUser):
        logout_user()
    flash(t("msg.logout_success"), "info")
    return redirect(url_for("owner_auth.login"))
