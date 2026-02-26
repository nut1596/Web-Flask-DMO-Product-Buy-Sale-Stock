from models import Category, Product, Discount, Order, OrderItem
from flask import Blueprint, render_template, session, redirect, url_for, request
from models import Category, Product, Discount, Order
from models import db

main = Blueprint("main", __name__)


# ---------------- HOME ----------------
@main.route("/")
def home():

    search = request.args.get("search")
    category_id = request.args.get("category")
    page = request.args.get("page", 1, type=int)

    query = Product.query

    if search:
        query = query.filter(Product.name.contains(search))

    if category_id:
        query = query.filter(Product.category_id == int(category_id))

    pagination = query.paginate(page=page, per_page=8)

    products = pagination.items
    categories = Category.query.all()

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        pagination=pagination,
        search=search,
        selected_category=category_id,
    )


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
        session["cart"] = {}

    cart = session["cart"]
    product_id_str = str(product_id)

    current_quantity = cart.get(product_id_str, 0)

    if current_quantity < product.stock:
        cart[product_id_str] = current_quantity + 1

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("main.cart"))


@main.route("/cart", methods=["GET", "POST"])
def cart():
    cart_items = []
    total = 0
    discount_amount = 0
    final_total = 0

    # 🔥 กันกรณี session เก่าเป็น list
    if "cart" in session and isinstance(session["cart"], list):
        session["cart"] = {}

    if "cart" in session:
        for product_id_str, quantity in session["cart"].items():
            product = Product.query.get(int(product_id_str))
            if product:
                subtotal = product.price * quantity
                cart_items.append((product, quantity, subtotal))
                total += subtotal

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


@main.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    if "cart" in session:
        cart = session["cart"]
        product_id_str = str(product_id)

        if product_id_str in cart:
            del cart[product_id_str]

        session["cart"] = cart
        session.modified = True

    return redirect(url_for("main.cart"))


@main.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("main.cart"))


@main.route("/increase_quantity/<int:product_id>")
def increase_quantity(product_id):
    if "cart" in session:
        cart = session["cart"]
        pid = str(product_id)

        product = Product.query.get_or_404(product_id)

        if pid in cart and cart[pid] < product.stock:
            cart[pid] += 1

        session["cart"] = cart
        session.modified = True

    return redirect(url_for("main.cart"))


@main.route("/decrease_quantity/<int:product_id>")
def decrease_quantity(product_id):
    if "cart" in session:
        cart = session["cart"]
        pid = str(product_id)

        if pid in cart:
            cart[pid] -= 1
            if cart[pid] <= 0:
                del cart[pid]

        session["cart"] = cart
        session.modified = True

    return redirect(url_for("main.cart"))


# ---------------- CHECKOUT ----------------
@main.route("/checkout")
def checkout():
    if "cart" not in session or not session["cart"]:
        return redirect(url_for("main.cart"))

    total = 0
    new_order = Order(total_amount=0)
    db.session.add(new_order)
    db.session.flush()  # เพื่อให้ได้ order.id ก่อน commit

    for product_id_str, quantity in session["cart"].items():
        product = Product.query.get(int(product_id_str))

        if product and product.stock >= quantity:
            product.stock -= quantity
            subtotal = product.price * quantity
            total += subtotal

            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=quantity,
                price=product.price,
            )

            db.session.add(order_item)

    new_order.total_amount = total
    db.session.commit()

    session.pop("cart", None)

    return render_template("checkout_success.html", total=total)
