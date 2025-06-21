import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4641203188"))  # Замените на реальный ID группы

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        user = message.from_user
        logger.info(f"User @{user.username} ({user.id}) started the bot")
        
        # Проверка участника группы
        chat_member = await bot.get_chat_member(GROUP_ID, user.id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            await message.answer(
                "✅ <b>Доступ разрешен!</b>\n\n"
                "Нажмите кнопку ниже, чтобы открыть приложение:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(
                        text="🌟 Открыть Stargram",
                        web_app=types.WebAppInfo(url="https://mattway231.github.io/Stargram/")
                ]])
            )
        else:
            await message.answer("❌ Доступ только для участников группы!")
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await message.answer("⚠️ Временные технические неполадки")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logger.info("Starting bot...")
    asyncio.run(main())
