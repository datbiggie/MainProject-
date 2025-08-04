// Variables globales para el mapa
let map = null;
let editMap = null;
let marker = null;
let editMarker = null;
let geocoder = null;
let locationObtained = false;
let editLocationObtained = false;
let mapInitialized = false;
let editMapInitialized = false;

// Función para limpiar el estado del mapa
function clearMapState() {
    if (map) {
        google.maps.event.clearInstanceListeners(map);
    }
    if (editMap) {
        google.maps.event.clearInstanceListeners(editMap);
    }
    if (marker) {
        google.maps.event.clearInstanceListeners(marker);
        marker.setMap(null);
    }
    if (editMarker) {
        google.maps.event.clearInstanceListeners(editMarker);
        editMarker.setMap(null);
    }
    
    map = null;
    editMap = null;
    marker = null;
    editMarker = null;
    geocoder = null;
    locationObtained = false;
    editLocationObtained = false;
    mapInitialized = false;
    editMapInitialized = false;
    
    console.log('Estado del mapa limpiado');
}

// Función de fallback si Google Maps no se carga
function initMapFallback() {
    console.log('Intentando inicializar mapa con fallback...');
    setTimeout(function() {
        if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
            initMap();
        } else {
            console.error('Google Maps no se pudo cargar');
            const locationStatus = document.getElementById('locationStatus');
            if (locationStatus) {
                locationStatus.innerHTML = '<span id="locationIcon">❌</span> Error al cargar Google Maps. Recarga la página.';
                locationStatus.style.color = '#dc3545';
            }
        }
    }, 2000);
}

