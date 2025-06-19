import os
import logging
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка логов
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигов
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    raise ValueError("Токен бота не найден! Проверь переменную TELEGRAM_BOT_TOKEN в Render.")

async def start(update: Update, context):
    try:
        user = update.message.from_user
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, username) 
                    VALUES (%s, %s) 
                    ON CONFLICT (user_id) DO NOTHING
                """, (user.id, user.username))
        await update.message.reply_text(f"🚀 Привет, {user.username}! Ты в Stargram.")
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await update.message.reply_text("❌ Ошибка сервера. Попробуй позже.")

async def balance(update: Update, context):
    try:
        user = update.message.from_user
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT nova, tix FROM users WHERE user_id = %s", (user.id,))
                result = cur.fetchone()
                if result:
                    await update.message.reply_text(f"💰 Баланс: {result[0]}❇️ | {result[1]}✴️")
                else:
                    await update.message.reply_text("ℹ️ Напиши /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка в !баланс: {e}")
        await update.message.reply_text("❌ Не удалось проверить баланс.")

def main():
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.Regex(r'!баланс'), balance))
        app.run_polling()
    except Exception as e:
        logger.critical(f"Бот упал: {e}")

if __name__ == "__main__":
    main()
