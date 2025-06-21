import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
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

# Инициализация бота (новая версия aiogram 3.0.0rc2)
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: Message):
    try:
        user = message.from_user
        logger.info(f"User {user.id} started bot")
        
        # Проверяем членство в группе
        try:
            chat_member = await bot.get_chat_member(GROUP_ID, user.id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                await message.reply("❌ Доступ только для участников группы!")
                return
        except Exception as group_error:
            logger.error(f"Group check error: {group_error}")
            await message.reply("⚠️ Ошибка проверки доступа")
            return

        # Создаем кнопку с WebApp
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="🌟 Открыть Stargram",
                        web_app=types.WebAppInfo(url="https://mattway231.github.io/Stargram/")
                    )
                ]
            ]
        )
        
        await message.reply(
            f"✅ <b>Добро пожаловать, {user.first_name}!</b>\n"
            "Доступ к Stargram разрешен!",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await message.reply("⚠️ Произошла ошибка. Попробуйте позже.")

async def main():
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot stopped: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
