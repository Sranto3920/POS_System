from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from forms.customer_forms import CustomerForm
from services.customer_service import CustomerService
from utils.decorators import shop_user_required
from utils.pagination import get_page, get_search

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")


@customers_bp.route("/")
@shop_user_required
def customers_index():
    page = get_page()
    search = get_search()
    pagination = CustomerService.list(current_user.shop_id, search=search, page=page)

    return render_template(
        "customers/index.html",
        user=current_user,
        pagination=pagination,
        customers=pagination.items,
        search_q=search,
    )


@customers_bp.route("/<int:customer_id>")
@shop_user_required
def view(customer_id):
    profile = CustomerService.get_profile_stats(current_user.shop_id, customer_id)
    if profile is None:
        flash("Customer not found.", "warning")
        return redirect(url_for("customers.customers_index"))

    return render_template("customers/view.html", profile=profile)


@customers_bp.route("/add", methods=["GET", "POST"])
@shop_user_required
def add():
    form = CustomerForm()

    if form.validate_on_submit():
        customer = CustomerService.create(current_user.shop_id, form)
        flash(f'Customer "{customer.name}" created successfully.', "success")
        return redirect(url_for("customers.customers_index"))

    return render_template(
        "customers/form.html",
        user=current_user,
        form=form,
        title="Add Customer",
        submit_label="Create Customer",
    )


@customers_bp.route("/edit/<int:customer_id>", methods=["GET", "POST"])
@shop_user_required
def edit(customer_id):
    customer = CustomerService.get(current_user.shop_id, customer_id)
    if customer is None:
        flash("Customer not found.", "warning")
        return redirect(url_for("customers.customers_index"))

    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        CustomerService.update(customer, form)
        flash(f'Customer "{customer.name}" updated successfully.', "success")
        return redirect(url_for("customers.customers_index"))

    return render_template(
        "customers/form.html",
        user=current_user,
        form=form,
        customer=customer,
        title="Edit Customer",
        submit_label="Save Changes",
    )


@customers_bp.route("/delete/<int:customer_id>", methods=["POST"])
@shop_user_required
def delete(customer_id):
    customer = CustomerService.get(current_user.shop_id, customer_id)
    if customer is None:
        flash("Customer not found.", "warning")
        return redirect(url_for("customers.customers_index"))

    success, message = CustomerService.delete(customer)
    flash(message, "success" if success else "danger")
    return redirect(url_for("customers.customers_index"))
