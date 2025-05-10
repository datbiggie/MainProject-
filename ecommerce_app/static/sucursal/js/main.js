
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
    document.getElementById('edit_id_sucursal').value = sucursal.id_sucursal;
    document.getElementById('edit_nombre_sucursal').value = sucursal.nombre_sucursal;
    document.getElementById('edit_telefono_sucursal').value = sucursal.telefono_sucursal;
    document.getElementById('edit_estado_sucursal').value = sucursal.estado_sucursal;
    document.getElementById('edit_direccion_sucursal').value = sucursal.direccion_sucursal;
    document.getElementById('edit_latitud').value = sucursal.latitud_sucursal;
    document.getElementById('edit_longitud').value = sucursal.longitud_sucursal;
    document.getElementById('edit_direccion_sucursal_mapa').value = sucursal.direccion_sucursal;
    
    // Centrar el mapa en la ubicación de la sucursal
    const position = { lat: parseFloat(sucursal.latitud_sucursal), lng: parseFloat(sucursal.longitud_sucursal) };
    editMap.setCenter(position);
    editMarker.setPosition(position);
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

// Manejar mensajes de éxito y error
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Mensaje de éxito al crear sucursal
    if (urlParams.get('success') === 'true') {
        Swal.fire({
            title: '¡Sucursal Registrada!',
            text: 'La sucursal ha sido creada correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    } else if (urlParams.has('updated')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La sucursal ha sido actualizada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('deleted')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La sucursal ha sido eliminada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('error')) {
        Swal.fire({
            title: 'Error',
            text: 'Ha ocurrido un error al procesar la solicitud',
            icon: 'error',
            confirmButtonText: 'Aceptar'
        });
    }
});
