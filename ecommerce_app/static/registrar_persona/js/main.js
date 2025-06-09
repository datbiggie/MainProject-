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

    // Evento para enfocar el campo de búsqueda cuando se abre el select
    $('#state').on('select2:open', function() {
        setTimeout(function() {
            document.querySelector('.select2-search__field').focus();
        }, 0);
    });

    // Manejar el envío del formulario
    $('form').on('submit', function(e) {
        e.preventDefault();
        
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
                            // Limpiar el formulario
                            $('form')[0].reset();
                            window.location.href = window.location.pathname; // recarga limpia sin scroll
                            // O redirigir a otra página si lo deseas
                            // window.location.href = '/ecommerce/iniciar_sesion/';
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
