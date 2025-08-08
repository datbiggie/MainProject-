document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);

    // Mensaje de éxito al crear categoría
    if (urlParams.get('success') === 'true') {
        Swal.fire({
            title: '¡Categoría Registrada!',
            text: 'La categoría ha sido creada correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    } else if (urlParams.has('updated')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La categoría ha sido actualizada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('deleted')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La categoría ha sido eliminada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('error')) {
        // Si hay mensaje de error y parámetro de campo, enfocar el campo correspondiente
        const errorMsg = urlParams.get('error_msg') || 'Ha ocurrido un error al procesar la solicitud';
        const errorField = urlParams.get('error_field');
        Swal.fire({
            title: 'Error',
            text: errorMsg,
            icon: 'error',
            confirmButtonText: 'Aceptar'
        }).then(() => {
            if (errorField) {
                const $el = document.getElementById(errorField);
                if ($el) $el.focus();
            }
        });
    }
});

// Inicializar flatpickr con configuración mejorada
// Fecha de hoy por defecto y deshabilitado
document.addEventListener('DOMContentLoaded', function() {
  var fechaInput = document.getElementById('fecha_creacion');
  if (fechaInput) {
    var today = new Date();
    var day = String(today.getDate()).padStart(2, '0');
    var month = String(today.getMonth() + 1).padStart(2, '0');
    var year = today.getFullYear();
    fechaInput.value = day + '/' + month + '/' + year;
  }
});

// Esperar a que el documento esté listo
$(document).ready(function() {
    // Verificar que jQuery y SweetAlert2 estén cargados
    if (typeof $ === 'undefined') {
        console.error('jQuery no está cargado');
        return;
    }
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 no está cargado');
        return;
    }

    // Manejar el envío del formulario
    const form = $('#categoriaForm');
    if (form.length === 0) {
        console.error('No se encontró el formulario con ID categoriaForm');
        return;
    }

    let isSubmitting = false;

    form.on('submit', function(e) {
        e.preventDefault();
        e.stopPropagation();

        if (isSubmitting) {
            console.log('Ya hay un envío en proceso');
            return false;
        }

        const submitButton = form.find('input[type="submit"]');
        submitButton.prop('disabled', true);
        isSubmitting = true;

        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: form.serialize(),
            success: function(response) {
                console.log('Respuesta del servidor:', response);
                if (response.success) {
                    Swal.fire({
                        title: '¡Registro exitoso!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            form[0].reset();
                            setTimeout(function() {
                                window.location.reload();
                            }, 1500);
                        }
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: response.message,
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then(() => {
                        // Foco automático según el mensaje de error
                        if (response.message && response.message.toLowerCase().includes('nombre')) {
                            $('#nombre_categoria').focus();
                        } else if (response.message && response.message.toLowerCase().includes('estatus')) {
                            $('#estatus_categoria').focus();
                        } else if (response.message && response.message.toLowerCase().includes('descrip')) {
                            $('#descripcion_categoria').focus();
                        }
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Error en la petición AJAX:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al procesar la solicitud',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
            },
            complete: function() {
                submitButton.prop('disabled', false);
                isSubmitting = false;
            }
        });

        return false;
    });
});