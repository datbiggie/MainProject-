// filtrado.js para productos - búsqueda y filtrado con peticiones al servidor

document.addEventListener('DOMContentLoaded', function() {
    const busquedaInput = document.getElementById('busqueda-producto');
    const contenedorProductos = document.getElementById('contenedor-productos');
    let estadoActual = 'todos';

    if (!busquedaInput || !contenedorProductos) return;

    let timeout = null;
    busquedaInput.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            filtrarProductos();
        }, 350);
    });



    function filtrarProductos() {
        const textoBusqueda = busquedaInput.value.trim();
        let url = `/ecommerce/api/filtrar_productos/?nombre=${encodeURIComponent(textoBusqueda)}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    contenedorProductos.innerHTML = '';
                    if (data.productos.length === 0) {
                        contenedorProductos.innerHTML = '<div class="text-center w-100 py-4"><p>No se encontraron productos.</p></div>';
                        return;
                    }
                    data.productos.forEach(producto => {
                        // Determinar si es producto de empresa o usuario
                        const esEmpresa = producto.hasOwnProperty('id_producto_empresa');
                        const esUsuario = producto.hasOwnProperty('id_producto_usuario');
                        
                        // Obtener valores según el tipo de producto
                        const productoId = esEmpresa ? producto.id_producto_empresa : producto.id_producto_usuario;
                        const productoNombre = esEmpresa ? producto.nombre_producto_empresa : producto.nombre_producto_usuario;
                        const productoMarca = esEmpresa ? producto.marca_producto_empresa : producto.marca_producto_usuario;
                        const productoModelo = esEmpresa ? producto.modelo_producto_empresa : producto.modelo_producto_usuario;
                        const productoDescripcion = esEmpresa ? producto.descripcion_producto_empresa : producto.descripcion_producto_usuario;
                        const productoCaracteristicas = esEmpresa ? producto.caracteristicas_generales_empresa : producto.caracteristicas_generales_usuario;
                        const userType = esEmpresa ? 'empresa' : 'persona';
                        
                        const productoHTML = `
                        <div class=\"col-lg-4 col-md-6 col-12 wow fadeInUp\" data-wow-delay=\".2s\">
                            <div class=\"single-featuer\" style=\"max-width: 240px; min-width: 180px; width: 100%; border-radius: 0.7rem; padding: 0.7rem 0.7rem 0.5rem 0.7rem; margin: 0 auto; box-shadow: 0 2px 12px rgba(0,0,0,0.07);\">
                                <img class=\"shape\" src=\"/static/producto_sucursal/images/features/shape.svg\" alt=\"#\" style=\"max-width: 32px;\">
                                <img class=\"shape2\" src=\"/static/producto_sucursal/images/features/shape2.svg\" alt=\"#\" style=\"max-width: 32px;\">
                                <span class=\"serial\" style=\"font-size: 0.95rem;\">${producto.serial}</span>
                                <div style=\"display: flex; align-items: center; justify-content: center; width: 100%; margin-bottom: 8px;\">
                                    ${producto.imagen_url ? `<img src=\"${producto.imagen_url}\" alt=\"Imagen del producto\" class=\"img-producto-hover\" style=\"width: 60px; height: 60px; object-fit: cover; border-radius: 0.7rem; background: #f8f9fa; border: 1.5px solid #e0e0e0; box-shadow: 0 1px 6px rgba(0,0,0,0.08); display: block;\">` : `<i class=\"lni lni-microphone\" style=\"font-size: 2rem; color: #b0b0b0;\"></i>`}
                                </div>
                                <h3 style=\"font-size: 1rem; margin-bottom: 0.5rem; margin-top: 0.2rem; text-align: center;\">${productoNombre}</h3>
                                <div class=\"feature-buttons\" style=\"display: flex; justify-content: center; gap: 0.3rem;\">
                                    <button href=\"#EditProductModal\" class=\"btn btn-edit\" data-bs-toggle=\"modal\" data-bs-target=\"#EditProductModal\"
                                            data-id=\"${productoId}\"
                                            data-nombre=\"${productoNombre}\"
                                            data-marca=\"${productoMarca || ''}\"
                                            data-modelo=\"${productoModelo || ''}\"
                                            data-categoria=\"${producto.categoria_producto || ''}\"
                                            data-descripcion=\"${productoDescripcion || ''}\"
                                            data-caracteristicas=\"${productoCaracteristicas || ''}\"
                                            data-imagen=\"${producto.imagen_url || ''}\"
                                            data-user-type=\"${userType}\">
                                        <i class=\"lni lni-pencil\"></i> Editar
                                    </button>
                                    <button class=\"btn btn-delete\" data-id=\"${productoId}\" data-nombre=\"${productoNombre}\" data-user-type=\"${userType}\">
                                        <i class=\"lni lni-trash\"></i> Eliminar
                                    </button>
                                </div>
                            </div>
                        </div>`;
                        contenedorProductos.innerHTML += productoHTML;
                    });
                }
            });
    }
});
