// Variables globales para el mapa de productos
let productoMap = null;
let productoMarker = null;
let productoGeocoder = null;
let productoLocationObtained = false;
let productoMapInitialized = false;

// Función para limpiar el estado del mapa de productos
function clearProductoMapState() {
    if (productoMap) {
        google.maps.event.clearInstanceListeners(productoMap);
    }
    if (productoMarker) {
        google.maps.event.clearInstanceListeners(productoMarker);
        productoMarker.setMap(null);
    }
    
    productoMap = null;
    productoMarker = null;
    productoGeocoder = null;
    productoLocationObtained = false;
    productoMapInitialized = false;
    
    console.log('Estado del mapa de productos limpiado');
}

// Función para obtener ubicación automáticamente para el mapa de productos
function getCurrentProductoLocation() {
    const locationStatus = document.getElementById('locationStatus');
    const locationIcon = document.getElementById('locationIcon');
    
    if (navigator.geolocation) {
        const options = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        };
        
        locationStatus.innerHTML = '<span id="locationIcon">⏳</span> Obteniendo ubicación con alta precisión...';
        document.getElementById('retryButton').style.display = 'none';
        
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                productoMap.setCenter(userLocation);
                productoMap.setZoom(16);
                productoMarker.setPosition(userLocation);
                
                document.getElementById('latitud_entrega').value = userLocation.lat.toFixed(6);
                document.getElementById('longitud_entrega').value = userLocation.lng.toFixed(6);
                
                productoGeocoder.geocode({ 
                    'location': userLocation,
                    'language': 'es'
                }, function(results, status) {
                    if (status === 'OK' && results[0]) {
                        locationStatus.innerHTML = '<span id="locationIcon">✅</span> Ubicación obtenida correctamente';
                        locationStatus.style.color = '#28a745';
                        document.getElementById('retryButton').style.display = 'none';
                        productoLocationObtained = true;
                    } else {
                        locationStatus.innerHTML = '<span id="locationIcon">⚠️</span> Ubicación obtenida pero no se pudo obtener la dirección';
                        locationStatus.style.color = '#ffc107';
                        document.getElementById('retryButton').style.display = 'inline-block';
                        productoLocationObtained = true;
                    }
                });
            },
            function(error) {
                console.error('Error al obtener ubicación:', error);
                let errorMessage = '';
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Permiso de ubicación denegado. Habilita la ubicación en tu navegador.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Información de ubicación no disponible.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Tiempo de espera agotado al obtener ubicación.';
                        break;
                    default:
                        errorMessage = 'Error desconocido al obtener ubicación.';
                        break;
                }
                
                locationStatus.innerHTML = `<span id="locationIcon">❌</span> ${errorMessage}`;
                locationStatus.style.color = '#dc3545';
                document.getElementById('retryButton').style.display = 'inline-block';
                
                // Centrar en Venezuela como fallback
                const venezuela = { lat: 6.42375, lng: -66.58973 };
                productoMap.setCenter(venezuela);
                productoMap.setZoom(6);
                productoMarker.setPosition(venezuela);
                
                document.getElementById('latitud_entrega').value = venezuela.lat.toFixed(6);
                document.getElementById('longitud_entrega').value = venezuela.lng.toFixed(6);
            },
            options
        );
    } else {
        locationStatus.innerHTML = '<span id="locationIcon">❌</span> Geolocalización no soportada por este navegador';
        locationStatus.style.color = '#dc3545';
        document.getElementById('retryButton').style.display = 'none';
        
        // Centrar en Venezuela como fallback
        const venezuela = { lat: 6.42375, lng: -66.58973 };
        productoMap.setCenter(venezuela);
        productoMap.setZoom(6);
        productoMarker.setPosition(venezuela);
        
        document.getElementById('latitud_entrega').value = venezuela.lat.toFixed(6);
        document.getElementById('longitud_entrega').value = venezuela.lng.toFixed(6);
    }
}

