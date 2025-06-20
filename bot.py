import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-10012345678"))  # Ваш ID группы

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    try:
        member = await bot.get_chat_member(GROUP_ID, message.from_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            await message.reply(
                "✅ Доступ разрешен!\n\n"
                "Используйте кнопку ниже:",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(
                        "🌟 Открыть Stargram",
                        web_app=types.WebAppInfo(url="https://ваш-ник.github.io/Stargram/")
                    )
                )
            )
        else:
            await message.reply("❌ Вы не участник группы!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply("⚠️ Временные технические неполадки")

if __name__ == "__main__":
    logger.info("Бот запускается...")
    executor.start_polling(dp, skip_updates=True)
