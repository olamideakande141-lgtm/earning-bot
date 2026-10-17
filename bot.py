import os, threading
from flask import Flask, render_template
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    webapp_url = "https://earning-bot-bdjm.onrender.com/"
    btn = types.InlineKeyboardButton(text="🚀 Launch App", web_app=types.WebAppInfo(url=webapp_url))
    markup.add(btn)
    bot.send_message(message.chat.id, f"Welcome {message.from_user.first_name}!\n\nClick to open USDT Earn App 👇", reply_markup=markup)

def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
