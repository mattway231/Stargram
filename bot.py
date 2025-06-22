import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
import sqlite3
import json

# Load environment
load_dotenv()

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        nova_balance INTEGER DEFAULT 0,
        tix_balance INTEGER DEFAULT 0,
        avatar_color TEXT DEFAULT 'orange'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        currency TEXT,
        type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Bot setup
bot = Bot(token=os.getenv("TOKEN"), parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: Message):
    user = message.from_user
    save_user(user)
    
    try:
        chat_member = await bot.get_chat_member(os.getenv("GROUP_ID"), user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            await message.reply("❌ Доступ только для участников группы!")
            return
    except Exception as e:
        logging.error(f"Group check error: {e}")
        await message.reply("⚠️ Ошибка проверки доступа")
        return

    webapp_url = f"{os.getenv('WEBAPP_URL')}?user_id={user.id}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌟 Открыть Stargram",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ]
        ]
    )
    
    await message.reply(
        f"✅ <b>Добро пожаловать, {user.first_name}!</b>\n"
        "Доступ к Stargram разрешен!",
        reply_markup=keyboard
    )

def save_user(user):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR IGNORE INTO users (id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    ''', (user.id, user.username, user.first_name, user.last_name))
    
    conn.commit()
    conn.close()

async def on_startup(bot: Bot):
    await bot.set_webhook(os.getenv("WEBHOOK_URL"))

async def main():
    await bot.delete_webhook()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
