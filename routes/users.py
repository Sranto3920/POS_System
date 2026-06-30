from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from forms.user_forms import PasswordForm, UserForm
from services.user_service import UserService
from utils.decorators import role_required, shop_user_required
from utils.roles import Role

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/")
@shop_user_required
@role_required(Role.ADMIN)
def users_index():
    users = UserService.list_users(current_user.shop_id)
    return render_template("users/index.html", users=users)


@users_bp.route("/add", methods=["GET", "POST"])
@shop_user_required
@role_required(Role.ADMIN)
def users_add():
    form = UserForm()
    password_form = PasswordForm()

    if form.validate_on_submit() and password_form.validate_on_submit():
        try:
            user = UserService.create_user(
                current_user.shop_id,
                form,
                password_form.password.data,
            )
            flash(f'User "{user.full_name}" created successfully.', "success")
            return redirect(url_for("users.users_index"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template(
        "users/form.html",
        form=form,
        password_form=password_form,
        title="Add User",
        submit_label="Create User",
        is_edit=False,
    )


@users_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@shop_user_required
@role_required(Role.ADMIN)
def users_edit(user_id):
    user = UserService.get_user(current_user.shop_id, user_id)
    if user is None:
        flash("User not found.", "warning")
        return redirect(url_for("users.users_index"))

    if Role.normalize(user.role) == Role.ADMIN:
        flash("Administrator accounts cannot be edited here.", "warning")
        return redirect(url_for("users.users_index"))

    form = UserForm(user_id=user.id, obj=user)

    if form.validate_on_submit():
        try:
            UserService.update_user(current_user.shop_id, user_id, form)
            flash(f'User "{form.full_name.data}" updated successfully.', "success")
            return redirect(url_for("users.users_index"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template(
        "users/form.html",
        form=form,
        password_form=None,
        title="Edit User",
        submit_label="Save Changes",
        is_edit=True,
        user=user,
    )


@users_bp.route("/delete/<int:user_id>", methods=["POST"])
@shop_user_required
@role_required(Role.ADMIN)
def users_delete(user_id):
    try:
        UserService.delete_user(current_user.shop_id, user_id, current_user.id)
        flash("User deleted successfully.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("users.users_index"))


@users_bp.route("/toggle-status/<int:user_id>", methods=["POST"])
@shop_user_required
@role_required(Role.ADMIN)
def users_toggle_status(user_id):
    try:
        user = UserService.toggle_active(
            current_user.shop_id, user_id, current_user.id
        )
        status = "activated" if user.is_active else "deactivated"
        flash(f'User "{user.full_name}" {status}.', "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("users.users_index"))


@users_bp.route("/reset-password/<int:user_id>", methods=["GET", "POST"])
@shop_user_required
@role_required(Role.ADMIN)
def users_reset_password(user_id):
    user = UserService.get_user(current_user.shop_id, user_id)
    if user is None:
        flash("User not found.", "warning")
        return redirect(url_for("users.users_index"))

    form = PasswordForm()

    if form.validate_on_submit():
        try:
            UserService.reset_password(
                current_user.shop_id, user_id, form.password.data
            )
            flash(f'Password reset for "{user.full_name}".', "success")
            return redirect(url_for("users.users_index"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("users/reset_password.html", form=form, user=user)
