import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from earning import create_user, get_user, can_watch, add_ad, today_ads, add_withdraw, withdraws
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN=os.getenv("BOT_TOKEN")
BOT_USERNAME=os.getenv("BOT_USERNAME")
MINI_APP_URL=os.getenv("MINI_APP_URL")
ADMIN_ID=int(os.getenv("ADMIN_ID","8323896060"))
FORCE_CHANNEL="@freeearningofusdt"
CHANNEL_LINK="https://t.me/freeearningofusdt"

async def is_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    joined = await is_joined(uid, context)
    if not joined:
        kb = [
            [InlineKeyboardButton("📢 Join @freeearningofusdt", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I Joined - Check", callback_data="check_join")]
        ]
        await update.message.reply_text(f"⚠️ Must join {FORCE_CHANNEL} to earn!\n\nJoin then click Check", reply_markup=InlineKeyboardMarkup(kb))
        return
    ref=context.args[0] if context.args else None
    create_user(update.effective_user, ref)
    u=get_user(update.effective_user.id)
    link=f"https://t.me/{BOT_USERNAME}?start={update.effective_user.id}"
    kb=[[InlineKeyboardButton("💰 Open App", web_app=WebAppInfo(url=MINI_APP_URL))],[InlineKeyboardButton("📺 Watch $0.005", callback_data="watch"), InlineKeyboardButton("💸 Withdraw $5", callback_data="wd")]]
    await update.message.reply_text(f"💰 Balance ${u['balance']:.4f}\n📺 {today_ads(u['user_id'])}/20\n👥 Ref {u['referrals']}\nLink: {link}\n$0.025/ref | $0.005/ad | Min $5 (you get $4)", reply_markup=InlineKeyboardMarkup(kb))

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    if q.data=="check_join":
        joined = await is_joined(uid, context)
        if not joined:
            await q.message.reply_text(f"❌ Not joined! Join {CHANNEL_LINK}"); return
        create_user(q.from_user, None); u=get_user(uid); link=f"https://t.me/{BOT_USERNAME}?start={uid}"
        kb=[[InlineKeyboardButton("💰 Open App", web_app=WebAppInfo(url=MINI_APP_URL))]]
        await q.message.reply_text(f"✅ Joined! Balance ${u['balance']:.4f}\nLink: {link}", reply_markup=InlineKeyboardMarkup(kb))
        return
    if q.data=="watch":
        if not await is_joined(uid, context): await q.message.reply_text(f"Join {CHANNEL_LINK} first"); return
        can,c=can_watch(uid)
        if not can: await q.message.reply_text("❌ 20/20 done today"); return
        add_ad(uid); u=get_user(uid); await q.message.reply_text(f"✅ +$0.005\nToday {c+1}/20\nBal ${u['balance']:.4f}")
    elif q.data=="wd":
        if not await is_joined(uid, context): await q.message.reply_text(f"Join {CHANNEL_LINK} first"); return
        u=get_user(uid)
        if u["balance"]<5: await q.message.reply_text(f"❌ Need $5, you have ${u['balance']:.4f}"); return
        context.user_data["wait_wallet"]=True; await q.message.reply_text("Send USDT TRC20 wallet:")
    elif q.data.startswith("ap_"):
        if q.from_user.id!=ADMIN_ID: return
        from bson import ObjectId; wd_id=q.data.split("_")[1]; wd=withdraws.find_one({"_id":ObjectId(wd_id)}); from earning import users; users.update_one({"user_id": wd["user_id"]}, {"$inc": {"balance": -wd["amount"]}}); withdraws.update_one({"_id": ObjectId(wd_id)}, {"$set": {"status": "approved"}}); await q.edit_message_text(f"✅ Paid ${wd['receive']} to {wd['user_id']}")
    elif q.data.startswith("rj_"):
        if q.from_user.id!=ADMIN_ID: return
        from bson import ObjectId; withdraws.update_one({"_id": ObjectId(q.data.split('_')[1])}, {"$set": {"status": "rejected"}}); await q.edit_message_text("❌ Rejected")

async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("wait_wallet"): return
    wd=add_withdraw(update.effective_user.id, 5, update.message.text)
    if not wd: await update.message.reply_text("❌ Low balance"); return
    await update.message.reply_text(f"✅ Requested $5 -> You get $4\nPending 24h")
    kb=[[InlineKeyboardButton(f"✅ Pay $4", callback_data=f"ap_{wd['_id']}"), InlineKeyboardButton("❌ Reject", callback_data=f"rj_{wd['_id']}")]]
    await context.bot.send_message(ADMIN_ID, f"💸 NEW WD\nUser {wd['user_id']}\n$5 -> $4\n{wd['wallet']}", reply_markup=InlineKeyboardMarkup(kb))
    context.user_data["wait_wallet"]=False

def get_app():
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wallet_handler))
    return app
