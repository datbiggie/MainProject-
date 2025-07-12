// Funciones para el modal de edición de categorías

// Función para abrir el modal de edición
function abrirModalEditar(idCategoria, nombreCategoria, descripcionCategoria, estatusCategoria) {
    console.log('Abriendo modal de edición para categoría:', idCategoria);
    console.log('=== DATOS RECIBIDOS ===');
    console.log('ID:', idCategoria);
    console.log('Nombre:', nombreCategoria);
    console.log('Descripción:', descripcionCategoria);
    console.log('Estatus:', estatusCategoria);
    console.log('Tipo de estatus:', typeof estatusCategoria);
    console.log('Longitud de estatus:', estatusCategoria ? estatusCategoria.length : 'null/undefined');
    
    // Cargar los datos en el modal
    document.getElementById('edit_id_categoria').value = idCategoria;
    document.getElementById('edit_nombre_categoria').value = nombreCategoria;
    document.getElementById('edit_descripcion_categoria').value = descripcionCategoria;
    
    // Cargar el estatus con verificación detallada
    const estatusSelect = document.getElementById('edit_estatus_categoria');
    console.log('=== SELECT DE ESTATUS ===');
    console.log('Elemento encontrado:', estatusSelect);
    console.log('Opciones disponibles:', Array.from(estatusSelect.options).map(opt => `"${opt.value}"`));
    console.log('Valor a establecer:', `"${estatusCategoria}"`);
    
    estatusSelect.value = estatusCategoria;
    
    console.log('Valor después de establecer:', `"${estatusSelect.value}"`);
    console.log('¿Coincide con el valor esperado?', estatusSelect.value === estatusCategoria);
    
    // Abrir el modal
    const modal = new bootstrap.Modal(document.getElementById('editCategoriaModal'));
    modal.show();
}

// Función para limpiar el modal cuando se cierre
function limpiarModal() {
    document.getElementById('edit_id_categoria').value = '';
    document.getElementById('edit_nombre_categoria').value = '';
    document.getElementById('edit_descripcion_categoria').value = '';
    document.getElementById('edit_estatus_categoria').value = '';
}

// Función para mostrar mensaje de éxito
function mostrarMensajeExito(mensaje) {
    Swal.fire({
        icon: 'success',
        title: '¡Éxito!',
        text: mensaje,
        confirmButtonColor: '#3085d6',
        confirmButtonText: 'Aceptar'
    });
}

// Función para mostrar mensaje de error
function mostrarMensajeError(mensaje) {
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: mensaje,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Aceptar'
    });
}

// Función para cerrar el modal
function cerrarModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('editCategoriaModal'));
    if (modal) {
        modal.hide();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Manejar el envío del formulario de edición
    const editForm = document.getElementById('editCategoriaForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            // Deshabilitar botón y mostrar loading
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Éxito
                    mostrarMensajeExito(data.message);
                    // Cerrar modal y recargar página
                    setTimeout(() => {
                        cerrarModal();
                        window.location.reload();
                    }, 1500);
                } else {
                    // Error
                    mostrarMensajeError(data.message);
                }
            })
            .catch(error => {
                console.error('Error al editar categoría:', error);
                mostrarMensajeError('Error al editar la categoría. Por favor, inténtalo de nuevo.');
            })
            .finally(() => {
                // Restaurar botón
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            });
        });
    }
    
    // Limpiar modal cuando se cierre
    const modal = document.getElementById('editCategoriaModal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            limpiarModal();
        });
    }
}); 