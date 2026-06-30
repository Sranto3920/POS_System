from flask import Blueprint, abort, send_file
from flask_login import current_user

from services.export_service import ExportService
from utils.decorators import shop_user_required

exports_bp = Blueprint("exports", __name__, url_prefix="/exports")

EXPORT_HANDLERS = {
    "products": ExportService.export_products,
    "customers": ExportService.export_customers,
    "suppliers": ExportService.export_suppliers,
    "sales": ExportService.export_sales,
    "purchases": ExportService.export_purchases,
    "payments": ExportService.export_payments,
    "ledger": ExportService.export_ledger,
}


@exports_bp.route("/<export_type>")
@shop_user_required
def exports_download(export_type):
    handler = EXPORT_HANDLERS.get(export_type)
    if handler is None:
        abort(404)

    buffer, filename = handler(current_user.shop_id)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
