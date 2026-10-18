
import os
import threading
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from flask import Flask, jsonify

from earning import earning_bp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBAPP_URL = "https://earning-bot-bdjm.onrender.com"
CHANNEL_URL = "https://t.me/freeearningofusdt"

if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN in your Render environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Register the membership verification API.
app.register_blueprint(earning_bp)


def membership_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(
            "📢 Join Our Channel",
            url=CHANNEL_URL
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            "✅ I've Joined — Verify",
            callback_data="verify_membership"
        )
    )
    return keyboard


def is_member(user_id):
    try:
        member = bot.get_chat_member(
            "@freeearningofusdt",
            user_id
        )

        if member.status in ("creator", "administrator", "member"):
            return True

        return (
            member.status == "restricted"
            and getattr(member, "is_member", False)
        )

    except Exception as exc:
        print("Membership verification error:", exc)
        return False


def send_access(message):
    user_id = message.from_user.id

    if not is_member(user_id):
        bot.send_message(
            message.chat.id,
            "🔒 Welcome to Ads Payout!\n\n"
            "Join our official Telegram channel first. "
            "Then tap the verification button below.",
            reply_markup=membership_keyboard()
        )
        return

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            "🚀 Open Ads Payout",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )

    bot.send_message(
        message.chat.id,
        "✅ Membership verified!\n\n"
        "Welcome to Ads Payout.",
        reply_markup=keyboard
    )


@bot.message_handler(commands=["start"])
def start(message):
    send_access(message)


@bot.callback_query_handler(
    func=lambda call: call.data == "verify_membership"
)
def verify_button(call):
    if is_member(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "Membership verified!"
        )

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                "🚀 Open Ads Payout",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )

        bot.send_message(
            call.message.chat.id,
            "✅ You have joined the channel. Open Ads Payout below.",
            reply_markup=keyboard
        )
    else:
        bot.answer_callback_query(
            call.id,
            "Membership not verified. Join the channel and try again.",
            show_alert=True
        )


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


def run_bot():
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
