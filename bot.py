import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4641203188"))

# Инициализация бота с HTTPX вместо aiohttp
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
)
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: Message):
    try:
        user = message.from_user
        logger.info(f"Пользователь {user.id} запустил бота")
        
        chat_member = await bot.get_chat_member(GROUP_ID, user.id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            button = InlineKeyboardButton(
                text="🌟 Открыть Stargram",
                web_app=WebAppInfo(url="https://mattway231.github.io/Stargram/")
            )
            
            await message.reply(
                f"✅ <b>Добро пожаловать, {user.first_name}!</b>\n"
                "Доступ к Stargram разрешен!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[button]])
            )
        else:
            await message.reply(
                "❌ Доступ только для участников группы!\n"
                "Пожалуйста, вступите в группу и попробуйте снова."
            )
            
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await message.reply("⚠️ Произошла ошибка. Попробуйте позже.")

async def main():
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
