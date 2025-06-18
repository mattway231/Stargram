from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 Бот Stargram активирован! Он работает только для передачи данных сайту.")

if __name__ == '__main__':
    executor.start_polling(dp)
