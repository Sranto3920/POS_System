from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models.customer import Customer
from services.ledger_service import LedgerService
from utils.decorators import role_required, shop_user_required
from utils.pagination import PER_PAGE_DEFAULT, get_page, get_search
from utils.roles import Role

ledger_bp = Blueprint("ledger", __name__, url_prefix="/customer-ledger")


@ledger_bp.route("/")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER)
def ledger_index():
    shop_id = current_user.shop_id
    service = LedgerService(shop_id)
    search_q = get_search()
    customer_id = request.args.get("customer_id", type=int)
    customers = (
        Customer.query.filter_by(shop_id=shop_id).order_by(Customer.name.asc()).all()
    )
    customer_summaries = service.list_customers_with_balance()

    pagination = service.list_all(
        page=get_page(),
        per_page=PER_PAGE_DEFAULT,
        customer_id=customer_id,
        search=search_q,
    )

    extra_args = {}
    if customer_id:
        extra_args["customer_id"] = customer_id

    return render_template(
        "ledger/index.html",
        pagination=pagination,
        entries=pagination.items,
        search_q=search_q,
        customers=customers,
        customer_summaries=customer_summaries,
        selected_customer_id=customer_id,
        extra_args=extra_args,
    )


@ledger_bp.route("/customer/<int:customer_id>")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER)
def customer(customer_id):
    shop_id = current_user.shop_id
    service = LedgerService(shop_id)
    customer_obj = service.get_customer(customer_id)
    if customer_obj is None:
        flash("Customer not found.", "warning")
        return redirect(url_for("ledger.ledger_index"))

    balance = service.get_customer_balance(customer_id)
    pagination = service.list_by_customer(
        customer_id, page=get_page(), per_page=PER_PAGE_DEFAULT
    )

    return render_template(
        "ledger/customer.html",
        customer=customer_obj,
        balance=balance,
        pagination=pagination,
        entries=pagination.items,
    )
