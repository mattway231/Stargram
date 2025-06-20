import os
import logging
from telegram import Update, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

# Настройки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4641203188"))  # Ваш ID группы с минусом
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-service.onrender.com
PORT = int(os.getenv("PORT", 10000))

async def start(update: Update, context: CallbackContext):
    try:
        user = update.message.from_user
        logger.info(f"User {user.id} started the bot")
        
        # Проверяем участника группы
        try:
            chat_member = await context.bot.get_chat_member(GROUP_ID, user.id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                await update.message.reply_text("❌ Доступ только для участников группы!")
                return
        except TelegramError as e:
            logger.error(f"Group check error: {e}")
            await update.message.reply_text("⚠️ Ошибка проверки доступа")
            return

        # Если проверка пройдена
        await update.message.reply_text(
            "🔐 Доступ разрешен!\n\n"
            "Нажмите кнопку ниже, чтобы открыть приложение:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🌟 Открыть Stargram",
                    web_app=WebAppInfo(url="https://ваш-ник.github.io/Stargram/")
                )
            ]])
        )

    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await update.message.reply_text("🚧 Технические неполадки. Попробуйте позже.")

def main():
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))

        # Webhook настройки
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
            secret_token=os.getenv("WEBHOOK_SECRET"),
            cert=None,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.critical(f"Bot failed: {e}")

if __name__ == "__main__":
    main()
