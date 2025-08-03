// Variables globales para el mapa
let map;
let marker;
let geocoder;

// Función para inicializar el mapa
function initMap() {
    try {
        // Crear el mapa inicialmente centrado en Venezuela
        const venezuela = { lat: 6.42375, lng: -66.58973 };
        const mapElement = document.getElementById('map');
        
        if (!mapElement) {
            console.error('No se encontró el elemento del mapa');
            return;
        }

        map = new google.maps.Map(mapElement, {
            center: venezuela,
            zoom: 6,
            mapTypeControl: true,
            streetViewControl: true,
            fullscreenControl: true
        });

        // Inicializar el geocoder
        geocoder = new google.maps.Geocoder();

        // Crear el marcador inicial
        marker = new google.maps.Marker({
            position: venezuela,
            map: map,
            draggable: true,
            title: 'Ubicación de la empresa'
        });

        // Configurar el botón de ubicación actual
        const currentLocationButton = document.getElementById('currentLocationButton');
        if (currentLocationButton) {
            currentLocationButton.addEventListener('click', function() {
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
                                    document.getElementById('direccion_empresa_mapa').value = results[0].formatted_address;
                                    document.getElementById('direccion_empresa').value = results[0].formatted_address;
                                }
                            });
                        },
                        function(error) {
                            Swal.fire({
                                title: 'Error',
                                text: 'Error al obtener la ubicación: ' + error.message,
                                icon: 'error',
                                confirmButtonText: 'Aceptar',
                                confirmButtonColor: '#3b82f6'
                            });
                        }
                    );
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: 'Tu navegador no soporta geolocalización',
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    });
                }
            });
        }

        // Actualizar coordenadas cuando se arrastra el marcador
        google.maps.event.addListener(marker, 'dragend', function() {
            const position = marker.getPosition();
            document.getElementById('latitud').value = position.lat();
            document.getElementById('longitud').value = position.lng();

            // Obtener la dirección al soltar el marcador
            geocoder.geocode({ 'location': position }, function(results, status) {
                if (status === 'OK' && results[0]) {
                    document.getElementById('direccion_empresa_mapa').value = results[0].formatted_address;
                    document.getElementById('direccion_empresa').value = results[0].formatted_address;
                }
            });
        });

        // Agregar autocompletado para el campo de dirección
        const input = document.getElementById('direccion_empresa_mapa');
        if (input) {
            const autocomplete = new google.maps.places.Autocomplete(input);
            autocomplete.addListener('place_changed', function() {
                const place = autocomplete.getPlace();
                if (place.geometry) {
                    map.setCenter(place.geometry.location);
                    map.setZoom(15);
                    marker.setPosition(place.geometry.location);
                    document.getElementById('latitud').value = place.geometry.location.lat();
                    document.getElementById('longitud').value = place.geometry.location.lng();
                    document.getElementById('direccion_empresa').value = place.formatted_address;
                }
            });
        }

        console.log('Mapa inicializado correctamente');
    } catch (error) {
        console.error('Error al inicializar el mapa:', error);
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
}

// Función para previsualizar la imagen
function previewImage(input) {
    const preview = document.getElementById('imagePreview');
    const file = input.files[0];
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '';
        preview.style.display = 'none';
    }
}

// Manejar errores de carga de la API de Google Maps
window.onerror = function(msg, url, lineNo, columnNo, error) {
    if (msg.includes('Google Maps')) {
        document.getElementById('map').innerHTML = `
            <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px;">
                <h3>Error al cargar el mapa</h3>
                <p>Por favor, verifica tu conexión a internet y recarga la página.</p>
                <p>Si el problema persiste, contacta al administrador.</p>
            </div>
        `;
    }
    return false;
};

