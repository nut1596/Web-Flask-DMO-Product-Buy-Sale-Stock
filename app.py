from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ------------------
# Model: Category
# ------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


# ------------------
# Route
# ------------------
@app.route("/")
def home():
    categories = Category.query.all()
    return render_template("index.html", categories=categories)


# ------------------
# Initialize Database
# ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # เพิ่มหมวดเริ่มต้น ถ้ายังไม่มี
        if Category.query.count() == 0:
            default_categories = ["AT", "HT", "CT", "HP", "DS", "DE", "EV", "BL"]
            for name in default_categories:
                db.session.add(Category(name=name))
            db.session.commit()

    app.run(debug=True)
