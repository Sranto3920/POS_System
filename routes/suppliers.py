from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from forms.supplier_forms import SupplierForm
from services.supplier_service import SupplierService
from utils.decorators import manager_or_owner_required, shop_user_required
from utils.pagination import get_page, get_search
from utils.roles import Role

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")


@suppliers_bp.before_request
def _suppliers_role_guard():
    from flask import abort, redirect, url_for
    from flask_login import current_user

    from models.platform_user import PlatformUser

    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.url))
    if isinstance(current_user, PlatformUser):
        abort(403)
    if not Role.matches(current_user.role, Role.ADMIN, Role.MANAGER):
        abort(403)


@suppliers_bp.route("/")
@shop_user_required
def suppliers_index():
    page = get_page()
    search = get_search()
    pagination = SupplierService.list(current_user.shop_id, search=search, page=page)

    return render_template(
        "suppliers/index.html",
        user=current_user,
        pagination=pagination,
        suppliers=pagination.items,
        search_q=search,
    )


@suppliers_bp.route("/add", methods=["GET", "POST"])
@shop_user_required
@manager_or_owner_required
def add():
    form = SupplierForm()

    if form.validate_on_submit():
        supplier = SupplierService.create(current_user.shop_id, form)
        flash(f'Supplier "{supplier.name}" created successfully.', "success")
        return redirect(url_for("suppliers.suppliers_index"))

    return render_template(
        "suppliers/form.html",
        user=current_user,
        form=form,
        title="Add Supplier",
        submit_label="Create Supplier",
    )


@suppliers_bp.route("/edit/<int:supplier_id>", methods=["GET", "POST"])
@shop_user_required
@manager_or_owner_required
def edit(supplier_id):
    supplier = SupplierService.get(current_user.shop_id, supplier_id)
    if supplier is None:
        flash("Supplier not found.", "warning")
        return redirect(url_for("suppliers.suppliers_index"))

    form = SupplierForm(obj=supplier)

    if form.validate_on_submit():
        SupplierService.update(supplier, form)
        flash(f'Supplier "{supplier.name}" updated successfully.', "success")
        return redirect(url_for("suppliers.suppliers_index"))

    return render_template(
        "suppliers/form.html",
        user=current_user,
        form=form,
        supplier=supplier,
        title="Edit Supplier",
        submit_label="Save Changes",
    )


@suppliers_bp.route("/delete/<int:supplier_id>", methods=["POST"])
@shop_user_required
@manager_or_owner_required
def delete(supplier_id):
    supplier = SupplierService.get(current_user.shop_id, supplier_id)
    if supplier is None:
        flash("Supplier not found.", "warning")
        return redirect(url_for("suppliers.suppliers_index"))

    success, message = SupplierService.delete(supplier)
    flash(message, "success" if success else "danger")
    return redirect(url_for("suppliers.suppliers_index"))
