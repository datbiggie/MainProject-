/**
 * Filtrado en tiempo real para categorías de productos
 * Este script maneja la búsqueda y filtrado de categorías de productos en tiempo real
 */
// Función para verificar si el usuario puede editar una categoría
function canUserEditCategory(categoria, userInfo) {
    if (!userInfo || !userInfo.is_authenticated) {
        return false;
    }
    
    const accountType = userInfo.account_type;
    const userId = userInfo.user_id;
    
    // Si es empresa, puede editar categorías de empresa
    if (accountType === 'empresa') {
        return categoria.hasOwnProperty('id_categoria_prod_empresa');
    }
    
    // Si es usuario, puede editar categorías de usuario
    if (accountType === 'usuario') {
        return categoria.hasOwnProperty('id_categoria_prod_usuario');
    }
    
    return false;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== FILTRADO.JS INICIADO ===');
    const busquedaInput = document.getElementById('busqueda');
    const filtroEstatus = document.getElementById('filtroEstatus');
    const contenedorCategorias = document.querySelector('.category-grid');
    
    console.log('Elementos encontrados:');
    console.log('- busquedaInput:', busquedaInput);
    console.log('- filtroEstatus:', filtroEstatus);
    console.log('- contenedorCategorias:', contenedorCategorias);
    
    // Función para filtrar categorías usando la API del servidor
    function filtrarCategorias() {
        console.log('=== EJECUTANDO FILTRADO ===');
        // Verificar que el contenedor existe
        if (!contenedorCategorias) {
            console.error('Contenedor de categorías no encontrado');
            return;
        }
        
        const textoBusqueda = busquedaInput ? busquedaInput.value.trim() : '';
        const estatusFiltro = filtroEstatus ? filtroEstatus.value : '';
        
        console.log('Parámetros de filtrado:');
        console.log('- textoBusqueda:', textoBusqueda);
        console.log('- estatusFiltro:', estatusFiltro);
        
        // Construir URL con parámetros de filtro
        const url = `/ecommerce/api/filtrar_categorias_producto/?nombre=${encodeURIComponent(textoBusqueda)}&estatus=${encodeURIComponent(estatusFiltro)}`;
        console.log('URL de la API:', url);
        
        // Realizar la solicitud a la API
        fetch(url, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': window.CSRF_TOKEN
            }
        })
            .then(response => {
                console.log('Respuesta de la API:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Datos recibidos de la API:', data);
                if (data.success) {
                    // Limpiar el contenedor
                    contenedorCategorias.innerHTML = '';
                    
                    // Si no hay resultados
                    if (data.categorias.length === 0) {
                        contenedorCategorias.innerHTML = '<div class="text-center w-100 py-4"><p>No se encontraron categorías con los filtros seleccionados.</p></div>';
                        return;
                    }
                    
                    // Generar HTML para cada categoría
                    data.categorias.forEach(categoria => {
                        // Determinar qué campos usar basándose en la estructura de datos
                        const isEmpresa = categoria.hasOwnProperty('id_categoria_prod_empresa');
                        const id = isEmpresa ? categoria.id_categoria_prod_empresa : categoria.id_categoria_prod_usuario;
                        const nombre = isEmpresa ? (categoria.nombre_categoria_prod_empresa || '') : (categoria.nombre_categoria_prod_usuario || '');
                        const descripcion = isEmpresa ? (categoria.descripcion_categoria_prod_empresa || '') : (categoria.descripcion_categoria_prod_usuario || '');
                        const estatus = isEmpresa ? categoria.estatus_categoria_prod_empresa : categoria.estatus_categoria_prod_usuario;
                        
                        // Verificar permisos para mostrar botones
                        const canEdit = canUserEditCategory(categoria, window.USER_INFO);
                        const actionButtons = canEdit ? `
                                <button class="action-btn btn-edit" onclick="abrirModalEditar('${id}', '${(nombre || '').replace(/'/g, "\\'")}', '${(descripcion || '').replace(/'/g, "\\'")}', '${(estatus || '').replace(/'/g, "\\'")}')" data-tooltip="Editar categoría">
                                    <i class="lni lni-pencil"></i>
                                </button>
                                <button class="action-btn btn-delete" onclick="confirmarEliminacion('${id}')" data-tooltip="Eliminar categoría">
                                    <i class="lni lni-trash-can"></i>
                                </button>
                                <button class="action-btn btn-info" onclick="verDetalles('${id}')" data-tooltip="Ver detalles">
                                    <i class="lni lni-eye"></i>
                                </button>
                        ` : '<small class="text-muted">Sin permisos</small>';

                        const categoriaHTML = `
                        <div class="category-card animate-card" data-nombre="${(nombre || '').toString().toLowerCase()}" data-estatus="${(estatus || '').toString().toLowerCase()}" data-type="${isEmpresa ? 'empresa' : 'usuario'}">
                            <div class="category-icon">
                                <i class="lni lni-cog"></i>
                            </div>
                            <div class="category-content">
                                <h3 class="category-title">${nombre}</h3>
                                <div class="category-meta">
                                    <span class="status-badge ${estatus === 'Activo' ? 'status-active' : 'status-inactive'}">${estatus === 'Activo' ? '✅ Activa' : '⏸️ Inactiva'}</span>
                                    <span class="category-type">${isEmpresa ? '🏢 Empresa' : '👤 Usuario'}</span>
                                </div>
                            </div>
                            <div class="category-actions">
                                 ${actionButtons}
                             </div>
                        </div>
                        `;
                        contenedorCategorias.innerHTML += categoriaHTML;
                    });
                } else {
                    console.error('Error al filtrar categorías:', data.message);
                    if (contenedorCategorias) {
                        contenedorCategorias.innerHTML = '<div class="text-center w-100 py-4"><p>Error al cargar las categorías.</p></div>';
                    }
                }
            })
            .catch(error => {
                console.error('Error en la solicitud:', error);
                if (contenedorCategorias) {
                    contenedorCategorias.innerHTML = '<div class="text-center w-100 py-4"><p>Error al cargar las categorías.</p></div>';
                }
            });
    }
    
    // Event listeners para filtrado en tiempo real
    if (busquedaInput) {
        busquedaInput.addEventListener('input', filtrarCategorias);
    }
    
    if (filtroEstatus) {
        filtroEstatus.addEventListener('change', filtrarCategorias);
    }
    
    // Ejecutar filtrado inicial para mostrar todas las categorías
    filtrarCategorias();
});