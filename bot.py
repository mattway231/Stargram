import os
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройки базы (используем переменные окружения Render)
DB_URL = os.getenv("DATABASE_URL")  # Автоматически есть в Render

async def start(update: Update, context):
    user = update.message.from_user
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT DO NOTHING", 
                (user.id, user.username))
    conn.commit()
    await update.message.reply_text(f"Привет, {user.username}! Твой профиль создан.")

async def balance(update: Update, context):
    user = update.message.from_user
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT nova, tix FROM users WHERE user_id = %s", (user.id,))
    result = cur.fetchone()
    if result:
        await update.message.reply_text(f"Баланс: {result[0]}❇️, {result[1]}✴️")
    else:
        await update.message.reply_text("Ты не зарегистрирован. Напиши /start.")

if __name__ == "__main__":
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'!баланс'), balance))
    app.run_polling()
