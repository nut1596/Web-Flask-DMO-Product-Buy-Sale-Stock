from flask import Blueprint, render_template, session, redirect, url_for, request

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["admin_logged_in"] = True
            return redirect(url_for("admin.admin_dashboard"))

        return render_template("login.html", error="Username หรือ Password ไม่ถูกต้อง")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("main.home"))
