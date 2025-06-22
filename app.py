import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import sqlite3
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app, cors_allowed_origins="*")

# Database setup
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            nova_balance INTEGER DEFAULT 0,
            tix_balance INTEGER DEFAULT 0,
            avatar_color TEXT DEFAULT 'orange',
            location_allowed BOOLEAN DEFAULT 0,
            steps_today INTEGER DEFAULT 0,
            steps_week INTEGER DEFAULT 0,
            points_total INTEGER DEFAULT 0,
            last_active DATETIME
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            currency TEXT,
            type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lng REAL,
            address TEXT,
            expires DATETIME,
            reward INTEGER,
            collected_by INTEGER,
            FOREIGN KEY(collected_by) REFERENCES users(id)
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS ai_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            model TEXT,
            title TEXT,
            last_used DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS ai_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES ai_chats(id)
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price INTEGER,
            currency TEXT,
            tix_amount INTEGER,
            is_limited BOOLEAN,
            time_left TEXT,
            icon TEXT
        )
        ''')
        
        db.commit()

init_db()

# SocketIO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('authenticate')
def handle_authenticate(user_id):
    with get_db() as db:
        db.execute('UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        db.commit()

@socketio.on('request_location_sharing')
def handle_location_sharing(data):
    user_id = data['user_id']
    allowed = data['allowed']
    
    with get_db() as db:
        db.execute('UPDATE users SET location_allowed = ? WHERE id = ?', (allowed, user_id))
        db.commit()
        
        if allowed:
            # Send initial points to user
            points = db.execute('''
                SELECT * FROM points 
                WHERE collected_by IS NULL 
                AND expires > CURRENT_TIMESTAMP
            ''').fetchall()
            
            socketio.emit('initial_points', {
                'user_id': user_id,
                'points': [dict(p) for p in points]
            })

# Routes
@app.route('/')
def index():
    user_id = request.args.get('user_id')
    return render_template('index.html', user_id=user_id)

@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    with get_db() as db:
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        members = db.execute('''
            SELECT * FROM users 
            WHERE id != ? 
            ORDER BY nova_balance DESC 
            LIMIT 50
        ''', (user_id,)).fetchall()
        
        shop_items = db.execute('SELECT * FROM shop_items').fetchall()
        
        ai_chats = db.execute('''
            SELECT * FROM ai_chats 
            WHERE user_id = ? 
            ORDER BY last_used DESC
        ''', (user_id,)).fetchall()
        
        steps_ranking = db.execute('''
            SELECT id, first_name || COALESCE(' ' || last_name, '') as name, 
                   steps_today, steps_week 
            FROM users 
            ORDER BY steps_today DESC 
            LIMIT 20
        ''').fetchall()
        
        user_points = db.execute('''
            SELECT * FROM points 
            WHERE collected_by IS NULL 
            AND expires > CURRENT_TIMESTAMP
        ''').fetchall()
        
        collected_points = db.execute('''
            SELECT p.*, u.first_name, u.last_name 
            FROM points p
            JOIN users u ON p.collected_by = u.id
            WHERE p.collected_by = ?
            ORDER BY p.expires DESC
        ''', (user_id,)).fetchall()
        
        stats = {
            'steps': user['steps_today'],
            'points': user['points_total'],
            'nova_earned': db.execute('''
                SELECT COALESCE(SUM(amount), 0) 
                FROM transactions 
                WHERE user_id = ? AND currency = 'nova' AND type = 'earn'
            ''', (user_id,)).fetchone()[0],
            'ranking': db.execute('''
                SELECT COUNT(*) + 1 
                FROM users 
                WHERE steps_today > ?
            ''', (user['steps_today'],)).fetchone()[0]
        }
        
        return jsonify({
            'user': dict(user),
            'members': [dict(m) for m in members],
            'shopItems': [dict(i) for i in shop_items],
            'aiChats': [dict(c) for c in ai_chats],
            'stepsRanking': [dict(r) for r in steps_ranking],
            'userPoints': [dict(p) for p in user_points],
            'collectedPoints': [dict(p) for p in collected_points],
            'stats': stats
        })

@app.route('/api/chat/<int:chat_id>')
def get_chat_messages(chat_id):
    with get_db() as db:
        messages = db.execute('''
            SELECT * FROM ai_messages 
            WHERE chat_id = ? 
            ORDER BY timestamp
        ''', (chat_id,)).fetchall()
        
        return jsonify({
            'messages': [dict(m) for m in messages]
        })

@app.route('/api/report', methods=['POST'])
def handle_report():
    data = request.json
    user_id = data['user_id']
    link = data['link']
    
    # Here you would call your Coze API to check the report
    # For now, we'll simulate it with random success (60% chance)
    is_valid_report = random.random() < 0.6
    
    with get_db() as db:
        if is_valid_report:
            # Deduct 5000 NOVA and add 6000 NOVA (net +1000)
            db.execute('''
                UPDATE users 
                SET nova_balance = nova_balance + 1000 
                WHERE id = ?
            ''', (user_id,))
            
            db.execute('''
                INSERT INTO transactions (user_id, amount, currency, type)
                VALUES (?, 1000, 'nova', 'report_reward')
            ''', (user_id,))
            
            # Notify admins
            admins = os.getenv('ADMINS').split(',')
            for admin_id in admins:
                socketio.emit('admin_notification', {
                    'message': f'Новая жалоба от пользователя {user_id}: {link}',
                    'admin_id': int(admin_id)
                })
            
            db.commit()
            return jsonify({'success': True})
        else:
            # Deduct 5000 NOVA
            db.execute('''
                UPDATE users 
                SET nova_balance = nova_balance - 5000 
                WHERE id = ?
            ''', (user_id,))
            
            db.execute('''
                INSERT INTO transactions (user_id, amount, currency, type)
                VALUES (?, -5000, 'nova', 'report_cost')
            ''', (user_id,))
            
            db.commit()
            return jsonify({'success': False, 'message': 'Нарушений не обнаружено'})

@app.route('/api/send-gift', methods=['POST'])
def send_gift():
    data = request.json
    sender_id = data['sender_id']
    recipient_id = data['recipient_id']
    amount = data['amount']
    currency = data['currency']
    
    with get_db() as db:
        # Check if recipient exists and has started the bot
        recipient = db.execute('SELECT 1 FROM users WHERE id = ?', (recipient_id,)).fetchone()
        if not recipient:
            return jsonify({'success': False, 'message': 'Получатель не найден'})
        
        # Check sender balance
        sender_balance = db.execute(f'''
            SELECT {currency}_balance FROM users WHERE id = ?
        ''', (sender_id,)).fetchone()[0]
        
        if sender_balance < amount:
            return jsonify({'success': False, 'message': 'Недостаточно средств'})
        
        # Perform transaction
        db.execute(f'''
            UPDATE users 
            SET {currency}_balance = {currency}_balance - ? 
            WHERE id = ?
        ''', (amount, sender_id))
        
        db.execute(f'''
            UPDATE users 
            SET {currency}_balance = {currency}_balance + ? 
            WHERE id = ?
        ''', (amount, recipient_id))
        
        db.execute('''
            INSERT INTO transactions (user_id, amount, currency, type)
            VALUES (?, ?, ?, 'gift_sent')
        ''', (sender_id, -amount, currency))
        
        db.execute('''
            INSERT INTO transactions (user_id, amount, currency, type)
            VALUES (?, ?, ?, 'gift_received')
        ''', (recipient_id, amount, currency))
        
        db.commit()
        
        # Notify recipient
        sender = db.execute('''
            SELECT first_name, last_name FROM users WHERE id = ?
        ''', (sender_id,)).fetchone()
        
        sender_name = f"{sender['first_name']} {sender['last_name']}" if sender['last_name'] else sender['first_name']
        
        socketio.emit('gift_received', {
            'user_id': recipient_id,
            'message': f'{sender_name} отправил вам {amount}{"❇️" if currency == "nova" else "✴️"}'
        })
        
        return jsonify({'success': True})

@app.route('/api/exchange', methods=['POST'])
def exchange_currency():
    data = request.json
    user_id = data['user_id']
    from_currency = data['from']
    to_currency = data['to']
    amount = data['amount']
    
    with get_db() as db:
        # Check user balance
        user_balance = db.execute(f'''
            SELECT {from_currency}_balance FROM users WHERE id = ?
        ''', (user_id,)).fetchone()[0]
        
        if user_balance < amount:
            return jsonify({'success': False, 'message': 'Недостаточно средств'})
        
        # Calculate exchange
        if from_currency == 'nova':
            exchanged_amount = amount / 10000
        else:
            exchanged_amount = amount * 10000
        
        # Perform exchange
        db.execute(f'''
            UPDATE users 
            SET {from_currency}_balance = {from_currency}_balance - ? 
            WHERE id = ?
        ''', (amount, user_id))
        
        db.execute(f'''
            UPDATE users 
            SET {to_currency}_balance = {to_currency}_balance + ? 
            WHERE id = ?
        ''', (exchanged_amount, user_id))
        
        db.execute('''
            INSERT INTO transactions (user_id, amount, currency, type)
            VALUES (?, ?, ?, 'exchange_out')
        ''', (user_id, -amount, from_currency))
        
        db.execute('''
            INSERT INTO transactions (user_id, amount, currency, type)
            VALUES (?, ?, ?, 'exchange_in')
        ''', (user_id, exchanged_amount, to_currency))
        
        db.commit()
        
        # Update client balance via WebSocket
        user = db.execute('''
            SELECT nova_balance, tix_balance FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        socketio.emit('balance_update', {
            'user_id': user_id,
            'nova_balance': user['nova_balance'],
            'tix_balance': user['tix_balance']
        })
        
        return jsonify({'success': True, 'exchanged_amount': exchanged_amount})

