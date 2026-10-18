
ADS PAYOUT - SETUP

FILES
- app.py: Flask website and API entry point
- bot.py: Telegram bot
- earning.py: API routes, membership verification, demo tasks
- templates/index.html: Mini App dashboard
- requirements.txt: Python dependencies
- render.yaml: Render deployment configuration

SETUP
1. Upload all files to GitHub.
2. Make sure index.html is inside the templates folder.
3. Deploy using the Render configuration.
4. Set BOT_TOKEN to your current Telegram bot token.
5. Set WEB_APP_URL to the deployed website URL.
6. Set TELEGRAM_CHANNEL to @freeearningofusdt.
7. Make the bot an administrator of the required channel.
8. Open the bot in Telegram and send /start.

TEST MODE
Demo credits have no cash value.
Live paid ads are not connected.
Withdrawals are disabled.
Referral attribution and referral rewards are not fully implemented.

SECURITY
Do not put your bot token in source code or publish it in GitHub.
If a token has been exposed, revoke it using BotFather.
Do not enable real withdrawals until real funding, identity checks
where required, secure payout processing, and server-side verification
have been implemented.
