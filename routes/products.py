from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from forms.product_forms import ProductForm
from models.category import Category
from services.product_service import ProductService
from utils.decorators import manager_or_owner_required, shop_user_required
from utils.pagination import get_page, get_search
from utils.roles import Role

products_bp = Blueprint("products", __name__, url_prefix="/products")


def _can_manage_products():
    return current_user.has_role(Role.ADMIN, Role.MANAGER)


def _can_edit_minimum_price():
    return current_user.has_role(Role.ADMIN)


def _get_category_filter():
    raw = request.args.get("category_id", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _get_stock_filter():
    value = request.args.get("stock", "all").strip().lower()
    if value in ("all", "in_stock", "low", "out"):
        return value
    return "all"


@products_bp.route("/")
@shop_user_required
def products_index():
    page = get_page()
    search = get_search()
    category_id = _get_category_filter()
    stock_filter = _get_stock_filter()

    pagination = ProductService.list(
        current_user.shop_id,
        search=search,
        category_id=category_id,
        stock_filter=stock_filter,
        page=page,
    )

    categories = (
        Category.query.filter_by(shop_id=current_user.shop_id)
        .order_by(Category.name.asc())
        .all()
    )

    return render_template(
        "products/index.html",
        user=current_user,
        pagination=pagination,
        products=pagination.items,
        search_q=search,
        categories=categories,
        category_id=category_id,
        stock_filter=stock_filter,
        extra_args={"category_id": category_id or "", "stock": stock_filter},
        can_edit_minimum=_can_edit_minimum_price(),
        can_manage_products=_can_manage_products(),
    )


@products_bp.route("/add", methods=["GET", "POST"])
@shop_user_required
@manager_or_owner_required
def add():
    can_edit_minimum = _can_edit_minimum_price()
    form = ProductForm(
        shop_id=current_user.shop_id,
        show_minimum_price=can_edit_minimum,
    )

    if form.validate_on_submit():
        product = ProductService.create(
            current_user.shop_id,
            form,
            can_edit_minimum=can_edit_minimum,
        )
        flash(f'Product "{product.name}" created successfully.', "success")
        return redirect(url_for("products.products_index"))

    return render_template(
        "products/form.html",
        user=current_user,
        form=form,
        title="Add Product",
        submit_label="Create Product",
        can_edit_minimum=can_edit_minimum,
    )


@products_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
@shop_user_required
@manager_or_owner_required
def edit(product_id):
    product = ProductService.get(current_user.shop_id, product_id)
    if product is None:
        flash("Product not found.", "warning")
        return redirect(url_for("products.products_index"))

    can_edit_minimum = _can_edit_minimum_price()
    form = ProductForm(
        shop_id=current_user.shop_id,
        show_minimum_price=can_edit_minimum,
        obj=product,
    )
    if product.market_price is None:
        form.market_price.data = product.default_selling_price
    if can_edit_minimum and product.minimum_selling_price is None:
        form.minimum_selling_price.data = product.cost_price

    if form.validate_on_submit():
        ProductService.update(
            product,
            form,
            can_edit_minimum=can_edit_minimum,
        )
        flash(f'Product "{product.name}" updated successfully.', "success")
        return redirect(url_for("products.products_index"))

    return render_template(
        "products/form.html",
        user=current_user,
        form=form,
        product=product,
        title="Edit Product",
        submit_label="Save Changes",
        can_edit_minimum=can_edit_minimum,
    )


@products_bp.route("/delete/<int:product_id>", methods=["POST"])
@shop_user_required
@manager_or_owner_required
def delete(product_id):
    product = ProductService.get(current_user.shop_id, product_id)
    if product is None:
        flash("Product not found.", "warning")
        return redirect(url_for("products.products_index"))

    success, message = ProductService.delete(product)
    flash(message, "success" if success else "danger")
    return redirect(url_for("products.products_index"))
