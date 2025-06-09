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

// Inicializar flatpickr con configuración mejorada
flatpickr("#fecha_creacion", {
  dateFormat: "d/m/Y",
  locale: "es",
  allowInput: true,
  altInput: true,
  altFormat: "d/m/Y",
  disableMobile: "true",
  minDate: "today",
  maxDate: new Date().fp_incr(365), // Un año desde hoy
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