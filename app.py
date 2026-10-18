import os
import logging
from flask import Flask, request, render_template, jsonify
from bot import bot, process_telegram_update
from earning import EarningEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'default_secret_key')
RENDER_URL = os.getenv('RENDER_EXTERNAL_URL')

@app.route('/')
def index():
    stats = EarningEngine.get_global_stats()
    return render_template('index.html', stats=stats)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "telegram-earning-bot"}), 200

@app.route(f'/webhook/{WEBHOOK_SECRET}', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        process_telegram_update(json_string)
        return 'OK', 200
    return 'Unauthorized', 403

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    if not RENDER_URL or not BOT_TOKEN:
        return jsonify({"error": "Missing configuration parameters."}), 400
    
    webhook_url = f"{RENDER_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET}"
    success = bot.set_webhook(url=webhook_url)
    if success:
        return jsonify({"message": f"Webhook successfully registered to {webhook_url}"}), 200
    return jsonify({"error": "Failed to set Telegram webhook."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
