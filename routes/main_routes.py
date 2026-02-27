from models import Category, Product, Discount, Order, OrderItem
from flask import Blueprint, render_template, session, redirect, url_for, request
from models import Category, Product, Discount, Order
from models import db

main = Blueprint("main", __name__)


# ---------------- HOME ----------------
@main.route("/")
def home():
    search = request.args.get("search")
    selected_category = request.args.get("category")
    sort = request.args.get("sort")
    page = request.args.get("page", 1, type=int)

    query = Product.query

    # Search
    if search:
        query = query.filter(Product.name.contains(search))

    # Filter Category
    if selected_category:
        query = query.filter_by(category_id=selected_category)

    # Sorting
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())

    pagination = query.paginate(page=page, per_page=8)

    categories = Category.query.all()

    return render_template(
        "index.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        search=search,
        selected_category=selected_category,
        sort=sort,
    )


# ---------------- CATEGORY ----------------
@main.route("/category/<int:id>")
def category_detail(id):
    category = Category.query.get_or_404(id)
    return render_template("category.html", category=category)


# ---------------- CART ----------------


from flask import jsonify


@main.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):

    product = Product.query.get_or_404(product_id)

    if product.stock <= 0:
        return jsonify({"success": False})

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]
    pid = str(product_id)

    current_quantity = cart.get(pid, 0)

    if current_quantity < product.stock:
        cart[pid] = current_quantity + 1

    session["cart"] = cart
    session.modified = True

    return jsonify({"success": True, "cart_count": sum(cart.values())})


@main.route("/cart", methods=["GET", "POST"])
def cart():

    cart_items = []
    total = 0

    # 🔥 กันกรณี session เก่าเป็น list
    if "cart" in session and isinstance(session["cart"], list):
        session["cart"] = {}

    # ================= CALCULATE TOTAL =================
    if "cart" in session:
        for product_id_str, quantity in session["cart"].items():
            product = Product.query.get(int(product_id_str))
            if product:
                subtotal = product.price * quantity
                cart_items.append((product, quantity, subtotal))
                total += subtotal

    # ================= APPLY DISCOUNT =================
    if request.method == "POST":
        code = request.form.get("discount_code")

        discount = Discount.query.filter_by(code=code).first()

        if discount:
            session["discount_percent"] = discount.percent
            session["discount_code"] = discount.code
        else:
            session.pop("discount_percent", None)
            session.pop("discount_code", None)

    percent = session.get("discount_percent", 0)
    discount_amount = total * (percent / 100)
    final_total = total - discount_amount

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total,
        discount_amount=discount_amount,
        final_total=final_total,
        discount_code=session.get("discount_code"),
        discount_percent=percent,
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
@main.route("/checkout", methods=["POST"])
def checkout():

    from datetime import datetime
    from werkzeug.utils import secure_filename
    import os

    if "cart" not in session or not session["cart"]:
        return redirect(url_for("main.cart"))

    tamer_name = request.form.get("tamer_name")
    note = request.form.get("note")
    transfer_time = request.form.get("transfer_time")
    slip = request.files.get("slip")

    filename = None
    if slip:
        filename = secure_filename(slip.filename)
        slip.save(os.path.join("static/images", filename))

    total = 0
    new_order = Order(
        total_amount=0,
        status="Waiting Verification",
        tamer_name=tamer_name,
        note=note,
        transfer_time=datetime.fromisoformat(transfer_time),
        slip_image=filename,
    )

    db.session.add(new_order)
    db.session.flush()

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


@main.route("/remove_discount")
def remove_discount():
    session.pop("discount_percent", None)
    session.pop("discount_code", None)
    return redirect(url_for("main.cart"))
