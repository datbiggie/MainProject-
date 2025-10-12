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

// Inicializar flatpickr para #fecha_creacion con configuración similar a categoria_producto
document.addEventListener('DOMContentLoaded', function () {
        var fechaInput = document.getElementById('fecha_creacion');
        if (fechaInput && typeof flatpickr !== 'undefined') {
            flatpickr(fechaInput, {
                dateFormat: "d/m/Y",
                locale: "es",
                altInput: true,
                altFormat: "d/m/Y",
                disableMobile: true,
                minDate: "today",
                maxDate: new Date().fp_incr(365),
                defaultDate: "today"
            });
        } else if (fechaInput) {
            // Fallback simple: asignar fecha de hoy si flatpickr no está disponible
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
                        // Foco automático según el mensaje de error y abrir la sección correspondiente
                        var fieldToFocus = null;
                        if (response.message && response.message.toLowerCase().includes('nombre')) {
                            fieldToFocus = $('#nombre_categoria');
                        } else if (response.message && response.message.toLowerCase().includes('estatus')) {
                            fieldToFocus = $('#estatus_categoria');
                        } else if (response.message && response.message.toLowerCase().includes('descrip')) {
                            fieldToFocus = $('#descripcion_categoria');
                        }

                        if (fieldToFocus && fieldToFocus.length) {
                            const section = fieldToFocus.closest('.accordion-section');
                            if (section.length && !section.hasClass('active')) {
                                section.find('.accordion-header').click();
                            }
                            setTimeout(() => fieldToFocus.focus(), 300); // pequeño delay para asegurar que la sección se abra
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

    // ----- Comportamiento del acordeón para categoria_servicio -----
    document.addEventListener('DOMContentLoaded', function() {
        // Cuando se hace clic en el header de una sección, alternar su estado
        document.querySelectorAll('.accordion-header').forEach(function(header) {
            header.addEventListener('click', function() {
                var section = header.closest('.accordion-section');
                var isActive = section.classList.contains('active');

                // Cerrar todas las secciones
                document.querySelectorAll('.accordion-section').forEach(function(s) {
                    s.classList.remove('active');
                });

                // Si no estaba activa, abrirla
                if (!isActive) section.classList.add('active');
            });
        });
    });