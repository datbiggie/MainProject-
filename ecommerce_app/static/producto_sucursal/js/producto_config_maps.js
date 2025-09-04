/**
 * Funcionalidad de Google Maps para el modal de edición de productos de usuario
 * Basado en producto_maps.js pero adaptado para el modal de edición
 */

// Variables globales para el mapa de edición
let editMap = null;
let editMarker = null;
let editGeocoder = null;

/**
 * Limpia el estado del mapa de edición
 */
function clearEditMapState() {
    if (editMarker) {
        editMarker.setMap(null);
        editMarker = null;
    }
    if (editMap) {
        editMap = null;
    }
    if (editGeocoder) {
        editGeocoder = null;
    }
}

/**
 * Muestra un mensaje informativo cuando el producto no tiene ubicación guardada
 */
function showNoLocationMessage() {
    console.log('=== DEBUG showNoLocationMessage ===');
    const statusElement = document.getElementById('edit_map_status');
    const statusText = document.getElementById('edit_map_status_text');
    
    console.log('Elemento de estado:', statusElement);
    console.log('Elemento de texto:', statusText);
    
    if (statusElement && statusText) {
        console.log('Mostrando mensaje de aviso');
        statusElement.style.display = 'block';
        statusElement.className = 'alert alert-warning';
        statusText.innerHTML = '<i class="lni lni-warning"></i> <strong>Aviso:</strong> Este producto no tiene una ubicación de entrega guardada. Se está mostrando tu ubicación actual como referencia. Puedes arrastrar el marcador para establecer la ubicación de entrega.';
        console.log('Mensaje de aviso configurado');
    } else {
        console.error('No se encontraron los elementos del DOM para mostrar el mensaje');
    }
}

/**
 * Obtiene la ubicación actual del usuario para el mapa de edición
 */
function getCurrentLocationForEdit() {
    const statusElement = document.getElementById('edit_map_status');
    const statusText = document.getElementById('edit_map_status_text');
    const retryButton = document.getElementById('edit_retry_map');
    
    if (!statusElement || !statusText) return;
    
    // Verificar si ya hay un mensaje de aviso (producto sin ubicación)
    const hasWarningMessage = statusElement.className.includes('alert-warning');
    
    if (!hasWarningMessage) {
        statusElement.style.display = 'block';
        statusElement.className = 'alert alert-info';
        statusText.textContent = 'Obteniendo tu ubicación actual...';
    }
    if (retryButton) {
        retryButton.style.display = 'none';
    }
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Si no hay mensaje de aviso, mostrar estado normal
                if (!hasWarningMessage) {
                    statusText.textContent = 'Ubicación obtenida. Inicializando mapa...';
                } else {
                    // Si hay mensaje de aviso, mantenerlo pero actualizar con información adicional
                    const currentMessage = statusText.innerHTML;
                    if (!currentMessage.includes('Ubicación actual obtenida')) {
                        statusText.innerHTML = currentMessage + '<br><small class="text-success">Ubicación actual obtenida correctamente.</small>';
                    }
                }
                initializeEditMapWithLocation(userLocation);
            },
            function(error) {
                console.warn('Error obteniendo geolocalización:', error);
                
                if (hasWarningMessage) {
                    // Mantener el mensaje de aviso pero agregar información del error
                    const currentMessage = statusText.innerHTML;
                    if (!currentMessage.includes('No se pudo obtener tu ubicación')) {
                        statusText.innerHTML = currentMessage + '<br><small class="text-muted">No se pudo obtener tu ubicación actual. Usando ubicación predeterminada.</small>';
                    }
                } else {
                    statusElement.className = 'alert alert-warning';
                    statusText.textContent = 'No se pudo obtener tu ubicación. Usando ubicación predeterminada.';
                }
                
                // Ubicación predeterminada (Ciudad de México)
                const defaultLocation = { lat: 19.4326, lng: -99.1332 };
                setTimeout(() => {
                    initializeEditMapWithLocation(defaultLocation);
                }, 1000);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            }
        );
    } else {
        if (hasWarningMessage) {
            // Mantener el mensaje de aviso pero agregar información
            const currentMessage = statusText.innerHTML;
            if (!currentMessage.includes('Geolocalización no soportada')) {
                statusText.innerHTML = currentMessage + '<br><small class="text-muted">Geolocalización no soportada. Usando ubicación predeterminada.</small>';
            }
        } else {
            statusElement.className = 'alert alert-warning';
            statusText.textContent = 'Geolocalización no soportada. Usando ubicación predeterminada.';
        }
        
        const defaultLocation = { lat: 19.4326, lng: -99.1332 };
        setTimeout(() => {
            initializeEditMapWithLocation(defaultLocation);
        }, 1000);
    }
}

/**
 * Inicializa el mapa de edición con una ubicación específica
 */
