// Initialize map with Leaflet.js
function initMap() {
    if (map) return;
    
    map = L.map('map').setView([55.7558, 37.6173], 12);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Add user marker if location is available
    if (userLocation) {
        updateUserLocation(userLocation.lat, userLocation.lng);
    }
    
    // Load points
    loadPoints();
}

// Update user location on map
function updateUserLocation(lat, lng) {
    userLocation = { lat, lng };
    
    if (map) {
        if (userMarker) {
            userMarker.setLatLng([lat, lng]);
        } else {
            userMarker = L.marker([lat, lng], {
                icon: L.divIcon({
                    className: 'user-marker',
                    html: `<div class="avatar-marker">${currentUser.username.charAt(0).toUpperCase()}</div>`,
                    iconSize: [40, 40]
                })
            }).addTo(map);
        }
        
        // Center map on user
        map.setView([lat, lng], 13);
    }
}

// Load points on map
function loadPoints() {
    // Clear existing points
    pointMarkers.forEach(marker => map.removeLayer(marker));
    pointMarkers = [];
    
    // Add new points
    activePoints.forEach(point => {
        const marker = L.marker([point.latitude, point.longitude], {
            icon: L.divIcon({
                className: 'point-marker',
                html: '📍',
                iconSize: [30, 30]
            })
        }).addTo(map);
        
        marker.on('click', () => showPointDetails(point));
        pointMarkers.push(marker);
    });
}
