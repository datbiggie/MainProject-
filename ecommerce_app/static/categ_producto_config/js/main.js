// Archivo JavaScript limpio para categ_producto_config
// Solo contiene funciones auxiliares que no interfieren con el template

// Definir URL de eliminación
window.DELETE_URL = '/ecommerce/eliminar_categoria_producto/';

// Función para gestionar atributos de categoría
function verDetalles(idCategoria) {
    console.log('Gestionar atributos de categoría ID:', idCategoria);
    
    try {
        // Validar que el ID no sea nulo o vacío
        if (!idCategoria || idCategoria === 'null' || idCategoria === 'undefined' || idCategoria === '') {
            console.error('ID de categoría inválido:', idCategoria);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'ID de categoría inválido.',
                confirmButtonColor: '#d33',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        console.log('Llamando a cargarAtributosCategoria con ID:', idCategoria);
        // Cargar atributos de la categoría
        cargarAtributosCategoria(idCategoria);
    } catch (error) {
        console.error('Error en verDetalles:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error inesperado: ' + error.message,
            confirmButtonColor: '#d33'
        });
    }
}

// Función para cargar atributos de una categoría
function cargarAtributosCategoria(categoriaId) {
    try {
        console.log('Iniciando carga de atributos para categoría:', categoriaId);
        console.log('SweetAlert2 disponible:', typeof Swal !== 'undefined');
        
        // Obtener el token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                         window.CSRF_TOKEN;
        
        fetch(`/ecommerce/obtener_atributos_categoria/?id_categoria=${categoriaId}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
            .then(response => {
                console.log('Respuesta recibida:', response.status, response.statusText);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Datos recibidos:', data);
                if (data.success) {
                    console.log('Llamando a mostrarModalGestionAtributos');
                    mostrarModalGestionAtributos(categoriaId, data.atributos);
                } else {
                    console.error('Error en respuesta:', data.message);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message || 'Error al cargar atributos',
                        confirmButtonColor: '#d33'
                    });
                }
            })
            .catch(error => {
                console.error('Error en fetch:', error);
                let errorMessage = 'Error de conexión al cargar atributos';
                if (error.message.includes('401')) {
                    errorMessage = 'Sesión expirada. Por favor, inicia sesión nuevamente.';
                } else if (error.message.includes('403')) {
                    errorMessage = 'No tienes permisos para realizar esta acción.';
                } else if (error.message.includes('404')) {
                    errorMessage = 'Endpoint no encontrado. Verifica la configuración.';
                } else if (error.message.includes('500')) {
                    errorMessage = 'Error interno del servidor. Contacta al administrador.';
                }
                
                Swal.fire({
                    icon: 'error',
                    title: 'Error de Conexión',
                    text: errorMessage,
                    confirmButtonColor: '#d33',
                    footer: `<small>Detalles técnicos: ${error.message}</small>`
                });
            });
    } catch (error) {
        console.error('Error crítico en cargarAtributosCategoria:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error Crítico',
            text: 'Error inesperado: ' + error.message,
            confirmButtonColor: '#d33'
        });
    }
}

// Función para mostrar el modal de gestión de atributos
function mostrarModalGestionAtributos(categoriaId, atributos) {
    console.log('Ejecutando mostrarModalGestionAtributos con:', categoriaId, atributos);
    // Establecer el ID de categoría actual
    setCurrentCategoriaId(categoriaId);
    
    const atributosHtml = generarHtmlAtributos(atributos);
    console.log('HTML generado:', atributosHtml);
    
    try {
        console.log('Intentando abrir modal con SweetAlert2...');
        console.log('Swal object:', Swal);
        
        Swal.fire({
            title: '<div class="modal-title-enhanced"><i class="lni lni-cog"></i> Gestión de Atributos de Categoría</div>',
            html: `
                <div class="atributos-container-enhanced">
                    <div class="atributos-header-enhanced">
                        <div class="header-info">
                            <p class="mb-3 text-muted">Administra los atributos específicos que definen esta categoría de productos</p>
                        </div>
                        <div class="header-actions">
                            <button type="button" class="btn-agregar-atributo-enhanced" onclick="mostrarFormularioAgregarAtributo(${categoriaId})">
                                <i class="lni lni-plus"></i>
                                <span>Agregar Nuevo Atributo</span>
                            </button>
                        </div>
                    </div>
                    <div class="atributos-content">
                        <div class="atributos-lista-enhanced" id="atributos-lista">
                            ${atributosHtml}
                        </div>
                    </div>
                </div>
            `,
            width: '900px',
            showConfirmButton: false,
            showCloseButton: true,
            customClass: {
                container: 'modal-atributos-container-enhanced',
                popup: 'modal-atributos-popup-enhanced'
            }
        }).then(() => {
            console.log('Modal abierto exitosamente');
        }).catch(error => {
            console.error('Error al abrir modal:', error);
        });
    } catch (error) {
        console.error('Error crítico en mostrarModalGestionAtributos:', error);
        alert('Error al abrir el modal: ' + error.message);
    }
}

// Función para generar HTML de la lista de atributos
function generarHtmlAtributos(atributos) {
    console.log('Generando HTML para atributos:', atributos);
    
    if (!atributos || atributos.length === 0) {
        return `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="lni lni-inbox"></i>
                </div>
                <h4>No hay atributos configurados</h4>
                <p class="text-muted">Esta categoría aún no tiene atributos específicos definidos.</p>
                <p class="text-muted small">Utiliza el botón "Agregar Nuevo Atributo" para comenzar.</p>
            </div>
        `;
    }
    
    let html = `
        <div class="atributos-table-container">
            <div class="table-header">
                <h5 class="mb-0">Atributos Configurados (${atributos.length})</h5>
            </div>
            <div class="table-responsive-enhanced">
                <table class="atributos-table-enhanced">
                    <thead>
                        <tr>
                            <th class="col-nombre">Nombre del Atributo</th>
                            <th class="col-tipo">Tipo de Dato</th>
                            <th class="col-obligatorio">Obligatorio</th>
                            <th class="col-descripcion">Descripción</th>
                            <th class="col-acciones">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    atributos.forEach((atributo, index) => {
        html += `
            <tr class="atributo-row" data-index="${index}">
                <td class="col-nombre">
                    <div class="atributo-nombre">
                        <strong>${atributo.nombre}</strong>
                    </div>
                </td>
                <td class="col-tipo">
                    <span class="tipo-badge tipo-${(atributo.tipo_dato || '').toString().toLowerCase()}">${atributo.tipo_dato || 'N/A'}</span>
                </td>
                <td class="col-obligatorio">
                    <div class="obligatorio-indicator">
                        <span class="badge-obligatorio ${atributo.obligatorio ? 'obligatorio-si' : 'obligatorio-no'}">
                            ${atributo.obligatorio ? '<i class="lni lni-checkmark"></i> Sí' : '<i class="lni lni-close"></i> No'}
                        </span>
                    </div>
                </td>
                <td class="col-descripcion">
                    <span class="descripcion-text">${atributo.descripcion || '-'}</span>
                </td>
                <td class="col-acciones">
                    <div class="acciones-group">
                        <button type="button" class="btn-accion btn-editar" onclick="editarAtributo(${atributo.id_categoria_atributo})" title="Editar atributo">
                            <i class="lni lni-pencil"></i>
                        </button>
                        <button type="button" class="btn-accion btn-eliminar" onclick="eliminarAtributo(${atributo.id_categoria_atributo})" title="Eliminar atributo">
                            <i class="lni lni-trash-can"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

// Función para mostrar formulario de agregar atributo
function mostrarFormularioAgregarAtributo(categoriaId) {
    Swal.fire({
        title: 'Agregar Nuevo Atributo',
        html: `
            <form id="form-agregar-atributo">
                <div class="mb-3">
                    <label class="form-label">Nombre del Atributo</label>
                    <input type="text" class="form-control" id="nombre-atributo" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Tipo de Dato</label>
                    <select class="form-control" id="tipo-dato" required>
                        <option value="">Seleccionar tipo</option>
                        <option value="texto">Texto</option>
                        <option value="numero">Número</option>
                        <option value="decimal">Decimal</option>
                        <option value="fecha">Fecha</option>
                        <option value="booleano">Booleano</option>
                        <option value="lista">Lista de opciones</option>
                    </select>
                </div>
                <div class="mb-3" id="opciones-container" style="display: none;">
                    <label class="form-label">Opciones (separadas por coma)</label>
                    <input type="text" class="form-control" id="opciones" placeholder="Opción1, Opción2, Opción3">
                </div>
                <div class="mb-3">
                    <label class="form-label">Descripción</label>
                    <textarea class="form-control" id="descripcion" rows="2"></textarea>
                </div>
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="obligatorio">
                        <label class="form-check-label" for="obligatorio">
                            Campo obligatorio
                        </label>
                    </div>
                </div>
            </form>
        `,
        showCancelButton: true,
        confirmButtonText: 'Agregar',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            const nombre = document.getElementById('nombre-atributo').value;
            const tipoDato = document.getElementById('tipo-dato').value;
            const opciones = document.getElementById('opciones').value;
            const descripcion = document.getElementById('descripcion').value;
            const obligatorio = document.getElementById('obligatorio').checked;
            
            if (!nombre || !tipoDato) {
                Swal.showValidationMessage('Nombre y tipo de dato son requeridos');
                return false;
            }
            
            return {
                categoria_id: categoriaId,
                nombre: nombre,
                tipo_dato: tipoDato,
                opciones: tipoDato === 'lista' ? opciones.split(',').map(o => o.trim()) : null,
                descripcion: descripcion,
                obligatorio: obligatorio
            };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            agregarAtributo(result.value);
        }
    });
    
    // Mostrar/ocultar campo de opciones según el tipo
    document.getElementById('tipo-dato').addEventListener('change', function() {
        const opcionesContainer = document.getElementById('opciones-container');
        if (this.value === 'lista') {
            opcionesContainer.style.display = 'block';
        } else {
            opcionesContainer.style.display = 'none';
        }
    });
}

// Función para agregar atributo
function agregarAtributo(datosAtributo) {
    fetch('/ecommerce/api/agregar_atributo_categoria/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.CSRF_TOKEN
        },
        body: JSON.stringify(datosAtributo)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Éxito',
                text: data.message,
                timer: 2000
            }).then(() => {
                cargarAtributosCategoria(datosAtributo.categoria_id);
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexión'
        });
    });
}

// Función para editar atributo
function editarAtributo(idCategoriaAtributo) {
    // Primero obtener los datos actuales del atributo
    fetch(`/ecommerce/api/obtener_atributos_categoria/?id_categoria_atributo=${idCategoriaAtributo}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.atributo) {
                mostrarFormularioEditarAtributo(data.atributo);
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo cargar la información del atributo'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Error de conexión'
            });
        });
}

