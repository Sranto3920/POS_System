from flask import Blueprint, redirect, url_for

from utils.decorators import role_required, shop_user_required
from utils.roles import Role

pos_bp = Blueprint("pos", __name__, url_prefix="/pos")


@pos_bp.route("/")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER, Role.CASHIER)
def index():
    return redirect(url_for("sales.sales_new"))
