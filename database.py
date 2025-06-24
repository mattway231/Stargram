from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    telegram_id = db.Column(db.Integer, unique=True, nullable=False)
    nova_coins = db.Column(db.Integer, default=0)
    tix_coins = db.Column(db.Integer, default=0)
    premium = db.Column(db.Boolean, default=False)
    premium_until = db.Column(db.DateTime, nullable=True)
    hide_balance = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(2), default='ru')
    share_location = db.Column(db.Boolean, default=False)
    visible_to = db.Column(db.String, default='all')  # 'all', 'friends', 'none'
    last_active = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # 'NOVA' or 'TIX'
    transaction_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class CollectedPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    collected_at = db.Column(db.DateTime, server_default=db.func.now())

class ActivePoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    min_amount = db.Column(db.Integer, nullable=False)
    max_amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    text = db.Column(db.String(1000))

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, nullable=False)
    approved = db.Column(db.Boolean, nullable=False)
    amount_spent = db.Column(db.Integer, nullable=False)
    amount_returned = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class GPTConversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), default='New Chat')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class GPTMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('gpt_conversation.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