// Función para mostrar formulario de editar atributo
function mostrarFormularioEditarAtributo(atributo) {
    const opcionesValue = atributo.opciones ? atributo.opciones.join(', ') : '';
    
    Swal.fire({
        title: 'Editar Atributo',
        html: `
            <form id="form-editar-atributo">
                <div class="mb-3">
                    <label class="form-label">Nombre del Atributo</label>
                    <input type="text" class="form-control" id="nombre-atributo-edit" value="${atributo.nombre}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Tipo de Dato</label>
                    <select class="form-control" id="tipo-dato-edit" required>
                        <option value="">Seleccionar tipo</option>
                        <option value="texto" ${atributo.tipo_dato === 'texto' ? 'selected' : ''}>Texto</option>
                        <option value="numero" ${atributo.tipo_dato === 'numero' ? 'selected' : ''}>Número</option>
                        <option value="decimal" ${atributo.tipo_dato === 'decimal' ? 'selected' : ''}>Decimal</option>
                        <option value="fecha" ${atributo.tipo_dato === 'fecha' ? 'selected' : ''}>Fecha</option>
                        <option value="booleano" ${atributo.tipo_dato === 'booleano' ? 'selected' : ''}>Booleano</option>
                        <option value="lista" ${atributo.tipo_dato === 'lista' ? 'selected' : ''}>Lista de opciones</option>
                    </select>
                </div>
                <div class="mb-3" id="opciones-container-edit" style="display: ${atributo.tipo_dato === 'lista' ? 'block' : 'none'};">
                    <label class="form-label">Opciones (separadas por coma)</label>
                    <input type="text" class="form-control" id="opciones-edit" value="${opcionesValue}" placeholder="Opción1, Opción2, Opción3">
                </div>
                <div class="mb-3">
                    <label class="form-label">Descripción</label>
                    <textarea class="form-control" id="descripcion-edit" rows="2">${atributo.descripcion || ''}</textarea>
                </div>
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="obligatorio-edit" ${atributo.obligatorio ? 'checked' : ''}>
                        <label class="form-check-label" for="obligatorio-edit">
                            Campo obligatorio
                        </label>
                    </div>
                </div>
            </form>
        `,
        showCancelButton: true,
        confirmButtonText: 'Guardar Cambios',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            const nombre = document.getElementById('nombre-atributo-edit').value;
            const tipoDato = document.getElementById('tipo-dato-edit').value;
            const opciones = document.getElementById('opciones-edit').value;
            const descripcion = document.getElementById('descripcion-edit').value;
            const obligatorio = document.getElementById('obligatorio-edit').checked;
            
            if (!nombre || !tipoDato) {
                Swal.showValidationMessage('Nombre y tipo de dato son requeridos');
                return false;
            }
            
            return {
                id_categoria_atributo: atributo.id_categoria_atributo,
                nombre: nombre,
                tipo_dato: tipoDato,
                opciones: tipoDato === 'lista' ? opciones.split(',').map(o => o.trim()) : null,
                descripcion: descripcion,
                obligatorio: obligatorio
            };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            modificarAtributo(result.value);
        }
    });
    
    // Mostrar/ocultar campo de opciones según el tipo
    document.getElementById('tipo-dato-edit').addEventListener('change', function() {
        const opcionesContainer = document.getElementById('opciones-container-edit');
        if (this.value === 'lista') {
            opcionesContainer.style.display = 'block';
        } else {
            opcionesContainer.style.display = 'none';
        }
    });
}

