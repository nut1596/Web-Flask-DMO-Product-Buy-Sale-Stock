from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models import AdminUser, Customer

auth = Blueprint("auth", __name__)


# =========================
# ADMIN LOGIN
# =========================
@auth.route("/login", methods=["GET", "POST"])
def login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = AdminUser.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["admin_logged_in"] = True
            session["role"] = user.role
            return redirect(url_for("admin.admin_dashboard"))

        return render_template("login.html", error="Username หรือ Password ไม่ถูกต้อง")

    return render_template("login.html")


# =========================
# CUSTOMER REGISTER
# =========================
@auth.route("/customer-register", methods=["GET", "POST"])
def customer_register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing = Customer.query.filter_by(username=username).first()
        if existing:
            flash("Username นี้ถูกใช้แล้ว")
            return redirect(url_for("auth.customer_register"))

        new_user = Customer(username=username)
        new_user.set_password(password)

        from models import db

        db.session.add(new_user)
        db.session.commit()

        flash("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
        return redirect(url_for("auth.customer_login"))

    return render_template("customer_register.html")


# =========================
# CUSTOMER LOGIN
# =========================
@auth.route("/customer-login", methods=["GET", "POST"])
def customer_login():

    if session.get("customer_id"):
        return redirect(url_for("main.home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = Customer.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["customer_id"] = user.id
            return redirect(url_for("main.home"))

        return render_template(
            "customer_login.html", error="Username หรือ Password ไม่ถูกต้อง"
        )

    return render_template("customer_login.html")


# =========================
# LOGOUT (ทั้ง admin + customer)
# =========================
@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))
