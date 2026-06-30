from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models.payment import PAYMENT_METHODS
from services.payment_service import PaymentService
from utils.decorators import role_required, shop_user_required
from utils.pagination import PER_PAGE_DEFAULT, get_page, get_search
from utils.roles import Role

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def payments_index():
    shop_id = current_user.shop_id
    service = PaymentService(shop_id)
    search_q = get_search()
    pagination = service.list_payments(
        page=get_page(), per_page=PER_PAGE_DEFAULT, search=search_q
    )
    return render_template(
        "payments/index.html",
        pagination=pagination,
        payments=pagination.items,
        search_q=search_q,
    )


@payments_bp.route("/record", methods=["GET", "POST"])
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def record():
    shop_id = current_user.shop_id
    service = PaymentService(shop_id)
    unpaid_sales = service.get_unpaid_sales()

    if request.method == "POST":
        sale_id = request.form.get("sale_id", type=int)
        payment_method = request.form.get("payment_method", "").strip()
        paid_amount_raw = request.form.get("paid_amount", "")
        remarks = request.form.get("remarks", "").strip() or None

        try:
            paid_amount = Decimal(paid_amount_raw)
        except (InvalidOperation, TypeError):
            flash("Enter a valid payment amount.", "danger")
            return render_template(
                "payments/record.html",
                unpaid_sales=unpaid_sales,
                payment_methods=PAYMENT_METHODS,
            )

        if not sale_id:
            flash("Please select a sale.", "danger")
            return render_template(
                "payments/record.html",
                unpaid_sales=unpaid_sales,
                payment_methods=PAYMENT_METHODS,
            )

        try:
            payment = service.record_payment(
                sale_id, payment_method, paid_amount, remarks
            )
            flash(f"Payment #{payment.id} recorded successfully.", "success")
            return redirect(url_for("payments.payments_index"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template(
        "payments/record.html",
        unpaid_sales=unpaid_sales,
        payment_methods=PAYMENT_METHODS,
    )


@payments_bp.route("/collect-due", methods=["GET", "POST"])
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def collect_due():
    shop_id = current_user.shop_id
    service = PaymentService(shop_id)
    search_q = get_search()
    customers_with_due = service.get_customers_with_due(search=search_q)

    if request.method == "POST":
        sale_id = request.form.get("sale_id", type=int)
        payment_method = request.form.get("payment_method", "").strip()
        paid_amount_raw = request.form.get("paid_amount", "")
        remarks = request.form.get("remarks", "").strip() or None

        try:
            paid_amount = Decimal(paid_amount_raw)
        except (InvalidOperation, TypeError):
            flash("Enter a valid payment amount.", "danger")
            return render_template(
                "payments/collect_due.html",
                customers_with_due=customers_with_due,
                payment_methods=PAYMENT_METHODS,
                search_q=search_q,
            )

        if not sale_id:
            flash("Please select an invoice.", "danger")
            return render_template(
                "payments/collect_due.html",
                customers_with_due=customers_with_due,
                payment_methods=PAYMENT_METHODS,
                search_q=search_q,
            )

        try:
            payment = service.record_payment(
                sale_id, payment_method, paid_amount, remarks
            )
            flash(f"Due payment #{payment.id} collected successfully.", "success")
            return redirect(url_for("payments.collect_due"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template(
        "payments/collect_due.html",
        customers_with_due=customers_with_due,
        payment_methods=PAYMENT_METHODS,
        search_q=search_q,
    )
