from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from config import Config
import database as db
import integrations as intg
from datetime import datetime, timedelta
import random
import pytz
import asyncio

# Initialize database
db.init_app(Config)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is in group
    try:
        member = await context.bot.get_chat_member(Config.GROUP_ID, user.id)
        if member.status in ['left', 'kicked']:
            await update.message.reply_text("Вы должны быть участником группы, чтобы использовать этого бота.")
            return
    except Exception as e:
        print(f"Error checking group membership: {e}")
        await update.message.reply_text("Произошла ошибка при проверке вашего членства в группе.")
        return
    
    # Register user if not exists
    existing_user = db.User.query.filter_by(telegram_id=user.id).first()
    if not existing_user:
        new_user = db.User(
            username=user.username or user.full_name,
            telegram_id=user.id,
            created_at=datetime.now()
        )
        db.session.add(new_user)
        db.session.commit()
    
    # Send web app button
    keyboard = [[InlineKeyboardButton("Открыть Stargram", web_app=Config.WEBAPP_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Добро пожаловать в Stargram! Нажмите кнопку ниже, чтобы открыть веб-приложение.",
        reply_markup=reply_markup
    )

async def balance(update: Update, context: CallbackContext):
    user = update.effective_user
    target_user = user
    
    # Check if replying to someone or mentioned username
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        target_user = update.message.reply_to_message.from_user
    elif len(context.args) > 0 and context.args[0].startswith('@'):
        username = context.args[0][1:]
        target_user = db.User.query.filter_by(username=username).first()
        if not target_user:
            await update.message.reply_text("Пользователь не найден.")
            return
        target_id = target_user.telegram_id
    else:
        target_id = user.id
    
    # Get user from DB
    db_user = db.User.query.filter_by(telegram_id=target_id).first()
    if not db_user:
        await update.message.reply_text("Пользователь не зарегистрирован в системе.")
        return
    
    # Check if balance is hidden
    if db_user.hide_balance and db_user.telegram_id != user.id and user.id not in Config.ADMINS + [Config.OWNER]:
        await update.message.reply_text("Этот пользователь скрыл свой баланс.")
        return
    
    await update.message.reply_text(
        f"Баланс {target_user.username}:\n"
        f"❇️ Новакоины: {db_user.nova_coins}\n"
        f"✴️ Тиксы: {db_user.tix_coins}"
    )

async def gift(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if in group
    if chat.id != Config.GROUP_ID:
        await update.message.reply_text("Эта команда работает только в группе.")
        return
    
    # Check if replying to someone or mentioned username
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        target_user = update.message.reply_to_message.from_user
    elif len(context.args) > 1 and context.args[0].startswith('@'):
        username = context.args[0][1:]
        target_user = db.User.query.filter_by(username=username).first()
        if not target_user:
            await update.message.reply_text("Пользователь не найден.")
            return
        target_id = target_user.telegram_id
        amount_str = context.args[1]
    else:
        await update.message.reply_text("Используйте команду в ответ на сообщение или укажите @username и сумму.")
        return
    
    # Parse amount
    try:
        if update.message.reply_to_message:
            amount_str = context.args[0]
        
        amount = int(''.join(filter(str.isdigit, amount_str)))
        currency = '❇️' if '❇️' in amount_str else '✴️'
    except (IndexError, ValueError):
        await update.message.reply_text("Укажите сумму и валюту (например, 1000❇️ или 5✴️)")
        return
    
    # Check sender balance
    sender = db.User.query.filter_by(telegram_id=user.id).first()
    if not sender:
        await update.message.reply_text("Вы не зарегистрированы в системе.")
        return
    
    if currency == '❇️' and sender.nova_coins < amount:
        await update.message.reply_text("У вас недостаточно Новакоинов для перевода.")
        return
    elif currency == '✴️' and sender.tix_coins < amount:
        await update.message.reply_text("У вас недостаточно Тиксов для перевода.")
        return
    
    # Update balances
    receiver = db.User.query.filter_by(telegram_id=target_id).first()
    if not receiver:
        await update.message.reply_text("Получатель не зарегистрирован в системе.")
        return
    
    if currency == '❇️':
        sender.nova_coins -= amount
        receiver.nova_coins += amount
        transaction_type = "Перевод пользователю NOVA"
    else:
        sender.tix_coins -= amount
        receiver.tix_coins += amount
        transaction_type = "Перевод пользователю TIX"
    
    # Record transaction
    sender_transaction = db.Transaction(
        user_id=sender.id,
        amount=-amount,
        currency=currency,
        transaction_type=transaction_type,
        details=f"Перевод {target_user.username}"
    )
    
    receiver_transaction = db.Transaction(
        user_id=receiver.id,
        amount=amount,
        currency=currency,
        transaction_type=transaction_type,
        details=f"Перевод от {user.username}"
    )
    
    db.session.add(sender_transaction)
    db.session.add(receiver_transaction)
    db.session.commit()
    
    # Notify group
    await context.bot.send_message(
        chat_id=Config.GROUP_ID,
        text=f"🎁 {user.username} подарил {target_user.username} {amount}{currency}"
    )

async def complaint(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if in group
    if chat.id != Config.GROUP_ID:
        await update.message.reply_text("Эта команда работает только в группе.")
        return
    
    # Check if replying to a message
    if not update.message.reply_to_message:
        await update.message.reply_text("Используйте команду в ответ на сообщение, на которое хотите пожаловаться.")
        return
    
    target_message = update.message.reply_to_message
    target_user = target_message.from_user
    
    # Check if complaining about self
    if user.id == target_user.id:
        await update.message.reply_text("Вы не можете пожаловаться на собственное сообщение.")
        return
    
    # Check if user has premium for free complaints
    db_user = db.User.query.filter_by(telegram_id=user.id).first()
    if not db_user:
        await update.message.reply_text("Вы не зарегистрированы в системе.")
        return
    
    # Charge 5000 NOVA (unless premium)
    if not db_user.premium:
        if db_user.nova_coins < 5000:
            await update.message.reply_text("Для подачи жалобы требуется 5000❇️. У вас недостаточно средств.")
            return
        
        db_user.nova_coins -= 5000
        transaction = db.Transaction(
            user_id=db_user.id,
            amount=-5000,
            currency='NOVA',
            transaction_type="Жалоба",
            details=f"Жалоба на сообщение {target_message.message_id}"
        )
        db.session.add(transaction)
        db.session.commit()
    
    # Get message text
    message_text = target_message.text or target_message.caption or ""
    
    # Check with Coze API
    coze = intg.CozeAPI()
    result = coze.check_complaint(user.id, message_text)
    
    if result == "approve":
        # Return 120% if approved
        return_amount = 6000 if not db_user.premium else 0
        if return_amount > 0:
            db_user.nova_coins += return_amount
            return_transaction = db.Transaction(
                user_id=db_user.id,
                amount=return_amount,
                currency='NOVA',
                transaction_type="Возврат за жалобу",
                details=f"Жалоба одобрена на сообщение {target_message.message_id}"
            )
            db.session.add(return_transaction)
        
        # Record complaint
        complaint = db.Complaint(
            from_user_id=db_user.id,
            to_user_id=target_user.id,
            message_id=target_message.message_id,
            approved=True,
            amount_spent=5000,
            amount_returned=return_amount
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Notify admins
        for admin_id in Config.ADMINS + [Config.OWNER]:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 Жалоба от {user.username} на {target_user.username}:\n"
                         f"Сообщение: {message_text[:200]}...\n"
                         f"Статус: ОДОБРЕНО\n"
                         f"Ссылка: https://t.me/c/{str(Config.GROUP_ID)[4:]}/{target_message.message_id}"
                )
            except Exception as e:
                print(f"Error notifying admin {admin_id}: {e}")
        
        await update.message.reply_text(
            f"Ваша жалоба одобрена. {'Вам возвращено 6000❇️ (120%).' if not db_user.premium else 'Как премиум пользователь, вы не были заряжены.'}"
        )
    else:
        # Record rejected complaint
        complaint = db.Complaint(
            from_user_id=db_user.id,
            to_user_id=target_user.id,
            message_id=target_message.message_id,
            approved=False,
            amount_spent=5000,
            amount_returned=0
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Notify admins
        for admin_id in Config.ADMINS + [Config.OWNER]:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 Жалоба от {user.username} на {target_user.username}:\n"
                         f"Сообщение: {message_text[:200]}...\n"
                         f"Статус: ОТКЛОНЕНО\n"
                         f"Ссылка: https://t.me/c/{str(Config.GROUP_ID)[4:]}/{target_message.message_id}"
                )
            except Exception as e:
                print(f"Error notifying admin {admin_id}: {e}")
        
        await update.message.reply_text(
            f"Жалоба отклонена. {'Вы потратили 5000❇️.' if not db_user.premium else 'Как премиум пользователь, вы не были заряжены.'}"
        )

async def daily_rewards(context: CallbackContext):
    # Get yesterday's date
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(tz)
    yesterday = now - timedelta(days=1)
    start_of_day = tz.localize(datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0))
    end_of_day = tz.localize(datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59))
    
    # Get all messages from yesterday
    messages = db.ChatMessage.query.filter(
        db.ChatMessage.date >= start_of_day,
        db.ChatMessage.date <= end_of_day
    ).all()
    
    # Count messages per user
    user_counts = {}
    for msg in messages:
        if msg.user_id not in user_counts:
            user_counts[msg.user_id] = 0
        user_counts[msg.user_id] += 1
    
    # Prepare message
    if not user_counts:
        message = "Вчера никто не писал в чат. Награды не будут распределены."
        await context.bot.send_message(chat_id=Config.GROUP_ID, text=message)
        return
    
    # Sort by message count
    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
    
    message_lines = ["🏆 Топ активности за вчерашний день:"]
    for user_id, count in sorted_users:
        user = db.User.query.get(user_id)
        if not user:
            continue
        
        # Calculate reward (150 NOVA per message for premium, 100 for regular)
        reward = count * (150 if user.premium else 100)
        user.nova_coins += reward
        
        # Record transaction
        transaction = db.Transaction(
            user_id=user_id,
            amount=reward,
            currency='NOVA',
            transaction_type="Активность в чате",
            details=f"{count} сообщений"
        )
        db.session.add(transaction)
        
        message_lines.append(f"{user.username}: {count} сообщений → +{reward}❇️")
    
    db.session.commit()
    
    # Send summary
    await context.bot.send_message(
        chat_id=Config.GROUP_ID,
        text="\n".join(message_lines)
    )

async def admin_actions(context: CallbackContext):
    # Get actions from last 24 hours
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    
    transactions = db.Transaction.query.filter(
        db.Transaction.created_at >= twenty_four_hours_ago
    ).order_by(db.Transaction.created_at.desc()).all()
    
    if not transactions:
        return
    
    message_lines = ["⏰ Последние действия пользователей за 24 часа:"]
    
    for tx in transactions:
        user = db.User.query.get(tx.user_id)
        if not user:
            continue
        
        amount_str = f"+{tx.amount}" if tx.amount > 0 else str(tx.amount)
        currency = '❇️' if tx.currency == 'NOVA' else '✴️'
        
        time_str = tx.created_at.strftime("%H:%M")
        message_lines.append(
            f"{time_str}: {user.username}, {tx.transaction_type} ({amount_str}{currency})"
        )
    
    # Send to all admins
    for admin_id in Config.ADMINS + [Config.OWNER]:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text="\n".join(message_lines[:50])  # Limit to 50 lines to avoid message too long
            )
        except Exception as e:
            print(f"Error sending admin actions to {admin_id}: {e}")

async def notify_all(update: Update, context: CallbackContext):
    user = update.effective_user
    
    # Check if owner
    if user.id != Config.OWNER:
        await update.message.reply_text("Эта команда только для владельца.")
        return
    
    # Get message text
    if not context.args:
        await update.message.reply_text("Укажите сообщение для отправки (например: /notify_all Привет всем!)")
        return
    
    message = " ".join(context.args)
    
    # Get all users
    users = db.User.query.all()
    
    await update.message.reply_text(f"Начинаю рассылку сообщения для {len(users)} пользователей...")
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=f"📢 Уведомление от администрации:\n\n{message}"
            )
            success += 1
        except Exception as e:
            print(f"Error notifying user {user.telegram_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)  # Rate limiting
    
    await update.message.reply_text(
        f"Рассылка завершена:\n"
        f"Успешно: {success}\n"
        f"Не удалось: {failed}"
    )

async def add_coins(update: Update, context: CallbackContext):
    user = update.effective_user
    
    # Check if owner
    if user.id != Config.OWNER:
        await update.message.reply_text("Эта команда только для владельца.")
        return
    
    # Parse arguments: /add_coins @username 1000 NOVA
    if len(context.args) < 3:
        await update.message.reply_text("Используйте: /add_coins @username количество валюта (NOVA/TIX)")
        return
    
    username = context.args[0]
    if not username.startswith('@'):
        await update.message.reply_text("Укажите @username пользователя.")
        return
    
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Укажите корректное количество.")
        return
    
    currency = context.args[2].upper()
    if currency not in ['NOVA', 'TIX']:
        await update.message.reply_text("Валюта должна быть NOVA или TIX.")
        return
    
    # Find user
    target_user = db.User.query.filter_by(username=username[1:]).first()
    if not target_user:
        await update.message.reply_text("Пользователь не найден.")
        return
    
    # Add coins
    if currency == 'NOVA':
        target_user.nova_coins += amount
    else:
        target_user.tix_coins += amount
    
    # Record transaction
    transaction = db.Transaction(
        user_id=target_user.id,
        amount=amount,
        currency=currency,
        transaction_type="Админ пополнение",
        details=f"Добавлено администратором"
    )
    db.session.add(transaction)
    db.session.commit()
    
    await update.message.reply_text(
        f"Баланс {username} обновлен:\n"
        f"{currency}: {amount:+}"
    )

async def add_premium(update: Update, context: CallbackContext):
    user = update.effective_user
    
    # Check if owner
    if user.id != Config.OWNER:
        await update.message.reply_text("Эта команда только для владельца.")
        return
    
    # Parse arguments: /add_premium @username 30
    if len(context.args) < 2:
        await update.message.reply_text("Используйте: /add_premium @username количество_дней")
        return
    
    username = context.args[0]
    if not username.startswith('@'):
        await update.message.reply_text("Укажите @username пользователя.")
        return
    
    try:
        days = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Укажите корректное количество дней.")
        return
    
    # Find user
    target_user = db.User.query.filter_by(username=username[1:]).first()
    if not target_user:
        await update.message.reply_text("Пользователь не найден.")
        return
    
    # Calculate premium until date
    premium_until = datetime.now() + timedelta(days=days)
    
    # Set premium
    target_user.premium = True
    target_user.premium_until = premium_until
    
    # Record transaction
    transaction = db.Transaction(
        user_id=target_user.id,
        amount=0,
        currency='NOVA',
        transaction_type="Премиум подписка",
        details=f"Добавлено администратором на {days} дней"
    )
    db.session.add(transaction)
    db.session.commit()
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_user.telegram_id,
            text=f"🎉 Вам выдана премиум подписка Stargram Plus на {days} дней!"
        )
    except Exception as e:
        print(f"Error notifying user {target_user.telegram_id}: {e}")
    
    await update.message.reply_text(
        f"Пользователю {username} выдана премиум подписка на {days} дней."
    )

