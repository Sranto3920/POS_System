from datetime import date

from flask import Blueprint, render_template, request

from flask_login import current_user

from services.report_service import ReportService
from utils.decorators import manager_or_owner_required, shop_user_required
from utils.roles import Role

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.before_request
def _reports_role_guard():
    from flask import abort, redirect, url_for
    from flask_login import current_user

    from models.platform_user import PlatformUser

    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.url))
    if isinstance(current_user, PlatformUser):
        abort(403)
    if not Role.matches(current_user.role, Role.ADMIN, Role.MANAGER):
        abort(403)

REPORT_LINKS = [
    {
        "endpoint": "reports.reports_daily_sales",
        "title": "Daily Sales",
        "icon": "calendar-day",
        "description": "Sales transactions for a specific day.",
    },
    {
        "endpoint": "reports.reports_monthly_sales",
        "title": "Monthly Sales",
        "icon": "calendar-month",
        "description": "Sales summary and breakdown by month.",
    },
    {
        "endpoint": "reports.reports_purchases",
        "title": "Purchase Report",
        "icon": "cart-plus",
        "description": "Stock purchases from suppliers.",
    },
    {
        "endpoint": "reports.reports_customers",
        "title": "Customer Report",
        "icon": "people",
        "description": "Customer activity and spending totals.",
    },
    {
        "endpoint": "reports.reports_suppliers",
        "title": "Supplier Report",
        "icon": "truck",
        "description": "Supplier purchase history and totals.",
    },
    {
        "endpoint": "reports.reports_products",
        "title": "Product Report",
        "icon": "box-seam",
        "description": "Full product catalog with pricing and stock.",
    },
    {
        "endpoint": "reports.reports_stock",
        "title": "Stock Report",
        "icon": "boxes",
        "description": "Inventory levels and stock valuation.",
    },
    {
        "endpoint": "reports.reports_low_stock",
        "title": "Low Stock Report",
        "icon": "exclamation-triangle",
        "description": "Products at or below the low-stock threshold.",
    },
    {
        "endpoint": "reports.reports_due_customers",
        "title": "Due Customers Report",
        "icon": "person-exclamation",
        "description": "Customers with outstanding due balances.",
    },
    {
        "endpoint": "reports.reports_outstanding_due",
        "title": "Outstanding Due Report",
        "icon": "cash-stack",
        "description": "All unpaid invoices and remaining due amounts.",
    },
    {
        "endpoint": "reports.reports_due_collection",
        "title": "Due Collection Report",
        "icon": "wallet2",
        "description": "Payments collected against previously due invoices.",
    },
    {
        "endpoint": "reports.reports_paid_vs_due",
        "title": "Paid vs Due Sales Report",
        "icon": "pie-chart",
        "description": "Compare paid and due amounts across sales.",
    },
]


@reports_bp.route("/")
@shop_user_required
def reports_index():
    return render_template("reports/index.html", reports=REPORT_LINKS)


@reports_bp.route("/daily-sales")
@shop_user_required
def reports_daily_sales():
    report_date = _parse_date(request.args.get("date")) or date.today()
    data = ReportService.daily_sales(current_user.shop_id, report_date)

    return render_template(
        "reports/report.html",
        title="Daily Sales Report",
        icon="calendar-day",
        data=data,
        columns=[
            ("sale_id", "Sale #"),
            ("sale_date", "Date"),
            ("customer_name", "Customer"),
            ("cashier_name", "Cashier"),
            ("total_amount", "Amount"),
        ],
        summary=[
            ("Date", report_date.strftime("%b %d, %Y")),
            ("Sales Count", data["sale_count"]),
            ("Total Amount", data["total_amount"]),
        ],
        filter_type="date",
        filter_value=report_date.isoformat(),
        export_type="sales",
    )


