import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Токен бота (берётся из переменных окружения Render)
TOKEN = os.getenv("7959499371:AAEV-_I36hL1mtdzSc5T21_2WSeMQQkkhBc")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я бот Stargram. Используй /help для списка команд.")

# Обработчик команды !баланс
@dp.message(lambda message: message.text and message.text.lower() == "!баланс")
async def balance(message: types.Message):
    await message.answer(f"Баланс {message.from_user.username}: NOVA - 0❇️, TIX - 0✴️")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
