import express from 'express';
import crypto from 'crypto';
import cors from 'cors';
import { Telegraf } from 'telegraf';
import path from 'path';
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const bot = new Telegraf(process.env.BOT_TOKEN);

const REQUIRED_CHANNEL = "@freeearningofusdt";
const REF_REWARD = 0.025;
const MIN_WITHDRAW = 5;
const BLOCKED = ["LTC","DOGE"];

let users = {};
let withdrawals = [];
let tasks = [
  { id: 1, title: "Join @freeearningofusdt", reward: 0.01, link: "https://t.me/freeearningofusdt", type: "Telegram" },
  { id: 2, title: "Daily Check-in", reward: 0.01, link: "", type: "Bonus" }
];
let processedEvents = new Set();

app.use('/api/adsgalaxy/reward', express.raw({type: '*/*'}));
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ADSGALAXY @Realads01_bot CALLBACK
app.post('/api/adsgalaxy/reward', (req,res) => {
  try{
    const raw = req.body.toString();
    const payload = JSON.parse(raw);
    const eventId = req.headers['x-adsgalaxy-event-id'] || payload.event_id;
    if(processedEvents.has(eventId)) return res.status(200).send("Already");
    const userId = payload.user_id?.toString();
    if(userId){
      if(!users[userId]) users[userId] = { balance: 0, tasks: 0, referrals: [], referredBy: null };
      processedEvents.add(eventId);
      users[userId].balance += 0.002;
      users[userId].tasks += 1;
    }
    res.status(200).send("OK");
  }catch(e){ res.status(200).send("OK"); }
});

app.get('/api/check-joined', async (req,res) => {
  try{
    const m = await bot.telegram.getChatMember(REQUIRED_CHANNEL, req.query.userId);
    res.json({joined: !['left','kicked','banned'].includes(m.status)});
  }catch(e){ res.json({joined:false}); }
});

app.get('/api/user', (req,res) => {
  const { userId } = req.query;
  if(!users[userId]) users[userId] = { balance: 0, tasks: 0, referrals: [], referredBy: null };
  const u = users[userId];
  res.json({ balance: u.balance, tasks: u.tasks, referralCount: u.referrals.length, referralLink: `https://t.me/${process.env.BOT_USERNAME || 'AdsPayoutBot'}?startapp=${userId}` });
});

app.get('/api/tasks', (req,res) => res.json(tasks));

app.post('/api/referral', (req,res) => {
  const { userId, refId } = req.body;
  if(!userId || !refId || userId==refId) return res.json({ok:false});
  if(!users[userId]) users[userId] = { balance: 0, tasks: 0, referrals: [], referredBy: null };
  if(!users[refId]) users[refId] = { balance: 0, tasks: 0, referrals: [], referredBy: null };
  if(users[userId].referredBy) return res.json({ok:false});
  users[userId].referredBy = refId;
  users[refId].referrals.push(userId);
  users[refId].balance += REF_REWARD;
  res.json({ok:true});
});

app.post('/api/earn', (req,res) => {
  const { userId, amount } = req.body;
  if(!users[userId]) users[userId] = { balance: 0, tasks: 0, referrals: [], referredBy: null };
  users[userId].balance += parseFloat(amount);
  users[userId].tasks += 1;
  res.json({ok:true});
});

app.post('/api/withdraw', (req,res) => {
  const { userId, wallet, cryptoType } = req.body;
  const user = users[userId];
  if(!user || user.balance < MIN_WITHDRAW) return res.json({ok:false, msg:`Min $${MIN_WITHDRAW}. You have $${user?.balance.toFixed(4) || 0}`});
  if(BLOCKED.includes(cryptoType)) return res.json({ok:false, msg:`${cryptoType} blocked. LTC & DOGE not allowed`});
  const fee = user.balance * 0.20;
  const payout = user.balance - fee;
  withdrawals.push({ id: Date.now(), userId, wallet, cryptoType, requested: user.balance, fee, payout, status: "pending", date: new Date().toISOString() });
  user.balance = 0;
  res.json({ok:true, msg:`Manual request sent! You will get $${payout.toFixed(4)} in ${cryptoType} (20% fee)`});
});

app.get('/api/admin/tasks', (req,res) => res.json(tasks));
app.post('/api/admin/tasks', (req,res) => {
  const { title, reward, link, type, secret } = req.body;
  if(secret !== process.env.ADMIN_SECRET) return res.status(403).json({ok:false});
  tasks.push({ id: Date.now(), title, reward: parseFloat(reward), link, type });
  res.json({ok:true, tasks});
});
app.delete('/api/admin/tasks/:id', (req,res) => {
  if(req.body.secret !== process.env.ADMIN_SECRET) return res.status(403).json({ok:false});
  tasks = tasks.filter(t => t.id != req.params.id);
  res.json({ok:true, tasks});
});
app.get('/api/admin/withdrawals', (req,res) => {
  if(req.query.secret !== process.env.ADMIN_SECRET) return res.status(403).json({ok:false});
  res.json(withdrawals);
});
app.post('/api/admin/withdrawals/approve', (req,res) => {
  if(req.body.secret !== process.env.ADMIN_SECRET) return res.status(403).json({ok:false});
  const w = withdrawals.find(x => x.id == req.body.id);
  if(w) w.status = "paid";
  res.json({ok:true, withdrawals});
});

app.get('/admin', (req,res) => res.sendFile(path.join(__dirname, 'public', 'admin.html')));
app.get('*', (req,res) => res.sendFile(path.join(__dirname, 'public', 'index.html')));

bot.launch();
app.listen(process.env.PORT || 10000, () => console.log("Ads Payout Running"));