// Función para obtener ubicación automáticamente para el mapa principal
function getCurrentLocation() {
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
                
                map.setCenter(userLocation);
                map.setZoom(16);
                marker.setPosition(userLocation);
                
                document.getElementById('latitud').value = userLocation.lat.toFixed(6);
                document.getElementById('longitud').value = userLocation.lng.toFixed(6);
                
                geocoder.geocode({ 
                    'location': userLocation,
                    'language': 'es'
                }, function(results, status) {
                    if (status === 'OK' && results[0]) {
                        document.getElementById('direccion_sucursal').value = results[0].formatted_address;
                        
                        locationStatus.innerHTML = '<span id="locationIcon">✅</span> Ubicación obtenida correctamente';
                        locationStatus.style.color = '#28a745';
                        document.getElementById('retryButton').style.display = 'none';
                        locationObtained = true;
                    } else {
                        locationStatus.innerHTML = '<span id="locationIcon">⚠️</span> Ubicación obtenida pero no se pudo obtener la dirección';
                        locationStatus.style.color = '#ffc107';
                        document.getElementById('retryButton').style.display = 'inline-block';
                    }
                });
            },
            function(error) {
                let errorMessage = 'Error al obtener la ubicación';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Permiso denegado. Por favor, permite el acceso a tu ubicación.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Información de ubicación no disponible.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Tiempo de espera agotado. Verifica tu conexión a internet.';
                        break;
                }
                
                locationStatus.innerHTML = '<span id="locationIcon">❌</span> ' + errorMessage;
                locationStatus.style.color = '#dc3545';
                document.getElementById('retryButton').style.display = 'inline-block';
                
                Swal.fire({
                    title: 'Error de ubicación',
                    text: errorMessage + '\n\nPuedes hacer clic en "Reintentar" o arrastrar el marcador en el mapa para seleccionar tu ubicación manualmente.',
                    icon: 'warning',
                    confirmButtonText: 'Reintentar',
                    cancelButtonText: 'Cancelar',
                    showCancelButton: true,
                    confirmButtonColor: '#3b82f6',
                    cancelButtonColor: '#6c757d'
                }).then((result) => {
                    if (result.isConfirmed) {
                        retryLocation();
                    }
                });
            },
            options
        );
    } else {
        locationStatus.innerHTML = '<span id="locationIcon">❌</span> Tu navegador no soporta geolocalización';
        locationStatus.style.color = '#dc3545';
        document.getElementById('retryButton').style.display = 'inline-block';
        
        Swal.fire({
            title: 'Error',
            text: 'Tu navegador no soporta geolocalización',
            icon: 'error',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    }
}

// Función para obtener ubicación automáticamente para el mapa de edición
function getCurrentEditLocation() {
    const locationStatus = document.getElementById('editLocationStatus');
    const locationIcon = document.getElementById('editLocationIcon');
    
    if (navigator.geolocation) {
        const options = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        };
        
        locationStatus.innerHTML = '<span id="editLocationIcon">⏳</span> Obteniendo ubicación con alta precisión...';
        document.getElementById('editRetryButton').style.display = 'none';
        
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                editMap.setCenter(userLocation);
                editMap.setZoom(16);
                editMarker.setPosition(userLocation);
                
                document.getElementById('edit_latitud').value = userLocation.lat.toFixed(6);
                document.getElementById('edit_longitud').value = userLocation.lng.toFixed(6);
                
                geocoder.geocode({ 
                    'location': userLocation,
                    'language': 'es'
                }, function(results, status) {
                    if (status === 'OK' && results[0]) {
                        document.getElementById('edit_direccion_sucursal').value = results[0].formatted_address;
                        
                        locationStatus.innerHTML = '<span id="editLocationIcon">✅</span> Ubicación obtenida correctamente';
                        locationStatus.style.color = '#28a745';
                        document.getElementById('editRetryButton').style.display = 'none';
                        editLocationObtained = true;
                    } else {
                        locationStatus.innerHTML = '<span id="editLocationIcon">⚠️</span> Ubicación obtenida pero no se pudo obtener la dirección';
                        locationStatus.style.color = '#ffc107';
                        document.getElementById('editRetryButton').style.display = 'inline-block';
                    }
                });
            },
            function(error) {
                let errorMessage = 'Error al obtener la ubicación';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Permiso denegado. Por favor, permite el acceso a tu ubicación.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Información de ubicación no disponible.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Tiempo de espera agotado. Verifica tu conexión a internet.';
                        break;
                }
                
                locationStatus.innerHTML = '<span id="editLocationIcon">❌</span> ' + errorMessage;
                locationStatus.style.color = '#dc3545';
                document.getElementById('editRetryButton').style.display = 'inline-block';
                
                Swal.fire({
                    title: 'Error de ubicación',
                    text: errorMessage + '\n\nPuedes hacer clic en "Reintentar" o arrastrar el marcador en el mapa para seleccionar tu ubicación manualmente.',
                    icon: 'warning',
                    confirmButtonText: 'Reintentar',
                    cancelButtonText: 'Cancelar',
                    showCancelButton: true,
                    confirmButtonColor: '#3b82f6',
                    cancelButtonColor: '#6c757d'
                }).then((result) => {
                    if (result.isConfirmed) {
                        retryEditLocation();
                    }
                });
            },
            options
        );
    } else {
        locationStatus.innerHTML = '<span id="editLocationIcon">❌</span> Tu navegador no soporta geolocalización';
        locationStatus.style.color = '#dc3545';
        document.getElementById('editRetryButton').style.display = 'inline-block';
        
        Swal.fire({
            title: 'Error',
            text: 'Tu navegador no soporta geolocalización',
            icon: 'error',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    }
}

// Función para inicializar el mapa - Versión mejorada
function initMap() {
    console.log('Inicializando mapa...');
    
    try {
        if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
            console.error('Google Maps no está cargado, reintentando en 1 segundo...');
            setTimeout(initMap, 1000);
            return;
        }
        
        clearMapState();
        
        const venezuela = { lat: 6.42375, lng: -66.58973 };
        
        // Inicializar mapa principal
        const mapElement = document.getElementById('map');
        if (mapElement) {
            map = new google.maps.Map(mapElement, {
                center: venezuela,
                zoom: 6,
                mapTypeControl: true,
                streetViewControl: true,
                fullscreenControl: true,
                gestureHandling: 'cooperative',
                zoomControl: true,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            });

            marker = new google.maps.Marker({
                position: venezuela,
                map: map,
                draggable: true,
                title: 'Ubicación de la sucursal',
                icon: {
                    url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                    scaledSize: new google.maps.Size(32, 32)
                }
            });
        }

        // Inicializar mapa de edición
        const editMapElement = document.getElementById('edit_map');
        if (editMapElement) {
            editMap = new google.maps.Map(editMapElement, {
                center: venezuela,
                zoom: 6,
                mapTypeControl: true,
                streetViewControl: true,
                fullscreenControl: true,
                gestureHandling: 'cooperative',
                zoomControl: true,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            });

            editMarker = new google.maps.Marker({
                position: venezuela,
                map: editMap,
                draggable: true,
                title: 'Ubicación de la sucursal',
                icon: {
                    url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                    scaledSize: new google.maps.Size(32, 32)
                }
            });
        }

        geocoder = new google.maps.Geocoder();

        // Obtener ubicación automáticamente después de un breve delay
        setTimeout(function() {
            getCurrentLocation();
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
            getCurrentLocation();
        };

        // Agregar función para reintentar ubicación de edición
        window.retryEditLocation = function() {
            const locationStatus = document.getElementById('editLocationStatus');
            locationStatus.innerHTML = '<span id="editLocationIcon">⏳</span> Reintentando obtener ubicación...';
            locationStatus.style.color = '#2196F3';
            document.getElementById('editRetryButton').style.display = 'none';
            getCurrentEditLocation();
        };

        // Actualizar coordenadas cuando se arrastra el marcador del mapa principal
        google.maps.event.addListener(marker, 'dragend', function() {
            const position = marker.getPosition();
            document.getElementById('latitud').value = position.lat().toFixed(6);
            document.getElementById('longitud').value = position.lng().toFixed(6);

            geocoder.geocode({ 
                'location': position,
                'language': 'es'
            }, function(results, status) {
                if (status === 'OK' && results[0]) {
                    document.getElementById('direccion_sucursal').value = results[0].formatted_address;
                    
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

        // Actualizar coordenadas cuando se arrastra el marcador del mapa de edición
        google.maps.event.addListener(editMarker, 'dragend', function() {
            const position = editMarker.getPosition();
            document.getElementById('edit_latitud').value = position.lat().toFixed(6);
            document.getElementById('edit_longitud').value = position.lng().toFixed(6);

            geocoder.geocode({ 
                'location': position,
                'language': 'es'
            }, function(results, status) {
                if (status === 'OK' && results[0]) {
                    document.getElementById('edit_direccion_sucursal').value = results[0].formatted_address;
                    
                    const locationStatus = document.getElementById('editLocationStatus');
                    if (locationStatus) {
                        locationStatus.innerHTML = '<span id="editLocationIcon">📍</span> Ubicación actualizada manualmente';
                        locationStatus.style.color = '#2196F3';
                    }
                } else {
                    console.warn('No se pudo obtener la dirección para las coordenadas:', position.lat(), position.lng());
                }
            });
        });

        console.log('Mapa inicializado correctamente');
        mapInitialized = true;
        editMapInitialized = true;
    } catch (error) {
        console.error('Error al inicializar el mapa:', error);
        mapInitialized = false;
        editMapInitialized = false;
        const mapElement = document.getElementById('map');
        if (mapElement) {
            mapElement.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px;">
                    <h3>Error al cargar el mapa</h3>
                    <p>Por favor, verifica tu conexión a internet y recarga la página.</p>
                    <p>Si el problema persiste, contacta al administrador.</p>
                    <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Recargar Página
                    </button>
                </div>
            `;
        }
    }
}

// Función para cargar los datos en el modal de edición
function cargarDatosEdicion(sucursal) {
    // Cargar datos básicos
    document.getElementById('edit_id_sucursal').value = sucursal.id_sucursal;
    document.getElementById('edit_nombre_sucursal').value = sucursal.nombre_sucursal;
    document.getElementById('edit_telefono_sucursal').value = sucursal.telefono_sucursal;
    document.getElementById('edit_estado_sucursal').value = sucursal.estado_sucursal;
    document.getElementById('edit_direccion_sucursal').value = sucursal.direccion_sucursal;
    
    // Cargar coordenadas
    const latitud = parseFloat(sucursal.latitud_sucursal);
    const longitud = parseFloat(sucursal.longitud_sucursal);
    
    document.getElementById('edit_latitud').value = latitud;
    document.getElementById('edit_longitud').value = longitud;
    
    // Actualizar el mapa de edición
    const position = { lat: latitud, lng: longitud };
    editMap.setCenter(position);
    editMap.setZoom(15);
    editMarker.setPosition(position);
    
    // Obtener la dirección actualizada
    geocoder.geocode({ 'location': position }, function(results, status) {
        if (status === 'OK' && results[0]) {
            document.getElementById('edit_direccion_sucursal').value = results[0].formatted_address;
        }
    });
}

// Agregar eventos a los botones de editar y eliminar
document.addEventListener('DOMContentLoaded', function() {
    // Eventos para editar
    document.querySelectorAll('.edit').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const latitud = this.getAttribute('data-latitud');
            const longitud = this.getAttribute('data-longitud');
            const row = this.closest('tr');
            const sucursal = {
                id_sucursal: id,
                nombre_sucursal: row.cells[1].textContent,
                telefono_sucursal: row.cells[3].textContent,
                estado_sucursal: row.cells[4].textContent,
                direccion_sucursal: row.cells[2].textContent,
                latitud_sucursal: latitud,
                longitud_sucursal: longitud
            };
            cargarDatosEdicion(sucursal);
        });
    });

    // Eventos para eliminar
    document.querySelectorAll('.delete').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const nombreSucursal = this.closest('tr').cells[1].textContent;
            document.getElementById('delete_id_sucursal').value = id;
            
            // Actualizar el mensaje del modal con el nombre de la sucursal
            const modalBody = document.querySelector('#deleteEmployeeModal .modal-body p:first-child');
            modalBody.textContent = `¿Estás seguro que deseas eliminar la sucursal "${nombreSucursal}"?`;
        });
    });
});

// Función para mostrar mensajes de éxito
function mostrarMensajeExito(mensaje) {
    Swal.fire({
        title: '¡Éxito!',
        text: mensaje,
        icon: 'success',
        confirmButtonText: 'Aceptar',
        confirmButtonColor: '#3b82f6'
    });
}

// Función para mostrar mensajes de error
function mostrarMensajeError(mensaje) {
    Swal.fire({
        title: 'Error',
        text: mensaje,
        icon: 'error',
        confirmButtonText: 'Aceptar',
        confirmButtonColor: '#3b82f6'
    });
}

// Manejar el envío del formulario de agregar sucursal
$('#sucursalForm').on('submit', function(e) {
    e.preventDefault();
    
    $.ajax({
        url: $(this).attr('action'),
        method: 'POST',
        data: $(this).serialize(),
        success: function(response) {
            if (response.success) {
                mostrarMensajeExito(response.message);
                // Limpiar el formulario
                $('#sucursalForm')[0].reset();
                // Recargar la página para mostrar la nueva sucursal
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                mostrarMensajeError(response.message);
            }
        },
        error: function() {
            mostrarMensajeError('Ha ocurrido un error al procesar la solicitud');
        }
    });
});

// Manejar el envío del formulario de editar sucursal
$('#editSucursalForm').on('submit', function(e) {
    e.preventDefault();
    
    $.ajax({
        url: $(this).attr('action'),
        method: 'POST',
        data: $(this).serialize(),
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                mostrarMensajeExito(response.message);
                // Cerrar el modal
                $('#editEmployeeModal').modal('hide');
                // Recargar la página para mostrar los cambios
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                mostrarMensajeError(response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            mostrarMensajeError('Ha ocurrido un error al procesar la solicitud');
        }
    });
});

// Manejar el envío del formulario de eliminar sucursal
$('#deleteSucursalForm').on('submit', function(e) {
    e.preventDefault();
    
    $.ajax({
        url: $(this).attr('action'),
        method: 'POST',
        data: $(this).serialize(),
        success: function(response) {
            if (response.success) {
                mostrarMensajeExito(response.message);
                // Cerrar el modal
                $('#deleteEmployeeModal').modal('hide');
                // Recargar la página para mostrar los cambios
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                mostrarMensajeError(response.message);
            }
        },
        error: function() {
            mostrarMensajeError('Ha ocurrido un error al procesar la solicitud');
        }
    });
});

// Manejar el envío del formulario de eliminar todas las sucursales
$('#deleteAllSucursalesForm').on('submit', function(e) {
    e.preventDefault();
    
    $.ajax({
        url: $(this).attr('action'),
        method: 'POST',
        data: $(this).serialize(),
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                mostrarMensajeExito(response.message);
                // Cerrar el modal
                $('#deleteAllModal').modal('hide');
                // Recargar la página para mostrar los cambios
                setTimeout(function() {
                    location.reload();
                }, 1500);
            } else {
                mostrarMensajeError(response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            mostrarMensajeError('Ha ocurrido un error al procesar la solicitud');
        }
    });
});

// Manejar errores de carga de la API de Google Maps
window.onerror = function(msg, url, lineNo, columnNo, error) {
    if (msg.includes('Google Maps')) {
        const mapElement = document.getElementById('map');
        if (mapElement) {
            mapElement.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px;">
                    <h3>Error al cargar el mapa</h3>
                    <p>Por favor, verifica tu conexión a internet y recarga la página.</p>
                    <p>Si el problema persiste, contacta al administrador.</p>
                </div>
            `;
        }
    }
    return false;
};

// Función para cargar Google Maps de forma robusta
function loadGoogleMapsRobustly() {
    if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
        console.log('Google Maps ya está cargado, inicializando mapa...');
        initMap();
        return;
    }

    console.log('Esperando a que Google Maps se cargue...');
    let attempts = 0;
    const maxAttempts = 10;
    
    const checkGoogleMaps = function() {
        attempts++;
        console.log(`Intento ${attempts} de ${maxAttempts} para cargar Google Maps...`);
        
        if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
            console.log('Google Maps cargado exitosamente, inicializando mapa...');
            initMap();
        } else if (attempts < maxAttempts) {
            setTimeout(checkGoogleMaps, 1000);
        } else {
            console.error('No se pudo cargar Google Maps después de múltiples intentos');
            const locationStatus = document.getElementById('locationStatus');
            if (locationStatus) {
                locationStatus.innerHTML = '<span id="locationIcon">❌</span> Error al cargar Google Maps. <button onclick="reloadPageWithCacheClear()" style="background: none; border: none; color: #007bff; text-decoration: underline; cursor: pointer;">Recargar página</button>';
                locationStatus.style.color = '#dc3545';
            }
        }
    };
    
    setTimeout(checkGoogleMaps, 500);
}

// Función para recargar la página limpiando el caché
function reloadPageWithCacheClear() {
    console.log('Recargando página con limpieza de caché...');
    clearMapState();
    window.location.reload(true);
}

// Inicialización cuando el documento está listo
$(document).ready(function() {
    // Iniciar la carga robusta de Google Maps
    loadGoogleMapsRobustly();
});
