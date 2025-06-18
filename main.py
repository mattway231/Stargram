from aiogram import Bot, Dispatcher, types
bot = Bot(token="7959499371:AAEV-_I36hL1mtdzSc5T21_2WSeMQQkkhBc")
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Я бот для твоего проекта!")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)
