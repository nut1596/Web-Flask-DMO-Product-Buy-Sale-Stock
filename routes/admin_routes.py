from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from flask import send_file
import io
from sqlalchemy import func
from flask import Blueprint, render_template, session, redirect, url_for, request
from models import Product, Order, Category
from models import db
from werkzeug.utils import secure_filename
from flask import current_app
import os
from models import ActivityLog

admin = Blueprint("admin", __name__)


@admin.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    # รับค่า filter จาก URL เช่น ?status=Paid
    status_filter = request.args.get("status")

    from datetime import datetime

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Order.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Order.created_at >= start)

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Order.created_at <= end)

    orders = query.order_by(Order.created_at.desc()).all()

    # ===============================
    # 🔥 Monthly Revenue Analytics
    # ===============================

    from sqlalchemy import func

    monthly_data = (
        db.session.query(
            func.strftime("%Y-%m", Order.created_at).label("month"),
            func.sum(Order.total_amount),
        )
        .filter(Order.status == "Paid")  # คิดเฉพาะ Paid
        .group_by("month")
        .order_by("month")
        .all()
    )

    monthly_labels = [m[0] for m in monthly_data]
    monthly_revenue = [float(m[1]) for m in monthly_data]

    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)

    # 🔥 คำนวณเฉพาะออเดอร์ที่ Paid

    paid_orders = Order.query.filter_by(status="Paid").all()
    paid_revenue = sum(order.total_amount for order in paid_orders)

    # 🔥 Average Order Value (AOV)
    average_order_value = 0
    if total_orders > 0:
        average_order_value = total_sales / total_orders

    # 🔥 Conversion Rate (Paid / Total)
    conversion_rate = 0
    if total_orders > 0:
        conversion_rate = (len(paid_orders) / total_orders) * 100

    # 🔥 Group by Date (รายวัน)
    daily_sales = (
        db.session.query(func.date(Order.created_at), func.sum(Order.total_amount))
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )

    labels = [str(row[0]) for row in daily_sales]
    data = [float(row[1]) for row in daily_sales]

    return render_template(
        "admin.html",
        orders=orders,
        total_sales=total_sales,
        total_orders=total_orders,
        labels=labels,
        data=data,
        status_filter=status_filter,
        average_order_value=average_order_value,
        paid_revenue=paid_revenue,
        conversion_rate=conversion_rate,
        monthly_labels=monthly_labels,
        monthly_revenue=monthly_revenue,
    )


@admin.route("/admin/export/pdf")
def export_pdf():

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    orders = Order.query.order_by(Order.created_at.desc()).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("DMO Stock - Sales Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    data = [["Order ID", "Total", "Date", "Status"]]

    for order in orders:
        data.append(
            [
                f"#{order.id}",
                f"{order.total_amount} Baht",
                order.created_at.strftime("%d/%m/%Y"),
                order.status,
            ]
        )

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="sales_report.pdf",
        mimetype="application/pdf",
    )


@admin.route("/admin/export/excel")
def export_excel():

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    orders = Order.query.order_by(Order.created_at.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    # Header
    ws.append(["Order ID", "Total (Baht)", "Date", "Status"])

    # Data
    for order in orders:
        ws.append(
            [
                order.id,
                order.total_amount,
                order.created_at.strftime("%d/%m/%Y"),
                order.status,
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="sales_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@admin.route("/admin/products")
def admin_products():

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        return redirect(url_for("admin.admin_dashboard"))

    products = Product.query.all()
    return render_template("admin_products.html", products=products)


@admin.route("/admin/products/delete/<int:id>")
def delete_product(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()

    log = ActivityLog(username=session.get("role"), action=f"Deleted product ID: {id}")
    db.session.add(log)
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

        log = ActivityLog(username=session.get("role"), action=f"Added product: {name}")
        db.session.add(log)
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

    allowed_transitions = {
        "Pending": ["Paid", "Cancelled"],
        "Paid": ["Completed"],
        "Completed": [],
        "Cancelled": [],
    }

    if status in allowed_transitions.get(order.status, []):
        order.status = status
        db.session.commit()

    return redirect(url_for("admin.admin_dashboard"))


@admin.route("/admin/logs")
def view_logs():

    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()

    return render_template("activity_logs.html", logs=logs)
