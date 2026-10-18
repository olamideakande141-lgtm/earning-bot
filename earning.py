import time

class EarningEngine:
    _users_db = {}
    _tasks = [
        {"id": "t1", "title": "Watch Promotional Ad ($0.50)", "reward": 0.50},
        {"id": "t2", "title": "Visit Partner Web Portal ($0.25)", "reward": 0.25},
        {"id": "t3", "title": "Subscribe to Official Channel ($1.00)", "reward": 1.00}
    ]

    @classmethod
    def register_user(cls, user_id: str, username: str):
        if user_id not in cls._users_db:
            cls._users_db[user_id] = {
                "username": username,
                "balance": 1.00,
                "last_daily": 0,
                "completed_tasks": [],
                "joined_timestamp": time.time()
            }

    @classmethod
    def get_user_balance(cls, user_id: str) -> float:
        user = cls._users_db.get(user_id)
        return user["balance"] if user else 0.0

    @classmethod
    def get_available_tasks(cls, user_id: str) -> list:
        user = cls._users_db.get(user_id)
        if not user:
            return []
        completed = user.get("completed_tasks", [])
        return [t for t in cls._tasks if t["id"] not in completed]

    @classmethod
    def complete_task(cls, user_id: str, task_id: str) -> float:
        user = cls._users_db.get(user_id)
        if not user:
            return 0.0
        
        for task in cls._tasks:
            if task["id"] == task_id and task_id not in user["completed_tasks"]:
                user["balance"] += task["reward"]
                user["completed_tasks"].append(task_id)
                return task["reward"]
        return 0.0

    @classmethod
    def claim_daily_bonus(cls, user_id: str) -> tuple[bool, str]:
        user = cls._users_db.get(user_id)
        if not user:
            return False, "User account record not found."
            
        current_time = time.time()
        one_day_seconds = 86400
        
        if current_time - user["last_daily"] >= one_day_seconds:
            bonus = 0.50
            user["balance"] += bonus
            user["last_daily"] = current_time
            return True, f"🎉 Daily reward claimed! ${bonus:.2f} added to your account balance."
        else:
            remaining_hours = int((one_day_seconds - (current_time - user["last_daily"])) / 3600)
            return False, f"⏳ Daily bonus already claimed. Please return in ~{remaining_hours} hours."

    @classmethod
    def get_global_stats(cls) -> dict:
        total_users = len(cls._users_db)
        total_payouts = sum(u["balance"] for u in cls._users_db.values())
        return {
            "total_users": total_users,
            "total_payouts": round(total_payouts, 2),
            "status": "Operational"
        }
