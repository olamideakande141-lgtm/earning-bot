import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@freeearningofusdt")
CHANNEL_ID = CHANNEL.replace("@", "")

def is_user_joined(user_id):
    # IF BOT TOKEN NOT SET, ALLOW USER TO PASS - SO DASHBOARD SHOWS
    if not BOT_TOKEN:
        return True
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": CHANNEL, "user_id": user_id}
        r = requests.get(url, params=params, timeout=5).json()
        status = r.get("result", {}).get("status", "")
        # Allow all valid statuses
        return status in ["creator", "administrator", "member", "restricted"]
    except:
        # IF API FAILS, STILL ALLOW - TO SHOW DASHBOARD
        return True

# EARNING LOGIC
AD_REWARD = 0.0025
DAILY_LIMIT = 20
MIN_WITHDRAW = 5.0
REFERRAL_REWARD = 0.25
