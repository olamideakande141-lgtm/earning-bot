
import os
from flask import Flask, jsonify, render_template
from earning import earning_bp, init_db

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "development-only-change-this"
)

init_db()
app.register_blueprint(earning_bp, url_prefix="/api")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Ads Payout",
        "mode": "test"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
