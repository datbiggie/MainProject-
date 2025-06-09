let map;
let editMap;
let marker;
let editMarker;
let geocoder;

function initMap() {
    // Crear el mapa inicialmente centrado en Venezuela
    const venezuela = { lat: 6.42375, lng: -66.58973 };
    map = new google.maps.Map(document.getElementById('map'), {
        center: venezuela,
        zoom: 6
    });

    // Inicializar el mapa de edición
    editMap = new google.maps.Map(document.getElementById('edit_map'), {
        center: venezuela,
        zoom: 6
    });

    // Inicializar el geocoder
    geocoder = new google.maps.Geocoder();

    // Crear los marcadores iniciales
    marker = new google.maps.Marker({
        position: venezuela,
        map: map,
        draggable: true
    });

    editMarker = new google.maps.Marker({
        position: venezuela,
        map: editMap,
        draggable: true
    });

    // Configurar el botón de ubicación actual para el mapa principal
    document.getElementById('currentLocationButton').addEventListener('click', function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const userLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    map.setCenter(userLocation);
                    map.setZoom(15);
                    marker.setPosition(userLocation);
                    document.getElementById('latitud').value = userLocation.lat;
                    document.getElementById('longitud').value = userLocation.lng;

                    // Obtener la dirección actual
                    geocoder.geocode({ 'location': userLocation }, function(results, status) {
                        if (status === 'OK' && results[0]) {
                            const direccion = results[0].formatted_address;
                            document.getElementById('direccion_sucursal_mapa').value = direccion;
                            document.getElementById('direccion_sucursal').value = direccion;
                        }
                    });
                },
                function(error) {
                    alert('Error al obtener la ubicación: ' + error.message);
                }
            );
        } else {
            alert('Tu navegador no soporta geolocalización');
        }
    });

    // Configurar el botón de ubicación actual para el mapa de edición
    document.getElementById('edit_currentLocationButton').addEventListener('click', function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const userLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    editMap.setCenter(userLocation);
                    editMap.setZoom(15);
                    editMarker.setPosition(userLocation);
                    document.getElementById('edit_latitud').value = userLocation.lat;
                    document.getElementById('edit_longitud').value = userLocation.lng;

                    // Obtener la dirección actual
                    geocoder.geocode({ 'location': userLocation }, function(results, status) {
                        if (status === 'OK' && results[0]) {
                            const direccion = results[0].formatted_address;
                            document.getElementById('edit_direccion_sucursal_mapa').value = direccion;
                            document.getElementById('edit_direccion_sucursal').value = direccion;
                        }
                    });
                },
                function(error) {
                    alert('Error al obtener la ubicación: ' + error.message);
                }
            );
        } else {
            alert('Tu navegador no soporta geolocalización');
        }
    });

    // Actualizar coordenadas cuando se arrastra el marcador del mapa principal
    google.maps.event.addListener(marker, 'dragend', function() {
        const position = marker.getPosition();
        document.getElementById('latitud').value = position.lat();
        document.getElementById('longitud').value = position.lng();

        // Obtener la dirección al soltar el marcador
        geocoder.geocode({ 'location': position }, function(results, status) {
            if (status === 'OK' && results[0]) {
                const direccion = results[0].formatted_address;
                document.getElementById('direccion_sucursal_mapa').value = direccion;
                document.getElementById('direccion_sucursal').value = direccion;
            }
        });
    });

    // Actualizar coordenadas cuando se arrastra el marcador del mapa de edición
    google.maps.event.addListener(editMarker, 'dragend', function() {
        const position = editMarker.getPosition();
        document.getElementById('edit_latitud').value = position.lat();
        document.getElementById('edit_longitud').value = position.lng();

        // Obtener la dirección al soltar el marcador
        geocoder.geocode({ 'location': position }, function(results, status) {
            if (status === 'OK' && results[0]) {
                const direccion = results[0].formatted_address;
                document.getElementById('edit_direccion_sucursal_mapa').value = direccion;
                document.getElementById('edit_direccion_sucursal').value = direccion;
            }
        });
    });
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
    document.getElementById('edit_direccion_sucursal_mapa').value = sucursal.direccion_sucursal;
    
    // Actualizar el mapa
    const position = { lat: latitud, lng: longitud };
    editMap.setCenter(position);
    editMap.setZoom(15); // Aumentar el zoom para mejor visualización
    editMarker.setPosition(position);
    
    // Obtener la dirección actualizada
    geocoder.geocode({ 'location': position }, function(results, status) {
        if (status === 'OK' && results[0]) {
            document.getElementById('edit_direccion_sucursal_mapa').value = results[0].formatted_address;
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
