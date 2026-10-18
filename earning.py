
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
    """Validate Telegram Mini App authentication data."""
    if not BOT_TOKEN or not init_data:
        return None

    try:
        pairs_list = parse_qsl(
            init_data,
            keep_blank_values=True,
            strict_parsing=True
        )
        pairs = dict(pairs_list)

        # Reject duplicate keys to avoid ambiguous authentication data.
        if len(pairs) != len(pairs_list):
            return None

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

        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            return None

        user = json.loads(pairs.get("user", "{}"))
        if not isinstance(user, dict):
            return None

        user_id = user.get("id")
        if type(user_id) is not int or user_id <= 0:
            return None

        return user

    except (
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError
    ):
        return None


def check_channel_membership(user_id):
    """Fail closed unless Telegram confirms membership."""
    if not BOT_TOKEN:
        return False, "Bot token is not configured."

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
        data = response.json()

        if not data.get("ok"):
            print("Telegram membership API returned an error.")
            return False, "Membership could not be verified. Try again."

        member = data.get("result", {})
        status = member.get("status")

        allowed = status in ("creator", "administrator", "member")

        if status == "restricted":
            allowed = member.get("is_member") is True

        if allowed:
            return True, None

        return False, "Join our channel before continuing."

    except requests.RequestException as exc:
        print("Telegram membership request failed:", str(exc))
        return False, "Membership verification is temporarily unavailable."

    except (ValueError, TypeError):
        return False, "Membership verification is temporarily unavailable."


@earning_bp.route("/api/verify-membership", methods=["POST"])
def verify_membership():
    data = request.get_json(silent=True) or {}
    init_data = data.get("initData", "")

    user = verify_init_data(init_data)

    if not user:
        return jsonify({
            "ok": False,
            "member": False,
            "message": "Invalid or expired Telegram session. Reopen the Mini App."
        }), 401

    member, error = check_channel_membership(user["id"])

    if not member:
        return jsonify({
            "ok": True,
            "member": False,
            "channel_url": CHANNEL_URL,
            "message": error
        }), 403

    return jsonify({
        "ok": True,
        "member": True,
        "user": {
            "id": user["id"],
            "first_name": user.get("first_name", "")
        }
    })


@earning_bp.route("/api/health", methods=["GET"])
def earning_health():
    return jsonify({"status": "ok"})

