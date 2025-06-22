// Инициализация приложения
document.addEventListener('DOMContentLoaded', async () => {
    // Проверка авторизации
    if (!window.Telegram.WebApp.initDataUnsafe?.user) {
        showAuthScreen();
        return;
    }

    // Загрузка данных пользователя
    const user = await loadUserData();
    if (!user) return;
    
    initUI(user);
    setupNavigation();
    loadHomePage();
});

// Загрузка данных пользователя
async function loadUserData() {
    try {
        const tgUser = window.Telegram.WebApp.initDataUnsafe.user;
        const response = await fetch(`/api/user?id=${tgUser.id}`);
        
        if (!response.ok) {
            showError("Ошибка доступа");
            return null;
        }
        
        return await response.json();
    } catch (e) {
        showError("Ошибка соединения");
        return null;
    }
}

// Инициализация интерфейса
function initUI(user) {
    // Установка аватара
    const avatar = document.getElementById('user-avatar');
    avatar.textContent = user.first_name.charAt(0);
    avatar.style.background = `linear-gradient(135deg, ${getRandomColor()}, ${getRandomColor()})`;
    
    // Установка имени и баланса
    document.getElementById('username').textContent = user.first_name;
    document.getElementById('user-balance').textContent = 
        `${user.nova_balance}❇️ | ${user.tix_balance}✴️`;
}

// Навигация
function setupNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Снимаем активность со всех кнопок
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            
            // Делаем текущую кнопку активной
            btn.classList.add('active');
            
            // Загружаем нужную страницу
            switch(btn.dataset.page) {
                case 'home': loadHomePage(); break;
                case 'ai': loadAIPage(); break;
                case 'map': loadMapPage(); break;
                case 'shop': loadShopPage(); break;
            }
        });
    });
}

// Загрузка главной страницы
async function loadHomePage() {
    const content = document.getElementById('app-content');
    content.innerHTML = `
        <section class="card">
            <h3>Быстрые действия</h3>
            <div class="actions-grid">
                <button class="action-btn" id="exchange-btn">
                    <span>Обменять</span>
                </button>
                <button class="action-btn" id="gift-btn">
                    <span>Подарить</span>
                </button>
            </div>
        </section>
        
        <section class="card">
            <h3>Нейросети</h3>
            <div class="input-group">
                <input type="text" placeholder="Ваш запрос..." id="ai-query">
                <button class="primary-btn" id="ask-ai">Спросить</button>
            </div>
        </section>
        
        <section class="card">
            <h3>Жалоба на нарушение</h3>
            <div class="input-group">
                <input type="text" placeholder="Ссылка на сообщение..." id="report-link">
                <button class="primary-btn" id="send-report">Отправить</button>
            </div>
            <p class="hint">Получите 6000❇️ за подтверждённую жалобу</p>
        </section>
    `;
    
    // Назначение обработчиков
    document.getElementById('exchange-btn').addEventListener('click', showExchangeModal);
    document.getElementById('gift-btn').addEventListener('click', showGiftModal);
    document.getElementById('ask-ai').addEventListener('click', askAI);
    document.getElementById('send-report').addEventListener('click', sendReport);
}

// Загрузка страницы нейросетей
async function loadAIPage() {
    const content = document.getElementById('app-content');
    content.innerHTML = `
        <section class="card ai-chat">
            <div class="ai-header">
                <h3>GPT-4o</h3>
                <button class="icon-btn" id="new-chat">
                    <svg><!-- Иконка --></svg>
                </button>
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <!-- Сообщения будут здесь -->
            </div>
            
            <div class="chat-input">
                <input type="text" placeholder="Напишите сообщение..." id="chat-input">
                <button class="primary-btn" id="send-message">Отправить</button>
            </div>
        </section>
        
        <section class="card ai-tools">
            <h3>Другие нейросети</h3>
            <div class="tools-grid">
                <div class="tool-card" data-tool="image">
                    <h4>Генератор изображений</h4>
                    <p>10✴️ за запрос</p>
                </div>
                <div class="tool-card" data-tool="video">
                    <h4>Генератор видео</h4>
                    <p>30✴️ за запрос</p>
                </div>
            </div>
        </section>
    `;
    
    // Инициализация чата
    initChat();
}

// Загрузка карты
async function loadMapPage() {
    const content = document.getElementById('app-content');
    content.innerHTML = `
        <section class="card map-container">
            <div id="map" style="height: 400px;"></div>
            <div class="map-controls">
                <button class="map-btn" id="locate-me">Моё местоположение</button>
                <button class="map-btn" id="show-points">Показать точки</button>
            </div>
        </section>
        
        <section class="card stats-card">
            <h3>Ваша статистика</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value" id="steps-today">0</span>
                    <span class="stat-label">Шаги сегодня</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value" id="points-today">0</span>
                    <span class="stat-label">Точки сегодня</span>
                </div>
            </div>
        </section>
    `;
    
    // Инициализация карты
    initMap();
}

// Инициализация карты Leaflet
function initMap() {
    const map = L.map('map').setView([55.7558, 37.6176], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    // Получение местоположения
    document.getElementById('locate-me').addEventListener('click', () => {
        navigator.geolocation.getCurrentPosition(pos => {
            map.setView([pos.coords.latitude, pos.coords.longitude], 15);
            L.marker([pos.coords.latitude, pos.coords.longitude])
                .addTo(map)
                .bindPopup("Вы здесь");
        });
    });
    
    // Загрузка точек
    document.getElementById('show-points').addEventListener('click', async () => {
        const points = await fetch('/api/map/points').then(r => r.json());
        points.forEach(p => {
            L.marker([p.lat, p.lon])
                .addTo(map)
                .bindPopup(`<b>${p.reward}❇️</b><br>${p.address}`)
                .openPopup();
        });
    });
}

// Отправка жалобы
async function sendReport() {
    const messageLink = document.getElementById('report-link').value;
    if (!messageLink) return;
    
    try {
        const response = await fetch('/api/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link: messageLink })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification("✅ Жалоба принята! +6000❇️");
            updateBalance(result.newBalance);
        } else {
            showNotification("❌ Нарушений не найдено");
        }
    } catch (e) {
        showNotification("⚠️ Ошибка отправки");
    }
}

// Обновление баланса в UI
function updateBalance({ nova, tix }) {
    document.getElementById('user-balance').textContent = `${nova}❇️ | ${tix}✴️`;
}

// Вспомогательные функции
function getRandomColor() {
    const colors = ['#9B5DE5', '#F15BB5', '#00BBF9', '#4BB543'];
    return colors[Math.floor(Math.random() * colors.length)];
}

function showNotification(text) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = text;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
