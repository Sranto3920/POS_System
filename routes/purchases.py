from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models.product import Product
from models.supplier import Supplier
from services.purchase_service import PurchaseService
from utils.decorators import role_required, shop_user_required
from utils.pagination import PER_PAGE_DEFAULT, get_page, get_search
from utils.roles import Role

purchases_bp = Blueprint("purchases", __name__, url_prefix="/purchases")


def _parse_purchase_items():
    product_ids = request.form.getlist("product_id[]")
    quantities = request.form.getlist("quantity[]")
    cost_prices = request.form.getlist("cost_price[]")

    items = []
    for product_id, quantity, cost_price in zip(product_ids, quantities, cost_prices):
        if not product_id or not quantity or not cost_price:
            continue
        try:
            items.append(
                {
                    "product_id": int(product_id),
                    "quantity": int(quantity),
                    "cost_price": Decimal(cost_price),
                }
            )
        except (ValueError, InvalidOperation):
            continue
    return items


@purchases_bp.route("/")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER)
def purchases_index():
    shop_id = current_user.shop_id
    service = PurchaseService(shop_id)
    search_q = get_search()
    pagination = service.list_purchases(
        page=get_page(), per_page=PER_PAGE_DEFAULT, search=search_q
    )
    return render_template(
        "purchases/index.html",
        pagination=pagination,
        purchases=pagination.items,
        search_q=search_q,
    )


@purchases_bp.route("/new", methods=["GET", "POST"])
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER)
def new():
    shop_id = current_user.shop_id
    suppliers = (
        Supplier.query.filter_by(shop_id=shop_id).order_by(Supplier.name.asc()).all()
    )
    products = (
        Product.query.filter_by(shop_id=shop_id).order_by(Product.name.asc()).all()
    )

    if request.method == "POST":
        supplier_id = request.form.get("supplier_id", type=int)
        items = _parse_purchase_items()

        if not supplier_id:
            flash("Please select a supplier.", "danger")
            return render_template(
                "purchases/new.html", suppliers=suppliers, products=products
            )

        if not items:
            flash("Add at least one product line.", "danger")
            return render_template(
                "purchases/new.html", suppliers=suppliers, products=products
            )

        try:
            service = PurchaseService(shop_id)
            purchase = service.create_purchase(
                shop_id, current_user.id, supplier_id, items
            )
            flash(f"Purchase #{purchase.id} recorded successfully.", "success")
            return redirect(url_for("purchases.view", purchase_id=purchase.id))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template(
        "purchases/new.html", suppliers=suppliers, products=products
    )


@purchases_bp.route("/<int:purchase_id>")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER)
def view(purchase_id):
    service = PurchaseService(current_user.shop_id)
    purchase = service.get_purchase(purchase_id)
    if purchase is None:
        flash("Purchase not found.", "warning")
        return redirect(url_for("purchases.purchases_index"))
    return render_template("purchases/view.html", purchase=purchase)
