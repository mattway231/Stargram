import os
import logging
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

def init_db():
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        nova INTEGER DEFAULT 100,
                        tix INTEGER DEFAULT 50
                    );
                """)
        logger.info("✅ Таблица users создана или уже существует")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблицы: {e}")

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
    init_db()  # Проверяем и создаем таблицу при запуске
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'!баланс'), balance))
    app.run_polling()

if __name__ == "__main__":
    main()
