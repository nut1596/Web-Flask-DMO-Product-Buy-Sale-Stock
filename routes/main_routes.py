from flask import Blueprint, render_template, session, redirect, url_for, request
from models import Category, Product, Discount, Order
from models import db

main = Blueprint("main", __name__)


# ---------------- HOME ----------------
@main.route("/")
def home():
    categories = Category.query.all()
    return render_template("index.html", categories=categories)


# ---------------- CATEGORY ----------------
@main.route("/category/<int:id>")
def category_detail(id):
    category = Category.query.get_or_404(id)
    return render_template("category.html", category=category)


# ---------------- CART ----------------
@main.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    if product.stock <= 0:
        return redirect(url_for("main.category_detail", id=product.category_id))

    if "cart" not in session:
        session["cart"] = []

    current_count = session["cart"].count(product_id)

    if current_count < product.stock:
        session["cart"].append(product_id)
        session.modified = True

    return redirect(url_for("main.cart"))


@main.route("/cart", methods=["GET", "POST"])
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


@main.route("/remove_from_cart/<int:index>")
def remove_from_cart(index):
    if "cart" in session:
        if 0 <= index < len(session["cart"]):
            session["cart"].pop(index)
            session.modified = True
    return redirect(url_for("main.cart"))


@main.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("main.cart"))


# ---------------- CHECKOUT ----------------
@main.route("/checkout")
def checkout():
    if "cart" not in session or not session["cart"]:
        return redirect(url_for("main.cart"))

    total = 0

    for product_id in session["cart"]:
        product = Product.query.get(product_id)
        if product and product.stock > 0:
            product.stock -= 1
            total += product.price

    new_order = Order(total_amount=total)
    db.session.add(new_order)
    db.session.commit()

    session.pop("cart", None)

    return render_template("checkout_success.html", total=total)
