// Инициализация Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(registration => {
            console.log('ServiceWorker registration successful');
        })
        .catch(err => {
            console.log('ServiceWorker registration failed: ', err);
        });
}

// Функция для отправки запросов к AI API
async function sendAIRequest(model, prompt, options = {}) {
    let endpoint;
    let body = { prompt };
    
    if (model === 'GPT-4o') {
        endpoint = '/api/ai/gpt';
    } else if (model === 'YaART Image') {
        endpoint = '/api/ai/image';
        body = { ...body, ...options };
    } else if (model === 'YaART Video' || model === 'Sora Pro') {
        endpoint = '/api/ai/video';
        body = { ...body, ...options };
    }
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.userToken}`
            },
            body: JSON.stringify(body)
        });
        
        return await response.json();
    } catch (error) {
        console.error('AI request error:', error);
        return { error: 'Failed to process request' };
    }
}

// Функция для работы с картой
function initMap(lat, lng) {
    const map = L.map('map-container').setView([lat, lng], 15);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    return map;
}

// Функция для обновления местоположения пользователя
function updateUserLocation(lat, lng) {
    if (window.socket) {
        window.socket.emit('update_location', {
            user_id: window.userId,
            lat,
            lng
        });
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    window.userId = urlParams.get('user_id');
    
    // Инициализация WebSocket
    window.socket = io();
    
    // Обработчики событий WebSocket
    window.socket.on('connect', () => {
        console.log('Connected to WebSocket server');
        window.socket.emit('authenticate', { user_id: window.userId });
    });
    
    window.socket.on('balance_updated', data => {
        if (data.user_id === window.userId) {
            // Обновляем баланс в интерфейсе
            if (window.updateBalanceUI) {
                window.updateBalanceUI(data.nova_balance, data.tix_balance);
            }
        }
    });
    
    // Загрузка начальных данных
    fetch(`/api/user/${window.userId}`)
        .then(response => response.json())
        .then(data => {
            // Инициализация интерфейса с данными пользователя
            if (window.initUI) {
                window.initUI(data);
            }
        });
});
