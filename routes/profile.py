from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from forms.auth_forms import ChangePasswordForm
from services.user_service import UserService
from utils.decorators import owner_required, shop_user_required
from utils.i18n import t
from utils.roles import Role

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@shop_user_required
def index():
    from extensions import db
    from models.shop import Shop

    shop = db.session.get(Shop, current_user.shop_id)
    staff_users = []
    if current_user.has_role(Role.ADMIN):
        staff_users = [
            u
            for u in UserService.list_users(current_user.shop_id)
            if u.normalized_role != Role.ADMIN
        ]
    return render_template(
        "profile/index.html",
        user=current_user,
        shop=shop,
        staff_users=staff_users,
    )


@profile_bp.route("/change-password", methods=["GET", "POST"])
@shop_user_required
@owner_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash(t("msg.wrong_password"), "danger")
            return render_template("profile/change_password.html", form=form)

        try:
            UserService.reset_password(
                current_user.shop_id, current_user.id, form.new_password.data
            )
            flash(t("msg.password_changed"), "success")
            return redirect(url_for("profile.index"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("profile/change_password.html", form=form)
