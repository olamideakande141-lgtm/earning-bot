import os, threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = "8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Inter,sans-serif}
body{background:#0b0b14;color:white;padding:0 0 90px 0}
.header{display:flex;justify-content:space-between;align-items:center;padding:16px 20px}
.logo{width:34px;height:34px;background:linear-gradient(135deg,#00d68f,#00ff88);border-radius:10px;display:flex;align-items:center;justify-content:center;color:#000}
.online{color:#00ff88;font-size:12px;background:#10281c;border:1px solid #1a4a2e;padding:5px 12px;border-radius:20px}
.xp-card{margin:15px;background:#181826;border-radius:22px;padding:22px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a}
.xp-card p{color:#6b6b8a;letter-spacing:1px;font-size:12px;font-weight:700}
.xp-card h1{font-size:42px;margin:6px 0 4px 0}
.xp-card h1 span{font-size:22px;color:#6b6b8a}
.xp-card small{color:#3dd68c;font-size:13px}
.gem{width:78px;height:78px;background:linear-gradient(135deg,#00d68f,#00ff88);border-radius:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px #00ff8855;transform:rotate(-5deg);color:#000;font-size:38px}
.btn-row{display:flex;gap:12px;padding:0 16px}
.btn{flex:1;padding:16px;border-radius:14px;border:none;font-weight:700;font-size:16px;display:flex;align-items:center;justify-content:center;gap:8px}
.btn-earn{background:#00d68f;color:#000}
.btn-with{background:#1e1e32;color:white;border:1px solid #2a2a45}
.stats{display:flex;gap:12px;padding:16px}
.stat{flex:1;background:#181826;padding:18px 10px;border-radius:18px;text-align:center;border:1px solid #23233a}
.stat i{color:#00d68f;background:#123a2a;width:36px;height:36px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;margin-bottom:10px;font-size:14px}
.stat p{font-size:12px;color:#6b6b8a;margin-bottom:6px}
.stat h3{font-size:18px;font-weight:800}
.checkin{margin:16px;background:linear-gradient(135deg,#00b073,#00d68f 50%,#00ff88);border-radius:22px;padding:20px}
.checkin-top{display:flex;justify-content:space-between;align-items:center}
.checkin-top button{background:#000;color:#00ff88;border:none;padding:12px 24px;border-radius:30px;font-weight:800}
.days{display:flex;gap:8px;margin-top:16px}
.day{flex:1;background:rgba(0,0,0,0.18);padding:10px 2px;border-radius:12px;text-align:center;font-size:11px;border:1px solid rgba(0,0,0,0.1)}
.day.active{background:white;color:#00b073;font-weight:800}
.watch-head{padding:8px 16px;display:flex;align-items:center;gap:8px;font-weight:700}
.ad-card{margin:12px 16px;background:#181826;border-radius:18px;padding:16px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a;position:relative}
.play{width:52px;height:52px;background:#1c8ef8;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px}
.hot{position:absolute;top:10px;right:12px;background:#ff9f0a;color:black;font-size:9px;padding:3px 8px;border-radius:10px;font-weight:900}
.watch-btn{background:#5ac8ff;color:#000;border:none;padding:10px 22px;border-radius:20px;font-weight:800;font-size:13px}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#11111f;display:flex;justify-content:space-around;align-items:center;padding:10px 0 22px 0;border-top:1px solid #1e1e32}
.nav-item{text-align:center;color:#5a5a7a;font-size:10px;font-weight:600}
.nav-item.active{color:#00d68f}
.nav-item i{font-size:20px;display:block;margin-bottom:5px}
.center-btn{width:62px;height:62px;background:linear-gradient(135deg,#ff9f0a,#ffcf5a);border-radius:50%;display:flex;align-items:center;justify-content:center;margin-top:-28px;border:4px solid #11111f;font-size:26px;color:#000}
</style></head>
<body>
<div class="header"><div style="display:flex;align-items:center;gap:10px"><div class="logo"><i class="fa-solid fa-dollar-sign"></i></div><div><b>USDT Earn</b><br><small style="color:#5a5a7a;font-size:12px">@username</small></div></div><div class="online">● Online</div></div>
<div class="xp-card"><div><p>YOUR BALANCE</p><h1>0.000 <span>USDT</span></h1><small>≈ $0.000  Earn more →</small></div><div class="gem"><i class="fa-solid fa-dollar-sign"></i></div></div>
<div class="btn-row"><button class="btn btn-earn"><i class="fa-solid fa-bolt"></i> Earn</button><button class="btn btn-with"><i class="fa-solid fa-wallet"></i> Withdraw</button></div>
<div class="stats"><div class="stat"><i class="fa-solid fa-list-check"></i><p>Tasks</p><h3>0/0</h3></div><div class="stat"><i class="fa-solid fa-fire"></i><p>Streak</p><h3>0 days</h3></div><div class="stat"><i class="fa-solid fa-users"></i><p>Refs</p><h3>0</h3></div></div>
<div class="checkin"><div class="checkin-top"><div><div style="font-weight:800;font-size:16px;color:#000">🔥 Daily Check-in</div><small style="color:#003322;font-size:12px;font-weight:600">Day 1 reward: +0.01 USDT</small></div><button>Check In</button></div><div class="days"><div class="day active">D1<br><b>0.01</b></div><div class="day">D2<br><b>0.02</b></div><div class="day">D3<br><b>0.03</b></div><div class="day">D4<br><b>0.05</b></div><div class="day">D5<br><b>0.08</b></div><div class="day">D6<br><b>0.10</b></div><div class="day">D7<br><b>0.20</b></div></div></div>
<div class="watch-head"><i class="fa-solid fa-dollar-sign" style="color:#000;background:#00ff88;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;font-size:12px"></i> Watch Ads & Earn USDT!</div>
<div class="ad-card"><span class="hot">HOT</span><div style="display:flex;align-items:center;gap:14px"><div class="play"><i class="fa-solid fa-play" style="margin-left:3px"></i></div><div><b style="font-size:14px">WATCH AD #1</b><br><small style="color:#00d68f;font-weight:700">0.05 USDT</small></div></div><button class="watch-btn">Watch</button></div>
<div class="bottom-nav"><div class="nav-item active"><i class="fa-solid fa-border-all"></i>Home</div><div class="nav-item"><i class="fa-solid fa-list-check"></i>Earn</div><div class="center-btn"><i class="fa-solid fa-gamepad"></i></div><div class="nav-item"><i class="fa-solid fa-gift"></i>Refer</div><div class="nav-item"><i class="fa-solid fa-user"></i>Account</div></div>
</body></html>
"""

@app.route('/')
def home():
    return HTML_PAGE

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    webapp_url = "https://earning-bot-bdjm.onrender.com/"
    btn = types.InlineKeyboardButton(text="🚀 Launch App", web_app=types.WebAppInfo(url=webapp_url))
    markup.add(btn)
    bot.send_message(message.chat.id, f"Welcome {message.from_user.first_name}!\n\n💰 USDT Earn App is ready!\nClick below 👇", reply_markup=markup)

def run_bot():
    try:
        bot.infinity_polling()
    except:
        pass

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
