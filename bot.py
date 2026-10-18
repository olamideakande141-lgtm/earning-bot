import os, threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = "8979359145:AAHB6EtVAAaAIh7DFEQIropXZt9_LfLQBPc"
CHANNEL_USERNAME = "@freeearningofusdt"
CHANNEL_LINK = "https://t.me/freeearningofusdt"

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
.btn-row{display:flex;gap:12px;padding:0 16px} .btn{flex:1;padding:16px;border-radius:14px;border:none;font-weight:700;font-size:15px;cursor:pointer}
.btn-earn{background:#00d68f;color:#000} .btn-with{background:#1e1e32;color:white;border:1px solid #2a2a45}
.notice{background:#1a1a2e;border:1px dashed #00d68f;margin:12px 16px;padding:12px 14px;border-radius:12px;font-size:12px;color:#a0a0c0}
.stats{display:flex;gap:12px;padding:16px} .stat{flex:1;background:#181826;padding:18px 10px;border-radius:18px;text-align:center;border:1px solid #23233a}
.checkin{margin:16px;background:linear-gradient(135deg,#00b073,#00d68f 50%,#00ff88);border-radius:22px;padding:20px}
.checkin-top{display:flex;justify-content:space-between;align-items:center} .checkin-top button{background:#000;color:#00ff88;border:none;padding:12px 24px;border-radius:30px;font-weight:800}
.days{display:flex;gap:8px;margin-top:16px} .day{flex:1;background:rgba(0,0,0,0.18);padding:10px 2px;border-radius:12px;text-align:center;font-size:11px} .day.active{background:white;color:#00b073;font-weight:800}
.ad-card{margin:12px 16px;background:#181826;border-radius:18px;padding:16px;display:flex;justify-content:space-between;align-items:center;border:1px solid #23233a}
.watch-btn{background:#5ac8ff;color:#000;border:none;padding:10px 22px;border-radius:20px;font-weight:800}
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
<div class="notice">⚠️ Min: <b>3 USDT</b> | <b>Monday Only</b> | <b>2-3 sec</b></div>
<div class="btn-row"><button class="btn btn-earn" onclick="showView('earn')">Earn</button><button class="btn btn-with" onclick="withdraw()">Withdraw</button></div>
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
<div><b id="accName" style="font-size:17px">Username</b><br><small style="color:#6b6b8a" id="accIdText">ID: 123 • @user</small><br><small style="color:#00ff88">● Verified</small></div>
</div>
<div class="pro-stats">
<div class="pro-stat"><h3 id="accBal">0.000</h3><p>Balance</p></div>
<div class="pro-stat"><h3 id="accTotal">0.000</h3><p>Earned</p></div>
<div class="pro-stat"><h3 id="accRef">0</h3><p>Friends</p></div>
<div class="pro-stat"><h3 id="accLevel">LV1</h3>
