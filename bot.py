
import os
import telebot
from flask import Flask
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN", "8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Bot is online! Balance: 0.000")

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    bot.reply_to(m, "Bot working!")

@app.route('/')
def home():
    return "Bot running"

def run_bot():
    bot.infinity_polling()

Thread(target=run_bot).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
