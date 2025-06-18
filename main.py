from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request
import os

app = Flask(__name__)
bot_app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

# Обработчик /start
async def start(update, context):
    await update.message.reply_text("👋 Бот Stargram активирован!")

# API-эндпоинт для сайта
@app.route('/api/group_data', methods=['GET'])
def get_group_data():
    # Здесь будет логика получения данных из группы
    return {"members": 150, "messages_today": 42}

# Вебхук для приёма данных от Telegram
@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(await request.get_json(), bot_app.bot)
    await bot_app.process_update(update)
    return '', 200

if __name__ == '__main__':
    # Регистрация обработчиков
    bot_app.add_handler(CommandHandler("start", start))
    
    # Запуск Flask и бота
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
