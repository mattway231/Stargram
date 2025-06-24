import requests
import json
import time
from config import Config

class FusionBrainAPI:
    def __init__(self):
        self.URL = "https://api-key.fusionbrain.ai/"
        self.AUTH_HEADERS = {
            'X-Key': f'Key {Config.FUSIONBRAIN_API_KEY}',
            'X-Secret': f'Secret {Config.FUSIONBRAIN_API_KEY}',
        }
        
    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']
    
    def generate(self, prompt, pipeline, style="DEFAULT", width=1024, height=1024, negative_prompt="", images=1):
        params = {
            "type": "GENERATE",
            "style": style,
            "numImages": images,
            "width": width,
            "height": height,
            "negativePromptDecoder": negative_prompt,
            "generateParams": {
                "query": prompt
            }
        }
        
        data = {
            'pipeline_id': (None, pipeline),
            'params': (None, json.dumps(params), 'application/json')
        }
        
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', 
                               headers=self.AUTH_HEADERS, 
                               files=data)
        data = response.json()
        return data['uuid']
    
    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/pipeline/status/' + request_id, 
                                  headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            attempts -= 1
            time.sleep(delay)
        return None

class OpenRouterAPI:
    def __init__(self):
        self.API_URL = "https://openrouter.ai/api/v1/chat/completions"
        self.HEADERS = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "HTTP-Referer": Config.WEBAPP_URL,
            "X-Title": "Stargram",
            "Content-Type": "application/json"
        }
    
    def chat_completion(self, messages, model="deepseek/deepseek-v3-base:free", temperature=0.7, max_tokens=2000):
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(self.API_URL, headers=self.HEADERS, json=data)
        return response.json()

class CozeAPI:
    def __init__(self):
        self.API_URL = "https://api.coze.com/v3/chat"
        self.HEADERS = {
            "Authorization": f"Bearer {Config.COEZ_API_KEY}",
            "Content-Type": "application/json"
        }
        self.BOT_ID = "7518741050719633464"
    
    def check_complaint(self, user_id, message_text):
        data = {
            "bot_id": self.BOT_ID,
            "user_id": str(user_id),
            "stream": False,
            "additional_messages": [
                {
                    "role": "user",
                    "content": message_text,
                    "content_type": "text"
                }
            ]
        }
        
        response = requests.post(self.API_URL, headers=self.HEADERS, json=data)
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            return "approve" if "approve" in content.lower() else "reject"
        return "reject"

class MapService:
    @staticmethod
    def get_address(lat, lng):
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
        response = requests.get(url)
        data = response.json()
        
        if 'address' in data:
            address = data.get('display_name', '')
            return address
        return ""

    @staticmethod
    def get_parks_nearby(lat, lng, radius=5000):
        url = f"https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          way["leisure"="park"](around:{radius},{lat},{lng});
          relation["leisure"="park"](around:{radius},{lat},{lng});
        );
        out center;
        """
        response = requests.get(url, params={'data': query})
        data = response.json()
        
        parks = []
        for element in data.get('elements', []):
            if 'center' in element:
                parks.append({
                    'lat': element['center']['lat'],
                    'lng': element['center']['lon'],
                    'name': element.get('tags', {}).get('name', 'Park')
                })
        return parks
