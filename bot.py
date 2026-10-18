import os, uuid
from flask import Flask, request
from threading import Thread
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatMemberStatus

from earning import (
    init_earning_tables, register_user, get_balance,
    get_daily_ad_count, can_watch_ad, credit_verified_ad,
    DAILY_AD_LIMIT, AD_REWARD, MIN_WITHDRAWAL, REFERRAL_REWARD
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@freeearningofusdt"
CHANNEL_LINK = "https://t.me/freeearningofusdt"
WEBAPP_URL = "https://earning-bot-bdjm.onrender.com"

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return f"<h1 style='text-align:center;margin-top:100px'>✅ USDT Earn Bot Running!<br><a href='{CHANNEL_LINK}'>{CHANNEL_USERNAME}</a></h1>"

@flask_app.route('/ad')
def ad_page():
    user_id = request.args.get('user', '0')
    event_id = str(uuid.uuid4())
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        body{{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:20px}}
        .card{{background:#1a1a1a;border:1px solid gold;border-radius:20px;padding:30px;max-width:400px;margin:30px auto}}
        .timer{{font-size:50px;color:gold;margin:20px}} 
        button{{background:gold;color:#000;padding:15px 30px;border:none;border-radius:10px;font-size:18px;font-weight:bold;width:100%;margin-top:15px}}
        button:disabled{{background:#555;color:#888}}
    </style></head>
    <body>
        <div class="card">
            <h2>📺 Watch Ad</h2>
            <p>Earn {AD_REWARD} USDT</p>
            <div class="timer" id="timer">15</div>
            <p id="status">Please wait... Ad playing</p>
            <!-- AdsGalaxy Ad Container - will auto-fill after approval -->
            <div id="ad-container" style="background:#222;height:250px;display:flex;align-items:center;justify-content:center;border-radius:10px;margin:15px 0">
                <span>ADS GALAXY AD LOADS HERE</span>
            </div>
            <button id="claim" disabled>⏳ Wait 15s</button>
        </div>
    <script>
        let s=15; const t=document.getElementById('timer'), c=document.getElementById('claim'), st=document.getElementById('status');
        let iv=setInterval(()=>{{ s--; t.textContent=s; if(s<=0){{ clearInterval(iv); st.textContent='✅ Ad Complete!'; c.textContent='💰 Claim {AD_REWARD} USDT'; c.disabled=false; c.style.background='#4ade80'; }} else{{ c.textContent='⏳ Wait '+s+'s'; }} }},1000);
        c.onclick=()=>{{ fetch('/verify?user={user_id}&event_id={event_id}').then(r=>r.json()).then(d=>{{ if(d.ok){{ st.textContent='🎉 '+d.message; c.textContent='✅ Claimed! Return to Bot'; setTimeout(()=>window.close(),2000); }} else{{ st.textContent='❌ '+d.message; }} }}); }};
    </script>
    </body></html>
    """

@flask_app.route('/verify')
def verify():
    user_id = request.args.get('user')
    event_id = request.args.get('event_id')
    if not user_id or not event_id: return {"ok": False, "message": "Invalid"}
    result = credit_verified_ad(int(user_id), event_id)
    return result

async def is_joined(uid, ctx):
    try:
        m = await ctx.bot.get_chat_member(CHANNEL_USERNAME, uid)
        return m.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except: return False

def welcome_txt(bal, cnt):
    bar = "🟩"*cnt + "⬜"*(DAILY_AD_LIMIT-cnt)
    return f"🚀 *Welcome to USDT Earn Bot!*\\n\\nBalance: `${bal} USDT`\\nAds: {cnt}/{DAILY_AD_LIMIT}\\n{bar}\\n\\n{DAILY_AD_LIMIT-cnt} ads left today"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ref = int(context.args[0]) if context.args and context.args[0].isdigit() else None
    register_user(uid, ref)
    if not await is_joined(uid, context):
        kb=[[InlineKeyboardButton("📢 Join @freeearningofusdt", url=CHANNEL_LINK)],[InlineKeyboardButton("✅ Check Join", callback_data="check")]]
        await update.message.reply_text(f"⚠️ Join {CHANNEL_LINK} first!", reply_markup=InlineKeyboardMarkup(kb)); return
    bal=get_balance(uid); cnt=get_daily_ad_count(uid)
    kb=[
        [InlineKeyboardButton("💰 Balance", callback_data="bal"), InlineKeyboardButton(f"📺 Watch Ad ({cnt}/{DAILY_AD_LIMIT})", callback_data="ad")],
        [InlineKeyboardButton("👥 Refer", callback_data="ref"), InlineKeyboardButton("💸 Withdraw", callback_data="wd")]
    ]
    await update.message.reply_text(welcome_txt(bal,cnt), reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def btns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    if q.data=="check":
        if not await is_joined(uid, context): await q.answer("❌ Not joined!", show_alert=True); return
        await q.edit_message_text("✅ Joined! Send /start"); return
    bal=get_balance(uid); cnt=get_daily_ad_count(uid)
    if q.data=="bal":
        await q.edit_message_text(f"💰 *Balance*\\n\\n`${bal} USDT`\\nEarned today: {cnt*AD_REWARD}\\nMin Withdraw: ${MIN_WITHDRAWAL}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))
    elif q.data=="ad":
        if not can_watch_ad(uid):
            await q.edit_message_text(f"❌ Limit reached {cnt}/{DAILY_AD_LIMIT}\\nTomorrow!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])); return
        url=f"{WEBAPP_URL}/ad?user={uid}"
        kb=[[InlineKeyboardButton("📺 Open Ad Page", web_app=WebAppInfo(url=url))],[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await q.edit_message_text(f"📺 *Watch Ad to Earn {AD_REWARD} USDT*\\n\\nClick below, wait 15s, claim!\\nProgress: {cnt}/{DAILY_AD_LIMIT}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data=="ref":
        link=f"https://t.me/{context.bot.username}?start={uid}"
        await q.edit_message_text(f"👥 *Refer*\\n\\nYour link:\\n`{link}`\\nReward: ${REFERRAL_REWARD}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))
    elif q.data=="wd":
        await q.edit_message_text(f"💸 *Withdraw*\\n\\nBal: ${bal}\\nMin: ${MIN_WITHDRAWAL}\\n\\nFormat:\\n`/withdraw 5 TRC20 address`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))
    elif q.data=="back":
        kb=[
            [InlineKeyboardButton("💰 Balance", callback_data="bal"), InlineKeyboardButton(f"📺 Watch Ad ({cnt}/{DAILY_AD_LIMIT})", callback_data="ad")],
            [InlineKeyboardButton("👥 Refer", callback_data="ref"), InlineKeyboardButton("💸 Withdraw", callback_data="wd")]
        ]
        await q.edit_message_text(welcome_txt(bal,cnt), reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

def run_flask(): flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
async def post_init(app): init_earning_tables()
def main():
    Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(btns))
    app.run_polling()
if __name__=="__main__": main()
