from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from services.cash_service import CashService
from services.dashboard_service import DashboardService
from utils.decorators import manager_or_owner_required, owner_required, shop_user_required
from utils.i18n import t
from utils.roles import Role

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET", "POST"])
@shop_user_required
def dashboard():
    shop_id = current_user.shop_id
    dash_service = DashboardService(shop_id)
    cash_service = CashService(shop_id)
    role = Role.normalize(current_user.role)
    is_cashier = role == Role.CASHIER
    is_owner = role == Role.ADMIN

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "reconcile":
                if not is_owner:
                    flash(t("msg.permission_denied"), "danger")
                    return redirect(url_for("dashboard.dashboard"))

                opening = request.form.get("opening_cash", "0")
                carry_forward = request.form.get("carry_forward_cash", "0")
                actual = request.form.get("actual_cash")
                supplier = request.form.get("supplier_payments", "0")
                withdrawals = request.form.get("cash_withdrawals", "0")
                notes = request.form.get("notes", "").strip() or None
                cash_service.save_daily_cash(
                    current_user.id,
                    opening_cash=opening,
                    carry_forward_cash=carry_forward,
                    actual_cash=actual if actual != "" else None,
                    supplier_payments=supplier,
                    cash_withdrawals=withdrawals,
                    notes=notes,
                )
                flash(t("msg.cash_saved"), "success")

            elif action == "expense":
                amount = request.form.get("expense_amount")
                description = request.form.get("expense_description", "").strip()
                cash_service.add_expense(current_user.id, amount, description)
                flash(t("msg.expense_saved"), "success")

            elif action == "delete_expense":
                if not is_owner:
                    flash(t("msg.permission_denied"), "danger")
                    return redirect(url_for("dashboard.dashboard"))
                expense_id = request.form.get("expense_id", type=int)
                cash_service.delete_expense(expense_id)
                flash(t("msg.expense_deleted"), "success")

        except (ValueError, InvalidOperation) as exc:
            flash(str(exc), "danger")
        return redirect(url_for("dashboard.dashboard"))

    cash = cash_service.get_today_summary()
    is_admin = current_user.has_role(Role.ADMIN, Role.MANAGER)

    return render_template(
        "dashboard.html",
        user=current_user,
        is_cashier=is_cashier,
        is_owner=is_owner,
        is_admin=is_admin,
        stats=dash_service.get_stats(),
        cash=cash,
        total_due=cash_service.get_total_customer_due(),
        recent_sales=dash_service.get_recent_sales(limit=6),
        recent_due_collections=cash_service.get_recent_due_collections(limit=6),
        today_expenses=cash_service.get_today_expenses(limit=10),
        low_stock_products=dash_service.get_low_stock_products(limit=6),
    )
