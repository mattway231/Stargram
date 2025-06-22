class StargramApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.state = {
            user: null,
            members: [],
            mapPoints: [],
            currentPage: 'home',
            selectedMember: null,
            exchangeFrom: 'nova',
            giftCurrency: 'nova',
            shopTab: 'items',
            map: null
        };
        
        this.init();
    }

    async init() {
        this.tg.expand();
        
        // Загрузка данных пользователя
        await this.loadUserData();
        
        // Инициализация интерфейса
        this.setupEventListeners();
        this.updateUI();
        
        // Инициализация карты при необходимости
        if (this.state.currentPage === 'map') {
            this.initMap();
        }
    }

    async loadUserData() {
        try {
            const response = await fetch(`/api/user?user_id=${this.tg.initDataUnsafe.user.id}`);
            if (!response.ok) throw new Error('Failed to load user data');
            
            this.state.user = await response.json();
            this.updateUserUI();
            
            // Загрузка участников группы
            await this.loadGroupMembers();
            
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showAlert('Ошибка загрузки данных');
        }
    }

    async loadGroupMembers() {
        try {
            // В реальном приложении - запрос к вашему API
            const response = await fetch('/api/members');
            if (!response.ok) throw new Error('Failed to load members');
            
            this.state.members = await response.json();
            this.updateMembersUI();
            
        } catch (error) {
            console.error('Error loading members:', error);
        }
    }

    initMap() {
        if (!this.state.map && document.getElementById('map-container')) {
            this.state.map = L.map('map-container').setView([55.7558, 37.6176], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(this.state.map);
            
            // Загрузка точек на карту
            this.loadMapPoints();
            
            // Отслеживание положения пользователя
            this.trackUserLocation();
        }
    }

    async loadMapPoints() {
        try {
            if (!this.state.user) return;
            
            // Получаем текущее положение
            const position = await this.getCurrentPosition();
            
            // Запрашиваем точки с сервера
            const response = await fetch(
                `/api/map/points?user_id=${this.state.user.id}&lat=${position.coords.latitude}&lon=${position.coords.longitude}`
            );
            
            if (!response.ok) throw new Error('Failed to load map points');
            
            const points = await response.json();
            this.state.mapPoints = points;
            
            // Добавляем маркеры на карту
            this.addPointsToMap();
            
        } catch (error) {
            console.error('Error loading map points:', error);
            this.showAlert('Не удалось загрузить точки на карте');
        }
    }

    addPointsToMap() {
        if (!this.state.map) return;
        
        // Очищаем старые точки
        this.state.map.eachLayer(layer => {
            if (layer instanceof L.Marker) {
                this.state.map.removeLayer(layer);
            }
        });
        
        // Добавляем новые точки
        this.state.mapPoints.forEach(point => {
            const marker = L.marker([point.lat, point.lon], {
                icon: L.divIcon({
                    className: 'map-point-icon',
                    html: '<div class="point-inner">🌟</div>',
                    iconSize: [30, 30]
                })
            })
            .addTo(this.state.map)
            .bindPopup(`
                <div class="map-point-popup">
                    <h4>${point.address}</h4>
                    <p>Награда: ${point.reward.toLocaleString()}❇️</p>
                    <button class="collect-btn" data-id="${point.id}">Собрать (50м)</button>
                </div>
            `);
            
            marker.on('popupopen', () => {
                document.querySelector('.collect-btn')?.addEventListener('click', async () => {
                    await this.collectPoint(point);
                });
            });
        });
    }

    async collectPoint(point) {
        try {
            // Проверяем расстояние до точки
            const position = await this.getCurrentPosition();
            const distance = this.calculateDistance(
                position.coords.latitude, 
                position.coords.longitude,
                point.lat,
                point.lon
            );
            
            if (distance > Config.POINT_RADIUS_M) {
                this.showAlert(`Подойдите ближе! Осталось ${Math.round(distance - Config.POINT_RADIUS_M)}м`);
                return;
            }
            
            // Отправляем запрос на сервер
            const response = await fetch('/api/map/collect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    point_id: point.id,
                    user_id: this.state.user.id,
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                })
            });
            
            if (!response.ok) throw new Error('Failed to collect point');
            
            const result = await response.json();
            
            // Обновляем баланс
            this.state.user.nova += result.reward;
            this.updateUserUI();
            
            // Удаляем точку с карты
            this.state.mapPoints = this.state.mapPoints.filter(p => p.id !== point.id);
            this.addPointsToMap();
            
            this.showAlert(`🎉 Вы собрали точку и получили ${result.reward.toLocaleString()}❇️!`);
            
        } catch (error) {
            console.error('Error collecting point:', error);
            this.showAlert('Ошибка при сборе точки');
        }
    }

    calculateDistance(lat1, lon1, lat2, lon2) {
        // Расчет расстояния в метрах
        const R = 6371e3; // Радиус Земли в метрах
        const φ1 = lat1 * Math.PI/180;
        const φ2 = lat2 * Math.PI/180;
        const Δφ = (lat2-lat1) * Math.PI/180;
        const Δλ = (lon2-lon1) * Math.PI/180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return R * c;
    }

    async getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject('Geolocation is not supported');
            }
            
            navigator.geolocation.getCurrentPosition(
                position => resolve(position),
                error => reject(error),
                {enableHighAccuracy: true, timeout: 10000}
            );
        });
    }

    trackUserLocation() {
        if (!this.state.map) return;
        
        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(
                position => {
                    this.state.map.setView(
                        [position.coords.latitude, position.coords.longitude],
                        this.state.map.getZoom()
                    );
                },
                error => console.error('Geolocation error:', error),
                {enableHighAccuracy: true, maximumAge: 10000}
            );
        }
    }

    updateUI() {
        this.updateUserUI();
        this.updateMembersUI();
        this.updateBalanceUI();
    }

    updateUserUI() {
        if (!this.state.user) return;
        
        // Обновляем аватар и имя
        const avatar = document.getElementById('user-avatar');
        if (avatar) {
            avatar.textContent = this.state.user.first_name.charAt(0).toUpperCase();
            
            // Градиент для аватара
            const colors = ['#FF6B35', '#9B5DE5', '#F15BB5', '#00BBF9', '#4BB543'];
            const color1 = colors[Math.floor(Math.random() * colors.length)];
            const color2 = colors[Math.floor(Math.random() * colors.length)];
            avatar.style.background = `linear-gradient(135deg, ${color1}, ${color2})`;
        }
        
        const username = document.getElementById('username');
        if (username) {
            username.textContent = this.state.user.first_name;
        }
    }

    updateBalanceUI() {
        if (!this.state.user) return;
        
        const novaBalance = document.getElementById('nova-balance');
        const tixBalance = document.getElementById('tix-balance');
        
        if (novaBalance) novaBalance.textContent = this.state.user.nova.toLocaleString();
        if (tixBalance) tixBalance.textContent = this.state.user.tix.toLocaleString();
    }

    updateMembersUI() {
        const membersList = document.getElementById('members-list');
        if (!membersList) return;
        
        membersList.innerHTML = '';
        
        this.state.members.forEach(member => {
            const memberCard = document.createElement('div');
            memberCard.className = 'member-card';
            
            // Градиент для аватара
            const colors = ['#6a4c93', '#9b5de5', '#f15bb5', '#00bbf9', '#4bb543'];
            const color1 = colors[Math.floor(Math.random() * colors.length)];
            const color2 = colors[Math.floor(Math.random() * colors.length)];
            
            memberCard.innerHTML = `
                <div class="member-avatar" style="background: linear-gradient(135deg, ${color1}, ${color2})">
                    ${member.first_name.charAt(0).toUpperCase()}
                </div>
                <div class="member-info">
                    <div class="member-name">${member.first_name}</div>
                    <div class="member-username">@${member.username || 'user'}</div>
                </div>
                <div class="member-balance">
                    <div class="balance-badge nova-badge">${member.nova.toLocaleString()}❇️</div>
                    <div class="balance-badge tix-badge">${member.tix.toLocaleString()}✴️</div>
                </div>
            `;
            
            membersList.appendChild(memberCard);
        });
    }

    setupEventListeners() {
        // Навигация
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = btn.getAttribute('data-page');
                if (page !== this.state.currentPage) {
                    this.state.currentPage = page;
                    this.updateUI();
                    
                    // Особые действия при смене страницы
                    if (page === 'map' && !this.state.map) {
                        this.initMap();
                    }
                }
            });
        });
        
        // Другие обработчики событий...
    }

    showAlert(message, duration = 3000) {
        const alert = document.createElement('div');
        alert.className = 'alert-message';
        alert.textContent = message;
        document.body.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, duration);
    }
}

// Запуск приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.app = new StargramApp();
});
