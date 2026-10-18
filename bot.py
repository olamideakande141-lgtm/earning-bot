import os
import threading
from decimal import Decimal
import psycopg
from psycopg.rows import dict_row
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# === YOUR EXISTING CODE ===
DATABASE_URL=os.environ.get("DATABASE_URL")
BOT_TOKEN=os.environ.get("BOT_TOKEN")
LIMITS={"ad1":5,"ad2":7}
REWARDS={"ad1":Decimal("0.01"),"ad2":Decimal("0.025")}
REF=Decimal("0.25")
MIN_WD=Decimal("3.00")

def get_db():
    if not DATABASE_URL: raise RuntimeError("DATABASE_URL missing")
    return psycopg.connect(DATABASE_URL,row_factory=dict_row)

def init_earning_tables():
    with get_db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS earning_users (user_id BIGINT PRIMARY KEY, balance NUMERIC(18,8) DEFAULT 0, referred_by BIGINT, created_at TIMESTAMPTZ DEFAULT NOW())")
        conn.execute("CREATE TABLE IF NOT EXISTS ad_completions (id BIGSERIAL PRIMARY KEY, user_id BIGINT REFERENCES earning_users(user_id), provider_event_id TEXT UNIQUE NOT NULL, ad_type TEXT NOT NULL, reward NUMERIC(18,8) NOT NULL, completed_at TIMESTAMPTZ DEFAULT NOW())")
        conn.execute("CREATE TABLE IF NOT EXISTS withdrawal_requests (id BIGSERIAL PRIMARY KEY, user_id BIGINT REFERENCES earning_users(user_id), amount NUMERIC(18,8) NOT NULL, network TEXT NOT NULL, wallet_address TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TIMESTAMPTZ DEFAULT NOW())")
        conn.commit()

def register_user(user_id,referred_by=None):
    user_id=int(user_id)
    with get_db() as conn:
        conn.execute("INSERT INTO earning_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",(user_id,))
        if referred_by and int(referred_by)!=user_id:
            r=conn.execute("SELECT referred_by FROM earning_users WHERE user_id=%s",(user_id,)).fetchone()
            if r and r["referred_by"] is None:
                conn.execute("UPDATE earning_users SET referred_by=%s WHERE user_id=%s",(int(referred_by),user_id))
                conn.execute("UPDATE earning_users SET balance=balance+%s WHERE user_id=%s",(REF,int(referred_by)))
        conn.commit()

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
    reward=REWARDS[ad_type]; limit=LIMITS[ad_type]
    with get_db() as conn:
        u=conn.execute("SELECT user_id FROM earning_users WHERE user_id=%s FOR UPDATE",(int(user_id),)).fetchone()
        if not u: return {"ok":False,"message":"Not registered"}
        cnt=conn.execute("SELECT COUNT(*) as c FROM ad_completions WHERE user_id=%s AND ad_type=%s AND completed_at >= date_trunc('day', NOW() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'",(int(user_id),ad_type)).fetchone()["c"]
        if int(cnt)>=limit: return {"ok":False,"message":f"Limit {limit} reached"}
        ins=conn.execute("INSERT INTO ad_completions (user_id,provider_event_id,ad_type,reward) VALUES (%s,%s,%s,%s) ON CONFLICT (provider_event_id) DO NOTHING RETURNING id",(int(user_id),provider_event_id,ad_type,reward)).fetchone()
        if not ins: return {"ok":False,"message":"Already rewarded"}
        conn.execute("UPDATE earning_users SET balance=balance+%s WHERE user_id=%s",(reward,int(user_id)))
        conn.commit()
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
        conn.commit()
    return {"ok":True}

# === BOT HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    ref = args[0] if args else None
    try:
        init_earning_tables()
        register_user(user_id, ref)
        bal = get_balance(user_id)
        counts = get_daily_counts(user_id)
    except Exception as e:
        await update.message.reply_text(f"DB Error: {e}")
        return

    text = f"Welcome! 💰\n\nBalance: ${bal}\nAd1: {counts['ad1']}/{LIMITS['ad1']} | Ad2: {counts['ad2']}/{LIMITS['ad2']}\nMin Withdraw: ${MIN_WD}"
    keyboard = [[InlineKeyboardButton("Watch Ad1 $0.01", callback_data="ad1"), InlineKeyboardButton("Watch Ad2 $0.025", callback_data="ad2")],
                [InlineKeyboardButton("Balance", callback_data="bal"), InlineKeyboardButton("Withdraw", callback_data="wd")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "bal":
        bal = get_balance(user_id)
        await query.edit_message_text(f"Balance: ${bal}")
    elif query.data.startswith("ad"):
        # Simulate verified ad - in production verify with provider
        import uuid
        res = credit_verified_ad(user_id, str(uuid.uuid4()), query.data)
        if res["ok"]:
            await query.edit_message_text(f"Credited ${res['reward']}! 🎉")
        else:
            await query.edit_message_text(f"Failed: {res['message']}")
    elif query.data == "wd":
        await query.edit_message_text(f"Send: /withdraw <amount> <network> <address>\nExample: /withdraw 3 BEP20 0x...")

async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /withdraw <amount> <network> <address>")
        return
    amount, network, addr = context.args[0], context.args[1], context.args[2]
    res = request_withdrawal(update.effective_user.id, amount, network, addr)
    await update.message.reply_text("Withdrawal requested!" if res["ok"] else f"Failed: {res['message']}")

# === FLASK + BOT RUNNER ===
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot is Running! ✅"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing! Add it in Environment")
        return
    init_earning_tables()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("withdraw", withdraw_cmd))
    application.add_handler(CallbackQueryHandler(button))
    print("Bot starting polling...")
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
