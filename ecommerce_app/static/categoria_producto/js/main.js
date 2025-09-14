// Verificar que jQuery esté cargado
if (typeof jQuery != 'undefined') {
    console.log('jQuery está cargado');
} else {
    console.error('jQuery no está cargado');
}

// Verificar que SweetAlert2 esté cargado
if (typeof Swal != 'undefined') {
    console.log('SweetAlert2 está cargado');
} else {
    console.error('SweetAlert2 no está cargado');
}

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
        Swal.fire({
            title: 'Error',
            text: 'Ha ocurrido un error al procesar la solicitud',
            icon: 'error',
            confirmButtonText: 'Aceptar'
        });
    }
});


document.addEventListener('DOMContentLoaded', function () {
    const fechaInput = document.getElementById('fecha_creacion');
    if (fechaInput) {
      flatpickr(fechaInput, {
        dateFormat: "d/m/Y",
        locale: "es",
        altInput: true,
        altFormat: "d/m/Y",
        disableMobile: true,
        minDate: "today",
        maxDate: new Date().fp_incr(365),
        defaultDate: "today" // 👉 Esta línea pone la fecha de hoy por defecto
      });
    }
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

    console.log('jQuery version:', $.fn.jquery);
    console.log('SweetAlert2 version:', Swal.version);

    // Inicializar flatpickr
    if (typeof flatpickr !== 'undefined') {
        flatpickr("#fecha_creacion", {
            dateFormat: "d/m/Y",
            locale: "es",
            allowInput: true,
            altInput: true,
            altFormat: "d/m/Y",
            disableMobile: "true",
            minDate: "today",
            maxDate: new Date().fp_incr(365),
            enableTime: false,
            time_24hr: true,
            showMonths: 1,
            static: true,
            position: "auto",
            monthSelectorType: "static",
            prevArrow: "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M15 18L9 12L15 6' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>",
            nextArrow: "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M9 18L15 12L9 6' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>",
            onOpen: function(selectedDates, dateStr, instance) {
                instance.set("position", "auto");
            }
        });
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

        // Validar atributos duplicados antes del envío
        if (typeof validarFormularioCompleto === 'function' && !validarFormularioCompleto()) {
            Swal.fire({
                title: 'Error de validación',
                text: 'Por favor, corrija los errores en los nombres de atributos antes de continuar.',
                icon: 'error',
                confirmButtonText: 'Entendido'
            });
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