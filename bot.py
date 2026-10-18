
import os
import uuid
from flask import Flask
from threading import Thread
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatMemberStatus
import asyncio

# Your earning logic
from earning import (
    init_earning_tables, register_user, get_balance, 
    get_daily_ad_count, can_watch_ad, credit_verified_ad,
    request_withdrawal, DAILY_AD_LIMIT, AD_REWARD,
    MIN_WITHDRAWAL, REFERRAL_REWARD, SUPPORTED_NETWORKS
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@freeearningofusdt"
CHANNEL_LINK = "https://t.me/freeearningofusdt"

flask_app = Flask(__name__)

# PREMIUM WEB DASHBOARD
@flask_app.route('/')
def home():
    return f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body{{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:40px}}
        .card{{background:linear-gradient(135deg,#1a1a1a,#2d2d2d);border:1px solid #d4af37;border-radius:20px;padding:30px;max-width:400px;margin:0 auto}}
        .coin{{width:100px;height:100px;background:gold;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:30px;font-weight:bold;color:#000}}
        h1{{color:#d4af37}} .bal{{color:#4ade80;font-size:28px}} 
        .btn{{background:#d4af37;color:#000;padding:12px 25px;border-radius:10px;text-decoration:none;display:inline-block;margin-top:20px;font-weight:bold}}
    </style></head>
    <body>
        <div class="card">
            <div class="coin">USDT</div>
            <h1>USDT Earn Bot</h1>
            <p>✅ Bot Is Running!</p>
            <p>Channel: {CHANNEL_LINK}</p>
            <p>💰 {AD_REWARD} USDT per ad<br>📺 {DAILY_AD_LIMIT} ads/day<br>👥 {REFERRAL_REWARD} USDT per referral</p>
            <a class="btn" href="{CHANNEL_LINK}">Join Channel</a>
        </div>
    </body>
    </html>
    """

async def is_joined(user_id, context):
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except:
        return False

def premium_welcome_text(balance, count):
    progress_bar = "🟩" * count + "⬜" * (DAILY_AD_LIMIT - count)
    return (
        f"🚀 *Welcome to USDT Earn Bot!*\n\n"
        f"Earn USDT rewards by watching short ads and inviting friends\\.\n"
        f"100% secure • Instant payouts • No deposits required\n\n"
        f"💰 *Your Balance*\n"
        f"`${balance} USDT` \n\n"
        f"📊 *Daily Progress*\n"
        f"Ads Watched: {count}/{DAILY_AD_LIMIT}\n"
        f"{progress_bar}\n\n"
        f"{DAILY_AD_LIMIT - count} ads remaining today"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ref = None
    if context.args:
        try: ref = int(context.args[0])
        except: pass
    
    register_user(user_id, ref)
    
    if not await is_joined(user_id, context):
        kb = [[InlineKeyboardButton("📢 Join Channel @freeearningofusdt", url=CHANNEL_LINK)],
              [InlineKeyboardButton("✅ I Joined - Check", callback_data="check_join")]]
        await update.message.reply_text(
            f"⚠️ *Must Join Channel First!*\n\nTo use this bot, please join:\n{CHANNEL_LINK}",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )
        return

    balance = get_balance(user_id)
    count = get_daily_ad_count(user_id)
    
    kb = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton(f"📺 Watch Ad ({DAILY_AD_LIMIT}/day)", callback_data="watch_ad")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer"),
         InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]
    
    await update.message.reply_text(
        premium_welcome_text(balance, count),
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    
    if q.data == "check_join":
        if not await is_joined(user_id, context):
            await q.answer("❌ Not joined yet!", show_alert=True)
            return
        await q.edit_message_text("✅ Joined! Send /start again")
        return

    balance = get_balance(user_id)
    count = get_daily_ad_count(user_id)

    if q.data == "balance":
        await q.edit_message_text(
            f"💰 *Balance Details*\n\n"
            f"Current: `${balance} USDT`\n"
            f"Today earned: `{count * AD_REWARD} USDT`\n"
            f"Ads: {count}/{DAILY_AD_LIMIT}\n\n"
            f"Min Withdraw: ${MIN_WITHDRAWAL}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif q.data == "watch_ad":
        if not can_watch_ad(user_id):
            await q.edit_message_text(f"❌ Limit reached! {DAILY_AD_LIMIT}/{DAILY_AD_LIMIT} today.\nCome back tomorrow!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))
            return
        # Simulate verified ad for demo - replace with real ad provider callback
        event_id = str(uuid.uuid4())
        result = credit_verified_ad(user_id, event_id)
        new_bal = get_balance(user_id)
        new_count = get_daily_ad_count(user_id)
        await q.edit_message_text(
            f"✅ *Ad Watched!*\n\n+{AD_REWARD} USDT credited\nNew Balance: `${new_bal} USDT`\nProgress: {new_count}/{DAILY_AD_LIMIT}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📺 Watch Next", callback_data="watch_ad")],[InlineKeyboardButton("🔙 Menu", callback_data="back")]])
        )
    elif q.data == "refer":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await q.edit_message_text(
            f"👥 *Referral Program*\n\nYour Link:\n`{link}`\n\nReward: ${REFERRAL_REWARD} USDT per friend\n\nShare and earn!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif q.data == "withdraw":
        await q.edit_message_text(
            f"💸 *Withdrawal*\n\nBalance: ${balance}\nMin: ${MIN_WITHDRAWAL}\nNetworks: {', '.join(SUPPORTED_NETWORKS)}\n\n"
            f"Format:\n`/withdraw 5 TRC20 YourAddress`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif q.data == "back":
        await q.edit_message_text(
            premium_welcome_text(balance, count),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Balance", callback_data="balance"),
                 InlineKeyboardButton(f"📺 Watch Ad ({DAILY_AD_LIMIT}/day)", callback_data="watch_ad")],
                [InlineKeyboardButton("👥 Refer", callback_data="refer"),
                 InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
            ]), parse_mode="Markdown"
        )

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def post_init(application):
    init_earning_tables()
    print("✅ Tables initialized")

def main():
    Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling()

if __name__ == "__main__":
    main()
