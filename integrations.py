import httpx
import random
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from config import Config

class AIService:
    @staticmethod
    async def check_violation(text: str) -> bool:
        """Проверка сообщения на нарушения через Coze API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.coze.com/v1/moderate",
                headers={"Authorization": f"Bearer {Config.COOZE_API_KEY}"},
                json={"text": text}
            )
            return response.json().get("result") == "approve"
    
    @staticmethod
    async def generate_text(prompt: str) -> str:
        """Генерация текста через OpenRouter"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                    "HTTP-Referer": Config.WEBAPP_URL
                },
                json={
                    "model": "google/gemma-7b-it:free",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            return response.json()["choices"][0]["message"]["content"]
    
    @staticmethod
    async def generate_image(prompt: str) -> str:
        """Генерация изображения через FusionBrain"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.fusionbrain.ai/v1/text2image/run",
                headers={"Authorization": f"Bearer {Config.FUSIONBRAIN_API_KEY}"},
                json={"text": prompt}
            )
            return response.json()["images"][0]

class MapService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="stargram", timeout=10)

    async def generate_points(self, user_id: int, lat: float, lon: float) -> list:
        """Генерация случайных точек в парках/аллеях"""
        async with AsyncSessionLocal() as session:
            # Получаем город пользователя
            user = await session.get(User, user_id)
            if not user.city:
                location = await self.geolocator.reverse((lat, lon))
                user.city = location.raw.get('address', {}).get('city', 'Unknown')
                user.country = location.raw.get('address', {}).get('country', 'Unknown')
                await session.commit()

            # Запрос к Overpass API для поиска парков
            query = f"""
            [out:json];
            (
              way["leisure"="park"](around:5000,{lat},{lon});
              way["landuse"="recreation_ground"](around:5000,{lat},{lon});
              way["leisure"="garden"](around:5000,{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.get(Config.OVERPASS_URL, params={'data': query})
                data = response.json()
                
                points = []
                for element in data.get('elements', []):
                    if element['type'] == 'way':
                        # Генерация случайной точки внутри полигона
                        point = self._random_point_in_polygon(element['nodes'])
                        address = await self._reverse_geocode(point)
                        
                        points.append(MapPoint(
                            lat=point[0],
                            lon=point[1],
                            address=address,
                            reward=random.randint(Config.MIN_POINT_REWARD, Config.MAX_POINT_REWARD),
                            user_id=user_id
                        ))
                
                # Сохраняем точки в БД
                session.add_all(points)
                await session.commit()
                
                return points

    def _random_point_in_polygon(self, polygon):
        """Генерация случайной точки внутри полигона"""
        min_lat = min(p[0] for p in polygon)
        max_lat = max(p[0] for p in polygon)
        min_lon = min(p[1] for p in polygon)
        max_lon = max(p[1] for p in polygon)
        
        while True:
            lat = random.uniform(min_lat, max_lat)
            lon = random.uniform(min_lon, max_lon)
            
            if self._point_in_polygon((lat, lon), polygon):
                return (lat, lon)

    def _point_in_polygon(self, point, polygon):
        """Проверка точки внутри полигона"""
        x, y = point
        inside = False
        n = len(polygon)
        
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

    async def _reverse_geocode(self, point):
        """Определение адреса по координатам"""
        try:
            location = await self.geolocator.reverse(point)
            return location.address
        except:
            return f"{point[0]:.4f}, {point[1]:.4f}"
