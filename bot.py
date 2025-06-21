import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4641203188"))  # Ваш ID группы

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        # Проверяем участника группы
        chat_member = await bot.get_chat_member(GROUP_ID, message.from_user.id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            await message.answer(
                "✅ <b>Доступ разрешен!</b>\n\n"
                "Используйте кнопку ниже:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="🌟 Открыть Stargram",
                        web_app=types.WebAppInfo(url="https://ваш-ник.github.io/Stargram/")
                    )]
                )
            )
        else:
            await message.answer("❌ Доступ только для участников группы!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("⚠️ Временные технические неполадки")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.info("Бот запускается...")
    asyncio.run(main())
