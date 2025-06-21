import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4641203188"))

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: Message):
    try:
        chat_member = await bot.get_chat_member(GROUP_ID, message.from_user.id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            await message.reply(
                "✅ <b>Доступ разрешен!</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🌟 Открыть Stargram",
                        web_app=WebAppInfo(url="https://mattway231.github.io/Stargram/")
                    )]
                ])
            )
        else:
            await message.reply("❌ Доступ только для участников группы!")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await message.reply("⚠️ Временные технические неполадки")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
