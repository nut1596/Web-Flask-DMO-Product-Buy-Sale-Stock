from flask import Blueprint, render_template, session, redirect, url_for
from models import Product, Order
from models import db

admin = Blueprint("admin", __name__)


@admin.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)

    return render_template(
        "admin.html",
        orders=orders,
        total_sales=total_sales,
        total_orders=total_orders,
    )


@admin.route("/admin/products")
def admin_products():
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    products = Product.query.all()
    return render_template("admin_products.html", products=products)


@admin.route("/admin/products/delete/<int:id>")
def delete_product(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for("admin.admin_products"))
