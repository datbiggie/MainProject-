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
                <button onclick="loadGoogleMapsRobustly()" style="margin-top: 10px; margin-left: 10px; padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 Reintentar
                </button>
            </div>
        `;
        
        const mapElement = document.getElementById('map');
        const editMapElement = document.getElementById('edit_map');
        
        if (mapElement) {
            mapElement.innerHTML = errorMessage;
        }
        if (editMapElement) {
            editMapElement.innerHTML = errorMessage;
        }
        
        // Actualizar estado de ubicación
        const locationStatus = document.getElementById('locationStatus');
        if (locationStatus) {
            locationStatus.innerHTML = `<span id="locationIcon">❌</span> ${errorType}: ${errorDetails}`;
            locationStatus.style.color = '#dc3545';
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

// Función para diagnosticar conectividad
function diagnosticarConectividad() {
    console.log('Iniciando diagnóstico de conectividad...');
    
    // Verificar conectividad básica
    if (!navigator.onLine) {
        return {
            conectado: false,
            mensaje: 'Sin conexión a internet detectada'
        };
    }
    
    // Intentar hacer ping a Google
    return fetch('https://www.google.com/favicon.ico', {
        method: 'HEAD',
        mode: 'no-cors',
        cache: 'no-cache'
    })
    .then(() => {
        console.log('Conectividad a Google confirmada');
        return {
            conectado: true,
            mensaje: 'Conexión a internet OK'
        };
    })
    .catch(() => {
        console.log('Problemas de conectividad detectados');
        return {
            conectado: false,
            mensaje: 'Problemas de conectividad a internet'
        };
    });
}

// Función para cargar Google Maps de forma robusta
function loadGoogleMapsRobustly() {
    console.log('Iniciando carga robusta de Google Maps...');
    
    // Primero diagnosticar conectividad
    diagnosticarConectividad().then(resultado => {
        console.log('Resultado diagnóstico:', resultado);
        
        if (!resultado.conectado) {
            const errorMessage = `
                <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px; margin: 10px;">
                    <h3>🌐 Sin conexión a internet</h3>
                    <p><strong>${resultado.mensaje}</strong></p>
                    <p>Por favor verifica tu conexión y vuelve a intentar.</p>
                    <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        🔄 Reintentar
                    </button>
                </div>
            `;
            
            const mapElement = document.getElementById('map');
            const editMapElement = document.getElementById('edit_map');
            
            if (mapElement) mapElement.innerHTML = errorMessage;
            if (editMapElement) editMapElement.innerHTML = errorMessage;
            
            const locationStatus = document.getElementById('locationStatus');
            if (locationStatus) {
                locationStatus.innerHTML = '<span id="locationIcon">🌐</span> Sin conexión a internet';
                locationStatus.style.color = '#dc3545';
            }
            return;
        }
        
        // Si hay conectividad, proceder con la carga de Google Maps
        if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
            console.log('Google Maps ya está cargado, inicializando mapa...');
            initMap();
            return;
        }

        console.log('Esperando a que Google Maps se cargue...');
        let attempts = 0;
        const maxAttempts = 15; // Aumentado el número de intentos
        
        const checkGoogleMaps = function() {
            attempts++;
            console.log(`Intento ${attempts} de ${maxAttempts} para cargar Google Maps...`);
            
            if (typeof google !== 'undefined' && typeof google.maps !== 'undefined') {
                console.log('Google Maps cargado exitosamente, inicializando mapa...');
                initMap();
            } else if (attempts < maxAttempts) {
                setTimeout(checkGoogleMaps, 1500); // Aumentado el tiempo entre intentos
            } else {
                console.error('No se pudo cargar Google Maps después de múltiples intentos');
                
                const errorMessage = `
                    <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px; margin: 10px;">
                        <h3>🗺️ Error al cargar Google Maps</h3>
                        <p><strong>No se pudo conectar con los servidores de Google Maps</strong></p>
                        <div style="margin: 15px 0; padding: 10px; background-color: #fff3cd; border-radius: 4px; font-size: 14px;">
                            <strong>Posibles causas:</strong><br>
                            • Problemas temporales con Google Maps<br>
                            • Firewall o proxy bloqueando la conexión<br>
                            • Problemas con la clave API<br>
                            • Restricciones de red
                        </div>
                        <button onclick="reloadPageWithCacheClear()" style="margin-top: 10px; padding: 8px 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 Recargar página
                        </button>
                        <button onclick="loadGoogleMapsRobustly()" style="margin-top: 10px; margin-left: 10px; padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 Reintentar carga
                        </button>
                    </div>
                `;
                
                const mapElement = document.getElementById('map');
                const editMapElement = document.getElementById('edit_map');
                
                if (mapElement) mapElement.innerHTML = errorMessage;
                if (editMapElement) editMapElement.innerHTML = errorMessage;
                
                const locationStatus = document.getElementById('locationStatus');
                if (locationStatus) {
                    locationStatus.innerHTML = '<span id="locationIcon">❌</span> Error al cargar Google Maps';
                    locationStatus.style.color = '#dc3545';
                }
            }
        };
        
        setTimeout(checkGoogleMaps, 1000);
    });
}

// Función para recargar la página limpiando el caché
function reloadPageWithCacheClear() {
    console.log('Recargando página con limpieza de caché...');
    clearMapState();
    window.location.reload(true);
}

// Función para manejar errores de autenticación de Google Maps
window.gm_authFailure = function() {
    console.error('Error de autenticación de Google Maps');
    const mapElement = document.getElementById('map');
    const editMapElement = document.getElementById('edit_map');
    
    const errorMessage = `
        <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px; margin: 10px;">
            <h3>❌ Error de conexión con Google Maps</h3>
            <p><strong>Problema de autenticación detectado</strong></p>
            <p>Esto puede deberse a:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>Problemas con la clave API de Google Maps</li>
                <li>Restricciones de dominio en la API</li>
                <li>Límites de uso excedidos</li>
                <li>Problemas de conectividad a internet</li>
            </ul>
            <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                🔄 Recargar Página
            </button>
        </div>
    `;
    
    if (mapElement) {
        mapElement.innerHTML = errorMessage;
    }
    if (editMapElement) {
        editMapElement.innerHTML = errorMessage;
    }
    
    // Actualizar estado de ubicación
    const locationStatus = document.getElementById('locationStatus');
    if (locationStatus) {
        locationStatus.innerHTML = '<span id="locationIcon">❌</span> Error de conexión con Google Maps';
        locationStatus.style.color = '#dc3545';
    }
    
    const editLocationStatus = document.getElementById('editLocationStatus');
    if (editLocationStatus) {
        editLocationStatus.innerHTML = '<span id="editLocationIcon">❌</span> Error de conexión con Google Maps';
        editLocationStatus.style.color = '#dc3545';
    }
};

// Inicialización cuando el documento está listo

$(document).ready(function() {
    // Iniciar la carga robusta de Google Maps
    loadGoogleMapsRobustly();

    // Evento para abrir el modal de productos de sucursal
    $(document).on('click', '.productos-sucursal', function() {
        const sucursalId = $(this).data('id');
        // Guardar el id de sucursal en el input oculto del modal
        $('#inputSucursalIdProducto').val(sucursalId);

        // Limpiar selects y campos del formulario
        $('#selectProducto').html('<option value="">Cargando productos...</option>');
        $('#inputStock').val('');
        $('#inputPrecio').val('');

        // AJAX para obtener productos disponibles
        $.ajax({
            url: '/ecommerce/api/productos_servicios_disponibles/',
            method: 'GET',
            data: { sucursal_id: sucursalId, tipo: 'productos' },
            dataType: 'json',
            success: function(data) {
                // Productos
                let prodOptions = '<option value="">Seleccione un producto</option>';
                if (data.productos && data.productos.length > 0) {
                    data.productos.forEach(function(prod) {
                        prodOptions += `<option value="${prod.id}">${prod.nombre}</option>`;
                    });
                } else {
                    prodOptions += '<option value="">No hay productos disponibles</option>';
                }
                $('#selectProducto').html(prodOptions);
            },
            error: function() {
                $('#selectProducto').html('<option value="">Error al cargar productos</option>');
            }
        });
    });
    
    // Evento para abrir el modal de servicios de sucursal
    $(document).on('click', '.servicios-sucursal', function() {
        const sucursalId = $(this).data('id');
        // Guardar el id de sucursal en el input oculto del modal
        $('#inputSucursalIdServicio').val(sucursalId);

        // Limpiar selects y campos del formulario
        $('#selectServicio').html('<option value="">Cargando servicios...</option>');
        $('#inputPrecioServicio').val('');

        // AJAX para obtener servicios disponibles
        $.ajax({
            url: '/ecommerce/api/productos_servicios_disponibles/',
            method: 'GET',
            data: { sucursal_id: sucursalId, tipo: 'servicios' },
            dataType: 'json',
            success: function(data) {
                // Servicios
                let servOptions = '<option value="">Seleccione un servicio</option>';
                if (data.servicios && data.servicios.length > 0) {
                    data.servicios.forEach(function(serv) {
                        servOptions += `<option value="${serv.id}">${serv.nombre}</option>`;
                    });
                } else {
                    servOptions += '<option value="">No hay servicios disponibles</option>';
                }
                $('#selectServicio').html(servOptions);
            },
            error: function() {
                $('#selectServicio').html('<option value="">Error al cargar servicios</option>');
            }
        });
    });

    // Manejar el envío del formulario de productos de sucursal
    $('#formAgregarProductoSucursal').on('submit', function(e) {
        e.preventDefault();
        
        // Obtener valores del formulario
        const sucursalId = $('#inputSucursalIdProducto').val();
        const productoId = $('#selectProducto').val();
        const stock = $('#inputStock').val();
        const precio = $('#inputPrecio').val();
        const estatusProducto = $('#selectEstatusProducto').val();
        
        // Validaciones básicas
        if (!sucursalId) {
            Swal.fire({
                title: 'Error',
                text: 'No se ha seleccionado una sucursal',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }
        
        // Validar que se haya seleccionado un producto
        if (!productoId) {
            Swal.fire({
                title: 'Error',
                text: 'Debe seleccionar un producto',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }
        
        // Validar stock y precio
        if (!stock) {
            Swal.fire({
                title: 'Error',
                text: 'El stock es obligatorio para productos',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }
        
        if (!precio) {
            Swal.fire({
                title: 'Error',
                text: 'El precio es obligatorio para productos',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }
        
        // Enviar datos al servidor
        $.ajax({
            url: '/ecommerce/api/guardar_producto_servicio_sucursal/',
            method: 'POST',
            data: {
                sucursal_id: sucursalId,
                producto_id: productoId,
                servicio_id: '',
                stock: stock,
                precio: precio,
                estatus_producto_sucursal: estatusProducto,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    // Mostrar mensaje de éxito
                    Swal.fire({
                        title: '¡Éxito!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        // Cerrar el modal
                        $('#productosSucursalModal').modal('hide');
                        
                        // Opcional: recargar la página para mostrar los cambios
                        // window.location.reload();
                    });
                } else {
                    // Mostrar mensaje de error
                    Swal.fire({
                        title: 'Error',
                        text: response.message,
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    });
                }
            },
            error: function() {
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al procesar la solicitud',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
            }
        });
    });
    
    // Manejar el envío del formulario de servicios de sucursal
    $('#formAgregarServicioSucursal').on('submit', function(e) {
        e.preventDefault();
        
        // Obtener valores del formulario
        const sucursalId = $('#inputSucursalIdServicio').val();
        const servicioId = $('#selectServicio').val();
        const precio = $('#inputPrecioServicio').val();
        const estatusServicio = $('#selectEstatusServicio').val();
        
        // Validaciones básicas
        if (!sucursalId) {
            Swal.fire({
                title: 'Error',
                text: 'No se ha seleccionado una sucursal',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }
        
        // Validar que se haya seleccionado un servicio
        if (!servicioId) {
            Swal.fire({
                title: 'Error',
                text: 'Debe seleccionar un servicio',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }
        
        // El precio no es obligatorio para servicios en sucursal
        
        // Enviar datos al servidor
        $.ajax({
            url: '/ecommerce/api/guardar_producto_servicio_sucursal/',
            method: 'POST',
            data: {
                sucursal_id: sucursalId,
                producto_id: '',
                servicio_id: servicioId,
                stock: 0,
                precio: precio,
                estatus_servicio_sucursal: estatusServicio,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    // Mostrar mensaje de éxito
                    Swal.fire({
                        title: '¡Éxito!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        // Cerrar el modal
                        $('#serviciosSucursalModal').modal('hide');
                        
                        // Opcional: recargar la página para mostrar los cambios
                        // window.location.reload();
                    });
                } else {
                    // Mostrar mensaje de error
                    Swal.fire({
                        title: 'Error',
                        text: response.message,
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    });
                }
            },
            error: function() {
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al procesar la solicitud',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
            }
        });
    });
});
