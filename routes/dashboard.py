from flask import Blueprint, render_template
from flask_login import current_user

from services.dashboard_service import DashboardService
from utils.decorators import shop_user_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@shop_user_required
def dashboard():
    service = DashboardService(current_user.shop_id)

    return render_template(
        "dashboard.html",
        user=current_user,
        stats=service.get_stats(),
        recent_sales=service.get_recent_sales(),
        low_stock_products=service.get_low_stock_products(),
    )
