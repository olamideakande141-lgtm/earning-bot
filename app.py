import os, requests
from flask import Flask, render_template, request, jsonify
from bot import get_app as get_bot_app, FORCE_CHANNEL, CHANNEL_LINK
from telegram import Update
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
bot_app = get_bot_app()
BOT_TOKEN=os.getenv("BOT_TOKEN")
WEBHOOK_URL=os.getenv("RENDER_EXTERNAL_URL")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/check_join", methods=["POST"])
def check_join_api():
    data = request.get_json()
    user_id = data.get("user_id")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={FORCE_CHANNEL}&user_id={user_id}"
        r = requests.get(url).json()
        status = r.get("result", {}).get("status", "")
        joined = status in ["member", "administrator", "creator"]
        return jsonify({"joined": joined})
    except:
        return jsonify({"joined": False})

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    await bot_app.process_update(update)
    return "ok"

@app.route("/setwebhook")
def sethook():
    url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={url}")
    return r.text

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
