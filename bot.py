import os
import logging
import psycopg2
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.error import Conflict

# Настройки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")
GROUP_ID = -4641203188  # Замени на ID группы

def init_db():
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        nova INTEGER DEFAULT 100,
                        tix INTEGER DEFAULT 50,
                        is_member BOOLEAN DEFAULT FALSE
                    );
                """)
        logger.info("✅ Таблица users создана")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблицы: {e}")

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    try:
        # Проверяем, есть ли пользователь в группе
        chat_member = await context.bot.get_chat_member(GROUP_ID, user.id)
        is_member = chat_member.status in ['member', 'administrator', 'creator']
        
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, username, is_member)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET is_member = EXCLUDED.is_member
                """, (user.id, user.username, is_member))
        
        if is_member:
            await update.message.reply_text(
                "Доступ разрешен! Открывайте приложение:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌟 Stargram", web_app=WebAppInfo(url="https://ваш-ник.github.io/Stargram/"))
                ]])
            )
        else:
            await update.message.reply_text("❌ Вы не участник группы!")
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await update.message.reply_text("⚠️ Ошибка сервера")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    try:
        app.run_polling()
    except Conflict:
        logger.error("Бот уже запущен! Остановите другие экземпляры.")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
