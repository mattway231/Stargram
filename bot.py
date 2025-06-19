import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Токен бота (используй переменную окружения!)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context):
    await update.message.reply_text("Привет! Я бот Stargram. Используй /help для списка команд.")

async def balance(update: Update, context):
    user = update.message.from_user
    await update.message.reply_text(f"Баланс {user.username}: NOVA - 100❇️, TIX - 50✴️")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'!баланс'), balance))
    app.run_polling()
