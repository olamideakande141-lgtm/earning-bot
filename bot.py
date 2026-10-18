import os
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from earning import init_earning_tables, register_user, get_balance, get_daily_counts, credit_verified_ad, REWARDS, get_db

BOT_TOKEN=os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME="@freeearningofusdt"
CHANNEL_LINK="https://t.me/freeearningofusdt"
WEBAPP_URL="https://earning-bot-bdjm.onrender.com"
TOTAL_LIMIT=20
flask_app=Flask(__name__)

@flask_app.route('/api/me')
def api_me():
    uid=request.args.get('user')
    try:
        bal=float(get_balance(int(uid)))
        counts=get_daily_counts(int(uid))
        total=counts.get('ad1',0)+counts.get('ad2',0)
        with get_db() as conn:
            refs=conn.execute("SELECT COUNT(*) as c FROM earning_users WHERE referred_by=%s",(int(uid),)).fetchone()["c"]
        return jsonify({"ok":True,"usdt":bal,"total":total,"total_limit":TOTAL_LIMIT,"refs":int(refs),"reward":str(REWARDS['ad1'])})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)})

@flask_app.route('/verify')
def verify():
    try:
        return credit_verified_ad(int(request.args.get('user')),request.args.get('event_id'),request.args.get('type','ad1'))
    except Exception as e:
        return {"ok":False,"message":str(e)}

@flask_app.route('/app')
@flask_app.route('/')
def app_ui():
    return """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}body{background:#0a0a12;color:#fff;padding-bottom:85px}
.card{background:linear-gradient(135deg,#1a1a26,#151520);border:1px solid #2a2a3a;border-radius:18px;padding:18px;margin:12px 14px;display:flex;justify-content:space-between;align-items:center}
.val{font-size:36px;font-weight:800}.lbl{font-size:11px;color:#888}.sub{color:#4ade80;font-size:13px}
.gem{width:62px;height:62px;background:radial-gradient(circle at 30% 30%,#facc15,#f59e0b);clip-path:polygon(50% 0%,100% 30%,80% 100%,20% 100%,0% 30%);display:flex;align-items:center;justify-content:center;font-size:28px}
.btn-row{display:flex;gap:10px;margin:12px 14px}.btn{flex:1;padding:14px;border-radius:14px;border:none;font-weight:700;cursor:pointer}.btn-earn{background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff}.btn-wd{background:#1e1e2a;color:#fff;border:1px solid #2a2a3a}
.stats{display:flex;gap:10px;margin:12px 14px}.stat{flex:1;background:#15151f;border:1px solid #232334;border-radius:16px;padding:14px;text-align:center}.sval{font-weight:800;font-size:18px}.slab{font-size:11px;color:#888}
.checkin{background:linear-gradient(135deg,#7c3aed,#8b5cf6);border-radius:18px;padding:16px;margin:12px 14px;display:flex;justify-content:space-between;align-items:center}
.ad{background:linear-gradient(135deg,#0f1a2a,#162035);border:1px solid #1e3a5a;border-radius:16px;margin:10px 14px;padding:14px;display:flex;justify-content:space-between;align-items:center;position:relative}.hot{position:absolute;top:0;right:0;background:#facc15;color:#000;font-size:10px;font-weight:800;padding:3px 10px;border-radius:0 16px 0 10px}.play{width:52px;height:52px;background:#38bdf8;border-radius:50%;display:flex;align-items:center;justify-content:center}.wbtn{background:#38bdf8;color:#000;border:none;padding:10px 22px;border-radius:20px;font-weight:800;cursor:pointer}.nav{position:fixed;bottom:0;left:0;right:0;background:#0f0f18;border-top:1px solid #1e1e2e;display:flex;justify-content:space-around;padding:10px 0 20px}.navit{flex:1;text-align:center;color:#555;font-size:11px}.navit.active{color:#a78bfa}
</style></head><body>
<div style="padding:14px 16px;display:flex;justify-content:space-between"><h3>USDT Earn</h3><span style="color:#4ade80;font-size:12px">● Online</span></div>
<div class="card"><div><div class="lbl">YOUR BALANCE</div><div class="val" id="bal">$0.0000</div><div class="sub" id="sub">TOTAL 20 ads/day</div></div><div class="gem">💰</div></div>
<div class="btn-row"><button class="btn btn-earn">⚡ Earn</button><button class="btn btn-wd" onclick="goWithdraw()">💳 Withdraw</button></div>
<div class="stats"><div class="stat"><div class="sval" id="tasks">0/20</div><div class="slab">Tasks Done</div></div><div class="stat"><div class="sval" id="left">20</div><div class="slab">Left Today</div></div><div class="stat"><div class="sval" id="refs">0</div><div class="slab">Refs</div></div></div>
<div class="checkin"><div><h4>🔥 Daily Limit: 20 Ads TOTAL</h4><p style="font-size:12px;opacity:.9">Earn $0.0025 per ad - Max $0.05/day</p></div></div>
<div style="margin:18px 14px 8px;font-weight:700">💰 Watch Ads & Earn $0.0025 USDT!</div>
<div class="ad"><span class="hot">HOT</span><div style="display:flex;gap:12px;align-items:center"><div class="play">▶</div><div><h4>WATCH AD</h4><p style="font-size:12px;color:#7dd3fc" id="adtxt1">Reward $0.0025 USDT</p></div></div><button class="wbtn" onclick="watchAd('ad1',this)">Watch</button></div>
<div class="ad"><span class="hot">HOT</span><div style="display:flex;gap:12px;align-items:center"><div class="play">▶</div><div><h4>WATCH AD #2</h4><p style="font-size:12px;color:#7dd3fc" id="adtxt2">Reward $0.0025 USDT</p></div></div><button class="wbtn" onclick="watchAd('ad2',this)">Watch</button></div>
<div class="nav"><div class="navit active">⊞<br>Home</div><div class="navit">☰<br>Earn</div><div class="navit">🎮<br>Play</div><div class="navit" onclick="goRefer()">🎁<br>Refer</div><div class="navit">👤<br>Account</div></div>
<script>
const uid=new URLSearchParams(location.search).get('user')||'0';
async function load(){
 const r=await fetch('/api/me?user='+uid);const d=await r.json();if(!d.ok)return;
 document.getElementById('bal').innerText='$'+d.usdt.toFixed(4);
 document.getElementById('sub').innerText=d.total+'/'+d.total_limit+' ads done - $'+d.reward+'/ad';
 document.getElementById('tasks').innerText=d.total+'/'+d.total_limit;
 document.getElementById('left').innerText=d.total_limit-d.total;
 document.getElementById('refs').innerText=d.refs;
 document.getElementById('adtxt1').innerText='$'+d.reward+' USDT - Total: '+d.total+'/'+d.total_limit;
 document.getElementById('adtxt2').innerText='$'+d.reward+' USDT - Total: '+d.total+'/'+d.total_limit;
 if(d.total>=d.total_limit){document.querySelectorAll('.wbtn').forEach(b=>{b.innerText='Limit Done';b.disabled=true;b.style.background='#444'});}
}
async function watchAd(type,btn){
 if(btn.disabled)return;btn.disabled=true;let s=15;const iv=setInterval(()=>{btn.innerText=s+'s';s--;if(s<0){clearInterval(iv);doClaim(type,btn);}},1000);
}
async function doClaim(type,btn){
 const eid='evt_'+Date.now()+'_'+Math.random().toString(36).substr(2,9);
 const r=await fetch('/verify?user='+uid+'&event_id='+eid+'&type='+type);const d=await r.json();
 if(d.ok){btn.innerText='Claimed $'+d.reward;btn.style.background='#4ade80';load();setTimeout(()=>{btn.innerText='Watch';btn.disabled=false;btn.style.background='';},2000);}
 else{btn.innerText=d.message;setTimeout(()=>{btn.innerText='Watch';btn.disabled=false;load();},2000);}
}
function goWithdraw(){alert('Min withdraw $3.00\\nUse /withdraw in bot');}
function goRefer(){alert('Link: https://t.me/Realads01_bot?start='+uid+'\\nYou get $0.25 per ref');}
load();
</script></body></html>"""

