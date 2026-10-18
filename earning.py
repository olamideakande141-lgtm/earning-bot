
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

# Test mode does not create withdrawable money.
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
            f"{key}={value}" for key, value in sorted(pairs.items())
        )

        secret = hmac.new(
            b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
        ).digest()

        expected = hmac.new(
            secret, check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, received_hash):
            return None

        user = json.loads(pairs.get("user", "{}"))
        if type(user.get("id")) is not int:
            return None

        return user

    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def is_channel_member(user_id):
    if not BOT_TOKEN:
        return False

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
            params={"chat_id": CHANNEL, "user_id": user_id},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            return False

        member = data["result"]
        status = member.get("status")

        return (
            status in ("creator", "administrator", "member")
            or (
                status == "restricted"
                and member.get("is_member") is True
            )
        )

    except (requests.RequestException, ValueError, KeyError):
        return False


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

        if not is_channel_member(user["id"]):
            return jsonify({
                "ok": False,
                "member": False,
                "channel_url": CHANNEL_URL,
                "message": "Join our Telegram channel to continue."
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
            "SELECT * FROM users WHERE user_id = ?", (uid,)
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
        "message": "This is a simulated test ad, not a real advertisement."
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
        return jsonify({"ok": False, "message": "Missing test session."}), 400

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
            "Test completed. No cash balance was credited. "
            "A real provider must verify live ad completion."
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

        return jsonify({
            "ok": True,
            "referral_code": user["referral_code"],
            "referral_link": (
                "https://t.me/YOUR_BOT_USERNAME?start="
                + user["referral_code"]
            ),
            "reward_usd": REFERRAL_REWARD,
            "message": "Referral rewards require verified eligibility."
        })


@earning_bp.route("/api/withdrawals", methods=["POST"])
@require_user
def request_withdrawal():
    if TEST_MODE:
        return jsonify({
            "ok": False,
            "message": "Withdrawals are disabled in test mode."
        }), 403

    payload = request.get_json(silent=True) or {}
    uid = g.telegram_user["id"]

    try:
        amount = round(float(payload.get("amount", 0)), 8)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "message": "Invalid amount."}), 400

    network = payload.get("network")
    address = payload.get("wallet_address", "")

    if amount < MIN_WITHDRAWAL:
        return jsonify({
            "ok": False,
            "message": "Minimum withdrawal is 5 USDT equivalent."
        }), 400

    if network not in ("TRC20", "ERC20"):
        return jsonify({"ok": False, "message": "Invalid network."}), 400

    if not isinstance(address, str) or not address.strip() or len(address) > 200:
        return jsonify({"ok": False, "message": "Invalid wallet address."}), 400

    fee = round(amount * WITHDRAWAL_FEE, 8)
    net = round(amount - fee, 8)

    with connect_db() as db:
        balance = get_balance(db, uid)

        pending = db.execute(
            "SELECT COALESCE(SUM(amount), 0) AS n FROM withdrawals "
            "WHERE user_id = ? AND status IN ('pending', 'approved')",
            (uid,)
        ).fetchone()["n"]

        if amount > balance - pending:
            return jsonify({
                "ok": False,
                "message": "Insufficient available balance."
            }), 400

        db.execute(
            """INSERT INTO withdrawals
               (user_id, amount, fee, net_amount, network,
                wallet_address, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                uid, amount, fee, net, network,
                address.strip(), int(time.time())
            )
        )

    return jsonify({
        "ok": True,
        "status": "pending",
        "requested": amount,
        "fee": fee,
        "estimated_net": net,
        "message": "Request submitted for manual admin review."
    })


init_db()
