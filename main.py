from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os

# Токен из переменных окружения (безопасность!)
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("🚀 Добро пожаловать в NovaCoinBot!")

if __name__ == '__main__':
    executor.start_polling(dp)
