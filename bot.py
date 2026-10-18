
import os
from decimal import Decimal
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row

# ==========================================
# USDT EARN SETTINGS
# ==========================================

DATABASE_URL = os.environ.get("DATABASE_URL")

DAILY_AD_LIMIT = 10
AD_REWARD = Decimal("0.05")
REFERRAL_REWARD = Decimal("0.25")
MIN_WITHDRAWAL = Decimal("5.00")

SUPPORTED_NETWORKS = {"TRC20", "ERC20", "BEP20"}


# ==========================================
# DATABASE CONNECTION
# Install: pip install "psycopg[binary]"
# Set DATABASE_URL in Render environment variables
# ==========================================

def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


def init_earning_tables():
    """Run once during application startup."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS earning_users (
                user_id BIGINT PRIMARY KEY,
                balance NUMERIC(18, 8) NOT NULL DEFAULT 0,
                referred_by BIGINT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ad_completions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES earning_users(user_id),
                provider_event_id TEXT NOT NULL UNIQUE,
                reward NUMERIC(18, 8) NOT NULL,
                completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES earning_users(user_id),
                amount NUMERIC(18, 8) NOT NULL,
                network TEXT NOT NULL,
                wallet_address TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


# ==========================================
# REGISTER / GET USER
# ==========================================

def register_user(user_id, referred_by=None):
    user_id = int(user_id)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO earning_users (user_id) VALUES (%s) "
            "ON CONFLICT (user_id) DO NOTHING",
            (user_id,)
        )

        if referred_by is not None:
            referred_by = int(referred_by)

            # Users cannot refer themselves.
            if referred_by != user_id:
                conn.execute("""
                    UPDATE earning_users
                    SET referred_by = %s
                    WHERE user_id = %s
                      AND referred_by IS NULL
                      AND EXISTS (
                          SELECT 1 FROM earning_users
                          WHERE user_id = %s
                      )
                """, (referred_by, user_id, referred_by))


def get_balance(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT balance FROM earning_users WHERE user_id = %s",
            (int(user_id),)
        ).fetchone()

    return Decimal(row["balance"]) if row else Decimal("0.00")


# ==========================================
# DAILY AD LIMIT
# 10 VERIFIED ADS PER UTC DAY
# ==========================================

def get_daily_ad_count(user_id):
    with get_db() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS total
            FROM ad_completions
            WHERE user_id = %s
              AND completed_at >= date_trunc('day', NOW() AT TIME ZONE 'UTC')
                                   AT TIME ZONE 'UTC'
              AND completed_at < (
                  date_trunc('day', NOW() AT TIME ZONE 'UTC')
                  + INTERVAL '1 day'
              ) AT TIME ZONE 'UTC'
        """, (int(user_id),)).fetchone()

    return int(row["total"])


def can_watch_ad(user_id):
    return get_daily_ad_count(user_id) < DAILY_AD_LIMIT


# ==========================================
# CREDIT A VERIFIED AD REWARD
# Call ONLY after your ad provider verifies
# a genuine completion server-side.
# provider_event_id must be unique per event.
# ==========================================

def credit_verified_ad(user_id, provider_event_id):
    if not provider_event_id:
        raise ValueError("A verified provider event ID is required.")

    user_id = int(user_id)

    with get_db() as conn:
        # Lock the user row to prevent concurrent reward races.
        user = conn.execute("""
            SELECT user_id FROM earning_users
            WHERE user_id = %s FOR UPDATE
        """, (user_id,)).fetchone()

        if not user:
            return {"ok": False, "message": "User is not registered."}

        today_count = conn.execute("""
            SELECT COUNT(*) AS total
            FROM ad_completions
            WHERE user_id = %s
              AND completed_at >=
                  (date_trunc('day', NOW() AT TIME ZONE 'UTC')
                   AT TIME ZONE 'UTC')
              AND completed_at <
                  ((date_trunc('day', NOW() AT TIME ZONE 'UTC')
                    + INTERVAL '1 day') AT TIME ZONE 'UTC')
        """, (user_id,)).fetchone()["total"]

        if int(today_count) >= DAILY_AD_LIMIT:
            return {"ok": False, "message": "Daily ad limit reached."}

        inserted = conn.execute("""
            INSERT INTO ad_completions
                (user_id, provider_event_id, reward)
            VALUES (%s, %s, %s)
            ON CONFLICT (provider_event_id) DO NOTHING
            RETURNING id
        """, (user_id, provider_event_id, AD_REWARD)).fetchone()

        if not inserted:
            return {"ok": False, "message": "This ad was already rewarded."}

        conn.execute("""
            UPDATE earning_users
            SET balance = balance + %s
            WHERE user_id = %s
        """, (AD_REWARD, user_id))

    return {
        "ok": True,
        "reward": str(AD_REWARD),
        "message": f"{AD_REWARD} USDT credited."
    }


# ==========================================
# REFERRAL REWARD
# Call only once after your own referral
# eligibility checks have been satisfied.
# ==========================================

def credit_referral_reward(referrer_id, referred_user_id):
    referrer_id = int(referrer_id)
    referred_user_id = int(referred_user_id)

    if referrer_id == referred_user_id:
        return False

    with get_db() as conn:
        referred = conn.execute("""
            SELECT referred_by
            FROM earning_users
            WHERE user_id = %s
            FOR UPDATE
        """, (referred_user_id,)).fetchone()

        if not referred or referred["referred_by"] != referrer_id:
            return False

        # A dedicated unique reward ledger should be added before
        # enabling this function in production. Do not call repeatedly.
        return False


# ==========================================
# WITHDRAWAL REQUEST
# This creates a pending request only.
# It does NOT send USDT automatically.
# ==========================================

def request_withdrawal(user_id, amount, network, wallet_address):
    user_id = int(user_id)
    amount = Decimal(str(amount))
    network = str(network).upper().strip()
    wallet_address = str(wallet_address).strip()

    if not amount.is_finite() or amount < MIN_WITHDRAWAL:
        return {"ok": False, "message": "Minimum withdrawal is 5 USDT."}

    if network not in SUPPORTED_NETWORKS:
        return {"ok": False, "message": "Unsupported network."}

    if not wallet_address:
        return {"ok": False, "message": "Wallet address is required."}

    with get_db() as conn:
        user = conn.execute("""
            SELECT balance FROM earning_users
            WHERE user_id = %s FOR UPDATE
        """, (user_id,)).fetchone()

        if not user:
            return {"ok": False, "message": "User is not registered."}

        if Decimal(user["balance"]) < amount:
            return {"ok": False, "message": "Insufficient balance."}

        # Reserve the amount immediately so it cannot be requested twice.
        conn.execute("""
            UPDATE earning_users
            SET balance = balance - %s
            WHERE user_id = %s
        """, (amount, user_id))

        conn.execute("""
            INSERT INTO withdrawal_requests
                (user_id, amount, network, wallet_address, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """, (user_id, amount, network, wallet_address))

    return {
        "ok": True,
        "message": "Withdrawal submitted for admin approval."
    }
