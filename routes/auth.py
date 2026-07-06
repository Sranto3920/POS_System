from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from forms.auth_forms import LoginForm
from models.platform_user import PlatformUser
from models.shop import Shop
from models.user import User
from utils.i18n import normalize_lang, set_lang, t
from utils.login_security import is_login_locked, log_login_attempt
from utils.roles import Role

auth_bp = Blueprint("auth", __name__)


def _redirect_for_role(user):
    role = Role.normalize(user.role)
    if role == Role.CASHIER:
        return url_for("dashboard.dashboard")
    if role == Role.MANAGER:
        return url_for("dashboard.dashboard")
    return url_for("dashboard.dashboard")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if isinstance(current_user, PlatformUser):
            return redirect(url_for("platform.dashboard"))
        return redirect(_redirect_for_role(current_user))

    form = LoginForm()
    login_error = False

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if is_login_locked(email, login_type="shop"):
            flash(t("msg.login_locked"), "danger")
            log_login_attempt(email, False, login_type="shop")
            return render_template(
                "auth/login.html", form=form, login_error=True
            ), 429

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            log_login_attempt(email, False, login_type="shop")
            flash(t("msg.login_failed_retry"), "danger")
            return render_template(
                "auth/login.html", form=form, login_error=True
            ), 401

        if not user.is_active:
            log_login_attempt(email, False, login_type="shop")
            flash(t("msg.account_deactivated"), "warning")
            return render_template("auth/login.html", form=form), 403

        shop = db.session.get(Shop, user.shop_id)
        if shop is None or not shop.is_active:
            log_login_attempt(email, False, login_type="shop")
            flash(t("msg.shop_inactive"), "warning")
            return render_template("auth/login.html", form=form), 403

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        pref = getattr(user, "preferred_language", None) or request.cookies.get("lang")
        set_lang(normalize_lang(pref or "bn"), user)

        log_login_attempt(email, True, login_type="shop")
        login_user(user, remember=form.remember_me.data)
        flash(t("msg.welcome", name=user.full_name), "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/") and not next_page.startswith("//"):
            if not next_page.startswith(("/platform", "/owner")):
                return redirect(next_page)

        return redirect(_redirect_for_role(user))

    return render_template("auth/login.html", form=form, login_error=login_error)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash(t("msg.logout_success"), "info")
    return redirect(url_for("auth.login"))