// Función para modificar atributo
function modificarAtributo(datosAtributo) {
    fetch('/ecommerce/api/modificar_atributo_categoria/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.CSRF_TOKEN
        },
        body: JSON.stringify(datosAtributo)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Éxito',
                text: data.message,
                timer: 2000
            }).then(() => {
                // Recargar la lista de atributos
                const categoriaId = getCurrentCategoriaId();
                if (categoriaId) {
                    cargarAtributosCategoria(categoriaId);
                }
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexión'
        });
    });
}

// Función para eliminar atributo
function eliminarAtributo(idCategoriaAtributo) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: '¿Deseas eliminar este atributo de la categoría?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/ecommerce/api/eliminar_atributo_categoria/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN
                },
                body: JSON.stringify({
                    id_categoria_atributo: idCategoriaAtributo
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Eliminado',
                        text: data.message,
                        timer: 2000
                    }).then(() => {
                        // Recargar la lista de atributos
                        const categoriaId = getCurrentCategoriaId();
                        if (categoriaId) {
                            cargarAtributosCategoria(categoriaId);
                        }
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Error de conexión'
                });
            });
        }
    });
}

// Variable global para almacenar el ID de categoría actual
let currentCategoriaId = null;

// Función auxiliar para obtener el ID de categoría actual
function getCurrentCategoriaId() {
    return currentCategoriaId;
}

// Función para establecer el ID de categoría actual
function setCurrentCategoriaId(categoriaId) {
    currentCategoriaId = categoriaId;
}

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