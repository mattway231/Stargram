import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TOKEN = os.getenv("TOKEN")
    GROUP_ID = int(os.getenv("GROUP_ID", "-1001234567890"))
    ADMINS = list(map(int, os.getenv("ADMINS", "").split(','))) if os.getenv("ADMINS") else []
    OWNER = int(os.getenv("OWNER", "0"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    SECRET_KEY = os.getenv("SECRET_KEY", "secret-key")
    
    # Web
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://yourdomain.com/webhook")
    
    # AI APIs
    COZE_API_KEY = os.getenv("COZE_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
    
    # Map Settings
    OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    POINT_RADIUS_M = 50  # Радиус сбора точки
    MIN_POINTS = 2       # Минимум точек в день
    MAX_POINTS = 7       # Максимум точек в день
    
    # Economy
    NOVA_TO_TIX_RATE = 10000
    REPORT_COST = 5000   # Стоимость жалобы
    REPORT_REWARD = 6000 # Награда за подтверждённую жалобу
    MIN_POINT_REWARD = 7000
    MAX_POINT_REWARD = 20000
    DAILY_MESSAGE_REWARD = 100  # NOVA за сообщение
    DAILY_MESSAGE_LIMIT = 300   # Максимум сообщений для награды
