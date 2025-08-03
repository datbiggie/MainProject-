$(document).ready(function() {
    // Inicializar Select2
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
        }
    });

    // Validación para nombre y apellido (solo letras y espacios)
    function validateName(input) {
        const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
        return nameRegex.test(input);
    }

    // Validación para teléfono (solo números)
    function validatePhone(input) {
        const phoneRegex = /^[0-9]+$/;
        return phoneRegex.test(input);
    }

    // Aplicar validación en tiempo real para nombre
    $('#nombre_usuario').on('input', function() {
        const value = $(this).val();
        if (value && !validateName(value)) {
            $(this).addClass('error-input');
            $(this).attr('title', 'Solo se permiten letras y espacios');
        } else {
            $(this).removeClass('error-input');
            $(this).removeAttr('title');
        }
    });

    // Aplicar validación en tiempo real para apellido
    $('#apellido').on('input', function() {
        const value = $(this).val();
        if (value && !validateName(value)) {
            $(this).addClass('error-input');
            $(this).attr('title', 'Solo se permiten letras y espacios');
        } else {
            $(this).removeClass('error-input');
            $(this).removeAttr('title');
        }
    });

    // Aplicar validación en tiempo real para teléfono
    $('#telefono').on('input', function() {
        const value = $(this).val();
        if (value && !validatePhone(value)) {
            $(this).addClass('error-input');
            $(this).attr('title', 'Solo se permiten números');
        } else {
            $(this).removeClass('error-input');
            $(this).removeAttr('title');
        }
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
    $('#nombre_usuario, #apellido, #email, #password, #telefono, #fecha_nacimiento, #country').on('blur', function() {
        validateRequiredField(this);
    });

    // Validación especial para el select de estado
    $('#state').on('change', function() {
        const value = $(this).val();
        if (!value) {
            $(this).addClass('required-error');
            $(this).attr('title', 'Debe seleccionar un estado');
        } else {
            $(this).removeClass('required-error');
            $(this).removeAttr('title');
        }
    });

    // Evento para enfocar el campo de búsqueda cuando se abre el select
    $('#state').on('select2:open', function() {
        setTimeout(function() {
            document.querySelector('.select2-search__field').focus();
        }, 0);
    });

    // Manejar el envío del formulario
    $('form').on('submit', function(e) {
        e.preventDefault();
        
        // Validar campos antes de enviar
        const nombre = $('#nombre_usuario').val();
        const apellido = $('#apellido').val();
        const telefono = $('#telefono').val();
        
        // Validar nombre
        if (!validateName(nombre)) {
            Swal.fire({
                title: 'Error de validación',
                text: 'El nombre solo puede contener letras y espacios',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            $('#nombre_usuario').focus();
            return false;
        }
        
        // Validar apellido
        if (!validateName(apellido)) {
            Swal.fire({
                title: 'Error de validación',
                text: 'El apellido solo puede contener letras y espacios',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            $('#apellido').focus();
            return false;
        }
        
        // Validar teléfono
        if (!validatePhone(telefono)) {
            Swal.fire({
                title: 'Error de validación',
                text: 'El teléfono solo puede contener números',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            $('#telefono').focus();
            return false;
        }
        
        // Validar que todos los campos estén completos
        const email = $('#email').val().trim();
        const password = $('#password').val().trim();
        const fecha_nacimiento = $('#fecha_nacimiento').val();
        const pais = $('#country').val().trim();
        const estado = $('#state').val();
        const checkbox = $('#supportCheckbox').is(':checked');
        
        // Validar campos vacíos
        if (!nombre || !apellido || !email || !password || !telefono || !fecha_nacimiento || !pais || !estado) {
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
        
        $.ajax({
            url: $(this).attr('action'),
            method: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    Swal.fire({
                        title: '¡Registro exitoso!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Si hay una URL de redirección en la respuesta, usarla
                            if (response.redirect_url) {
                                window.location.href = response.redirect_url;
                            } else {
                                // Limpiar el formulario y recargar la página
                                $('form')[0].reset();
                                window.location.href = window.location.pathname;
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