async def is_joined(uid,ctx):
    try:
        m=await ctx.bot.get_chat_member(CHANNEL_USERNAME,uid)
        from telegram.constants import ChatMemberStatus
        return m.status not in [ChatMemberStatus.LEFT,ChatMemberStatus.KICKED]
    except: return True

async def start(update,context):
    uid=update.effective_user.id
    ref=int(context.args[0]) if context.args and context.args[0].isdigit() else None
    register_user(uid,ref)
    if not await is_joined(uid,context):
        kb=[[InlineKeyboardButton("📢 Join @freeearningofusdt",url=CHANNEL_LINK)],[InlineKeyboardButton("✅ Check Join",callback_data="check")]]
        await update.message.reply_text("Join channel first!",reply_markup=InlineKeyboardMarkup(kb));return
    bal=get_balance(uid)
    url=f"{WEBAPP_URL}/app?user={uid}"
    kb=[[InlineKeyboardButton(f"💰 Open Earn App - {TOTAL_LIMIT} ads total",web_app=WebAppInfo(url=url))]]
    await update.message.reply_text(f"💰 USDT Earn Bot\n\nBalance: ${bal} USDT\nReward: $0.0025 per ad\nTotal Limit: {TOTAL_LIMIT} ads/day\nMax: $0.05/day\n\nClick to open app!",reply_markup=InlineKeyboardMarkup(kb))

async def btns(update,context):
    q=update.callback_query;await q.answer()
    if q.data=="check": await q.edit_message_text("Joined! Send /start again")

def run_flask(): flask_app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
async def post_init(app): init_earning_tables()
def main():
    Thread(target=run_flask,daemon=True).start()
    app=Application.builder().token(os.environ.get("BOT_TOKEN")).post_init(post_init).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(btns))
    print("Bot Running FINAL $0.0025 - 20 TOTAL")
    app.run_polling()
if __name__=="__main__": main()
