/**
 * Filtrado en tiempo real para categorías de servicios
 * Este script maneja la búsqueda y filtrado de categorías de servicios en tiempo real
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
        return categoria.hasOwnProperty('id_categoria_serv_empresa');
    }
    
    // Si es usuario, puede editar categorías de usuario
    if (accountType === 'usuario') {
        return categoria.hasOwnProperty('id_categoria_serv_usuario');
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
        const url = `/ecommerce/api/filtrar_categorias_servicio/?nombre=${encodeURIComponent(textoBusqueda)}&estatus=${encodeURIComponent(estatusFiltro)}`;
        
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
                        const isEmpresa = categoria.hasOwnProperty('id_categoria_serv_empresa');
                        const id = isEmpresa ? categoria.id_categoria_serv_empresa : categoria.id_categoria_serv_usuario;
                        const nombre = isEmpresa ? (categoria.nombre_categoria_serv_empresa || '') : (categoria.nombre_categoria_serv_usuario || '');
                        const descripcion = isEmpresa ? (categoria.descripcion_categoria_serv_empresa || '') : (categoria.descripcion_categoria_serv_usuario || '');
                        const estatus = isEmpresa ? categoria.estatus_categoria_serv_empresa : categoria.estatus_categoria_serv_usuario;
                        
                        // Verificar permisos para mostrar botones
                        const canEdit = canUserEditCategory(categoria, window.USER_INFO);
                        const editButtons = canEdit ? `
                            <div class="btn-group" role="group">
                                <button class="btn btn-primary btn-edit btn-sm px-2 py-1" style="font-size:0.9rem;" onclick="abrirModalEditar('${id}', '${(nombre || '').replace(/'/g, "\\'")}', '${(descripcion || '').replace(/'/g, "\\'")}', '${(estatus || '').replace(/'/g, "\\'")}')">
                                    <i class="lni lni-pencil"></i> Editar
                                </button>
                                <button class="btn btn-danger btn-delete btn-sm px-2 py-1" style="font-size:0.9rem;" onclick="confirmarEliminacion('${id}')">
                                    <i class="lni lni-trash"></i> Eliminar
                                </button>
                            </div>
                        ` : `
                            <div class="text-muted small" style="font-size:0.8rem;">
                                Sin permisos
                            </div>
                        `;
                        
                        const categoriaHTML = `
                        <div class="col-md-6 col-lg-4 mb-3">
                            <div class="card shadow-sm bg-white wow fadeInUp" data-wow-delay=".2s" data-estatus="${estatus}" style="border-radius: 0.7rem; height: 100%;">
                                <div class="card-body p-3 d-flex flex-column h-100">
                                    <div class="d-flex align-items-center mb-3">
                                        <div style="width:40px; height:40px; background:#e9ecef; border-radius:0.4rem; display:flex; align-items:center; justify-content:center; color:#0d6efd; font-size:1.2rem; margin-right: 12px;">
                                            <i class="lni lni-folder"></i>
                                        </div>
                                        <div class="flex-grow-1">
                                            <h5 class="mb-1 fs-6">${nombre}</h5>
                                            <small class="text-muted">Estado: ${estatus}</small>
                                        </div>
                                    </div>
                                    <div class="mt-auto d-flex justify-content-center">
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