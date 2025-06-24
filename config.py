import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    WEBAPP_URL = os.getenv('WEBAPP_URL')
    DATABASE_URL = os.getenv('DATABASE_URL')
    GROUP_ID = int(os.getenv('GROUP_ID'))
    OWNER = int(os.getenv('OWNER'))
    ADMINS = list(map(int, os.getenv('ADMINS').split(',')))
    SECRET_KEY = os.getenv('SECRET_KEY')
    FUSIONBRAIN_API_KEY = os.getenv('FUSIONBRAIN_API_KEY')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    COZE_API_KEY = os.getenv('COZE_API_KEY')
    GROUP_IMG = os.getenv('GROUP_IMG', 'https://example.com/group_img.jpg')
    
    # Onboarding images
    ONBOARDING_IMAGES = [
        os.getenv('ONBOARDING_1'),
        os.getenv('ONBOARDING_2'),
        os.getenv('ONBOARDING_3'),
        os.getenv('ONBOARDING_4')
    ]
    
    # Currency rates
    NOVA_RATE = 10000  # 10000❇️ = 1✴️
    CURRENCY_RATES = {
        'RUB': 29.99,  # 10000❇️ = 29.99₽
        'BYN': 1.0,    # TODO: Add actual rate
        'UAH': 12.0    # TODO: Add actual rate
    }
    
    # Premium subscription prices
    PREMIUM_PRICES = {
        '1': {'RUB': 149, 'BYN': 5.0, 'UAH': 60.0},
        '3': {'RUB': 399, 'BYN': 13.0, 'UAH': 160.0},
        '6': {'RUB': 699, 'BYN': 23.0, 'UAH': 280.0},
        '12': {'RUB': 1199, 'BYN': 40.0, 'UAH': 480.0}
    }
