from flask import Flask, render_template, request, jsonify
from earning import is_user_joined
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/check_join")
def check_join():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"joined": True}) # Always show dashboard
    
    joined = is_user_joined(user_id)
    return jsonify({"joined": joined, "channel": "@freeearningofusdt"})

@app.route("/api/earn")
def earn():
    return jsonify({
        "reward": 0.0025,
        "daily_limit": 20,
        "min_withdraw": 5.0,
        "message": "Ad watched - $0.0025 added! Fast withdrawal in MINUTES"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