@app.route('/api/buy-item', methods=['POST'])
def buy_item():
    data = request.json
    user_id = data['user_id']
    item_id = data['item_id']
    
    with get_db() as db:
        # Get item info
        item = db.execute('''
            SELECT * FROM shop_items WHERE id = ?
        ''', (item_id,)).fetchone()
        
        if not item:
            return jsonify({'success': False, 'message': 'Товар не найден'})
        
        # Check user balance
        user_balance = db.execute('''
            SELECT nova_balance FROM users WHERE id = ?
        ''', (user_id,)).fetchone()[0]
        
        if user_balance < item['price']:
            return jsonify({'success': False, 'message': 'Недостаточно NOVA'})
        
        # Process purchase
        db.execute('''
            UPDATE users 
            SET nova_balance = nova_balance - ? 
            WHERE id = ?
        ''', (item['price'], user_id))
        
        if item['currency'] == 'tix':
            db.execute('''
                UPDATE users 
                SET tix_balance = tix_balance + ? 
                WHERE id = ?
            ''', (item['tix_amount'], user_id))
        
        db.execute('''
            INSERT INTO transactions (user_id, amount, currency, type)
            VALUES (?, ?, 'nova', 'shop_purchase')
        ''', (user_id, -item['price']))
        
        if item['currency'] == 'tix':
            db.execute('''
                INSERT INTO transactions (user_id, amount, currency, type)
                VALUES (?, ?, 'tix', 'shop_purchase')
            ''', (user_id, item['tix_amount']))
        
        # Handle special items
        if item['name'] == 'Тишина!':
            # Implement silence logic for the group
            pass
        
        db.commit()
        
        # Update client balance
        user = db.execute('''
            SELECT nova_balance, tix_balance FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        socketio.emit('balance_update', {
            'user_id': user_id,
            'nova_balance': user['nova_balance'],
            'tix_balance': user['tix_balance']
        })
        
        return jsonify({'success': True})

@app.route('/api/collect-point', methods=['POST'])
def collect_point():
    data = request.json
    user_id = data['user_id']
    point_id = data['point_id']
    
    with get_db() as db:
        # Check if point exists and not collected
        point = db.execute('''
            SELECT * FROM points 
            WHERE id = ? AND collected_by IS NULL AND expires > CURRENT_TIMESTAMP
        ''', (point_id,)).fetchone()
        
        if not point:
            return jsonify({'success': False, 'message': 'Точка не найдена или уже собрана'})
        
        # Calculate reward based on time, weather, etc. (simplified)
        base_reward = random.randint(7000, 20000)
        
        # Update point and user balance
        db.execute('''
            UPDATE points 
            SET collected_by = ?, reward = ?
            WHERE id = ?
        ''', (user_id, base_reward, point_id))
        
        db.execute('''
            UPDATE users 
            SET nova_balance = nova_balance + ?, points_total = points_total + 1
            WHERE id = ?
        ''', (base_reward, user_id))
        
        db.execute('''
            INSERT INTO transactions (user_id, amount, currency, type)
            VALUES (?, ?, 'nova', 'point_collected')
        ''', (user_id, base_reward))
        
        db.commit()
        
        # Update client balance
        user = db.execute('''
            SELECT nova_balance FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        socketio.emit('balance_update', {
            'user_id': user_id,
            'nova_balance': user['nova_balance']
        })
        
        # Notify about collected point
        socketio.emit('point_collected', {
            'user_id': user_id,
            'point_id': point_id
        })
        
        return jsonify({'success': True, 'reward': base_reward})

# Background task to generate new points
def generate_points():
    with app.app_context():
        with get_db() as db:
            # Generate 2-7 new points per day
            num_points = random.randint(2, 7)
            
            for _ in range(num_points):
                # Generate random point in parks/alleys (simplified)
                lat = 55.75 + random.uniform(-0.05, 0.05)
                lng = 37.61 + random.uniform(-0.05, 0.05)
                address = f"Парк {random.choice(['Горького', 'Сокольники', 'Зарядье', 'Коломенское'])}"
                expires = datetime.now() + timedelta(hours=24)
                reward = random.randint(7000, 20000)
                
                db.execute('''
                    INSERT INTO points (lat, lng, address, expires, reward)
                    VALUES (?, ?, ?, ?, ?)
                ''', (lat, lng, address, expires, reward))
                
                db.commit()
                
                # Notify users who have location sharing enabled
                users = db.execute('''
                    SELECT id FROM users WHERE location_allowed = 1
                ''').fetchall()
                
                for user in users:
                    socketio.emit('new_point', {
                        'user_id': user['id'],
                        'point': {
                            'id': db.execute('SELECT last_insert_rowid()').fetchone()[0],
                            'lat': lat,
                            'lng': lng,
                            'address': address,
                            'expires': expires.isoformat(),
                            'reward': reward
                        }
                    })

if __name__ == '__main__':
    # Start background tasks
    from threading import Thread
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_points, 'interval', hours=24)
    scheduler.start()
    
    socketio.run(app, host='0.0.0.0', port=5000)
