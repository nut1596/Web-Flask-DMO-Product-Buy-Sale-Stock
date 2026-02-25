from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

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
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)


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
                ("จูเรย์มอน", 5),
                ("ทาเนมอน", 10),
                ("กิลมอน", 30),
                ("จินลอนมอน", 40),
                ("อัลฟอร์ซ วีดรามอน X", 500),
            ]

            ht_products = [
                ("โดริโมเกมอน", 4),
                ("ฟานบีมอน", 7),
                ("ไนท์มอน", 30),
                ("แกมมามอน", 60),
                ("พาราไซมอน", 140),
            ]

            for name, price in at_products:
                db.session.add(
                    Product(name=name, price=price, category_id=at_category.id)
                )

            for name, price in ht_products:
                db.session.add(
                    Product(name=name, price=price, category_id=ht_category.id)
                )

            db.session.commit()

    app.run(debug=True)
