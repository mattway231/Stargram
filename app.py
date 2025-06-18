from telegram.ext import Application, CommandHandler
from flask import Flask, request
import os
from telegram import Update

flask_app = Flask(__name__)
bot_app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

async def start(update: Update, context):
    await update.message.reply_text("👋 Бот Stargram активирован!")

@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    json_data = await request.get_json()
    update = Update.de_json(json_data, bot_app.bot)
    await bot_app.process_update(update)
    return '', 200

@flask_app.route('/')
def home():
    return "Stargram Bot is running!"

async def set_webhook():
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    await bot_app.bot.set_webhook(webhook_url)
    print(f"Webhook установлен на {webhook_url}")

if __name__ == '__main__':
    bot_app.add_handler(CommandHandler("start", start))
    
    # Установка вебхука при старте
    import asyncio
    asyncio.run(set_webhook())
    
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
