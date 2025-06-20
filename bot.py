# bot.py
import os
import logging
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import Conflict

# Настройки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://your-bot-service.onrender.com
GROUP_ID = -4641203188  # Замените на реальный ID группы

async def start(update: Update, context: CallbackContext):
    try:
        user = update.message.from_user
        chat_member = await context.bot.get_chat_member(GROUP_ID, user.id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            await update.message.reply_text(
                "Доступ разрешен! Открывайте приложение:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌟 Stargram", web_app=WebAppInfo(url="https://mattway231.github.io/Stargram/"))
                ]])
            )
        else:
            await update.message.reply_text("❌ Доступ только для участников группы!")
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await update.message.reply_text("⚠️ Временная ошибка сервера")

async def set_webhook(app: Application):
    await app.bot.set_webhook(WEBHOOK_URL)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    # Настройка webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        webhook_url=WEBHOOK_URL,
        secret_token='YOUR_SECRET_TOKEN',
        cert=None
    )

if __name__ == "__main__":
    main()
