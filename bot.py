import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context):
    # Кнопка для перехода в веб-приложение
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Открыть Stargram", web_app={"url": "https://ВАШ_САЙТ.github.io/Stargram/"})]
    ])
    await update.message.reply_text(
        "Привет! Я бот Stargram. Вот твой доступ к веб-приложению:",
        reply_markup=keyboard
    )

async def balance(update: Update, context):
    user = update.message.from_user
    # Здесь позже будем брать реальный баланс из базы
    await update.message.reply_text(f"Баланс {user.username}: NOVA - 0❇️, TIX - 0✴️")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'!баланс'), balance))
    app.run_polling()
