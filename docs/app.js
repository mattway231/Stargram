document.addEventListener('DOMContentLoaded', async () => {
    // Инициализация Telegram Web App
    const tg = window.Telegram.WebApp;
    tg.expand();
    
    // Получение токена пользователя
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    // Проверка авторизации
    if (!token) {
        showAuthScreen();
        return;
    }
    
    try {
        const decoded = jwt_decode(token);
        const user = await getUserData(decoded.user_id);
        
        if (!user) {
            showAuthScreen();
            return;
        }
        
        initApp(user);
    } catch (e) {
        showAuthScreen();
    }
    
    // Инициализация карты
    const map = L.map('map').setView([55.751244, 37.618423], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);
});

async function getUserData(userId) {
    try {
        const response = await fetch(`${config.API_URL}/user?user_id=${userId}`);
        return await response.json();
    } catch (e) {
        return null;
    }
}

function initApp(user) {
    // Обновление UI
    document.getElementById('nova-balance').textContent = `${user.nova}❇️`;
    document.getElementById('tix-balance').textContent = `${user.tix}✴️`;
    
    // Премиум статус
    if (user.is_premium) {
        document.querySelector('.avatar').classList.add('premium');
        document.getElementById('premium-banner').style.display = 'none';
    }
    
    // Обработчики вкладок
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Переключение экранов
            const tabName = tab.dataset.tab;
            document.querySelectorAll('.screen').forEach(screen => {
                screen.classList.add('hidden');
            });
            document.getElementById(`${tabName}-screen`).classList.remove('hidden');
        });
    });
    
    // Закрытие премиум баннера
    document.querySelector('.close-banner').addEventListener('click', () => {
        document.getElementById('premium-banner').style.display = 'none';
    });
    
    // Генерация точек на карте
    if (user.allow_location) {
        generateMapPoints(user);
    }
}

function generateMapPoints(user) {
    // Запрос геопозиции
    navigator.geolocation.getCurrentPosition(pos => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        
        // Центрирование карты
        map.setView([lat, lon], 13);
        
        // Генерация точек
        const points = integrations.GeoAPI.generate_points(lat, lon);
        
        points.forEach(point => {
            const marker = L.marker([point[0], point[1]]).addTo(map)
                .bindPopup(`<b>Точка сбора</b><br>${point[2]}<br>Награда: ${point[3]}❇️`);
            
            marker.on('click', () => {
                collectPoint(user.id, point);
            });
        });
        
        // Отображение друзей
        user.friends.forEach(friend => {
            if (friend.location) {
                L.marker([friend.location.lat, friend.location.lon])
                    .addTo(map)
                    .bindPopup(`<b>${friend.username}</b>`);
            }
        });
    });
}

async function collectPoint(userId, point) {
    try {
        const response = await fetch(`${config.API_URL}/collect-point`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: userId,
                lat: point[0],
                lon: point[1],
                value: point[3]
            })
        });
        
        if (response.ok) {
            alert(`Точка собрана! +${point[3]}❇️`);
        }
    } catch (e) {
        console.error('Ошибка сбора точки:', e);
    }
}
