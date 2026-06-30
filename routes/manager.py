from flask import Blueprint, render_template
from flask_login import current_user

from utils.decorators import role_required, shop_user_required
from utils.roles import Role

manager_bp = Blueprint("manager", __name__, url_prefix="/manager")


@manager_bp.route("/")
@shop_user_required
@role_required(Role.ADMIN, Role.MANAGER)
def index():
    return render_template("manager/index.html", user=current_user)
