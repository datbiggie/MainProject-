/**
 * Funciones JavaScript para la gestión de productos por sucursal
 */

/**
 * Abre el modal de edición con los datos del producto
 * @param {HTMLElement} button - Elemento botón que contiene los datos en atributos data-*
 */
function editarProducto(button) {
    const id = button.getAttribute('data-id');
    const precio = button.getAttribute('data-precio');
    const stock = button.getAttribute('data-stock');
    const estatus = button.getAttribute('data-estatus');
    const condicion = button.getAttribute('data-condicion');
    
    document.getElementById('editProductoId').value = id;
    document.getElementById('editPrecio').value = precio;
    document.getElementById('editStock').value = stock;
    document.getElementById('editEstatus').value = estatus;
    document.getElementById('editCondicion').value = condicion;
    
    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

/**
 * Guarda los cambios realizados en el modal de edición
 */
function guardarCambios() {
    const id = document.getElementById('editProductoId').value;
    const precio = document.getElementById('editPrecio').value;
    const stock = document.getElementById('editStock').value;
    const estatus = document.getElementById('editEstatus').value;
    const condicion = document.getElementById('editCondicion').value;
    
    if (!precio || !stock) {
        Swal.fire({
            icon: 'warning',
            title: 'Campos requeridos',
            text: 'Por favor, completa todos los campos requeridos.',
            confirmButtonColor: '#3085d6'
        });
        return;
    }
    
    const formData = new FormData();
    formData.append('id_producto_sucursal', id);
    formData.append('precio', precio);
    formData.append('stock', stock);
    formData.append('estatus', estatus);
    formData.append('condicion', condicion);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    fetch('/ecommerce/editar_producto_sucursal/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: 'Producto actualizado exitosamente',
                confirmButtonColor: '#28a745'
            }).then(() => {
                location.reload();
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message,
                confirmButtonColor: '#dc3545'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'Error al actualizar el producto. Inténtalo de nuevo.',
            confirmButtonColor: '#dc3545'
        });
    });
}

/**
 * Elimina un producto de la sucursal
 * @param {HTMLElement} button - Elemento botón que contiene los datos en atributos data-*
 */
function eliminarProducto(button) {
    const id = button.getAttribute('data-id');
    const nombre = button.getAttribute('data-nombre');
    
    Swal.fire({
        title: '¿Estás seguro?',
        text: `¿Deseas eliminar el producto "${nombre}" de la sucursal?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
        const formData = new FormData();
        formData.append('id_producto_sucursal', id);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        fetch('/ecommerce/eliminar_producto_sucursal/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Eliminado!',
                    text: 'Producto eliminado exitosamente',
                    confirmButtonColor: '#28a745'
                }).then(() => {
                    location.reload();
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message,
                    confirmButtonColor: '#dc3545'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'Error al eliminar el producto. Inténtalo de nuevo.',
                confirmButtonColor: '#dc3545'
            });
        });
        }
    });
}

/**
 * Funciones para mejorar la experiencia de filtrado
 */

/**
 * Limpia todos los filtros del formulario
 */
function limpiarFiltros() {
    document.getElementById('nombre_producto').value = '';
    document.getElementById('sucursal_filtro').value = '';
    document.getElementById('estado_filtro').value = '';
    
    // Enviar formulario automáticamente para mostrar todos los productos
    document.querySelector('.search-form').submit();
}

/**
 * Aplica filtros automáticamente cuando se cambia un select
 */
function aplicarFiltroAutomatico() {
    // Opcional: aplicar filtros automáticamente al cambiar selects
    // document.querySelector('.search-form').submit();
}

/**
 * Maneja el evento de Enter en el campo de búsqueda
 */
function manejarEnterBusqueda(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        document.querySelector('.search-form').submit();
    }
}

/**
 * Resalta los términos de búsqueda en los resultados
 */
function resaltarTerminosBusqueda() {
    const termino = document.getElementById('nombre_producto').value.trim();
    if (!termino) return;
    
    const productCards = document.querySelectorAll('.product-title');
    productCards.forEach(card => {
        const texto = card.textContent;
        const regex = new RegExp(`(${termino})`, 'gi');
        if (regex.test(texto)) {
            card.innerHTML = texto.replace(regex, '<mark>$1</mark>');
        }
    });
}

/**
 * Muestra contador de resultados
 */
function mostrarContadorResultados() {
    const productos = document.querySelectorAll('.product-card');
    const contador = productos.length;
    
    // Buscar si ya existe un contador
    let contadorElement = document.querySelector('.results-counter');
    
    if (!contadorElement) {
        // Crear elemento contador si no existe
        contadorElement = document.createElement('div');
        contadorElement.className = 'results-counter';
        contadorElement.style.cssText = `
            background: #f3f4f6;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-weight: 500;
            color: #374151;
            border-left: 4px solid #2563eb;
        `;
        
        // Insertar antes de la grilla de productos
        const productsGrid = document.querySelector('.products-grid');
        if (productsGrid) {
            productsGrid.parentNode.insertBefore(contadorElement, productsGrid);
        }
    }
    
    // Actualizar texto del contador
    const texto = contador === 1 ? 'producto encontrado' : 'productos encontrados';
    contadorElement.innerHTML = `
        <i class="fas fa-info-circle me-2"></i>
        ${contador} ${texto}
    `;
}

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Productos Sucursal JS cargado correctamente');
    
    // Configurar eventos para el formulario de búsqueda
    const nombreInput = document.getElementById('nombre_producto');
    const sucursalSelect = document.getElementById('sucursal_filtro');
    const estadoSelect = document.getElementById('estado_filtro');
    
    // Evento Enter en campo de búsqueda
    if (nombreInput) {
        nombreInput.addEventListener('keypress', manejarEnterBusqueda);
    }
    
    // Eventos opcionales para filtrado automático (comentados por defecto)
    // if (sucursalSelect) {
    //     sucursalSelect.addEventListener('change', aplicarFiltroAutomatico);
    // }
    // if (estadoSelect) {
    //     estadoSelect.addEventListener('change', aplicarFiltroAutomatico);
    // }
    
    // Resaltar términos de búsqueda si hay alguno
    resaltarTerminosBusqueda();
    
    // Mostrar contador de resultados
    mostrarContadorResultados();
    
    // Agregar funcionalidad al botón de limpiar (si existe)
    const limpiarBtn = document.querySelector('.btn-outline-secondary');
    if (limpiarBtn && limpiarBtn.href && limpiarBtn.href.includes('productos_sucursal')) {
        limpiarBtn.addEventListener('click', function(e) {
            e.preventDefault();
            limpiarFiltros();
        });
    }
});