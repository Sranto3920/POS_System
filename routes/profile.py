from flask import Blueprint, render_template
from flask_login import current_user

from extensions import db
from models.shop import Shop
from utils.decorators import shop_user_required

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@shop_user_required
def index():
    shop = db.session.get(Shop, current_user.shop_id)
    return render_template("profile/index.html", user=current_user, shop=shop)
