import os
import logging
import psycopg2
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from flask import Flask, request, jsonify

# Настройки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")
GROUP_ID = -4641203188
# Flask-сервер
app_flask = Flask(__name__)

def init_db():
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        nova INTEGER DEFAULT 0,
                        tix INTEGER DEFAULT 0,
                        is_member BOOLEAN DEFAULT FALSE
                    );
                """)
        logger.info("✅ Таблица users создана")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблицы: {e}")

async def check_member(user_id: int) -> bool:
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT is_member FROM users WHERE user_id = %s", (user_id,))
                result = cur.fetchone()
                return result[0] if result else False
    except Exception as e:
        logger.error(f"Ошибка проверки участника: {e}")
        return False

@app_flask.route('/check_user', methods=['POST'])
def handle_check_user():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "No user_id"}), 400
    
    is_member = check_member(user_id)
    return jsonify({"is_member": is_member})

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                # Проверяем, есть ли пользователь в группе
                chat_member = await context.bot.get_chat_member(GROUP_ID, user.id)
                is_member = chat_member.status in ['member', 'administrator', 'creator']
                
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

def run_flask():
    app_flask.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    init_db()
    from threading import Thread
    Thread(target=run_flask).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
