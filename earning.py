import os
from decimal import Decimal
import psycopg
from psycopg.rows import dict_row
DATABASE_URL=os.environ.get("DATABASE_URL")
LIMITS={"ad1":20,"ad2":20}
REWARDS={"ad1":Decimal("0.0025"),"ad2":Decimal("0.0025")}
REF=Decimal("0.25")
MIN_WD=Decimal("3.00")
TOTAL_DAILY_LIMIT=20
def get_db():
    if not DATABASE_URL: raise RuntimeError("DATABASE_URL missing")
    return psycopg.connect(DATABASE_URL,row_factory=dict_row)
def init_earning_tables():
    with get_db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS earning_users (user_id BIGINT PRIMARY KEY, balance NUMERIC(18,8) DEFAULT 0, referred_by BIGINT, created_at TIMESTAMPTZ DEFAULT NOW())")
        conn.execute("CREATE TABLE IF NOT EXISTS ad_completions (id BIGSERIAL PRIMARY KEY, user_id BIGINT REFERENCES earning_users(user_id), provider_event_id TEXT UNIQUE NOT NULL, ad_type TEXT NOT NULL, reward NUMERIC(18,8) NOT NULL, completed_at TIMESTAMPTZ DEFAULT NOW())")
        conn.execute("CREATE TABLE IF NOT EXISTS withdrawal_requests (id BIGSERIAL PRIMARY KEY, user_id BIGINT REFERENCES earning_users(user_id), amount NUMERIC(18,8) NOT NULL, network TEXT NOT NULL, wallet_address TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TIMESTAMPTZ DEFAULT NOW())")
def register_user(user_id,referred_by=None):
    user_id=int(user_id)
    with get_db() as conn:
        conn.execute("INSERT INTO earning_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",(user_id,))
        if referred_by and int(referred_by)!=user_id:
            r=conn.execute("SELECT referred_by FROM earning_users WHERE user_id=%s",(user_id,)).fetchone()
            if r and r["referred_by"] is None:
                conn.execute("UPDATE earning_users SET referred_by=%s WHERE user_id=%s",(int(referred_by),user_id))
                conn.execute("UPDATE earning_users SET balance=balance+%s WHERE user_id=%s",(REF,int(referred_by)))
def get_balance(user_id):
    with get_db() as conn:
        row=conn.execute("SELECT balance FROM earning_users WHERE user_id=%s",(int(user_id),)).fetchone()
    return Decimal(row["balance"]) if row else Decimal("0")
def get_daily_counts(user_id):
    with get_db() as conn:
        rows=conn.execute("SELECT ad_type, COUNT(*) as c FROM ad_completions WHERE user_id=%s AND completed_at >= date_trunc('day', NOW() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC' GROUP BY ad_type",(int(user_id),)).fetchall()
    counts={"ad1":0,"ad2":0}
    for x in rows: counts[x["ad_type"]]=int(x["c"])
    return counts
def credit_verified_ad(user_id,provider_event_id,ad_type):
    if ad_type not in REWARDS: return {"ok":False,"message":"Invalid"}
    reward=REWARDS[ad_type]
    with get_db() as conn:
        u=conn.execute("SELECT user_id FROM earning_users WHERE user_id=%s FOR UPDATE",(int(user_id),)).fetchone()
        if not u: return {"ok":False,"message":"Not registered"}
        total=conn.execute("SELECT COUNT(*) as c FROM ad_completions WHERE user_id=%s AND completed_at >= date_trunc('day', NOW() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'",(int(user_id),)).fetchone()["c"]
        if int(total)>=TOTAL_DAILY_LIMIT: return {"ok":False,"message":f"Daily limit {TOTAL_DAILY_LIMIT} reached"}
        ins=conn.execute("INSERT INTO ad_completions (user_id,provider_event_id,ad_type,reward) VALUES (%s,%s,%s,%s) ON CONFLICT (provider_event_id) DO NOTHING RETURNING id",(int(user_id),provider_event_id,ad_type,reward)).fetchone()
        if not ins: return {"ok":False,"message":"Already rewarded"}
        conn.execute("UPDATE earning_users SET balance=balance+%s WHERE user_id=%s",(reward,int(user_id)))
    return {"ok":True,"reward":str(reward)}
def request_withdrawal(user_id,amount,network,wallet_address):
    amount=Decimal(str(amount))
    with get_db() as conn:
        row=conn.execute("SELECT balance FROM earning_users WHERE user_id=%s FOR UPDATE",(int(user_id),)).fetchone()
        if not row: return {"ok":False,"message":"Not registered"}
        if Decimal(row["balance"])<amount: return {"ok":False,"message":"Insufficient"}
        if amount<MIN_WD: return {"ok":False,"message":f"Min {MIN_WD}"}
        conn.execute("UPDATE earning_users SET balance=balance-%s WHERE user_id=%s",(amount,int(user_id)))
        conn.execute("INSERT INTO withdrawal_requests (user_id,amount,network,wallet_address) VALUES (%s,%s,%s,%s)",(int(user_id),amount,network,wallet_address))
    return {"ok":True}
