import os
import logging
import psycopg2
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
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
                        nova INTEGER DEFAULT 0,
                        tix INTEGER DEFAULT 0
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
    init_db()  # Создаем таблицу при запуске
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(MessageHandler(filters.Regex(r'!баланс'), balance))
    
    app.run_polling()

from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import psycopg2
import os
from flask import Flask, request, jsonify

# Flask-сервер для проверки участников
app_flask = Flask(__name__)

@app_flask.route('/check_user', methods=['POST'])
def check_user():
    data = request.get_json()
    user_id = data['user_id']
    
    # Проверка в базе (или через Telegram API)
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            if cur.fetchone():
                return jsonify({"is_member": True})
    
    return jsonify({"is_member": False})

async def send_webapp(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Открыть Stargram:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🌟 Открыть",
                web_app=WebAppInfo(url="https://mattway231.github.io/Stargram/")
            )
        ]])
    )

def main():
    # Запуск Flask в отдельном потоке
    from threading import Thread
    Thread(target=app_flask.run, kwargs={'port': 5000}).start()
    
    # Инициализация бота
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", send_webapp))
    app.run_polling()
    
if __name__ == "__main__":
    main()
