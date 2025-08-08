// Archivo JavaScript limpio para categ_producto_config
// Solo contiene funciones auxiliares que no interfieren con el template



// Función de eliminación de categorías
function confirmarEliminacion(idCategoria) {
    console.log('Función confirmarEliminacion llamada con ID:', idCategoria);
    console.log('Tipo de ID:', typeof idCategoria);
    
    // Validar que el ID no sea nulo o vacío
    if (!idCategoria || idCategoria === 'null' || idCategoria === 'undefined' || idCategoria === '') {
        console.error('ID de categoría inválido:', idCategoria);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'ID de categoría inválido. No se puede eliminar esta categoría.',
            confirmButtonColor: '#d33',
            confirmButtonText: 'Aceptar'
        });
        return;
    }
    
    Swal.fire({
        title: '¿Estás seguro?',
        text: "¿Realmente quieres eliminar esta categoría? Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            console.log('Usuario confirmó eliminación');
            
            // Obtener CSRF token directamente del input oculto
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
            const formData = new FormData();
            formData.append('id_categoria', idCategoria);
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            console.log('FormData creado, enviando a: /ecommerce/eliminar_categoria_producto/');
            console.log('ID a enviar:', idCategoria);
            
            // Mostrar indicador de carga
            Swal.fire({
                title: 'Eliminando...',
                text: 'Por favor espera mientras se elimina la categoría',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Enviar solicitud de eliminación
            fetch('/ecommerce/eliminar_categoria_producto/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN
                }
            })
            .then(response => {
                console.log('Respuesta recibida:', response);
                return response.json();
            })
            .then(data => {
                console.log('Datos recibidos:', data);
                if (data.success) {
                    // Éxito
                    Swal.fire({
                        icon: 'success',
                        title: '¡Categoría Eliminada!',
                        text: data.message,
                        confirmButtonColor: '#3085d6',
                        confirmButtonText: 'Aceptar'
                    }).then((result) => {
                        // Recargar página para mostrar cambios
                        window.location.reload();
                    });
                } else {
                    // Error
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message,
                        confirmButtonColor: '#d33',
                        confirmButtonText: 'Aceptar'
                    });
                }
            })
            .catch(error => {
                console.error('Error al eliminar categoría:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Error al eliminar la categoría. Por favor, inténtalo de nuevo.',
                    confirmButtonColor: '#d33',
                    confirmButtonText: 'Aceptar'
                });
            });
        }
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Obtener el token CSRF del template
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        window.CSRF_TOKEN = csrfToken;
    }
    
    console.log('Template cargado - DELETE_URL:', window.DELETE_URL);
    console.log('CSRF_TOKEN:', window.CSRF_TOKEN);
    
    // Manejar mensajes de éxito/error de URL parameters
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