import os
import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import WebAppInfo, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from config import Config
from database import init_db, AsyncSessionLocal, User, Transaction, Report, MapPoint
from integrations import AIService, MapService
from sqlalchemy import select, func

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=Config.TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
map_service = MapService()

async def is_member(user_id: int) -> bool:
    """Проверка, что пользователь в группе"""
    try:
        member = await bot.get_chat_member(Config.GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки участника: {e}")
        return False

async def update_user_activity(user_id: int):
    """Обновление времени последней активности"""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if user:
            user.last_active = datetime.utcnow()
            await session.commit()

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    if not await is_member(message.from_user.id):
        return await message.answer("❌ Доступ только для участников группы!")
    
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                is_admin=message.from_user.id in Config.ADMINS,
                is_owner=message.from_user.id == Config.OWNER
            )
            session.add(user)
            await session.commit()
        
        # Кнопка для веб-приложения
        builder = InlineKeyboardBuilder()
        builder.button(
            text="🌟 Открыть Stargram", 
            web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}?user_id={message.from_user.id}")
        )
        
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n"
            "Добро пожаловать в Stargram - твой цифровой мир!",
            reply_markup=builder.as_markup()
        )

@dp.message(Command('balance'))
async def cmd_balance(message: types.Message):
    """Проверка баланса"""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            return await message.answer("❌ Сначала запустите бота командой /start")
        
        await message.answer(
            f"💰 Ваш баланс:\n"
            f"$NOVA: {user.nova}❇️\n"
            f"$TIX: {user.tix}✴️"
        )

@dp.message(Command('report'))
async def cmd_report(message: types.Message):
    """Отправка жалобы на сообщение"""
    if not message.reply_to_message:
        return await message.answer("ℹ️ Ответьте на сообщение, на которое хотите пожаловаться")
    
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            return await message.answer("❌ Сначала запустите бота командой /start")
        
        if user.nova < Config.REPORT_COST:
            return await message.answer(f"❌ Недостаточно NOVA. Нужно {Config.REPORT_COST}❇️")
        
        # Проверка через Coze API
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
        is_violation = await AIService.check_violation(text)
        
        # Создаем запись о жалобе
        report = Report(
            user_id=user.id,
            message_id=message.reply_to_message.message_id,
            message_text=text[:1000],
            status="approved" if is_violation else "rejected"
        )
        session.add(report)
        
        if is_violation:
            user.nova += (Config.REPORT_REWARD - Config.REPORT_COST)
            response_text = (
                f"✅ Нарушение найдено! Вам начислено {Config.REPORT_REWARD - Config.REPORT_COST}❇️\n"
                f"Текущий баланс: {user.nova}❇️"
            )
            
            # Уведомление админов
            for admin_id in Config.ADMINS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"🚨 Пользователь @{user.username} сообщил о нарушении:\n"
                        f"Сообщение: {text[:500]}\n"
                        f"Ссылка: https://t.me/c/{str(Config.GROUP_ID).replace('-100', '')}/{message.reply_to_message.message_id}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления админа {admin_id}: {e}")
        else:
            user.nova -= Config.REPORT_COST
            response_text = (
                f"❌ Нарушение не найдено. Стоимость проверки: {Config.REPORT_COST}❇️\n"
                f"Текущий баланс: {user.nova}❇️"
            )
        
        await session.commit()
        await message.answer(response_text)

@dp.message(Command('admin'))
async def cmd_admin(message: types.Message):
    """Админ-панель"""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user or not user.is_admin:
            return await message.answer("❌ Доступ запрещён")
        
        # Статистика
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(User.id)).where(
                User.last_active >= datetime.utcnow() - timedelta(days=1)
            )
        )
        
        # Последние 5 транзакций
        transactions = await session.execute(
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(5)
        )
        
        text = (
            f"👑 Админ-панель\n\n"
            f"Пользователей: {total_users}\n"
            f"Активных: {active_users}\n\n"
            f"Последние операции:\n"
        )
        
        for tx in transactions.scalars():
            text += f"{tx.created_at.strftime('%H:%M')} - {tx.type} {tx.amount}{'❇️' if tx.currency == 'nova' else '✴️'}\n"
        
        # Кнопки для админа
        builder = InlineKeyboardBuilder()
        if user.is_owner:
            builder.button(text="Выдать валюту", callback_data="admin_give_currency")
            builder.button(text="Статистика", callback_data="admin_stats")
            builder.button(text="Рассылка", callback_data="admin_broadcast")
        
        builder.button(text="Список жалоб", callback_data="admin_reports")
        builder.adjust(2)
        
        await message.answer(text, reply_markup=builder.as_markup())

@dp.message()
async def handle_messages(message: types.Message):
    """Начисление валюты за сообщения"""
    await update_user_activity(message.from_user.id)
    
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            # Начисляем 100 NOVA за каждое сообщение (но не более 100 в день)
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            messages_today = await session.scalar(
                select(func.count(Transaction.id)).where(
                    Transaction.user_id == user.id,
                    Transaction.type == "message_reward",
                    Transaction.created_at >= today_start
                )
            )
            
            if messages_today < Config.DAILY_MESSAGE_LIMIT:
                user.nova += Config.DAILY_MESSAGE_REWARD
                
                tx = Transaction(
                    user_id=user.id,
                    amount=Config.DAILY_MESSAGE_REWARD,
                    currency="nova",
                    type="message_reward"
                )
                session.add(tx)
                await session.commit()

async def start_web_app():
    """Запуск веб-сервера для обработки запросов из веб-приложения"""
    app = web.Application()
    
    app.add_routes([
        web.get('/api/user', handle_get_user),
        web.post('/api/report', handle_report),
        web.post('/api/exchange', handle_exchange),
        web.post('/api/gift', handle_gift),
        web.get('/api/map/points', handle_map_points),
        web.post('/api/map/collect', handle_collect_point),
        web.get('/api/admin/reports', handle_admin_reports),
        web.post('/api/admin/broadcast', handle_admin_broadcast)
    ])
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def handle_get_user(request):
    """Получение данных пользователя"""
    user_id = request.query.get('user_id')
    if not user_id:
        return web.json_response({'error': 'User ID is required'}, status=400)
    
    async with AsyncSessionLocal() as session:
        user = await session.get(User, int(user_id))
        if not user:
            return web.json_response({'error': 'User not found'}, status=404)
        
        return web.json_response({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'nova': user.nova,
            'tix': user.tix,
            'is_admin': user.is_admin,
            'is_owner': user.is_owner
        })

async def handle_map_points(request):
    """Получение точек на карте"""
    user_id = request.query.get('user_id')
    lat = request.query.get('lat')
    lon = request.query.get('lon')
    
    if not all([user_id, lat, lon]):
        return web.json_response({'error': 'Missing parameters'}, status=400)
    
    try:
        # Генерация новых точек
        points = await map_service.generate_points(int(user_id), float(lat), float(lon))
        
        # Возвращаем только не собранные точки
        async with AsyncSessionLocal() as session:
            active_points = await session.execute(
                select(MapPoint)
                .where(
                    MapPoint.user_id == int(user_id),
                    MapPoint.collected == False
                )
            )
            
            return web.json_response([
                {
                    'id': p.id,
                    'lat': p.lat,
                    'lon': p.lon,
                    'address': p.address,
                    'reward': p.reward
                }
                for p in active_points.scalars()
            ])
            
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def main():
    """Запуск бота и веб-сервера"""
    await init_db()
    await start_web_app()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
