from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from models.customer import Customer
from models.payment import PAYMENT_METHODS, Payment
from services.product_service import ProductService
from services.sale_service import SaleService
from utils.decorators import role_required, shop_user_required
from utils.i18n import t
from utils.pagination import PER_PAGE_DEFAULT, get_page, get_search
from utils.roles import Role

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


def _parse_sale_items():
    product_ids = request.form.getlist("product_id[]")
    quantities = request.form.getlist("quantity[]")
    selling_prices = request.form.getlist("selling_price[]")
    discounts = request.form.getlist("discount[]")

    items = []
    for index, product_id in enumerate(product_ids):
        quantity = quantities[index] if index < len(quantities) else ""
        selling_price = selling_prices[index] if index < len(selling_prices) else ""
        discount = discounts[index] if index < len(discounts) else "0"

        if not product_id or not quantity or selling_price == "":
            continue
        try:
            items.append(
                {
                    "product_id": int(product_id),
                    "quantity": int(quantity),
                    "selling_price": Decimal(selling_price),
                    "discount": Decimal(discount or "0"),
                }
            )
        except (ValueError, InvalidOperation):
            continue
    return items


@sales_bp.route("/")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def sales_index():
    shop_id = current_user.shop_id
    service = SaleService(shop_id)
    search_q = get_search()
    pagination = service.list_sales(
        page=get_page(), per_page=PER_PAGE_DEFAULT, search=search_q
    )
    return render_template(
        "sales/index.html",
        pagination=pagination,
        sales=pagination.items,
        search_q=search_q,
        sale_service=service,
    )


@sales_bp.route("/api/products/search")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def search_products():
    query_text = request.args.get("q", "").strip()
    products = ProductService.search_for_sale(current_user.shop_id, query_text)
    return jsonify(
        [
            {
                "id": product.id,
                "name": product.name,
                "barcode": product.barcode,
                "sku": product.sku,
                "stock": product.stock_quantity or 0,
                "market_price": float(product.effective_market_price),
            }
            for product in products
        ]
    )


@sales_bp.route("/new", methods=["GET", "POST"])
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def sales_new():
    shop_id = current_user.shop_id
    service = SaleService(shop_id)
    walkin = service.get_or_create_walkin_customer(shop_id)
    customers = (
        Customer.query.filter_by(shop_id=shop_id).order_by(Customer.name.asc()).all()
    )

    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        payment_method = request.form.get("payment_method", "").strip()
        paid_amount = request.form.get("paid_amount", "")
        items = _parse_sale_items()

        if not customer_id:
            flash(t("msg.select_customer"), "danger")
            return render_template(
                "sales/new.html",
                customers=customers,
                payment_methods=PAYMENT_METHODS,
                walkin_customer_id=walkin.id,
            )

        if not items:
            flash(t("msg.add_product_line"), "danger")
            return render_template(
                "sales/new.html",
                customers=customers,
                payment_methods=PAYMENT_METHODS,
                walkin_customer_id=walkin.id,
            )

        try:
            sale = service.create_sale(
                shop_id,
                current_user.id,
                customer_id,
                items,
                payment_method,
                paid_amount,
            )
            flash(t("msg.sale_success", id=sale.id), "success")
            return redirect(url_for("sales.view", sale_id=sale.id))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template(
        "sales/new.html",
        customers=customers,
        payment_methods=PAYMENT_METHODS,
        walkin_customer_id=walkin.id,
    )


@sales_bp.route("/<int:sale_id>")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def view(sale_id):
    service = SaleService(current_user.shop_id)
    sale = service.get_sale(sale_id)
    if sale is None:
        flash(t("msg.not_found"), "warning")
        return redirect(url_for("sales.sales_index"))

    paid_total = service.get_sale_paid_total(sale)
    balance_due = service.get_sale_balance_due(sale)
    payments = sale.payments.order_by(Payment.payment_date.desc()).all()
    return render_template(
        "sales/view.html",
        sale=sale,
        paid_total=paid_total,
        balance_due=balance_due,
        payments=payments,
    )
