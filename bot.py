import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4641203188"))  # Ваш ID группы

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    try:
        chat_member = await bot.get_chat_member(GROUP_ID, message.from_user.id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            await message.reply(
                "✅ <b>Доступ разрешен!</b>",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(
                        "🌟 Открыть Stargram",
                        web_app=types.WebAppInfo(url="https://mattway231.github.io/Stargram/")
                    )
                )
            )
        else:
            await message.reply("❌ Доступ только для участников группы!")
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply("⚠️ Временные технические неполадки")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
