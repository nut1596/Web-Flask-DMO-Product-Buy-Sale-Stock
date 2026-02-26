from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SECRET_KEY"] = "supersecretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ------------------
# Models
# ------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    products = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)  # 👈 เพิ่มตรงนี้
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)


class Discount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    percent = db.Column(db.Float, nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 👈 เพิ่มตรงนี้


# ------------------
# Routes
# ------------------
@app.route("/")
def home():
    categories = Category.query.all()
    return render_template("index.html", categories=categories)


@app.route("/category/<int:id>")
def category_detail(id):
    category = Category.query.get_or_404(id)
    return render_template("category.html", category=category)


@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    if product.stock <= 0:
        return redirect(url_for("category_detail", id=product.category_id))

    if "cart" not in session:
        session["cart"] = []

    # นับจำนวนที่อยู่ใน cart แล้ว
    current_count = session["cart"].count(product_id)

    if current_count < product.stock:
        session["cart"].append(product_id)
        session.modified = True

    return redirect(url_for("cart"))


@app.route("/cart", methods=["GET", "POST"])
def cart():
    cart_items = []
    total = 0
    discount_amount = 0
    final_total = 0

    if "cart" in session:
        for index, product_id in enumerate(session["cart"]):
            product = Product.query.get(product_id)
            if product:
                cart_items.append((index, product))
                total += product.price

    if request.method == "POST":
        code = request.form.get("discount_code")
        discount = Discount.query.filter_by(code=code).first()

        if discount:
            discount_amount = total * (discount.percent / 100)

    final_total = total - discount_amount

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total,
        discount_amount=discount_amount,
        final_total=final_total,
    )


@app.route("/remove_from_cart/<int:index>")
def remove_from_cart(index):
    if "cart" in session:
        if 0 <= index < len(session["cart"]):
            session["cart"].pop(index)
            session.modified = True
    return redirect(url_for("cart"))


@app.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("cart"))


@app.route("/checkout")
def checkout():
    if "cart" not in session or not session["cart"]:
        return redirect(url_for("cart"))

    total = 0

    for product_id in session["cart"]:
        product = Product.query.get(product_id)
        if product and product.stock > 0:
            product.stock -= 1
            total += product.price

    # บันทึกคำสั่งซื้อ
    new_order = Order(total_amount=total)
    db.session.add(new_order)

    db.session.commit()

    # ล้างตะกร้า
    session.pop("cart", None)

    return render_template("checkout_success.html", total=total)


@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)

    return render_template(
        "admin.html",
        orders=orders,
        total_sales=total_sales,
        total_orders=total_orders,
    )


@app.route("/admin/products")
def admin_products():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    products = Product.query.all()
    return render_template("admin_products.html", products=products)


@app.route("/admin/products/delete/<int:id>")
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("admin_products"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # กำหนด user แบบง่ายก่อน (hardcoded)
        if username == "admin" and password == "1234":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        return render_template("login.html", error="Username หรือ Password ไม่ถูกต้อง")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))


# ------------------
# Initialize Database
# ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Seed Category
        if Category.query.count() == 0:
            default_categories = ["AT", "HT", "CT", "HP", "DS", "DE", "EV", "BL"]
            for name in default_categories:
                db.session.add(Category(name=name))
            db.session.commit()

        # Seed Product (เฉพาะ AT และ HT ก่อน)
        if Product.query.count() == 0:
            at_category = Category.query.filter_by(name="AT").first()
            ht_category = Category.query.filter_by(name="HT").first()

            at_products = [
                ("จูเรย์มอน", 5, "default.png", 10),
                ("ทาเนมอน", 10, "default.png", 8),
                ("กิลมอน", 30, "default.png", 5),
                ("จินลอนมอน", 40, "default.png", 3),
                ("อัลฟอร์ซ วีดรามอน X", 500, "default.png", 1),
            ]

            ht_products = [
                ("โดริโมเกมอน", 4, "default.png", 10),
                ("ฟานบีมอน", 7, "default.png", 7),
                ("ไนท์มอน", 30, "default.png", 5),
                ("แกมมามอน", 60, "default.png", 4),
                ("พาราไซมอน", 140, "default.png", 2),
            ]

            for name, price, image, stock in at_products:
                db.session.add(
                    Product(
                        name=name,
                        price=price,
                        image=image,
                        stock=stock,
                        category_id=at_category.id,
                    )
                )

            for name, price, image, stock in ht_products:
                db.session.add(
                    Product(
                        name=name,
                        price=price,
                        image=image,
                        stock=stock,
                        category_id=ht_category.id,
                    )
                )
        # Seed Discount
        if Discount.query.count() == 0:
            discounts = [
                ("NEWYEAR10", 10),
                ("VIP20", 20),
                ("EV15", 15),
            ]

            for code, percent in discounts:
                db.session.add(Discount(code=code, percent=percent))

            db.session.commit()

    app.run(debug=True)
