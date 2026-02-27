from flask import Blueprint, jsonify
from models import Product, Order
from models import db
from sqlalchemy import func
from flask import request
from flask_jwt_extended import create_access_token, jwt_required
from models import AdminUser
from flask_jwt_extended import get_jwt
from functools import wraps
from extensions import limiter


def role_required(required_role):

    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):

            claims = get_jwt()
            user_role = claims.get("role")

            if user_role != required_role:
                return jsonify({"message": "Access forbidden"}), 403

            return fn(*args, **kwargs)

        return decorator

    return wrapper


api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def api_login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = AdminUser.query.filter_by(username=username).first()

    if user and user.check_password(password):

        access_token = create_access_token(
            identity=user.username, additional_claims={"role": user.role}
        )

        return jsonify({"access_token": access_token})

    return jsonify({"message": "Invalid credentials"}), 401


# ---------------- PRODUCTS ----------------
@api.route("/products")
@jwt_required()
@limiter.limit("30 per minute")
def get_products():
    products = Product.query.all()

    data = []
    for p in products:
        data.append(
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock": p.stock,
                "category_id": p.category_id,
            }
        )

    return jsonify(data)


# ---------------- ORDERS ----------------
@api.route("/orders")
@role_required("admin")
@limiter.limit("20 per minute")
def get_orders():
    orders = Order.query.all()

    data = []
    for o in orders:
        data.append(
            {
                "id": o.id,
                "total_amount": o.total_amount,
                "status": o.status,
                "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    return jsonify(data)


# ---------------- DASHBOARD KPI ----------------
@api.route("/dashboard/kpi")
def dashboard_kpi():

    total_sales = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).scalar()

    total_orders = db.session.query(func.count(Order.id)).scalar()

    paid_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.status == "Paid")
        .scalar()
    )

    paid_count = (
        db.session.query(func.count(Order.id)).filter(Order.status == "Paid").scalar()
    )

    average_order_value = 0
    conversion_rate = 0

    if total_orders > 0:
        average_order_value = total_sales / total_orders
        conversion_rate = (paid_count / total_orders) * 100

    return jsonify(
        {
            "total_sales": total_sales,
            "total_orders": total_orders,
            "paid_revenue": paid_revenue,
            "average_order_value": average_order_value,
            "conversion_rate": conversion_rate,
        }
    )
