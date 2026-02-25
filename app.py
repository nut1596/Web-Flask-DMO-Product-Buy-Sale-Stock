from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "DMO Product Buy-Sale-Stock System is Running!"


if __name__ == "__main__":
    app.run(debug=True)
