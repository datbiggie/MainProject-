/**
 * Filtrado en tiempo real para categorías de productos
 * Este script maneja la búsqueda y filtrado de categorías de productos en tiempo real
 */
document.addEventListener('DOMContentLoaded', function() {
    const busquedaInput = document.getElementById('busqueda');
    const filtroEstatus = document.getElementById('filtroEstatus');
    const contenedorCategorias = document.querySelector('.d-flex.flex-wrap.justify-content-center.gap-3.w-100');
    
    // Función para filtrar categorías usando la API
    function filtrarCategorias() {
        const textoBusqueda = busquedaInput.value.trim();
        const estatusFiltro = filtroEstatus.value;
        
        // Método 1: Filtrado del lado del cliente (más rápido para conjuntos pequeños de datos)
        const categorias = document.querySelectorAll('.d-flex.flex-wrap.justify-content-center.gap-3.w-100 > div');
        
        categorias.forEach(categoria => {
            const nombreCategoria = categoria.querySelector('h3').textContent.toLowerCase();
            const estatusCategoria = categoria.getAttribute('data-estatus');
            
            // Verificar si cumple con ambos filtros
            const coincideTexto = nombreCategoria.includes(textoBusqueda.toLowerCase());
            const coincideEstatus = estatusFiltro === 'todos' || estatusCategoria === estatusFiltro;
            
            // Mostrar u ocultar según los filtros
            if (coincideTexto && coincideEstatus) {
                categoria.style.display = 'block';
            } else {
                categoria.style.display = 'none';
            }
        });
        
        // Método 2: Filtrado del lado del servidor (comentado, pero disponible si se prefiere)
        /*
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
                        const categoriaHTML = `
                        <div class="card shadow-sm bg-white wow fadeInUp" data-wow-delay=".2s" data-estatus="${categoria.estatus_categoria_prod}" style="max-width:300px; min-width:200px; width:100%; border-radius: 0.7rem;">
                            <div class="card-body p-2 d-flex flex-row align-items-center h-100" style="gap: 0.7rem; min-height: 90px;">
                                <div class="d-flex flex-column align-items-center justify-content-center" style="min-width:48px; max-width:60px;">
                                    <div style="width:38px; height:38px; background:#e9ecef; border-radius:0.4rem; display:flex; align-items:center; justify-content:center; color:#0d6efd; font-size:1.3rem;">
                                        <i class="lni lni-folder"></i>
                                    </div>
                                </div>
                                <div style="border-left:1px solid #dee2e6; height:45px; margin-right:0.7rem;"></div>
                                <div class="flex-grow-1 d-flex flex-column align-items-center justify-content-between h-100">
                                    <h3 class="mb-2 fs-6 text-center w-100" style="margin-top: 6px; font-size: 1rem;">${categoria.nombre_categoria_prod}</h3>
                                    <div class="d-flex gap-1" style="margin-top:auto;">
                                        <button class="btn btn-primary btn-edit btn-sm px-2 py-1" style="font-size:0.9rem;" onclick="abrirModalEditar('${categoria.id_categoria_prod}', '${categoria.nombre_categoria_prod.replace(/'/g, "\\'").replace(/"/g, '\\"')}', '${(categoria.descripcion_categoria_prod || '').replace(/'/g, "\\'").replace(/"/g, '\\"')}', '${categoria.estatus_categoria_prod}')">
                                            <i class="lni lni-pencil"></i> Editar
                                        </button>
                                        <button class="btn btn-danger btn-delete btn-sm px-2 py-1" style="font-size:0.9rem;" onclick="confirmarEliminacion('${categoria.id_categoria_prod}')">
                                            <i class="lni lni-trash"></i> Eliminar
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        `;
                        contenedorCategorias.innerHTML += categoriaHTML;
                    });
                } else {
                    console.error('Error al filtrar categorías:', data.message);
                }
            })
            .catch(error => {
                console.error('Error en la solicitud:', error);
            });
        */
    }
    
    // Configurar un pequeño retraso para evitar demasiadas solicitudes durante la escritura
    let timeoutId;
    busquedaInput.addEventListener('input', function() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(filtrarCategorias, 300);
    });
    
    // Filtrar inmediatamente al cambiar el select
    filtroEstatus.addEventListener('change', filtrarCategorias);
});