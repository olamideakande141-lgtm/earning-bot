import os
import uuid
from decimal import Decimal
from flask import Flask, request
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ChatMemberStatus

from earning import (
    init_earning_tables, register_user, get_balance,
    get_daily_counts, credit_verified_ad, request_withdrawal,
    LIMITS, REWARDS, REF, MIN_WD
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@freeearningofusdt"
CHANNEL_LINK = "https://t.me/freeearningofusdt"
WEBAPP_URL = "https://earning-bot-bdjm.onrender.com"

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return f"<h1 style='text-align:center;margin-top:80px'>✅ USDT Earn Bot Running!<br>{CHANNEL_USERNAME}<br><br>ad1: $0.01 x 5/day<br>ad2: $0.025 x 7/day</h1>"

@flask_app.route('/ad')
def ad_page():
    user_id = request.args.get('user', '0')
    ad_type = request.args.get('type', 'ad1')
    if ad_type not in REWARDS: ad_type = 'ad1'
    reward = REWARDS[ad_type]
    event_id = str(uuid.uuid4())
    return f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        body{{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:20px}}
        .card{{background:#1a1a1a;border:1px solid gold;border-radius:20px;padding:25px;max-width:400px;margin:20px auto}}
        .timer{{font-size:48px;color:gold;margin:15px}}
        button{{background:gold;color:#000;padding:15px;border:none;border-radius:10px;font-size:18px;font-weight:bold;width:100%;margin-top:15px}}
        button:disabled{{background:#444;color:#888}}
        .adbox{{background:#222;height:250px;display:flex;align-items:center;justify-content:center;border-radius:12px;margin:15px 0;border:1px dashed #555}}
    </style></head><body>
        <div class="card">
            <h2>📺 {ad_type.upper()} Ad</h2>
            <p>Earn <b>{reward} USDT</b> - Limit {LIMITS[ad_type]}/day</p>
            <div class="timer" id="timer">15</div>
            <p id="status">Ad playing...</p>
            <div class="adbox">ADS GALAXY AD WILL SHOW HERE<br>(After approval)</div>
            <button id="claim" disabled>⏳ Wait 15s</button>
        </div>
    <script>
        let s=15; const t=document.getElementById('timer'), c=document.getElementById('claim'), st=document.getElementById('status');
        let iv=setInterval(()=>{{ s--; t.textContent=s; if(s<=0){{ clearInterval(iv); st.textContent='✅ Complete!'; c.textContent='💰 Claim {reward} USDT'; c.disabled=false; c.style.background='#4ade80'; }} else{{ c.textContent='⏳ Wait '+s+'s'; }} }},1000);
        c.onclick=()=>{{ fetch('/verify?user={user_id}&event_id={event_id}&type={ad_type}').then(r=>r.json()).then(d=>{{ if(d.ok){{ st.textContent='🎉 Claimed '+d.reward+' USDT!'; c.textContent='✅ Done - Return to Bot'; setTimeout(()=>window.close(),1500); }} else{{ st.textContent='❌ '+d.message; }} }}); }};
    </script>
    </body></html>
    """

@flask_app.route('/verify')
def verify():
    user_id = request.args.get('user')
    event_id = request.args.get('event_id')
    ad_type = request.args.get('type', 'ad1')
    if not user_id or not event_id: return {"ok": False, "message": "Invalid"}
    try:
        result = credit_verified_ad(int(user_id), event_id, ad_type)
        return result
    except Exception as e:
        return {"ok": False, "message": str(e)}

async def is_joined(uid, ctx):
    try:
        m = await ctx.bot.get_chat_member(CHANNEL_USERNAME, uid)
        return m.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except:
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ref = int(context.args[0]) if context.args and context.args[0].isdigit() else None
    register_user(uid, ref)
    if not await is_joined(uid, context):
        kb=[[InlineKeyboardButton("📢 Join @freeearningofusdt", url=CHANNEL_LINK)],[InlineKeyboardButton("✅ Check Join", callback_data="check")]]
        await update.message.reply_text(f"⚠️ Join {CHANNEL_LINK} first!", reply_markup=InlineKeyboardMarkup(kb)); return
    bal = get_balance(uid); counts = get_daily_counts(uid)
    txt = f"🚀 *USDT Earn Bot*\\n\\n💰 Balance: `${bal} USDT`\\n\\n📺 Ad1: {counts['ad1']}/{LIMITS['ad1']} - ${REWARDS['ad1']}\\n📺 Ad2: {counts['ad2']}/{LIMITS['ad2']} - ${REWARDS['ad2']}\\n\\nRefer: ${REF} each"
    kb=[
        [InlineKeyboardButton(f"📺 Ad1 ${REWARDS['ad1']} ({counts['ad1']}/{LIMITS['ad1']})", callback_data="ad_ad1"), InlineKeyboardButton(f"📺 Ad2 ${REWARDS['ad2']} ({counts['ad2']}/{LIMITS['ad2']})", callback_data="ad_ad2")],
        [InlineKeyboardButton("💰 Balance", callback_data="bal"), InlineKeyboardButton("👥 Refer", callback_data="ref")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="wd")]
    ]
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def btns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    if q.data=="check":
        if not await is_joined(uid, context): await q.answer("❌ Not joined!", show_alert=True); return
        await q.edit_message_text("✅ Joined! Send /start"); return
    bal=get_balance(uid); counts=get_daily_counts(uid)
    if q.data=="bal":
        await q.edit_message_text(f"💰 Balance: ${bal} USDT\\nAd1: {counts['ad1']}/{LIMITS['ad1']}\\nAd2: {counts['ad2']}/{LIMITS['ad2']}\\nMin WD: ${MIN_WD}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))
    elif q.data.startswith("ad_"):
        ad_type=q.data.split("_")[1]
        cnt=counts.get(ad_type,0); lim=LIMITS[ad_type]
        if cnt>=lim: await q.edit_message_text(f"❌ {ad_type} limit {lim} reached today!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])); return
        url=f"{WEBAPP_URL}/ad?user={uid}&type={ad_type}"
        kb=[[InlineKeyboardButton(f"▶️ Open {ad_type.upper()} Ad", web_app=WebAppInfo(url=url))],[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await q.edit_message_text(f"📺 Watch {ad_type} Ad\\nReward: ${REWARDS[ad_type]}\\nProgress: {cnt}/{lim}", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data=="ref":
        link=f"https://t.me/{context.bot.username}?start={uid}"
        await q.edit_message_text(f"👥 Refer Link:\\n`{link}`\\nReward: ${REF}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))
    elif q.data=="wd":
        await q.edit_message_text(f"💸 Withdraw\\nBal: ${bal}\\nMin: ${MIN_WD}\\n\\nSend: `/withdraw 3 TRC20 your_wallet`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))
    elif q.data=="back":
        txt = f"🚀 *USDT Earn Bot*\\n\\n💰 Balance: `${bal} USDT`\\n\\n📺 Ad1: {counts['ad1']}/{LIMITS['ad1']}\\n📺 Ad2: {counts['ad2']}/{LIMITS['ad2']}"
        kb=[
            [InlineKeyboardButton(f"📺 Ad1 ${REWARDS['ad1']} ({counts['ad1']}/{LIMITS['ad1']})", callback_data="ad_ad1"), InlineKeyboardButton(f"📺 Ad2 ${REWARDS['ad2']} ({counts['ad2']}/{LIMITS['ad2']})", callback_data="ad_ad2")],
            [InlineKeyboardButton("💰 Balance", callback_data="bal"), InlineKeyboardButton("👥 Refer", callback_data="ref")],
            [InlineKeyboardButton("💸 Withdraw", callback_data="wd")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if len(context.args)<3: await update.message.reply_text("Usage: /withdraw 3 TRC20 your_wallet_address"); return
    try:
        amt=context.args[0]; net=context.args[1]; addr=context.args[2]
        res=request_withdrawal(uid, amt, net, addr)
        await update.message.reply_text(f"{'✅' if res['ok'] else '❌'} {res.get('message','')} Result: {res}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def run_flask(): flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
async def post_init(app): init_earning_tables()
def main():
    Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(os.environ.get("BOT_TOKEN")).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("withdraw", withdraw_cmd))
    app.add_handler(CallbackQueryHandler(btns))
    print("Bot Running ✅")
    app.run_polling()
if __name__=="__main__": main()
