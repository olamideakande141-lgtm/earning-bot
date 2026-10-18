import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from earning import EarningEngine

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Your Telegram Channel Username or ID
CHANNEL_USERNAME = "@freeearningofusdt"

def check_subscription(user_id: int) -> bool:
    """Checks if the user is a member, administrator, or creator of the channel."""
    if not BOT_TOKEN:
        return True # Bypass for local testing if token isn't set yet
    try:
        member = bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

def get_subscription_markup():
    """Returns an inline keyboard prompting the user to join the channel."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Join Channel", url="https://t.me/freeearningofusdt"))
    markup.add(InlineKeyboardButton("🔄 Verify Membership", callback_data="verify_subscription"))
    return markup

def process_telegram_update(json_str):
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    # Enforce mandatory channel subscription check
    if not check_subscription(user_id):
        bot.send_message(
            message.chat.id,
            f"⚠️ **Access Denied!**\n\nTo use this bot and earn USDT, you must first join our official Telegram channel: {CHANNEL_USERNAME}\n\nClick the button below to join, then click 'Verify Membership'.",
            reply_markup=get_subscription_markup(),
            parse_mode="Markdown"
        )
        return

    EarningEngine.register_user(str(user_id), username)
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("💰 Earn Money", callback_data="btn_earn"),
        InlineKeyboardButton("📊 Balance", callback_data="btn_balance"),
        InlineKeyboardButton("🎁 Daily Reward", callback_data="btn_daily"),
        InlineKeyboardButton("💳 Withdraw", callback_data="btn_withdraw")
    )
    
    welcome_text = (
        f"Welcome to the Earning Bot, {username}!\n\n"
        "Complete simple tasks, claim daily bonuses, and invite friends to earn real rewards."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # Handle subscription verification callback
    if call.data == "verify_subscription":
        if check_subscription(user_id):
            bot.answer_callback_query(call.id, "✅ Membership verified successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            fake_message = call.message
            fake_message.from_user = call.from_user
            send_welcome(fake_message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)
        return

    # Security check: ensure they are still joined before allowing navigation
    if not check_subscription(user_id):
        bot.answer_callback_query(call.id, "⚠️ Please join our channel first!", show_alert=True)
        bot.send_message(
            chat_id,
            f"⚠️ You must join {CHANNEL_USERNAME} to continue using features.",
            reply_markup=get_subscription_markup()
        )
        return

    str_user_id = str(user_id)
    
    if call.data == "btn_earn":
        tasks = EarningEngine.get_available_tasks(str_user_id)
        markup = InlineKeyboardMarkup()
        for task in tasks:
            markup.add(InlineKeyboardButton(task['title'], callback_data=f"task_{task['id']}"))
        bot.send_message(chat_id, "Select an active task to complete:", reply_markup=markup)
        
    elif call.data.startswith("task_"):
        task_id = call.data.split("_")[1]
        reward = EarningEngine.complete_task(str_user_id, task_id)
        bot.answer_callback_query(call.id, f"Task completed! Earned ${reward:.2f}")
        bot.send_message(chat_id, f"✅ Task finished. ${reward:.2f} added to your account.")
        
    elif call.data == "btn_balance":
        balance = EarningEngine.get_user_balance(str_user_id)
        bot.send_message(chat_id, f"💳 Your current available balance is: ${balance:.2f} USDT")
        
    elif call.data == "btn_daily":
        success, message_text = EarningEngine.claim_daily_bonus(str_user_id)
        bot.send_message(chat_id, message_text)
        
    elif call.data == "btn_withdraw":
        balance = EarningEngine.get_user_balance(str_user_id)
        if balance < 10.0:
            bot.send_message(chat_id, f"⚠️ Minimum withdrawal threshold is $10.00 USDT. Current balance: ${balance:.2f}")
        else:
            bot.send_message(chat_id, "Enter your TRC20/ERC20 wallet address to initiate payout:")
