/**
 * Funciones JavaScript para la gestión de servicios por sucursal
 */

/**
 * Abre el modal de edición con los datos del servicio
 * @param {HTMLElement} button - Elemento botón que contiene los datos en atributos data-*
 */
function editarServicio(button) {
    const id = button.getAttribute('data-id');
    const precio = button.getAttribute('data-precio');
    const estatus = button.getAttribute('data-estatus');
    
    document.getElementById('editServicioId').value = id;
    document.getElementById('editPrecio').value = precio;
    document.getElementById('editEstatus').value = estatus;
    
    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

/**
 * Guarda los cambios realizados en el modal de edición
 */
function guardarCambios() {
    const id = document.getElementById('editServicioId').value;
    const precio = document.getElementById('editPrecio').value;
    const estatus = document.getElementById('editEstatus').value;
    
    // Validaciones básicas
    if (!precio || precio < 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Precio inválido',
            text: 'El precio no puede ser negativo',
            confirmButtonColor: '#2563eb'
        });
        return;
    }
    
    // Mostrar loading
    Swal.fire({
        title: 'Guardando cambios...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    // Preparar datos para envío
    const formData = new FormData();
    formData.append('id', id);
    formData.append('precio', precio);
    formData.append('estatus', estatus);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    // Realizar petición AJAX
    fetch('/ecommerce/editar_servicio_sucursal/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: 'Servicio actualizado correctamente',
                confirmButtonColor: '#2563eb'
            }).then(() => {
                // Cerrar modal y recargar página
                const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
                modal.hide();
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
            text: 'Error al guardar los cambios. Inténtalo de nuevo.',
            confirmButtonColor: '#dc3545'
        });
    });
}

/**
 * Elimina un servicio de la sucursal
 * @param {HTMLElement} button - Elemento botón que contiene los datos en atributos data-*
 */
function eliminarServicio(button) {
    const id = button.getAttribute('data-id');
    const nombre = button.getAttribute('data-nombre');
    
    Swal.fire({
        title: '¿Estás seguro?',
        text: `¿Deseas eliminar el servicio "${nombre}" de esta sucursal?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Mostrar loading
            Swal.fire({
                title: 'Eliminando servicio...',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Preparar datos para envío
            const formData = new FormData();
            formData.append('id', id);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            
            // Realizar petición AJAX
            fetch('/ecommerce/eliminar_servicio_sucursal/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Eliminado!',
                        text: 'El servicio ha sido eliminado correctamente',
                        confirmButtonColor: '#2563eb'
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
                    text: 'Error al eliminar el servicio. Inténtalo de nuevo.',
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
    document.getElementById('nombre_servicio').value = '';
    document.getElementById('sucursal_filtro').value = '';
    document.getElementById('estado_filtro').value = '';
    
    // Enviar formulario automáticamente para mostrar todos los servicios
    document.querySelector('.search-form').submit();
}

/**
 * Maneja el evento Enter en el campo de búsqueda
 * @param {Event} event - Evento de teclado
 */
function manejarEnterBusqueda(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        document.querySelector('.search-form').submit();
    }
}

/**
 * Aplica filtros automáticamente cuando cambian los selects
 */
function aplicarFiltroAutomatico() {
    // Opcional: aplicar filtros automáticamente
    // document.querySelector('.search-form').submit();
}

/**
 * Resalta los términos de búsqueda en los resultados
 */
function resaltarTerminosBusqueda() {
    const nombreInput = document.getElementById('nombre_servicio');
    if (!nombreInput || !nombreInput.value.trim()) return;
    
    const termino = nombreInput.value.trim().toLowerCase();
    const serviceTitles = document.querySelectorAll('.service-title');
    
    serviceTitles.forEach(title => {
        const texto = title.textContent;
        const textoLower = texto.toLowerCase();
        
        if (textoLower.includes(termino)) {
            const regex = new RegExp(`(${termino})`, 'gi');
            const textoResaltado = texto.replace(regex, '<mark style="background: #fef08a; padding: 0.1em 0.2em; border-radius: 3px;">$1</mark>');
            title.innerHTML = textoResaltado;
        }
    });
}

/**
 * Muestra contador de resultados
 */
function mostrarContadorResultados() {
    const servicios = document.querySelectorAll('.service-card');
    const contador = servicios.length;
    
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
        
        // Insertar antes de la grilla de servicios
        const servicesGrid = document.querySelector('.services-grid');
        if (servicesGrid) {
            servicesGrid.parentNode.insertBefore(contadorElement, servicesGrid);
        }
    }
    
    // Actualizar texto del contador
    const texto = contador === 1 ? 'servicio encontrado' : 'servicios encontrados';
    contadorElement.innerHTML = `
        <i class="fas fa-info-circle me-2"></i>
        ${contador} ${texto}
    `;
}

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Servicios Sucursal JS cargado correctamente');
    
    // Configurar eventos para el formulario de búsqueda
    const nombreInput = document.getElementById('nombre_servicio');
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
    if (limpiarBtn && limpiarBtn.href && limpiarBtn.href.includes('servicios_sucursal')) {
        limpiarBtn.addEventListener('click', function(e) {
            e.preventDefault();
            limpiarFiltros();
        });
    }
});

/**
 * Funciones adicionales para servicios
 */

/**
 * Formatea la duración del servicio
 * @param {string} duracion - Duración en formato texto
 * @returns {string} Duración formateada
 */
function formatearDuracion(duracion) {
    if (!duracion) return 'No especificada';
    
    // Convertir minutos a formato legible
    const minutos = parseInt(duracion);
    if (!isNaN(minutos)) {
        if (minutos < 60) {
            return `${minutos} min`;
        } else {
            const horas = Math.floor(minutos / 60);
            const minutosRestantes = minutos % 60;
            return minutosRestantes > 0 ? `${horas}h ${minutosRestantes}min` : `${horas}h`;
        }
    }
    
    return duracion;
}

/**
 * Valida los datos del formulario de edición
 * @returns {boolean} True si los datos son válidos
 */
function validarFormularioEdicion() {
    const precio = document.getElementById('editPrecio').value;
    const estatus = document.getElementById('editEstatus').value;
    
    if (!precio || precio < 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Precio inválido',
            text: 'El precio no puede ser negativo',
            confirmButtonColor: '#2563eb'
        });
        return false;
    }
    
    if (!estatus) {
        Swal.fire({
            icon: 'warning',
            title: 'Estado requerido',
            text: 'Debe seleccionar un estado para el servicio',
            confirmButtonColor: '#2563eb'
        });
        return false;
    }
    
    return true;
}