
import os
import time
import hmac
import hashlib
import json
import sqlite3
from urllib.parse import parse_qsl
from functools import wraps

import requests
from flask import Blueprint, request, jsonify, g

earning_bp = Blueprint("earning", __name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL = "@freeearningofusdt"
CHANNEL_URL = "https://t.me/freeearningofusdt"
DATABASE = os.environ.get("DATABASE_PATH", "ads_payout.db")

AD_REWARD = 0.0025
REFERRAL_REWARD = 0.025
MIN_WITHDRAWAL = 5.0
WITHDRAWAL_FEE = 0.10

# Keep test mode enabled until real integrations are ready.
TEST_MODE = os.environ.get("ADS_TEST_MODE", "true").lower() == "true"


def connect_db():
    db = sqlite3.connect(DATABASE, timeout=15)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL DEFAULT '',
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            kind TEXT NOT NULL,
            reference TEXT UNIQUE NOT NULL,
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ad_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            fee REAL NOT NULL,
            net_amount REAL NOT NULL,
            network TEXT NOT NULL,
            wallet_address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL
        );
        """)


def verify_init_data(init_data):
    """Validate Telegram Mini App initData on the server."""
    if not BOT_TOKEN or not init_data:
        return None

    try:
        items = parse_qsl(init_data, keep_blank_values=True)
        pairs = dict(items)

        if len(pairs) != len(items):
            return None

        received_hash = pairs.pop("hash", None)
        if not received_hash:
            return None

        auth_date = int(pairs.get("auth_date", "0"))
        now = int(time.time())

        if auth_date > now + 60 or now - auth_date > 3600:
            return None

        check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(pairs.items())
        )

        secret = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        expected = hmac.new(
            secret,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, received_hash):
            return None

        user = json.loads(pairs.get("user", "{}"))

        if not isinstance(user, dict):
            return None

        if type(user.get("id")) is not int or user["id"] <= 0:
            return None

        return user

    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def check_channel_membership(user_id):
    """
    Return (True, None) if membership is confirmed.
    Return (False, message) if not a member or verification fails.
    """
    if not BOT_TOKEN:
        return False, "BOT_TOKEN is not configured."

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
            return False, "Telegram could not verify membership."

        member = data.get("result", {})
        status = member.get("status")

        if status in ("creator", "administrator", "member"):
            return True, None

        if status == "restricted" and member.get("is_member") is True:
            return True, None

        return False, "Join @freeearningofusdt before continuing."

    except (requests.RequestException, ValueError, KeyError) as exc:
        print("Membership verification failed:", exc)
        return False, "Membership verification is temporarily unavailable."


# Compatibility helper: existing code may expect a Boolean.
def is_channel_member(user_id):
    member, _ = check_channel_membership(user_id)
    return member


def require_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        payload = request.get_json(silent=True) or {}
        user = verify_init_data(payload.get("initData", ""))

        if not user:
            return jsonify({
                "ok": False,
                "message": "Invalid session. Reopen Ads Payout in Telegram."
            }), 401

        member, error = check_channel_membership(user["id"])

        if not member:
            return jsonify({
                "ok": False,
                "member": False,
                "channel_url": CHANNEL_URL,
                "message": error or "Join our Telegram channel to continue."
            }), 403

        g.telegram_user = user
        return func(*args, **kwargs)

    return wrapper


def get_balance(db, user_id):
    row = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM ledger "
        "WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    return round(row["total"], 8)


def make_referral_code(user_id):
    return hashlib.sha256(
        f"{user_id}:{BOT_TOKEN}".encode()
    ).hexdigest()[:12]


@earning_bp.route("/api/verify-membership", methods=["POST"])
@require_user
def verify_membership():
    user = g.telegram_user
    uid = user["id"]

    with connect_db() as db:
        db.execute(
            """INSERT OR IGNORE INTO users
               (user_id, first_name, referral_code, created_at)
               VALUES (?, ?, ?, ?)""",
            (
                uid,
                user.get("first_name", ""),
                make_referral_code(uid),
                int(time.time())
            )
        )

    return jsonify({
        "ok": True,
        "member": True,
        "user": {
            "id": uid,
            "first_name": user.get("first_name", "")
        }
    })


@earning_bp.route("/api/dashboard", methods=["POST"])
@require_user
def dashboard():
    uid = g.telegram_user["id"]

    with connect_db() as db:
        db.execute(
            """INSERT OR IGNORE INTO users
               (user_id, first_name, referral_code, created_at)
               VALUES (?, ?, ?, ?)""",
            (
                uid,
                g.telegram_user.get("first_name", ""),
                make_referral_code(uid),
                int(time.time())
            )
        )

        user = db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (uid,)
        ).fetchone()

        ads = db.execute(
            "SELECT COUNT(*) AS n FROM ad_sessions "
            "WHERE user_id = ? AND status = 'completed_test'",
            (uid,)
        ).fetchone()["n"]

        referral_count = db.execute(
            "SELECT COUNT(*) AS n FROM users WHERE referred_by = ?",
            (uid,)
        ).fetchone()["n"]

        referral_earnings = db.execute(
            "SELECT COALESCE(SUM(amount), 0) AS n FROM ledger "
            "WHERE user_id = ? AND kind = 'referral'",
            (uid,)
        ).fetchone()["n"]

        return jsonify({
            "ok": True,
            "test_mode": TEST_MODE,
            "balance_usd": get_balance(db, uid),
            "completed_test_ads": ads,
            "referral_count": referral_count,
            "referral_earnings_usd": round(referral_earnings, 8),
            "referral_code": user["referral_code"],
            "channel_url": CHANNEL_URL,
            "notice": (
                "TEST MODE: simulated ads are not real earnings "
                "and cannot be withdrawn."
                if TEST_MODE else
                "Live rewards require verified advertising provider callbacks."
            )
        })


@earning_bp.route("/api/test-ad/start", methods=["POST"])
@require_user
def start_test_ad():
    if not TEST_MODE:
        return jsonify({
            "ok": False,
            "message": "Test ads are disabled."
        }), 403

    import uuid

    uid = g.telegram_user["id"]
    session_id = str(uuid.uuid4())

    with connect_db() as db:
        db.execute(
            """INSERT INTO ad_sessions
               (id, user_id, status, created_at)
               VALUES (?, ?, 'started_test', ?)""",
            (session_id, uid, int(time.time()))
        )

    return jsonify({
        "ok": True,
        "test_mode": True,
        "session_id": session_id,
        "message": "Simulated test ad only. No real earnings are created."
    })


@earning_bp.route("/api/test-ad/complete", methods=["POST"])
@require_user
def complete_test_ad():
    if not TEST_MODE:
        return jsonify({
            "ok": False,
            "message": "Test ads are disabled."
        }), 403

    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")
    uid = g.telegram_user["id"]

    if not isinstance(session_id, str) or not session_id:
        return jsonify({
            "ok": False,
            "message": "Missing test session."
        }), 400

    with connect_db() as db:
        session = db.execute(
            "SELECT * FROM ad_sessions WHERE id = ? AND user_id = ?",
            (session_id, uid)
        ).fetchone()

        if not session or session["status"] != "started_test":
            return jsonify({
                "ok": False,
                "message": "Invalid or already completed test session."
            }), 409

        db.execute(
            "UPDATE ad_sessions SET status = 'completed_test' "
            "WHERE id = ? AND user_id = ?",
            (session_id, uid)
        )

    return jsonify({
        "ok": True,
        "test_mode": True,
        "message": (
            "Test completed. No balance was credited. "
            "Real rewards require verified provider callbacks."
        )
    })


@earning_bp.route("/api/referrals", methods=["POST"])
@require_user
def referrals():
    uid = g.telegram_user["id"]

    with connect_db() as db:
        user = db.execute(
            "SELECT referral_code FROM users WHERE user_id = ?",
            (uid,)
        ).fetchone()

        if not user:
            return jsonify({
                "ok": False,
                "message": "Open the dashboard first."
            }), 400

        bot_username = os.environ.get("BOT_USERNAME", "").lstrip("@")

        link = None
        if bot_username:
            link = (
                f"https://t.me/{bot_username}?start="
                f"{user['referral_code']}"
            )

        return jsonify({
            "ok": True,
            "referral_code": user["referral_code"],
            "referral_link": link,
            "reward_usd": REFERRAL_REWARD,
            "message": (
                "Referral rewards are not credited until referral "
                "eligibility and first verified ad completion are implemented."
            )
        })


@earning_bp.route("/api/withdrawals", methods=["POST"])
@require_user
def request_withdrawal():
    # Keep withdrawals disabled until live funding and admin approval
    # are implemented and tested.
    return jsonify({
        "ok": False,
        "message": (
            "Withdrawals are currently disabled while Ads Payout "
            "is in test mode."
        )
    }), 403


init_db()

