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
    console.log('Valor original recibido:', `"${estatusCategoria}"`);
    
    // Normalizar estatus: primera letra mayúscula, resto minúscula
    let estatusNormalizado = '';
    if (estatusCategoria) {
        estatusNormalizado = estatusCategoria.charAt(0).toUpperCase() + estatusCategoria.slice(1).toLowerCase();
    }
    console.log('Valor normalizado:', `"${estatusNormalizado}"`);
    
    estatusSelect.value = estatusNormalizado;
    
    console.log('Valor después de establecer:', `"${estatusSelect.value}"`);
    console.log('¿Coincide con el valor esperado?', estatusSelect.value === estatusNormalizado);
    
    // Cargar atributos asociados a la categoría
    cargarAtributosCategoriaModal(idCategoria);
    
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

// Función para cargar atributos asociados a una categoría
function cargarAtributosCategoriaModal(idCategoria) {
    const loadingElement = document.getElementById('loadingAtributos');
    const noAtributosElement = document.getElementById('noAtributos');
    const listaAtributosElement = document.getElementById('listaAtributos');
    
    // Mostrar loading y ocultar otros elementos
    loadingElement.style.display = 'block';
    noAtributosElement.style.display = 'none';
    listaAtributosElement.innerHTML = '';
    
    // Realizar petición AJAX para obtener atributos
    fetch(`/ecommerce/obtener_atributos_categoria/?id_categoria=${idCategoria}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        loadingElement.style.display = 'none';
        
        if (data.success && data.atributos && data.atributos.length > 0) {
            // Mostrar atributos
            mostrarAtributos(data.atributos);
        } else {
            // Mostrar mensaje de no atributos
            noAtributosElement.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error al cargar atributos:', error);
        loadingElement.style.display = 'none';
        noAtributosElement.style.display = 'block';
        noAtributosElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error al cargar los atributos.';
        noAtributosElement.className = 'alert alert-danger';
    });
}

// Función para mostrar la lista de atributos
function mostrarAtributos(atributos) {
    const listaAtributosElement = document.getElementById('listaAtributos');
    let html = '';
    
    atributos.forEach(atributo => {
        const tipoIcon = obtenerIconoTipo(atributo.tipo);
        const obligatorioText = atributo.obligatorio ? 'Obligatorio' : 'Opcional';
        const obligatorioClass = atributo.obligatorio ? 'badge-danger' : 'badge-secondary';
        
        html += `
            <div class="atributo-item">
                <div class="atributo-info">
                    <div class="atributo-nombre">
                        <i class="${tipoIcon}"></i>
                        <strong>${atributo.nombre}</strong>
                    </div>
                    <div class="atributo-detalles">
                        <span class="badge badge-primary">${atributo.tipo}</span>
                        <span class="badge ${obligatorioClass}">${obligatorioText}</span>
                        ${atributo.orden ? `<span class="badge badge-info">Orden: ${atributo.orden}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    listaAtributosElement.innerHTML = html;
}

// Función para obtener el icono según el tipo de atributo
function obtenerIconoTipo(tipo) {
    const iconos = {
        'texto': 'fas fa-font',
        'numero': 'fas fa-hashtag',
        'decimal': 'fas fa-calculator',
        'fecha': 'fas fa-calendar-alt',
        'booleano': 'fas fa-toggle-on',
        'lista': 'fas fa-list-ul',
        'email': 'fas fa-envelope',
        'url': 'fas fa-link',
        'telefono': 'fas fa-phone',
        'color': 'fas fa-palette'
    };
    
    return iconos[tipo] || 'fas fa-tag';
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