@reports_bp.route("/monthly-sales")
@shop_user_required
def reports_monthly_sales():
    today = date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month
    data = ReportService.monthly_sales(current_user.shop_id, year, month)

    return render_template(
        "reports/report.html",
        title="Monthly Sales Report",
        icon="calendar-month",
        data=data,
        columns=[
            ("sale_id", "Sale #"),
            ("sale_date", "Date"),
            ("customer_name", "Customer"),
            ("cashier_name", "Cashier"),
            ("total_amount", "Amount"),
        ],
        summary=[
            ("Period", f"{year}-{month:02d}"),
            ("Sales Count", data["sale_count"]),
            ("Total Amount", data["total_amount"]),
        ],
        filter_type="month",
        filter_year=year,
        filter_month=month,
        export_type="sales",
        daily_breakdown=data["daily"],
    )


@reports_bp.route("/purchases")
@shop_user_required
def reports_purchases():
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))
    data = ReportService.purchase_report(
        current_user.shop_id, date_from=date_from, date_to=date_to
    )

    return render_template(
        "reports/report.html",
        title="Purchase Report",
        icon="cart-plus",
        data=data,
        columns=[
            ("purchase_id", "Purchase #"),
            ("purchase_date", "Date"),
            ("supplier_name", "Supplier"),
            ("recorded_by", "Recorded By"),
            ("total_amount", "Amount"),
        ],
        summary=[
            ("Purchases", data["purchase_count"]),
            ("Total Amount", data["total_amount"]),
        ],
        filter_type="range",
        filter_date_from=date_from.isoformat() if date_from else "",
        filter_date_to=date_to.isoformat() if date_to else "",
        export_type="purchases",
    )


