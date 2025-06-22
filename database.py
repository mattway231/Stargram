from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey, Float, Text
from datetime import datetime
from config import Config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    nova = Column(Integer, default=0)
    tix = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    is_owner = Column(Boolean, default=False)
    location_access = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    city = Column(String(100))
    country = Column(String(100))

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    amount = Column(Integer)
    currency = Column(String(10))
    type = Column(String(50))  # exchange, gift, reward, purchase
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    message_id = Column(BigInteger)
    message_text = Column(Text)
    status = Column(String(20))  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

class MapPoint(Base):
    __tablename__ = 'map_points'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lat = Column(Float)
    lon = Column(Float)
    address = Column(Text)
    reward = Column(Integer)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    collected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    collected_at = Column(DateTime)

engine = create_async_engine(Config.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