async def generate_points(context: CallbackContext):
    # Get all users who share location
    users = db.User.query.filter_by(share_location=True).all()
    
    for user in users:
        # Get last known location (simplified - in real app would get from DB)
        # For demo, we'll use a random location near a city center
        lat = 55.7558 + random.uniform(-0.2, 0.2)
        lng = 37.6173 + random.uniform(-0.2, 0.2)
        
        # Find parks nearby
        osm = intg.OpenStreetMap()
        parks = osm.get_parks_nearby(lat, lng, radius=10000)  # 10km radius
        
        if not parks:
            continue
        
        # Generate 3-7 points (5-10 for premium)
        num_points = random.randint(5, 10) if user.premium else random.randint(3, 7)
        points_added = 0
        
        for _ in range(num_points):
            # Select random park
            park = random.choice(parks)
            
            # Generate random point in park (simplified)
            point_lat = park['lat'] + random.uniform(-0.005, 0.005)
            point_lng = park['lng'] + random.uniform(-0.005, 0.005)
            
            # Get address
            address = osm.get_address(point_lat, point_lng)
            if not address:
                address = park['name'] or "Неизвестное место"
            
            # Calculate distance from user
            distance = ((point_lat - lat)**2 + (point_lng - lng)**2)**0.5 * 111  # approx km
            
            # Determine reward amount based on distance
            if distance < 1:  # within 1km
                min_reward = 10000
                max_reward = 25000
            else:
                min_reward = 20000
                max_reward = 35000
            
            # Add 20% bonus for premium
            if user.premium:
                min_reward = int(min_reward * 1.2)
                max_reward = int(max_reward * 1.2)
            
            reward = random.randint(min_reward, max_reward)
            
            # Create point
            point = db.ActivePoint(
                latitude=point_lat,
                longitude=point_lng,
                address=address,
                min_amount=min_reward,
                max_amount=max_reward
            )
            db.session.add(point)
            points_added += 1
        
        if points_added > 0:
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"📍 На карте появилось {points_added} новых точек для сбора! Откройте Stargram, чтобы найти их."
                )
            except Exception as e:
                print(f"Error notifying user {user.telegram_id}: {e}")
    
    db.session.commit()

