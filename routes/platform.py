"""
Platform owner routes — shop management dashboard.

All routes require platform owner authentication via @platform_required.
Shop staff cannot access these URLs.
"""

from flask import Blueprint, flash, redirect, render_template, url_for

from forms.shop_forms import CreateShopForm, EditShopForm
from forms.user_forms import PasswordForm
from services.shop_service import ShopService
from utils.decorators import platform_required

platform_bp = Blueprint("platform", __name__, url_prefix="/platform")


@platform_bp.route("/")
@platform_bp.route("/dashboard")
@platform_required
def dashboard():
    shops = ShopService.get_all_shops()
    return render_template(
        "platform/dashboard.html",
        shops=shops,
        total_shops=ShopService.count_shops(),
        active_shops=ShopService.count_active_shops(),
    )


@platform_bp.route("/shops/create", methods=["GET", "POST"])
@platform_required
def create_shop():
    form = CreateShopForm()

    if form.validate_on_submit():
        try:
            shop = ShopService.create_shop_with_admin(form)
            flash(
                f'Shop "{shop.shop_name}" created successfully with admin account.',
                "success",
            )
            return redirect(url_for("platform.dashboard"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            flash("An unexpected error occurred while creating the shop.", "danger")

    return render_template("platform/shops/create.html", form=form)


@platform_bp.route("/profile")
@platform_required
def profile():
    from flask_login import current_user

    return render_template(
        "platform/profile.html",
        shop_credentials=ShopService.get_shop_credentials(),
        platform_user=current_user,
    )


@platform_bp.route("/shops/<int:shop_id>")
@platform_required
def view_shop(shop_id):
    shop = ShopService.get_shop(shop_id)
    if shop is None:
        flash("Shop not found.", "warning")
        return redirect(url_for("platform.dashboard"))

    admin = ShopService.get_shop_admin(shop_id)
    return render_template("platform/shops/view.html", shop=shop, admin=admin)


@platform_bp.route("/shops/<int:shop_id>/reset-admin-password", methods=["GET", "POST"])
@platform_required
def reset_shop_admin_password(shop_id):
    shop = ShopService.get_shop(shop_id)
    if shop is None:
        flash("Shop not found.", "warning")
        return redirect(url_for("platform.dashboard"))

    admin = ShopService.get_shop_admin(shop_id)
    if admin is None:
        flash("No shop admin account found.", "warning")
        return redirect(url_for("platform.view_shop", shop_id=shop_id))

    form = PasswordForm()
    if form.validate_on_submit():
        try:
            ShopService.reset_shop_admin_password(shop_id, form.password.data)
            flash(
                f'Login password reset for "{admin.full_name}" ({admin.email}). '
                f"It is now visible on your Platform Profile.",
                "success",
            )
            return redirect(url_for("platform.view_shop", shop_id=shop_id))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template(
        "platform/shops/reset_admin_password.html",
        form=form,
        shop=shop,
        admin=admin,
    )


@platform_bp.route("/shops/<int:shop_id>/edit", methods=["GET", "POST"])
@platform_required
def edit_shop(shop_id):
    shop = ShopService.get_shop(shop_id)
    if shop is None:
        flash("Shop not found.", "warning")
        return redirect(url_for("platform.dashboard"))

    form = EditShopForm(shop_id=shop.id, obj=shop)

    if form.validate_on_submit():
        ShopService.update_shop(shop, form)
        flash(f'Shop "{shop.shop_name}" updated successfully.', "success")
        return redirect(url_for("platform.view_shop", shop_id=shop.id))

    return render_template("platform/shops/edit.html", form=form, shop=shop)


@platform_bp.route("/shops/<int:shop_id>/toggle-status", methods=["POST"])
@platform_required
def toggle_shop_status(shop_id):
    shop = ShopService.get_shop(shop_id)
    if shop is None:
        flash("Shop not found.", "warning")
        return redirect(url_for("platform.dashboard"))

    shop = ShopService.toggle_status(shop)
    status = "activated" if shop.is_active else "deactivated"
    flash(f'Shop "{shop.shop_name}" has been {status}.', "success")
    return redirect(url_for("platform.dashboard"))