// Inicialización cuando el documento está listo
$(document).ready(function() {
    // Inicializar Select2 para estados
    $('#state').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Selecciona un estado',
        allowClear: true,
        language: {
            noResults: function() {
                return "No se encontraron resultados";
            },
            searching: function() {
                return "Buscando...";
            }
        },
        dropdownCssClass: 'select2-dropdown-custom'
    });

    // Asegurar que el contenedor de Select2 tenga la misma altura
    $('.select2-container').css('height', '45px');
    $('.select2-selection').css('height', '45px');
    $('.select2-selection__rendered').css('line-height', '45px');

    // Evento para enfocar el campo de búsqueda cuando se abre el select
    $('#state').on('select2:open', function() {
        setTimeout(function() {
            document.querySelector('.select2-search__field').focus();
        }, 0);
    });

    // Inicializar Select2 para tipo de empresa
    $('#tipo_empresa').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Selecciona el tipo de empresa',
        allowClear: true,
        minimumResultsForSearch: -1,
        language: {
            noResults: function() {
                return "No se encontraron resultados";
            },
            searching: function() {
                return "Buscando...";
            }
        },
        dropdownCssClass: 'select2-dropdown-custom'
    });

    // Manejar cambio de país
    $('#country').on('change', function() {
        const countryCode = $(this).val();
        const stateSelect = $('#state');
        
        if (countryCode === 'VE') {
            stateSelect.prop('disabled', false);
            stateSelect.select2('enable');
        } else {
            stateSelect.prop('disabled', true);
            stateSelect.select2('disable');
            stateSelect.val('').trigger('change');
        }
        
        // Validar campo obligatorio
        validateRequiredField(this);
    });

    // Validación en tiempo real para campos obligatorios
    function validateRequiredField(field) {
        const value = $(field).val().trim();
        if (!value) {
            $(field).addClass('required-error');
            $(field).attr('title', 'Este campo es obligatorio');
        } else {
            $(field).removeClass('required-error');
            $(field).removeAttr('title');
        }
    }

    // Aplicar validación a todos los campos obligatorios
    $('#firstname, #email, #phone, #descripcion_empresa, #direccion_empresa, #direccion_empresa_mapa').on('blur input', function() {
        validateRequiredField(this);
    });

    // Validación especial para textarea
    $('#descripcion_empresa').on('blur input', function() {
        validateRequiredField(this);
    });

    // Validación especial para selects
    $('#state, #tipo_empresa').on('change', function() {
        const value = $(this).val();
        if (!value) {
            $(this).addClass('required-error');
            $(this).attr('title', 'Debe seleccionar una opción');
        } else {
            $(this).removeClass('required-error');
            $(this).removeAttr('title');
        }
    });

    // Validación para coordenadas
    $('#latitud, #longitud').on('blur', function() {
        const value = $(this).val();
        if (!value) {
            $(this).addClass('required-error');
            $(this).attr('title', 'Debe seleccionar una ubicación en el mapa');
        } else {
            $(this).removeClass('required-error');
            $(this).removeAttr('title');
        }
    });

    // Validación para checkbox de términos
    $('#supportCheckbox').on('change', function() {
        if (!$(this).is(':checked')) {
            $(this).addClass('required-error');
            $(this).attr('title', 'Debe aceptar los términos y condiciones');
        } else {
            $(this).removeClass('required-error');
            $(this).removeAttr('title');
        }
    });

    // Manejar el envío del formulario
    $('form').on('submit', function(e) {
        e.preventDefault();
        
        // Validar campos obligatorios antes de enviar
        const nombre_empresa = $('#firstname').val().trim();
        const descripcion_empresa = $('#descripcion_empresa').val().trim();
        const pais_empresa = $('#country').val();
        const estado_empresa = $('#state').val();
        const tipo_empresa = $('#tipo_empresa').val();
        const direccion_empresa = $('#direccion_empresa').val().trim();
        const latitud = $('#latitud').val();
        const longitud = $('#longitud').val();
        
        // Validar checkbox de términos y condiciones
        const checkbox = $('#supportCheckbox').is(':checked');
        
        // Validar campos vacíos
        if (!nombre_empresa || !descripcion_empresa || !pais_empresa || !estado_empresa || !tipo_empresa || !direccion_empresa || !latitud || !longitud) {
            Swal.fire({
                title: 'Campos obligatorios',
                text: 'Todos los campos son obligatorios. Por favor complete todos los campos.',
                icon: 'warning',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }
        
        // Validar checkbox de términos y condiciones
        if (!checkbox) {
            Swal.fire({
                title: 'Términos y condiciones',
                text: 'Debe aceptar los términos y condiciones para continuar.',
                icon: 'warning',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            $('#supportCheckbox').focus();
            return false;
        }
        
        // Crear un objeto FormData para manejar archivos
        const formData = new FormData(this);
        
        $.ajax({
            url: $(this).attr('action'),
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    Swal.fire({
                        title: '¡Empresa Registrada!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Limpiar el formulario
                            $('form')[0].reset();
                            // Limpiar la previsualización de la imagen
                            $('#imagePreview').html('').hide();
                            // Resetear el mapa
                            if (map && marker) {
                                const venezuela = { lat: 6.42375, lng: -66.58973 };
                                map.setCenter(venezuela);
                                map.setZoom(6);
                                marker.setPosition(venezuela);
                                $('#latitud').val('');
                                $('#longitud').val('');
                                $('#direccion_empresa_mapa').val('');
                                $('#direccion_empresa').val('');
                            }
                        }
                    });
                } else {
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

// Manejar mensajes de URL al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);

    // Mensaje de éxito al crear empresa
    if (urlParams.get('success') === 'true') {
        Swal.fire({
            title: '¡Empresa Registrada!',
            text: 'La empresa ha sido creada correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    } else if (urlParams.has('updated')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La empresa ha sido actualizada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('deleted')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La empresa ha sido eliminada correctamente',
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
