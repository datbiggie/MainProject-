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
    const busquedaInput = document.getElementById('busqueda');
    const filtroEstatus = document.getElementById('filtroEstatus');
    const contenedorCategorias = document.querySelector('.d-flex.flex-wrap.justify-content-center.gap-3.w-100');
    
    // Función para filtrar categorías usando la API del servidor
    function filtrarCategorias() {
        const textoBusqueda = busquedaInput.value.trim();
        const estatusFiltro = filtroEstatus.value;
        
        // Construir URL con parámetros de filtro
        const url = `/ecommerce/api/filtrar_categorias_producto/?nombre=${encodeURIComponent(textoBusqueda)}&estatus=${encodeURIComponent(estatusFiltro)}`;
        
        // Realizar la solicitud a la API
        fetch(url)
            .then(response => response.json())
            .then(data => {
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
                        const editButtons = canEdit ? `
                            <div class="btn-group" role="group">
                                <button class="btn btn-primary btn-edit btn-sm px-2 py-1" style="font-size:0.9rem;" onclick="abrirModalEditar('${id}', '${(nombre || '').replace(/'/g, "\'")}', '${(descripcion || '').replace(/'/g, "\'")}', '${(estatus || '').replace(/'/g, "\'")}')">
                                    <i class="lni lni-pencil"></i> Editar
                                </button>
                                <button class="btn btn-danger btn-delete btn-sm px-2 py-1" style="font-size:0.9rem;" onclick="confirmarEliminacion('${id}')">
                                    <i class="lni lni-trash"></i> Eliminar
                                </button>
                            </div>
                        ` : '<small class="text-muted">Sin permisos</small>';

                        const categoriaHTML = `
                        <div class="col-md-6 col-lg-4 mb-3">
                            <div class="card h-100 shadow-sm" style="border-radius: 1rem; border: none; transition: transform 0.2s;">
                                <div class="card-body d-flex flex-column">
                                    <h5 class="card-title fw-bold mb-2" style="color: #2c3e50;">${nombre}</h5>
                                    <p class="card-text text-muted mb-3 flex-grow-1">${descripcion}</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge ${estatus === 'Activo' ? 'bg-success' : 'bg-secondary'}" style="font-size: 0.85rem;">${estatus}</span>
                                        ${editButtons}
                                    </div>
                                </div>
                            </div>
                        </div>
                        `;
                        contenedorCategorias.innerHTML += categoriaHTML;
                    });
                } else {
                    console.error('Error al filtrar categorías:', data.message);
                    contenedorCategorias.innerHTML = '<div class="text-center w-100 py-4"><p>Error al cargar las categorías.</p></div>';
                }
            })
            .catch(error => {
                console.error('Error en la solicitud:', error);
                contenedorCategorias.innerHTML = '<div class="text-center w-100 py-4"><p>Error al cargar las categorías.</p></div>';
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