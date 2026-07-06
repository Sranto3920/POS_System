from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from forms.category_forms import CategoryForm
from services.category_service import CategoryService
from utils.decorators import manager_or_owner_required, shop_user_required
from utils.pagination import get_page, get_search

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


@categories_bp.route("/")
@shop_user_required
def categories_index():
    page = get_page()
    search = get_search()
    pagination = CategoryService.list(current_user.shop_id, search=search, page=page)

    return render_template(
        "categories/index.html",
        user=current_user,
        pagination=pagination,
        categories=pagination.items,
        search_q=search,
    )


@categories_bp.route("/add", methods=["GET", "POST"])
@shop_user_required
@manager_or_owner_required
def add():
    form = CategoryForm()

    if form.validate_on_submit():
        category = CategoryService.create(current_user.shop_id, form)
        flash(f'Category "{category.name}" created successfully.', "success")
        return redirect(url_for("categories.categories_index"))

    return render_template(
        "categories/form.html",
        user=current_user,
        form=form,
        title="Add Category",
        submit_label="Create Category",
    )


@categories_bp.route("/edit/<int:category_id>", methods=["GET", "POST"])
@shop_user_required
@manager_or_owner_required
def edit(category_id):
    category = CategoryService.get(current_user.shop_id, category_id)
    if category is None:
        flash("Category not found.", "warning")
        return redirect(url_for("categories.categories_index"))

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        CategoryService.update(category, form)
        flash(f'Category "{category.name}" updated successfully.', "success")
        return redirect(url_for("categories.categories_index"))

    return render_template(
        "categories/form.html",
        user=current_user,
        form=form,
        category=category,
        title="Edit Category",
        submit_label="Save Changes",
    )


@categories_bp.route("/delete/<int:category_id>", methods=["POST"])
@shop_user_required
@manager_or_owner_required
def delete(category_id):
    category = CategoryService.get(current_user.shop_id, category_id)
    if category is None:
        flash("Category not found.", "warning")
        return redirect(url_for("categories.categories_index"))

    success, message = CategoryService.delete(category)
    flash(message, "success" if success else "danger")
    return redirect(url_for("categories.categories_index"))