// Función principal para inicializar el mapa de productos
function initProductoMap() {
    console.log('Inicializando mapa de productos...');
    
    try {
        if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
            console.error('Google Maps no está cargado, reintentando en 1 segundo...');
            setTimeout(initProductoMap, 1000);
            return;
        }
        
        clearProductoMapState();
        
        const venezuela = { lat: 6.42375, lng: -66.58973 };
        
        // Inicializar mapa de productos
        const mapElement = document.getElementById('producto_map');
        if (mapElement) {
            productoMap = new google.maps.Map(mapElement, {
                center: venezuela,
                zoom: 6,
                mapTypeControl: true,
                streetViewControl: true,
                fullscreenControl: true,
                gestureHandling: 'cooperative',
                zoomControl: true,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            });

            productoMarker = new google.maps.Marker({
                position: venezuela,
                map: productoMap,
                draggable: true,
                title: 'Posible punto de encuentro del producto',
                icon: {
                    url: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
                    scaledSize: new google.maps.Size(32, 32)
                }
            });
        }

        productoGeocoder = new google.maps.Geocoder();

        // Obtener ubicación automáticamente después de un breve delay
        setTimeout(function() {
            getCurrentProductoLocation();
        }, 1000);
        
        // Actualizar estado inicial
        const locationStatus = document.getElementById('locationStatus');
        if (locationStatus) {
            locationStatus.innerHTML = '<span id="locationIcon">📍</span> Obteniendo ubicación automáticamente...';
            locationStatus.style.color = '#2196F3';
        }
        
        // Agregar función para reintentar ubicación
        window.retryLocation = function() {
            const locationStatus = document.getElementById('locationStatus');
            locationStatus.innerHTML = '<span id="locationIcon">⏳</span> Reintentando obtener ubicación...';
            locationStatus.style.color = '#2196F3';
            document.getElementById('retryButton').style.display = 'none';
            getCurrentProductoLocation();
        };

        // Actualizar coordenadas cuando se arrastra el marcador
        google.maps.event.addListener(productoMarker, 'dragend', function() {
            const position = productoMarker.getPosition();
            document.getElementById('latitud_entrega').value = position.lat().toFixed(6);
            document.getElementById('longitud_entrega').value = position.lng().toFixed(6);

            productoGeocoder.geocode({ 
                'location': position,
                'language': 'es'
            }, function(results, status) {
                if (status === 'OK' && results[0]) {
                    const locationStatus = document.getElementById('locationStatus');
                    if (locationStatus) {
                        locationStatus.innerHTML = '<span id="locationIcon">📍</span> Ubicación actualizada manualmente';
                        locationStatus.style.color = '#2196F3';
                    }
                } else {
                    console.warn('No se pudo obtener la dirección para las coordenadas:', position.lat(), position.lng());
                }
            });
        });

        console.log('Mapa de productos inicializado correctamente');
        productoMapInitialized = true;
    } catch (error) {
        console.error('Error al inicializar el mapa de productos:', error);
        productoMapInitialized = false;
        
        // Determinar el tipo de error
        let errorType = 'Error desconocido';
        let errorDetails = '';
        
        if (error.message.includes('Network')) {
            errorType = 'Error de red';
            errorDetails = 'Verifica tu conexión a internet';
        } else if (error.message.includes('API')) {
            errorType = 'Error de API';
            errorDetails = 'Problema con la clave de Google Maps';
        } else if (error.message.includes('quota')) {
            errorType = 'Límite excedido';
            errorDetails = 'Se ha excedido el límite de uso de la API';
        }
        
        const errorMessage = `
            <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px; margin: 10px;">
                <h3>❌ Error al cargar el mapa</h3>
                <p><strong>${errorType}</strong></p>
                <p>${errorDetails}</p>
                <div style="margin: 15px 0; padding: 10px; background-color: #fff3cd; border-radius: 4px; font-size: 14px;">
                    <strong>Posibles soluciones:</strong><br>
                    • Verifica tu conexión a internet<br>
                    • Recarga la página<br>
                    • Intenta más tarde<br>
                    • Contacta al administrador si persiste
                </div>
                <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 Recargar Página
                </button>
            </div>
        `;
        
        const mapElement = document.getElementById('producto_map');
        if (mapElement) {
            mapElement.innerHTML = errorMessage;
        }
        
        // Actualizar estado de ubicación
        const locationStatus = document.getElementById('locationStatus');
        if (locationStatus) {
            locationStatus.innerHTML = `<span id="locationIcon">❌</span> ${errorType}: ${errorDetails}`;
            locationStatus.style.color = '#dc3545';
        }
    }
}

// Función de fallback si Google Maps no se carga
function initProductoMapFallback() {
    console.log('Intentando inicializar mapa de productos con fallback...');
    setTimeout(function() {
        if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
            initProductoMap();
        } else {
            console.error('Google Maps no se pudo cargar para productos');
            const locationStatus = document.getElementById('locationStatus');
            if (locationStatus) {
                locationStatus.innerHTML = '<span id="locationIcon">❌</span> Error al cargar Google Maps. Recarga la página.';
                locationStatus.style.color = '#dc3545';
            }
        }
    }, 2000);
}

// Manejo de errores de autenticación de Google Maps
window.gm_authFailure = function() {
    console.error('Error de autenticación de Google Maps');
    const locationStatus = document.getElementById('locationStatus');
    if (locationStatus) {
        locationStatus.innerHTML = '<span id="locationIcon">❌</span> Error de autenticación de Google Maps';
        locationStatus.style.color = '#dc3545';
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, preparando mapa de productos...');
    
    // Si Google Maps ya está cargado, inicializar inmediatamente
    if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
        initProductoMap();
    } else {
        // Si no, usar el fallback
        initProductoMapFallback();
    }
});