function confirmarEliminacion(idCategoriaservicio) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Crear un formulario dinámicamente
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/ecommerce/eliminar_categoria_servicio/';
            
            // Agregar el token CSRF
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = window.CSRF_TOKEN;
            form.appendChild(csrfInput);
            
            // Agregar el ID de la categoría de servicio
            const idInput = document.createElement('input');
            idInput.type = 'hidden';
            idInput.name = 'id_categoriaservicio';
            idInput.value = idCategoriaservicio;
            form.appendChild(idInput);
            
            // Agregar el formulario al documento y enviarlo
            document.body.appendChild(form);
            form.submit();
        }
    });
}

// Manejar mensajes de éxito/error
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('deleted')) {
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