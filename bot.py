import os, threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = "8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc"
CHANNEL_USERNAME = "@earning_channel_12"  # <-- CHANGE TO YOUR CHANNEL
CHANNEL_LINK = "https://t.me/earning_channel_12"  # <-- CHANGE TO YOUR CHANNEL

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Inter,sans-serif}
body{background:#0b0b14;color:white;padding:0 0 90px 0}
.header{display:flex;justify-content:space-between;align-items:center;padding:16px 20px}
.logo{width:34px;height:34px;background:linear-gradient(135deg,#00d68f,#00ff88);border-radius:10px;display:flex;align-items:center;justify-content:center;color:#000}
.online{color:#00ff88;font-size:12px;background:#10281c;border:1px solid #1a4a2e;padding:5px 12px;border-radius:20px}
.xp-card{margin:15px;background:#181826;border-radius:22px;padding:22px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a}
.xp-card p{color:#6b6b8a;letter-spacing:1px;font-size:12px;font-weight:700}
.xp-card h1{font-size:38px;margin:6px 0 4px 0}
.xp-card h1 span{font-size:18px;color:#6b6b8a}
.xp-card small{color:#3dd68c;font-size:13px}
.gem{width:78px;height:78px;background:linear-gradient(135deg,#00d68f,#00ff88);border-radius:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px #00ff8855;transform:rotate(-5deg);color:#000;font-size:38px}
.btn-row{display:flex;gap:12px;padding:0 16px}
.btn{flex:1;padding:16px;border-radius:14px;border:none;font-weight:700;font-size:16px;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer}
.btn-earn{background:#00d68f;color:#000}
.btn-with{background:#1e1e32;color:white;border:1px solid #2a2a45}
.notice{background:#1a1a2e;border:1px dashed #00d68f;margin:12px 16px;padding:12px 14px;border-radius:12px;font-size:12px;line-height:16px;color:#a0a0c0}
.notice b{color:#00ff88}
.stats{display:flex;gap:12px;padding:16px}
.stat{flex:1;background:#181826;padding:18px 10px;border-radius:18px;text-align:center;border:1px solid #23233a;cursor:pointer}
.stat i{color:#00d68f;background:#123a2a;width:36px;height:36px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;margin-bottom:10px;font-size:14px}
.stat p{font-size:12px;color:#6b6b8a;margin-bottom:6px}
.stat h3{font-size:18px;font-weight:800}
.checkin{margin:16px;background:linear-gradient(135deg,#00b073,#00d68f 50%,#00ff88);border-radius:22px;padding:20px}
.checkin-top{display:flex;justify-content:space-between;align-items:center}
.checkin-top button{background:#000;color:#00ff88;border:none;padding:12px 24px;border-radius:30px;font-weight:800;cursor:pointer}
.days{display:flex;gap:8px;margin-top:16px}
.day{flex:1;background:rgba(0,0,0,0.18);padding:10px 2px;border-radius:12px;text-align:center;font-size:11px;border:1px solid rgba(0,0,0,0.1)}
.day.active{background:white;color:#00b073;font-weight:800}
.watch-head{padding:8px 16px;display:flex;align-items:center;gap:8px;font-weight:700}
.ad-card{margin:12px 16px;background:#181826;border-radius:18px;padding:16px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a;position:relative}
.play{width:52px;height:52px;background:#1c8ef8;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px}
.hot{position:absolute;top:10px;right:12px;background:#ff9f0a;color:black;font-size:9px;padding:3px 8px;border-radius:10px;font-weight:900}
.watch-btn{background:#5ac8ff;color:#000;border:none;padding:10px 22px;border-radius:20px;font-weight:800;font-size:13px;cursor:pointer}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#11111f;display:flex;justify-content:space-around;align-items:center;padding:10px 0 22px 0;border-top:1px solid #1e1e32}
.nav-item{text-align:center;color:#5a5a7a;font-size:10px;font-weight:600;cursor:pointer}
.nav-item.active{color:#00d68f}
.nav-item i{font-size:20px;display:block;margin-bottom:5px}
.center-btn{width:62px;height:62px;background:linear-gradient(135deg,#ff9f0a,#ffcf5a);border-radius:50%;display:flex;align-items:center;justify-content:center;margin-top:-28px;border:4px solid #11111f;font-size:26px;color:#000;cursor:pointer}
.toast{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#00d68f;color:#000;padding:18px 28px;border-radius:14px;font-weight:800;z-index:9999;display:none;box-shadow:0 10px 40px rgba(0,0,0,0.5);text-align:center;max-width:80%}
</style></head>
<body>
<div id="toast" class="toast"></div>
<div class="header"><div style="display:flex;align-items:center;gap:10px"><div class="logo"><i class="fa-solid fa-dollar-sign"></i></div><div><b>USDT Earn</b><br><small style="color:#5a5a7a;font-size:12px" id="uname">@username</small></div></div><div class="online">● Online</div></div>
<div class="xp-card"><div><p>YOUR BALANCE</p><h1 id="bal">0.000 <span>USDT</span></h1><small id="usd">≈ $0.000  Earn more →</small></div><div class="gem"><i class="fa-solid fa-dollar-sign"></i></div></div>

<div class="notice">⚠️ <b>WITHDRAWAL NOTICE:</b><br>• Minimum withdrawal: <b>3.000 USDT</b><br>• Withdrawal day: <b>Monday Only (Once per day)</b><br>• Payment arrives in <b>2-3 seconds</b> after request</div>

<div class="btn-row"><button class="btn btn-earn" onclick="goEarn()"><i class="fa-solid fa-bolt"></i> Earn</button><button class="btn btn-with" onclick="withdraw()"><i class="fa-solid fa-wallet"></i> Withdraw</button></div>
<div class="stats"><div class="stat" onclick="showTasks()"><i class="fa-solid fa-list-check"></i><p>Tasks</p><h3 id="tasks">0/0</h3></div><div class="stat"><i class="fa-solid fa-fire"></i><p>Streak</p><h3 id="streak">0 days</h3></div><div class="stat" onclick="showRefer()"><i class="fa-solid fa-users"></i><p>Refs</p><h3 id="refs">0</h3></div></div>
<div class="checkin"><div class="checkin-top"><div><div style="font-weight:800;font-size:16px;color:#000">🔥 Daily Check-in</div><small style="color:#003322;font-size:12px;font-weight:600" id="rewardText">Day 1 reward: +0.01 USDT</small></div><button id="checkBtn" onclick="claimDaily()">Check In</button></div><div class="days" id="days"></div></div>
<div class="watch-head"><i class="fa-solid fa-dollar-sign" style="color:#000;background:#00ff88;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;font-size:12px"></i> Watch Ads & Earn USDT!</div>
<div class="ad-card"><span class="hot">HOT</span><div style="display:flex;align-items:center;gap:14px"><div class="play"><i class="fa-solid fa-play" style="margin-left:3px"></i></div><div><b style="font-size:14px">WATCH AD #1</b><br><small style="color:#00d68f;font-weight:700">0.05 USDT</small></div></div><button class="watch-btn" onclick="watchAd(0.05, this)">Watch</button></div>
<div class="ad-card"><span class="hot" style="background:#00ff88">NEW</span><div style="display:flex;align-items:center;gap:14px"><div class="play" style="background:#ff5a5a"><i class="fa-solid fa-play" style="margin-left:3px"></i></div><div><b style="font-size:14px">WATCH AD #2</b><br><small style="color:#00d68f;font-weight:700">0.10 USDT</small></div></div><button class="watch-btn" onclick="watchAd(0.10, this)">Watch</button></div>
<div class="bottom-nav"><div class="nav-item active"><i class="fa-solid fa-border-all"></i>Home</div><div class="nav-item" onclick="goEarn()"><i class="fa-solid fa-list-check"></i>Earn</div><div class="center-btn" onclick="goEarn()"><i class="fa-solid fa-gamepad"></i></div><div class="nav-item" onclick="showRefer()"><i class="fa-solid fa-gift"></i>Refer</div><div class="nav-item" onclick="showAccount()"><i class="fa-solid fa-user"></i>Account</div></div>

<script>
let tg = window.Telegram.WebApp; tg.expand();
let balance = parseFloat(localStorage.getItem('usdt_balance') || '0');
let streak = parseInt(localStorage.getItem('usdt_streak') || '0');
let lastCheck = localStorage.getItem('usdt_lastCheck') || '';
let lastWithdraw = localStorage.getItem('usdt_lastWithdraw') || '';
let rewards = [0.01,0.02,0.03,0.05,0.08,0.10,0.20];

function showToast(msg){
 let t=document.getElementById('toast');
 t.innerText=msg; t.style.display='block';
 setTimeout(()=>t.style.display='none',3000);
}
function updateUI(){
 document.getElementById('bal').innerHTML = balance.toFixed(3)+' <span>USDT</span>';
 document.getElementById('usd').innerText = '≈ $'+balance.toFixed(3)+'  Earn more →';
 document.getElementById('streak').innerText = streak+' days';
 document.getElementById('uname').innerText = '@'+(tg.initDataUnsafe?.user?.username || 'username');
 let today = new Date().toDateString();
 let canClaim = lastCheck !== today;
 document.getElementById('checkBtn').innerText = canClaim ? 'Check In' : 'Claimed ✓';
 document.getElementById('checkBtn').style.opacity = canClaim ? '1' : '0.5';
 let dayIndex = streak % 7;
 document.getElementById('rewardText').innerText = 'Day '+(dayIndex+1)+' reward: +'+rewards[dayIndex]+' USDT';
 let daysHTML='';
 for(let i=0;i<7;i++){
   let cls = i===dayIndex && canClaim ? 'day active' : (i < (streak%7) && !canClaim ? 'day active' : 'day');
   daysHTML+=`<div class="${cls}">D${i+1}<br><b>${rewards[i].toFixed(2)}</b></div>`;
 }
 document.getElementById('days').innerHTML=daysHTML;
}
function claimDaily(){
 let today = new Date().toDateString();
 if(lastCheck === today){ showToast('Already claimed today!'); return; }
 let dayIndex = streak % 7;
 let reward = rewards[dayIndex];
 balance+=reward; streak+=1; lastCheck=today;
 localStorage.setItem('usdt_balance', balance);
 localStorage.setItem('usdt_streak', streak);
 localStorage.setItem('usdt_lastCheck', lastCheck);
 updateUI();
 showToast('+' + reward + ' USDT Claimed! 🔥');
 if(tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
}
function watchAd(amount, btn){
 btn.innerText='Loading...'; btn.disabled=true;
 showToast('Watching Ad... 10s');
 setTimeout(()=>{
   balance+=amount;
   localStorage.setItem('usdt_balance', balance);
   updateUI();
   btn.innerText='Watch';
   btn.disabled=false;
   showToast('+'+amount+' USDT Added! 💰');
   if(tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
 }, 10000);
}
function withdraw(){
 if(balance < 3){
   showToast('❌ Minimum withdrawal is 3.000 USDT!\\nYour balance: '+balance.toFixed(3));
   return;
 }
 let now = new Date();
 let day = now.getDay(); // 0=Sunday, 1=Monday
 if(day !== 1){
   showToast('⚠️ Withdrawals are only on MONDAY!\\nToday is not Monday.');
   return;
 }
 let todayStr = now.toDateString();
 if(lastWithdraw === todayStr){
   showToast('❌ You already withdrew today!\\nOnly once per day on Monday.');
   return;
 }
 // Process withdrawal
 let amount = balance;
 showToast('⏳ Processing '+amount.toFixed(3)+' USDT...\\nArriving in 2-3 seconds...');
 setTimeout(()=>{
   lastWithdraw = todayStr;
   localStorage.setItem('usdt_lastWithdraw', lastWithdraw);
   balance = 0;
   localStorage.setItem('usdt_balance', balance);
   updateUI();
   showToast('✅ '+amount.toFixed(3)+' USDT Sent!\\nArrived in your wallet in 2-3 seconds! 💸');
   if(tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
 }, 2500);
}
function goEarn(){ document.querySelector('.watch-head').scrollIntoView({behavior:'smooth'}); showToast('Watch ads to earn!'); }
function showTasks(){ showToast('Tasks coming soon!'); }
function showRefer(){ showToast('Refer friends to earn more!'); }
function showAccount(){ showToast('Balance: '+balance.toFixed(3)+' USDT'); }
updateUI();
</script>
</body></html>
"""

@app.route('/')
def home():
    return HTML_PAGE

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member','administrator','creator']
    except:
        return True

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_member(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="📢 Join Channel", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton(text="✅ I Joined - Check Again", callback_data="check_join"))
        bot.send_message(message.chat.id, f"⚠️ You must join our channel {CHANNEL_USERNAME} first!\n\n1. Join Channel\n2. Click Check Again", reply_markup=markup)
        return
    markup = types.InlineKeyboardMarkup()
    webapp_url = "https://earning-bot-bdjm.onrender.com/"
    btn = types.InlineKeyboardButton(text="🚀 Launch USDT App", web_app=types.WebAppInfo(url=webapp_url))
    markup.add(btn)
    bot.send_message(message.chat.id, f"Welcome {message.from_user.first_name}!\n\n💰 USDT Earn App Ready!\nMin Withdraw: 3 USDT (Monday only)", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_member(call.from_user.id):
        markup = types.InlineKeyboardMarkup()
        webapp_url = "https://earning-bot-bdjm.onrender.com/"
        btn = types.InlineKeyboardButton(text="🚀 Launch USDT App", web_app=types.WebAppInfo(url=webapp_url))
        markup.add(btn)
        bot.edit_message_text("✅ Verified! You can use the bot now:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "❌ Not joined yet!")

def run_bot():
    try: bot.infinity_polling()
    except: pass

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
