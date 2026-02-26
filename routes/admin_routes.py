from flask import Blueprint, render_template, session, redirect, url_for, request
from models import Product, Order, Category
from models import db
from werkzeug.utils import secure_filename
from flask import current_app
import os

admin = Blueprint("admin", __name__)


@admin.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    orders = Order.query.order_by(Order.created_at.asc()).all()

    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)

    # เตรียมข้อมูลกราฟ
    labels = [f"Order {order.id}" for order in orders]
    data = [order.total_amount for order in orders]

    return render_template(
        "admin.html",
        orders=orders,
        total_sales=total_sales,
        total_orders=total_orders,
        labels=labels,
        data=data,
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


@admin.route("/admin/products/add", methods=["GET", "POST"])
def add_product():

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        category_id = int(request.form["category_id"])

        file = request.files["image"]

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
        else:
            filename = "default.png"

        new_product = Product(
            name=name,
            price=price,
            stock=stock,
            image=filename,
            category_id=category_id,
        )

        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for("admin.admin_products"))

    categories = Category.query.all()
    return render_template("add_product.html", categories=categories)


@admin.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    product = Product.query.get_or_404(id)

    if request.method == "POST":
        product.name = request.form["name"]
        product.price = float(request.form["price"])
        product.stock = int(request.form["stock"])
        product.category_id = int(request.form["category_id"])

        file = request.files["image"]

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            product.image = filename

        db.session.commit()

        return redirect(url_for("admin.admin_products"))

    categories = Category.query.all()
    return render_template("edit_product.html", product=product, categories=categories)


@admin.route("/admin/orders/<int:id>")
def order_detail(id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    order = Order.query.get_or_404(id)

    return render_template("order_detail.html", order=order)


@admin.route("/admin/orders/<int:id>/status/<string:status>")
def update_status(id, status):

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    order = Order.query.get_or_404(id)

    if status in ["Pending", "Paid", "Cancelled"]:
        order.status = status
        db.session.commit()

    return redirect(url_for("admin.admin_dashboard"))
