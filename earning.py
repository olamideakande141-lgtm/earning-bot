from pymongo import MongoClient
from datetime import datetime, date
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["earni_bot"]

users = db["users"]
earnings = db["earnings"]
ads_daily = db["ads_daily"]
withdraws = db["withdraws"]

def get_user(uid): 
    return users.find_one({"user_id": uid})

def create_user(user, ref=None):
    if get_user(user.id): 
        return get_user(user.id)
    if ref and int(ref)==user.id: 
        ref=None
    doc = {
        "user_id": user.id,
        "first_name": user.first_name,
        "username": user.username,
        "balance": 0.0,
        "ads_watched": 0,
        "referrals": 0,
        "total_earned_from_refs": 0.0,
        "referred_by": int(ref) if ref else None,
        "joined_at": datetime.utcnow()
    }
    users.insert_one(doc)
    if ref:
        r = get_user(int(ref))
        if r:
            users.update_one({"user_id": int(ref)}, {"$inc": {"balance": 0.025, "referrals": 1, "total_earned_from_refs": 0.025}})
            earnings.insert_one({"user_id": int(ref), "type": "referral", "amount": 0.025, "description": f"Referral {user.first_name}", "created_at": datetime.utcnow()})
    return get_user(user.id)

def can_watch(uid):
    today=str(date.today())
    d=ads_daily.find_one({"user_id": uid, "date": today})
    return (d["count"]<20, d["count"]) if d else (True,0)

def add_ad(uid):
    today=str(date.today())
    can,c=can_watch(uid)
    if not can: 
        return False
    ads_daily.update_one({"user_id": uid, "date": today}, {"$inc": {"count": 1}, "$set": {"last": datetime.utcnow()}}, upsert=True)
    users.update_one({"user_id": uid}, {"$inc": {"balance": 0.005, "ads_watched": 1}})
    earnings.insert_one({"user_id": uid, "type": "ad", "amount": 0.005, "description": f"Ad {c+1}/20", "created_at": datetime.utcnow()})
    return True

def today_ads(uid):
    d=ads_daily.find_one({"user_id": uid, "date": str(date.today())})
    return d["count"] if d else 0

def add_withdraw(uid, amount, wallet):
    u=get_user(uid)
    if not u or u["balance"]<amount: 
        return None
    doc={
        "user_id": uid,
        "amount": amount,
        "fee": amount*0.20,
        "receive": amount*0.80,
        "wallet": wallet,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    res=withdraws.insert_one(doc)
    doc["_id"]=res.inserted_id
    return doc
