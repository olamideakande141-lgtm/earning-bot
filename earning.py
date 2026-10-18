
import os
import time
import hmac
import hashlib
import json
from urllib.parse import parse_qsl

import requests
from flask import Blueprint, request, jsonify

earning_bp = Blueprint("earning", __name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL = "@freeearningofusdt"
CHANNEL_URL = "https://t.me/freeearningofusdt"
MAX_AUTH_AGE = 3600


def verify_init_data(init_data):
    """Validate Telegram Mini App initData server-side."""
    if not BOT_TOKEN or not init_data:
        return None

    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = pairs.pop("hash", None)

        if not received_hash:
            return None

        auth_date = int(pairs.get("auth_date", "0"))
        now = int(time.time())

        if auth_date > now + 60 or now - auth_date > MAX_AUTH_AGE:
            return None

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(pairs.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        user = json.loads(pairs.get("user", "{}"))
        user_id = user.get("id")

        if not isinstance(user_id, int) or user_id <= 0:
            return None

        return user

    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def check_channel_membership(user_id):
    """Return True only when Telegram confirms channel membership."""
    if not BOT_TOKEN:
        return False

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
            params={
                "chat_id": CHANNEL,
                "user_id": user_id
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            return False

        member = result["result"]
        status = member.get("status")

        if status in ("creator", "administrator", "member"):
            return True

        return (
            status == "restricted"
            and member.get("is_member") is True
        )

    except (requests.RequestException, ValueError, KeyError):
        return False


@earning_bp.route("/api/verify-membership", methods=["POST"])
def verify_membership():
    data = request.get_json(silent=True) or {}
    init_data = data.get("initData", "")

    user = verify_init_data(init_data)

    if not user:
        return jsonify({
            "ok": False,
            "member": False,
            "error": "Invalid or expired Telegram session. Reopen the Mini App."
        }), 401

    if not check_channel_membership(user["id"]):
        return jsonify({
            "ok": True,
            "member": False,
            "channel_url": CHANNEL_URL,
            "message": "Join our Telegram channel before continuing."
        }), 403

    return jsonify({
        "ok": True,
        "member": True,
        "user": {
            "id": user["id"],
            "first_name": user.get("first_name", "")
        }
    })
