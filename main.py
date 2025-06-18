from telegram.ext import Application, CommandHandler
from flask import Flask, request
import os

# Инициализация Flask
flask_app = Flask(__name__)

# Инициализация бота
bot_app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

# Обработчик команды /start
async def start(update, context):
    await update.message.reply_text("👋 Бот Stargram активирован!")

# Регистрация обработчиков
bot_app.add_handler(CommandHandler("start", start))

# Вебхук
@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    from telegram import Update
    json_data = await request.get_json()
    update = Update.de_json(json_data, bot_app.bot)
    await bot_app.process_update(update)
    return '', 200

# Главная страница для проверки работы
@flask_app.route('/')
def home():
    return "Stargram Bot is running!"

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
