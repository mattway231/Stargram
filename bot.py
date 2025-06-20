import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4641203188"))  # Ваш ID группы
ADMIN_ID = int(os.getenv("ADMIN_ID", "815270560"))  # Ваш ID для уведомлений

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

async def on_startup(dp):
    logger.info("Бот запущен")
    await bot.send_message(ADMIN_ID, "🤖 Бот успешно запущен!")

async def on_shutdown(dp):
    logger.info("Бот остановлен")
    await bot.send_message(ADMIN_ID, "🛑 Бот остановлен!")

async def health_check():
    try:
        await bot.get_me()
        logger.info("Проверка здоровья: OK")
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {e}")
        await restart_bot()

async def restart_bot():
    logger.warning("Перезапуск бота...")
    await dp.storage.close()
    await bot.session.close()
    asyncio.create_task(start_bot())

async def start_bot():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        await asyncio.sleep(10)
        await restart_bot()

async def web_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Stargram Bot is alive"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    return runner

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    try:
        chat_member = await bot.get_chat_member(GROUP_ID, message.from_user.id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            await message.reply(
                "Доступ разрешен!",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(
                        "🌟 Открыть Stargram",
                        web_app=types.WebAppInfo(url="https://ваш-ник.github.io/Stargram/")
                    )
                )
            )
        else:
            await message.reply("❌ Доступ только для участников группы!")
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await message.reply("⚠️ Временные технические неполадки")

async def main():
    runner = await web_server()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(health_check, 'interval', minutes=3)
    scheduler.start()
    
    try:
        await on_startup(dp)
        await start_bot()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        scheduler.shutdown()
        await on_shutdown(dp)
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")
