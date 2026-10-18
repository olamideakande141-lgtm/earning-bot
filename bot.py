
import os
import threading
import logging

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from flask import Flask, jsonify

from earning import earning_bp, check_channel_membership

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = "https://earning-bot-bdjm.onrender.com"
CHANNEL = "@freeearningofusdt"
CHANNEL_URL = "https://t.me/freeearningofusdt"

if not BOT_TOKEN:
    raise RuntimeError(
        "Missing BOT_TOKEN. Set it in your Render environment variables."
    )

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
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


def miniapp_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            "🚀 Open Ads Payout",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    return keyboard


def send_access(chat_id, user_id):
    is_member, error = check_channel_membership(user_id)

    if not is_member:
        bot.send_message(
            chat_id,
            "🔒 Welcome to Ads Payout!\n\n"
            "Join our official channel first, then tap "
            "\"I've Joined — Verify\".\n\n"
            f"{error or ''}",
            reply_markup=membership_keyboard()
        )
        return

    bot.send_message(
        chat_id,
        "✅ Channel membership verified.\n\n"
        "Welcome to Ads Payout. Tap below to open the Mini App.",
        reply_markup=miniapp_keyboard()
    )


@bot.message_handler(commands=["start"])
def start(message):
    send_access(
        message.chat.id,
        message.from_user.id
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "Ads Payout Help\n\n"
        "1. Join @freeearningofusdt.\n"
        "2. Tap /start and verify your membership.\n"
        "3. Open the Mini App.\n\n"
        "If verification fails, try again later."
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "verify_membership"
)
def verify_button(call):
    try:
        is_member, error = check_channel_membership(
            call.from_user.id
        )

        if not is_member:
            bot.answer_callback_query(
                call.id,
                "Membership not verified. Join the channel and retry.",
                show_alert=True
            )
            return

        bot.answer_callback_query(
            call.id,
            "Membership verified!"
        )

        bot.send_message(
            call.message.chat.id,
            "✅ You have joined the channel. Open Ads Payout below.",
            reply_markup=miniapp_keyboard()
        )

    except Exception:
        logger.exception("Membership callback failed")
        bot.answer_callback_query(
            call.id,
            "Verification failed. Please try again.",
            show_alert=True
        )


@app.route("/", methods=["GET"])
def home():
    # This is the Mini App entry page.
    # Financial actions must be implemented and authorized server-side.
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport"
        content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Ads Payout</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 28px 20px;
      min-height: 100vh;
      background: #101827;
      color: #f8fafc;
      font-family: Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    main {
      width: 100%;
      max-width: 430px;
      padding: 26px 20px;
      background: #1c293b;
      border: 1px solid #34445a;
      border-radius: 20px;
      text-align: center;
    }
    h1 { margin-top: 0; font-size: 30px; }
    p { color: #cbd5e1; line-height: 1.6; }
    button {
      width: 100%;
      padding: 15px;
      margin-top: 14px;
      border: 0;
      border-radius: 12px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
    }
    .primary { background: #229ed9; color: white; }
    .secondary { background: #334155; color: white; }
    #status { overflow-wrap: anywhere; }
  </style>
</head>
<body>
<main>
  <h1>Ads Payout</h1>
  <p id="intro">
    Join our official Telegram channel and verify your membership
    to continue.
  </p>

  <button id="join" class="primary">📢 Join Our Channel</button>
  <button id="verify" class="secondary">
    ✅ I've Joined — Verify
  </button>

  <p id="status" role="status"></p>
</main>

<script>
(function () {
  const tg = window.Telegram && window.Telegram.WebApp;
  const status = document.getElementById("status");
  const verifyButton = document.getElementById("verify");
  const joinButton = document.getElementById("join");

  if (tg) {
    tg.ready();
    tg.expand();
  }

  joinButton.addEventListener("click", function () {
    if (tg && typeof tg.openTelegramLink === "function") {
      tg.openTelegramLink("https://t.me/freeearningofusdt");
    } else {
      window.open(
        "https://t.me/freeearningofusdt",
        "_blank",
        "noopener"
      );
    }
  });

  verifyButton.addEventListener("click", async function () {
    if (!tg || !tg.initData) {
      status.textContent =
        "Open this page from your Ads Payout bot inside Telegram to verify.";
      return;
    }

    verifyButton.disabled = true;
    status.textContent = "Checking your channel membership...";

    try {
      const response = await fetch("/api/verify-membership", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ initData: tg.initData })
      });

      const result = await response.json();

      if (response.ok && result.member === true) {
        document.getElementById("intro").textContent =
          "Welcome, " + (result.user.first_name || "user") +
          ". Your channel membership is verified.";

        status.textContent =
          "Membership verified. Your dashboard and earning APIs must still be connected to this app.";

        joinButton.style.display = "none";
        verifyButton.style.display = "none";
      } else {
        status.textContent = result.message ||
          "Membership not verified. Join the channel and try again.";
      }
    } catch (error) {
      status.textContent =
        "Could not verify membership. Check your connection and retry.";
    } finally {
      verifyButton.disabled = false;
    }
  });
})();
</script>
</body>
</html>
"""


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Ads Payout"
    })


def run_bot():
    logger.info("Starting Ads Payout Telegram bot polling")
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=20
    )


if __name__ == "__main__":
    # Use one process for both Flask and Telegram polling.
    # Do not enable Flask's reloader, which can start duplicate threads.
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    port = int(os.environ.get("PORT", "10000"))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )

