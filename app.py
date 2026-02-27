import os
from flask import Flask
from flask_jwt_extended import JWTManager

from extensions import db, cache
from models import Category, Product, Discount, AdminUser
from routes.main_routes import main
from routes.admin_routes import admin
from routes.auth_routes import auth
from routes.api_routes import api


app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SECRET_KEY"] = "supersecretkey"
app.config["JWT_SECRET_KEY"] = "super-jwt-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 60

app.config["UPLOAD_FOLDER"] = "static/images"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- INIT EXTENSIONS ----------------
db.init_app(app)
cache.init_app(app)
jwt = JWTManager(app)

# ---------------- REGISTER BLUEPRINTS ----------------
app.register_blueprint(main)
app.register_blueprint(admin)
app.register_blueprint(auth)
app.register_blueprint(api)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Seed Category
        if Category.query.count() == 0:
            default_categories = ["AT", "HT", "CT", "HP", "DS", "DE", "EV", "BL"]
            for name in default_categories:
                db.session.add(Category(name=name))
            db.session.commit()

        # Seed Product
        if Product.query.count() == 0:
            at_category = Category.query.filter_by(name="AT").first()
            ht_category = Category.query.filter_by(name="HT").first()

            at_products = [
                ("จูเรย์มอน", 5, "default.png", 10),
                ("ทาเนมอน", 10, "default.png", 8),
            ]

            ht_products = [
                ("โดริโมเกมอน", 4, "default.png", 10),
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

            db.session.commit()

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

        # Seed Admin User
        if AdminUser.query.count() == 0:
            admin_user = AdminUser(username="admin")
            admin_user.set_password("1234")
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)
