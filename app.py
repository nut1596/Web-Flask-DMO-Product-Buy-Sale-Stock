import os
from werkzeug.utils import secure_filename
from flask import Flask
from models import db, Category, Product, Discount
from models import AdminUser
from routes.main_routes import main
from routes.admin_routes import admin
from routes.auth_routes import auth
from flask_caching import Cache
from app import cache


app = Flask(__name__)

app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 60  # cache 60 วินาที

cache = Cache(app)

app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.config["UPLOAD_FOLDER"] = "static/images"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


db.init_app(app)

app.register_blueprint(main)
app.register_blueprint(admin)
app.register_blueprint(auth)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # 1️⃣ Seed Category ก่อน
        if Category.query.count() == 0:
            default_categories = ["AT", "HT", "CT", "HP", "DS", "DE", "EV", "BL"]
            for name in default_categories:
                db.session.add(Category(name=name))
            db.session.commit()

        # 2️⃣ Seed Product หลังจากมี Category แล้ว
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

        # 3️⃣ Seed Discount
        if Discount.query.count() == 0:
            discounts = [
                ("NEWYEAR10", 10),
                ("VIP20", 20),
                ("EV15", 15),
            ]
            for code, percent in discounts:
                db.session.add(Discount(code=code, percent=percent))
            db.session.commit()

        # 4️⃣ Seed Admin User
        # ตรวจสอบว่ามีผู้ใช้ admin อยู่แล้วหรือไม่
        if AdminUser.query.count() == 0:
            admin = AdminUser(username="admin")
            admin.set_password("1234")
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