def setup_handlers(application):
    # Commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('balance', balance))
    application.add_handler(CommandHandler('gift', gift))
    application.add_handler(CommandHandler('complaint', complaint))
    application.add_handler(CommandHandler('notify_all', notify_all))
    application.add_handler(CommandHandler('add_coins', add_coins))
    application.add_handler(CommandHandler('add_premium', add_premium))
    
    # Scheduled jobs
    job_queue = application.job_queue
    
    # Daily rewards at 23:59 Moscow time
    job_queue.run_daily(daily_rewards, time=datetime.time(20, 59, 0, tzinfo=pytz.timezone('Europe/Moscow')))
    
    # Admin actions summary every 24 hours
    job_queue.run_repeating(admin_actions, interval=86400, first=10)
    
    # Generate points daily at midnight
    job_queue.run_daily(generate_points, time=datetime.time(21, 0, 0, tzinfo=pytz.timezone('Europe/Moscow')))

def main():
    application = Application.builder().token(Config.TOKEN).build()
    
    # Set bot commands
    commands = [
        BotCommand('start', 'Запустить бота'),
        BotCommand('balance', 'Проверить баланс'),
        BotCommand('gift', 'Подарить валюту'),
        BotCommand('complaint', 'Пожаловаться на сообщение')
    ]
    application.bot.set_my_commands(commands)
    
    # Setup handlers
    setup_handlers(application)
    
    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()
