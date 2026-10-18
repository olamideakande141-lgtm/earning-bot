import os, threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = "8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc"
CHANNEL_USERNAME = "@freeearningofusdt"
CHANNEL_LINK = "https://t.me/freeearningofusdt"
BOT_USERNAME = "earning_12_1_bot"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

@app.route("/")
def home():
    return open("index.html","r",encoding="utf-8").read()

def is_member(uid):
    try:
        m=bot.get_chat_member(CHANNEL_USERNAME,uid)
        return m.status in ["member","administrator","creator"]
    except:
        return True

@bot.message_handler(commands=["start"])
def start(message):
    if not is_member(message.from_user.id):
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Join @freeearningofusdt",url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton(text="I Joined",callback_data="check_join"))
        bot.send_message(message.chat.id,"Join @freeearningofusdt first!",reply_markup=markup)
        return
    markup=types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Launch App",web_app=types.WebAppInfo(url="https://earning-bot-bdjm.onrender.com/")))
    bot.send_message(message.chat.id,f"Welcome! https://t.me/{BOT_USERNAME}?start={message.from_user.id} | Task1=0.25 Task2=0.5 Ref=0.25 Ad1=0.01x5 Ad2=0.025x7 2-5sec",reply_markup=markup)

@bot.callback_query_handler(func=lambda c:c.data=="check_join")
def check_join(call):
    if is_member(call.from_user.id):
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Launch App",web_app=types.WebAppInfo(url="https://earning-bot-bdjm.onrender.com/")))
        bot.edit_message_text(f"Verified! https://t.me/{BOT_USERNAME}?start={call.from_user.id}",call.message.chat.id,call.message.message_id,reply_markup=markup)
    else:
        bot.answer_callback_query(call.id,"Not joined!",show_alert=True)

def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot,daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