@reports_bp.route("/customers")
@shop_user_required
def reports_customers():
    data = ReportService.customer_report(current_user.shop_id)

    return render_template(
        "reports/report.html",
        title="Customer Report",
        icon="people",
        data=data,
        columns=[
            ("customer_name", "Customer"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("sale_count", "Sales"),
            ("total_spent", "Total Spent"),
        ],
        summary=[
            ("Customers", data["customer_count"]),
            ("Total Spent", data["total_spent"]),
        ],
        export_type="customers",
    )


@reports_bp.route("/suppliers")
@shop_user_required
def reports_suppliers():
    data = ReportService.supplier_report(current_user.shop_id)

    return render_template(
        "reports/report.html",
        title="Supplier Report",
        icon="truck",
        data=data,
        columns=[
            ("supplier_name", "Supplier"),
            ("phone", "Phone"),
            ("email", "Email"),
            ("purchase_count", "Purchases"),
            ("total_purchased", "Total Purchased"),
        ],
        summary=[
            ("Suppliers", data["supplier_count"]),
            ("Total Purchased", data["total_purchased"]),
        ],
        export_type="suppliers",
    )


@reports_bp.route("/products")
@shop_user_required
def reports_products():
    data = ReportService.product_report(current_user.shop_id)

    return render_template(
        "reports/report.html",
        title="Product Report",
        icon="box-seam",
        data=data,
        columns=[
            ("product_name", "Product"),
            ("category_name", "Category"),
            ("supplier_name", "Supplier"),
            ("cost_price", "Cost"),
            ("default_selling_price", "Selling Price"),
            ("stock_quantity", "Stock"),
            ("expiry_date", "Expiry"),
        ],
        summary=[("Products", data["product_count"])],
        export_type="products",
    )


@reports_bp.route("/stock")
@shop_user_required
def reports_stock():
    data = ReportService.stock_report(current_user.shop_id)

    return render_template(
        "reports/report.html",
        title="Stock Report",
        icon="boxes",
        data=data,
        columns=[
            ("product_name", "Product"),
            ("category_name", "Category"),
            ("stock_quantity", "Stock"),
            ("cost_price", "Cost"),
            ("default_selling_price", "Selling Price"),
            ("stock_value", "Stock Value"),
        ],
        summary=[
            ("Products", data["product_count"]),
            ("Total Units", data["total_units"]),
            ("Total Value", data["total_value"]),
        ],
        export_type="products",
    )


@reports_bp.route("/low-stock")
@shop_user_required
def reports_low_stock():
    data = ReportService.low_stock_report(current_user.shop_id)

    return render_template(
        "reports/report.html",
        title="Low Stock Report",
        icon="exclamation-triangle",
        data=data,
        columns=[
            ("product_name", "Product"),
            ("category_name", "Category"),
            ("stock_quantity", "Stock"),
            ("default_selling_price", "Selling Price"),
        ],
        summary=[
            ("Threshold", data["threshold"]),
            ("Products", data["product_count"]),
        ],
        export_type="products",
    )


@reports_bp.route("/due-customers")
@shop_user_required
def reports_due_customers():
    data = ReportService.due_customers_report(current_user.shop_id)

    return render_template(
        "reports/report.html",
        title="Due Customers Report",
        icon="person-exclamation",
        data=data,
        columns=[
            ("customer_name", "Customer"),
            ("phone", "Phone"),
            ("due_invoice_count", "Due Invoices"),
            ("total_due", "Total Due"),
        ],
        summary=[
            ("Customers", data["customer_count"]),
            ("Total Due", data["total_due"]),
        ],
        export_type="customers",
    )


@reports_bp.route("/outstanding-due")
@shop_user_required
def reports_outstanding_due():
    data = ReportService.outstanding_due_report(current_user.shop_id)

    return render_template(
        "reports/report.html",
        title="Outstanding Due Report",
        icon="cash-stack",
        data=data,
        columns=[
            ("sale_id", "Invoice #"),
            ("sale_date", "Date"),
            ("customer_name", "Customer"),
            ("total_amount", "Original Total"),
            ("paid_amount", "Already Paid"),
            ("due_amount", "Remaining Due"),
            ("payment_status", "Status"),
        ],
        summary=[
            ("Invoices", data["invoice_count"]),
            ("Total Due", data["total_due"]),
        ],
        export_type="sales",
    )


@reports_bp.route("/due-collection")
@shop_user_required
def reports_due_collection():
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))
    data = ReportService.due_collection_report(
        current_user.shop_id, date_from=date_from, date_to=date_to
    )

    return render_template(
        "reports/report.html",
        title="Due Collection Report",
        icon="wallet2",
        data=data,
        columns=[
            ("payment_date", "Date"),
            ("sale_id", "Invoice #"),
            ("customer_name", "Customer"),
            ("payment_method", "Method"),
            ("paid_amount", "Collected"),
        ],
        summary=[
            ("Payments", data["payment_count"]),
            ("Total Collected", data["total_collected"]),
        ],
        filter_type="range",
        filter_date_from=date_from.isoformat() if date_from else "",
        filter_date_to=date_to.isoformat() if date_to else "",
        export_type="payments",
    )


@reports_bp.route("/paid-vs-due")
@shop_user_required
def reports_paid_vs_due():
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))
    data = ReportService.paid_vs_due_sales_report(
        current_user.shop_id, date_from=date_from, date_to=date_to
    )

    return render_template(
        "reports/report.html",
        title="Paid vs Due Sales Report",
        icon="pie-chart",
        data=data,
        columns=[
            ("sale_id", "Invoice #"),
            ("sale_date", "Date"),
            ("customer_name", "Customer"),
            ("total_amount", "Total"),
            ("paid_amount", "Paid"),
            ("due_amount", "Due"),
            ("payment_status", "Status"),
        ],
        summary=[
            ("Sales", data["sale_count"]),
            ("Total Paid", data["paid_total"]),
            ("Total Due", data["due_total"]),
        ],
        filter_type="range",
        filter_date_from=date_from.isoformat() if date_from else "",
        filter_date_to=date_to.isoformat() if date_to else "",
        export_type="sales",
    )


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
