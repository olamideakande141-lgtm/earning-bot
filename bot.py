import os, threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = "8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc"
CHANNEL_USERNAME = "@earning_channel_12"
CHANNEL_LINK = "https://t.me/earning_channel_12"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Inter,sans-serif}
body{background:#0b0b14;color:white;padding:0 0 90px 0}
.view{display:none} .view.active{display:block}
.header{display:flex;justify-content:space-between;align-items:center;padding:16px 20px}
.logo{width:34px;height:34px;background:linear-gradient(135deg,#00d68f,#00ff88);border-radius:10px;display:flex;align-items:center;justify-content:center;color:#000}
.online{color:#00ff88;font-size:12px;background:#10281c;border:1px solid #1a4a2e;padding:5px 12px;border-radius:20px}
.xp-card{margin:15px;background:#181826;border-radius:22px;padding:22px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a}
.btn-row{display:flex;gap:12px;padding:0 16px} .btn{flex:1;padding:16px;border-radius:14px;border:none;font-weight:700;font-size:15px;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer}
.btn-earn{background:#00d68f;color:#000} .btn-with{background:#1e1e32;color:white;border:1px solid #2a2a45}
.notice{background:#1a1a2e;border:1px dashed #00d68f;margin:12px 16px;padding:12px 14px;border-radius:12px;font-size:12px;color:#a0a0c0} .notice b{color:#00ff88}
.stats{display:flex;gap:12px;padding:16px} .stat{flex:1;background:#181826;padding:18px 10px;border-radius:18px;text-align:center;border:1px solid #23233a}
.checkin{margin:16px;background:linear-gradient(135deg,#00b073,#00d68f 50%,#00ff88);border-radius:22px;padding:20px}
.checkin-top{display:flex;justify-content:space-between;align-items:center} .checkin-top button{background:#000;color:#00ff88;border:none;padding:12px 24px;border-radius:30px;font-weight:800}
.days{display:flex;gap:8px;margin-top:16px} .day{flex:1;background:rgba(0,0,0,0.18);padding:10px 2px;border-radius:12px;text-align:center;font-size:11px} .day.active{background:white;color:#00b073;font-weight:800}
.ad-card{margin:12px 16px;background:#181826;border-radius:18px;padding:16px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a}
.watch-btn{background:#5ac8ff;color:#000;border:none;padding:10px 22px;border-radius:20px;font-weight:800;cursor:pointer}
.play{width:52px;height:52px;background:#1c8ef8;border-radius:50%;display:flex;align-items:center;justify-content:center}
.task-card{margin:10px 0;background:#0b0b14;border-radius:14px;padding:14px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a}
.task-btn{background:#00d68f;color:#000;border:none;padding:8px 16px;border-radius:20px;font-weight:800;font-size:12px} .task-btn.done{background:#333;color:#777}
.pro-header{background:linear-gradient(135deg,#181826 0%,#1e1e32 100%);padding:20px;border-bottom:1px solid #23233a}
.pro-profile{display:flex;align-items:center;gap:16px}
.pro-avatar{width:64px;height:64px;background:linear-gradient(135deg,#00d68f,#00ff88);border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:28px;color:#000;font-weight:800}
.pro-stats{display:flex;gap:8px;margin-top:16px}
.pro-stat{flex:1;background:#0b0b14;border:1px solid #23233a;padding:12px;border-radius:12px;text-align:center}
.pro-stat h3{color:#00ff88;font-size:16px} .pro-stat p{color:#6b6b8a;font-size:10px;margin-top:3px}
.wallet-box{margin:12px 16px;background:#181826;border-radius:18px;padding:16px;border:1px solid #23233a}
.wallet-input{background:#0b0b14;border:1px solid #23233a;color:white;padding:12px;border-radius:10px;width:100%;margin-top:8px;font-size:13px}
.ref-link{background:#0b0b14;border:1px solid #23233a;padding:12px;border-radius:10px;margin:10px 0;word-break:break-all;font-size:12px;color:#00ff88}
.copy-btn{background:#00d68f;color:#000;border:none;padding:12px 24px;border-radius:12px;font-weight:800;width:100%;cursor:pointer}
.menu-list{margin:12px 16px;background:#181826;border-radius:18px;border:1px solid #23233a;overflow:hidden}
.menu-item{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid #1e1e32;cursor:pointer;font-size:13px}
.menu-item:last-child{border:none}
.history-item{display:flex;justify-content:space-between;padding:12px;background:#0b0b14;border-radius:10px;margin:6px 0;font-size:12px}
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#11111f;display:flex;justify-content:space-around;align-items:center;padding:10px 0 22px 0;border-top:1px solid #1e1e32}
.nav-item{text-align:center;color:#5a5a7a;font-size:10px;font-weight:600;cursor:pointer} .nav-item.active{color:#00d68f} .nav-item i{font-size:20px;display:block;margin-bottom:5px}
.center-btn{width:62px;height:62px;background:linear-gradient(135deg,#ff9f0a,#ffcf5a);border-radius:50%;display:flex;align-items:center;justify-content:center;margin-top:-28px;border:4px solid #11111f;font-size:26px;color:#000}
.toast{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#00d68f;color:#000;padding:14px 20px;border-radius:12px;font-weight:800;z-index:9999;display:none;text-align:center;max-width:85%}
</style></head><body>
<div id="toast" class="toast"></div>
<div class="header"><div style="display:flex;align-items:center;gap:10px"><div class="logo"><i class="fa-solid fa-dollar-sign"></i></div><div><b>USDT Earn</b><br><small style="color:#5a5a7a" id="uname">@user</small></div></div><div class="online">● Online</div></div>

<div id="homeView" class="view active">
<div class="xp-card"><div><p>YOUR BALANCE</p><h1 id="bal">0.000 USDT</h1><small id="usd">≈ $0.000</small></div><div style="width:70px;height:70px;background:linear-gradient(135deg,#00d68f,#00ff88);border-radius:18px;display:flex;align-items:center;justify-content:center;color:#000;font-size:32px"><i class="fa-solid fa-dollar-sign"></i></div></div>
<div class="notice">⚠️ Min: <b>3 USDT</b> | <b>Monday Only</b> | <b>2-3 sec</b> arrival</div>
<div class="btn-row"><button class="btn btn-earn" onclick="showView('earn')"><i class="fa-solid fa-bolt"></i> Earn</button><button class="btn btn-with" onclick="withdraw()"><i class="fa-solid fa-wallet"></i> Withdraw</button></div>
<div class="stats"><div class="stat" onclick="showView('earn')"><p>Tasks</p><h3 id="tasksCount">0/4</h3></div><div class="stat"><p>Streak</p><h3 id="streak">0d</h3></div><div class="stat" onclick="showView('account')"><p>Refs</p><h3 id="refs">0</h3></div></div>
<div class="checkin"><div class="checkin-top"><div><div style="font-weight:800;color:#000">🔥 Daily Check-in</div><small id="rewardText" style="color:#003322">Day 1: +0.01</small></div><button id="checkBtn" onclick="claimDaily()">Check In</button></div><div class="days" id="days"></div></div>
</div>

<div id="earnView" class="view">
<div style="padding:12px 16px;font-weight:700">🎬 Watch & Earn</div>
<div class="ad-card"><div style="display:flex;gap:12px;align-items:center"><div class="play"><i class="fa-solid fa-play"></i></div><div><b>WATCH AD</b><br><small style="color:#00d68f">0.05 USDT</small></div></div><button class="watch-btn" onclick="watchAd(0.05,this)">Watch</button></div>
<div class="ad-card"><div style="display:flex;gap:12px;align-items:center"><div class="play" style="background:#ff5a5a"><i class="fa-solid fa-play"></i></div><div><b>WATCH AD #2</b><br><small style="color:#00d68f">0.10 USDT</small></div></div><button class="watch-btn" onclick="watchAd(0.10,this)">Watch</button></div>
</div>

<div id="accountView" class="view">
<div class="pro-header">
<div class="pro-profile">
<div class="pro-avatar" id="avatar">U</div>
<div><b id="accName" style="font-size:17px">Username</b><br><small style="color:#6b6b8a" id="accIdText">ID: 123 • @user</small><br><small style="color:#00ff88">● Verified Trader</small></div>
</div>
<div class="pro-stats">
<div class="pro-stat"><h3 id="accBal">0.000</h3><p>Balance</p></div>
<div class="pro-stat"><h3 id="accTotal">0.000</h3><p>Earned</p></div>
<div class="pro-stat"><h3 id="accRef">0</h3><p>Friends</p></div>
<div class="pro-stat"><h3 id="accLevel">LV1</h3><p>Level</p></div>
</div>
</div>

<div class="wallet-box">
<b style="font-size:14px"><i class="fa-solid fa-wallet" style="color:#00d68f"></i> USDT Wallet (TRC20)</b>
<input id="walletAddr" class="wallet-input" placeholder="Enter T... address" />
<div style="display:flex;gap:8px;margin-top:10px"><button class="copy-btn" style="flex:1" onclick="saveWallet()">Save Wallet</button><button class="copy-btn" style="flex:1;background:#1e1e32;color:white;border:1px solid #2a2a45" onclick="withdraw()">Withdraw</button></div>
<small style="color:#6b6b8a;font-size:11px;margin-top:8px;display:block">Withdraw: 3 USDT min, Monday only, arrives 2-3 sec</small>
</div>

<div class="wallet-box">
<b style="font-size:14px">👥 Referral System</b>
<div style="display:flex;gap:8px;margin:10px 0"><div style="flex:1;background:#0b0b14;border:1px solid #23233a;padding:12px;border-radius:10px;text-align:center"><h3 id="refCount" style="color:#00ff88">0</h3><small style="color:#6b6b8a;font-size:10px">Friends</small></div><div style="flex:1;background:#0b0b14;border:1px solid #23233a;padding:12px;border-radius:10px;text-align:center"><h3 id="refEarn" style="color:#00ff88">0.000</h3><small style="color:#6b6b8a;font-size:10px">Ref Earn</small></div></div>
<p style="font-size:11px;color:#6b6b8a">Your Referral Link:</p>
<div class="ref-link" id="refLink">Generating...</div>
<button class="copy-btn" onclick="copyRef()"><i class="fa-solid fa-copy"></i> Copy & Share Link</button>
<small style="color:#6b6b8a;font-size:11px;margin-top:8px;display:block">Earn 20% lifetime from friends!</small>
</div>

<div class="wallet-box">
<b style="font-size:14px">📋 Tasks Progress <small id="taskProg" style="color:#00ff88">0/4</small></b>
<div class="task-card"><div><b style="font-size:13px">Join Channel</b><br><small style="color:#00d68f;font-size:11px">+0.10</small></div><button class="task-btn" id="task1" onclick="doTask(1,0.10)">Join</button></div>
<div class="task-card"><div><b style="font-size:13px">Follow Twitter</b><br><small style="color:#00d68f;font-size:11px">+0.10</small></div><button class="task-btn" id="task2" onclick="doTask(2,0.10)">Follow</button></div>
<div class="task-card"><div><b style="font-size:13px">Invite 1 Friend</b><br><small style="color:#00d68f;font-size:11px">+0.20</small></div><button class="task-btn" id="task3" onclick="doTask(3,0.20)">Invite</button></div>
<div class="task-card"><div><b style="font-size:13px">Watch 3 Ads</b><br><small style="color:#00d68f;font-size:11px">+0.15</small></div><button class="task-btn" id="task4" onclick="doTask(4,0.15)">Watch</button></div>
</div>

<div class="wallet-box">
<div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:14px">📜 Full History</b><small style="color:#6b6b8a" onclick="clearHistory()">Clear</small></div>
<div id="historyList" style="margin-top:10px"><p style="color:#6b6b8a;text-align:center;padding:15px;font-size:12px">No transactions</p></div>
</div>
</div>

<div class="bottom-nav">
<div class="nav-item active" onclick="showView('home')"><i class="fa-solid fa-house"></i>Home</div>
<div class="nav-item" onclick="showView('earn')"><i class="fa-solid fa-play"></i>Earn</div>
<div class="center-btn" onclick="showView('earn')"><i class="fa-solid fa-bolt"></i></div>
<div class="nav-item" onclick="showView('account')"><i class="fa-solid fa-user"></i>Account</div>
<div class="nav-item" onclick="showView('account')"><i class="fa-solid fa-gear"></i>More</div>
</div>

<script>
let tg=window.Telegram.WebApp; tg.expand();
let balance=parseFloat(localStorage.getItem('usdt_balance')||'0');
let totalEarned=parseFloat(localStorage.getItem('usdt_total')||'0');
let streak=parseInt(localStorage.getItem('usdt_streak')||'0');
let lastCheck=localStorage.getItem('usdt_lastCheck')||'';
let lastWithdraw=localStorage.getItem('usdt_lastWithdraw')||'';
let history=JSON.parse(localStorage.getItem('usdt_history')||'[]');
let tasksDone=JSON.parse(localStorage.getItem('usdt_tasks')||'[]');
let refCount=parseInt(localStorage.getItem('usdt_refCount')||'0');
let wallet=localStorage.getItem('usdt_wallet')||'';
let rewards=[0.01,0.02,0.03,0.05,0.08,0.10,0.20];
let userId=tg.initDataUnsafe?.user?.id||Math.floor(Math.random()*1000000);
let username=tg.initDataUnsafe?.user?.username||'user';
let botUsername='earning_12_1_bot';
function showToast(m){let t=document.getElementById('toast');t.innerText=m;t.style.display='block';setTimeout(()=>t.style.display='none',3000);}
function addHistory(type,amount){history.unshift({type,amount,date:new Date().toLocaleString()});localStorage.setItem('usdt_history',JSON.stringify(history));}
function showView(v){document.querySelectorAll('.view').forEach(x=>x.classList.remove('active'));document.getElementById(v+'View').classList.add('active');document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));let map={home:0,earn:1,account:3};if(map[v]!==undefined)document.querySelectorAll('.nav-item')[map[v]].classList.add('active');if(v==='account')updateAccount();}
function updateUI(){document.getElementById('bal').innerHTML=balance.toFixed(3)+' USDT';document.getElementById('usd').innerText='≈ $'+balance.toFixed(3);document.getElementById('streak').innerText=streak+'d';document.getElementById('refs').innerText=refCount;document.getElementById('uname').innerText='@'+username;document.getElementById('tasksCount').innerText=tasksDone.length+'/4';let today=new Date().toDateString();let canClaim=lastCheck!==today;document.getElementById('checkBtn').innerText=canClaim?'Check In':'Claimed ✓';document.getElementById('rewardText').innerText='Day '+(streak%7+1)+' +'+rewards[streak%7]+' USDT';let daysHTML='';for(let i=0;i<7;i++){let cls=i===streak%7&&canClaim?'day active':(i<streak%7&&!canClaim?'day active':'day');daysHTML+=`<div class="${cls}">D${i+1}<br><b>${rewards[i].toFixed(2)}</b></div>`;}document.getElementById('days').innerHTML=daysHTML;tasksDone.forEach(id=>{let b=document.getElementById('task'+id);if(b){b.innerText='Done ✓';b.classList.add('done');}});document.getElementById('walletAddr').value=wallet;updateAccount();}
function claimDaily(){let today=new Date().toDateString();if(lastCheck===today){showToast('Already claimed!');return;}let r=rewards[streak%7];balance+=r;totalEarned+=r;streak++;lastCheck=today;localStorage.setItem('usdt_balance',balance);localStorage.setItem('usdt_total',totalEarned);localStorage.setItem('usdt_streak',streak);localStorage.setItem('usdt_lastCheck',lastCheck);addHistory('Daily Check-in',r);updateUI();showToast('+'+r+' USDT!');}
function watchAd(a,b){b.innerText='Loading...';b.disabled=true;showToast('Watching 10s...');setTimeout(()=>{balance+=a;totalEarned+=a;localStorage.setItem('usdt_balance',balance);localStorage.setItem('usdt_total',totalEarned);addHistory('Watch Ad',a);updateUI();b.innerText='Watch';b.disabled=false;showToast('+'+a+' USDT!');},10000);}
function doTask(id,amount){if(tasksDone.includes(id)){showToast('Done!');return;}tasksDone.push(id);localStorage.setItem('usdt_tasks',JSON.stringify(tasksDone));balance+=amount;totalEarned+=amount;localStorage.setItem('usdt_balance',balance);localStorage.setItem('usdt_total',totalEarned);addHistory('Task '+id,amount);updateUI();showToast('+'+amount+'!');}
function withdraw(){if(balance<3){showToast('Min 3 USDT! You: '+balance.toFixed(3));return;}let now=new Date();if(now.getDay()!==1){showToast('Only Monday!');return;}if(lastWithdraw===now.toDateString()){showToast('Once per day!');return;}if(!wallet){showToast('Set wallet first!');showView('account');return;}let amt=balance;showToast('Processing '+amt.toFixed(3)+'... 2-3 sec');setTimeout(()=>{lastWithdraw=now.toDateString();localStorage.setItem('usdt_lastWithdraw',lastWithdraw);addHistory('Withdrawal',-amt);balance=0;localStorage.setItem('usdt_balance',balance);updateUI();showToast('✅ '+amt.toFixed(3)+' Sent to '+wallet.slice(0,6)+'!');},2500);}
function updateAccount(){document.getElementById('accName').innerText=username;document.getElementById('accIdText').innerText='ID: '+userId+' • @'+username;document.getElementById('avatar').innerText=username[0].toUpperCase();document.getElementById('accBal').innerText=balance.toFixed(3);document.getElementById('accTotal').innerText=totalEarned.toFixed(3);document.getElementById('accRef').innerText=refCount;document.getElementById('accLevel').innerText='LV'+(Math.floor(totalEarned)+1);document.getElementById('refCount').innerText=refCount;document.getElementById('refEarn').innerText=(refCount*0.2).toFixed(3);document.getElementById('taskProg').innerText=tasksDone.length+'/4';let link='https://t.me/'+botUsername+'?start='+userId;document.getElementById('refLink').innerText=link;let h=document.getElementById('historyList');if(history.length===0){h.innerHTML='<p style="color:#6b6b8a;text-align:center;padding:15px;font-size:12px">No transactions</p>';return;}h.innerHTML=history.map(x=>`<div class="history-item"><span>${x.type}<br><small style="color:#6b6b8a">${x.date}</small></span><b style="color:${x.amount>0?'#00ff88':'#ff5a5a'}">${x.amount>0?'+':''}${x.amount.toFixed(3)}</b></div>`).join('');}
function saveWallet(){let v=document.getElementById('walletAddr').value;if(v.length<10){showToast('Invalid wallet!');return;}wallet=v;localStorage.setItem('usdt_wallet',wallet);showToast('Wallet saved!');}
function copyRef(){navigator.clipboard.writeText(document.getElementById('refLink').innerText);showToast('Link copied!');}
function clearHistory(){history=[];localStorage.setItem('usdt_history','[]');updateAccount();showToast('Cleared');}
updateUI();
</script></body></html>
"""

@app.route('/')
def home():
    return HTML_PAGE

def is_member(user_id):
    try:
        m=bot.get_chat_member(CHANNEL_USERNAME,user_id)
        return m.status in ['member','administrator','creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    if not is_member(message.from_user.id):
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="📢 Join Channel",url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton(text="✅ I Joined",callback_data="check_join"))
        bot.send_message(message.chat.id,f"🔒 Join {CHANNEL_USERNAME} first!",reply_markup=markup)
        return
    markup=types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="🚀 Launch App",web_app=types.WebAppInfo(url="https://earning-bot-bdjm.onrender.com/")))
    bot.send_message(message.chat.id,f"✅ Welcome {message.from_user.first_name}!",reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data=="check_join")
def check_join(call):
    if is_member(call.from_user.id):
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="🚀 Launch App",web_app=types.WebAppInfo(url="https://earning-bot-bdjm.onrender.com/")))
        bot.edit_message_text("✅ Verified!",call.message.chat.id,call.message.message_id,reply_markup=markup)
    else:
        bot.answer_callback_query(call.id,"❌ Not joined!",show_alert=True)

def run_bot():
    bot.infinity_polling()
threading.Thread(target=run_bot,daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
