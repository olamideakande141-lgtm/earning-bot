import os
import telebot
from telebot import types
import sqlite3

8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc


conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL)')
conn.commit()

@bot.message_handler(commands=['start'])
def start(m):
    c.execute("INSERT OR IGNORE INTO users VALUES (?,0)", (m.from_user.id,))
    conn.commit()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Watch Ad +0.005", callback_data="watch"))
    kb.add(types.InlineKeyboardButton("Balance", callback_data="bal"))
    kb.add(types.InlineKeyboardButton("Withdraw", callback_data="wd"))
    bot.send_message(m.chat.id, "Earn 0.005 per ad - TON/BEP20/BTC\nClick Watch Ad to start!", reply_markup=kb)

@bot.callback_query_handler(func=lambda x: True)
def call(q):
    c.execute("SELECT balance FROM users WHERE id=?", (q.from_user.id,))
    bal = c.fetchone()[0]
    if q.data == "watch":
        c.execute("UPDATE users SET balance=balance+? WHERE id=?", (0.005, q.from_user.id))
        conn.commit()
        bot.answer_callback_query(q.id, "Earned 0.005!")
        bot.send_message(q.message.chat.id, f"Earned! Balance: {bal+0.005:.3f}")
    elif q.data == "bal":
        bot.send_message(q.message.chat.id, f"Balance: {bal:.3f}")
    else:
        if bal < 1:
            bot.send_message(q.message.chat.id, f"Min 1.0 needed. You have {bal:.3f}")
        else:
            bot.send_message(q.message.chat.id, "Send wallet:\nTON: UQ...\nBEP20: 0x...\nBTC: bc1...")

bot.polling()