function initializeEditMapWithLocation(location) {
    const mapElement = document.getElementById('edit_map');
    const statusElement = document.getElementById('edit_map_status');
    const statusText = document.getElementById('edit_map_status_text');
    const retryButton = document.getElementById('edit_retry_map');
    const latitudInput = document.getElementById('edit_latitud_entrega');
    const longitudInput = document.getElementById('edit_longitud_entrega');
    
    if (!mapElement) {
        console.error('Elemento del mapa de edición no encontrado');
        return;
    }
    
    try {
        // Limpiar estado anterior
        clearEditMapState();
        
        // Crear el mapa
        editMap = new google.maps.Map(mapElement, {
            zoom: 15,
            center: location,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            streetViewControl: false,
            mapTypeControl: true,
            fullscreenControl: true,
            zoomControl: true
        });
        
        // Crear geocoder
        editGeocoder = new google.maps.Geocoder();
        
        // Crear marcador arrastrable
        editMarker = new google.maps.Marker({
            position: location,
            map: editMap,
            draggable: true,
            title: 'Punto de entrega del producto (arrastra para cambiar ubicación)'
        });
        
        // Actualizar campos de entrada con la ubicación inicial
        if (latitudInput && longitudInput) {
            latitudInput.value = location.lat.toFixed(6);
            longitudInput.value = location.lng.toFixed(6);
        }
        
        // Evento cuando se arrastra el marcador
        editMarker.addListener('dragend', function(event) {
            const newPosition = {
                lat: event.latLng.lat(),
                lng: event.latLng.lng()
            };
            
            if (latitudInput && longitudInput) {
                latitudInput.value = newPosition.lat.toFixed(6);
                longitudInput.value = newPosition.lng.toFixed(6);
            }
            
            console.log('Nueva posición del marcador:', newPosition);
        });
        
        // Solo ocultar mensaje de estado si no es un mensaje de aviso importante
        if (statusElement && !statusElement.className.includes('alert-warning')) {
            statusElement.style.display = 'none';
        }
        
        console.log('Mapa de edición inicializado correctamente');
        
    } catch (error) {
        console.error('Error inicializando el mapa de edición:', error);
        if (statusText && retryButton) {
            statusText.textContent = 'Error al cargar el mapa. Intenta nuevamente.';
            retryButton.style.display = 'inline-block';
        }
    }
}

/**
 * Actualiza el mapa de edición con coordenadas específicas
 */
function updateEditMapWithCoordinates(lat, lng) {
    console.log('=== DEBUG updateEditMapWithCoordinates ===');
    console.log('Latitud recibida:', lat, 'Tipo:', typeof lat);
    console.log('Longitud recibida:', lng, 'Tipo:', typeof lng);
    
    // Convertir a números y verificar si son válidos
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);
    
    console.log('Latitud convertida:', latNum, 'Es válida:', !isNaN(latNum));
    console.log('Longitud convertida:', lngNum, 'Es válida:', !isNaN(lngNum));
    
    // Verificar si las coordenadas son números válidos
    if (isNaN(latNum) || isNaN(lngNum) || lat === 'None' || lng === 'None' || lat === '' || lng === '' || lat === null || lng === null || lat === undefined || lng === undefined) {
        console.log('No hay coordenadas válidas, mostrando mensaje de aviso');
        // Si no hay coordenadas, mostrar mensaje informativo y obtener ubicación actual
        showNoLocationMessage();
        getCurrentLocationForEdit();
        return;
    }
    
    const location = {
        lat: latNum,
        lng: lngNum
    };
    
    // Validar coordenadas (verificar que estén en rangos válidos)
    if (isNaN(location.lat) || isNaN(location.lng) || location.lat < -90 || location.lat > 90 || location.lng < -180 || location.lng > 180) {
        console.warn('Coordenadas inválidas o fuera de rango, usando ubicación actual');
        console.log('Coordenadas parseadas:', location);
        showNoLocationMessage();
        getCurrentLocationForEdit();
        return;
    }
    
    console.log('Actualizando mapa con coordenadas guardadas:', location);
    // Cuando hay coordenadas válidas, inicializar directamente sin mostrar mensaje de aviso
    initializeEditMapWithLocation(location);
}

/**
 * Función callback para la API de Google Maps (modal de edición)
 */
function initEditMap() {
    console.log('Google Maps API cargada para modal de edición');
    
    // Configurar botón de reintentar
    const retryButton = document.getElementById('edit_retry_map');
    if (retryButton) {
        retryButton.addEventListener('click', function() {
            console.log('Reintentando cargar mapa de edición');
            getCurrentLocationForEdit();
        });
    }
    
    // El mapa se inicializará cuando se abra el modal
    console.log('Configuración de mapa de edición lista');
}

/**
 * Inicializa el mapa cuando se abre el modal de edición
 */
function initializeEditMapOnModalShow(lat, lng) {
    // Esperar un poco para que el modal se renderice completamente
    setTimeout(() => {
        if (lat && lng && lat !== '' && lng !== '') {
            updateEditMapWithCoordinates(lat, lng);
        } else {
            getCurrentLocationForEdit();
        }
    }, 300);
}

// Asegurar que las funciones estén disponibles globalmente
window.initEditMap = initEditMap;
window.initializeEditMapOnModalShow = initializeEditMapOnModalShow;
window.updateEditMapWithCoordinates = updateEditMapWithCoordinates;
window.clearEditMapState = clearEditMapState;
window.showNoLocationMessage = showNoLocationMessage;
