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
                        const productoDescripcion = esEmpresa ? producto.descripcion_producto_empresa : producto.descripcion_producto_usuario;
                        const productoCaracteristicas = esEmpresa ? producto.caracteristicas_generales_empresa : producto.caracteristicas_generales_usuario;
                        const productoMarca = esEmpresa ? producto.marca_producto_empresa : producto.marca_producto_usuario;
                        const productoModelo = esEmpresa ? producto.modelo_producto_empresa : producto.modelo_producto_usuario;
                        const userType = esEmpresa ? 'empresa' : 'persona';
                        
                        const productoHTML = `
                        <div class="product-card animate-card" data-nombre="${productoNombre.toLowerCase()}">
                            <div class="modern-product-wrapper">
                                <!-- Número de Producto -->
                                <div class="product-number">${producto.serial || ''}</div>
                                <!-- Contenedor de Imagen Mejorado -->
                                <div class="product-image-container">
                                    ${producto.imagen_url ? 
                                        `<img src="${producto.imagen_url}" 
                                             alt="${productoNombre}" 
                                             class="product-image loaded"
                                             loading="lazy"
                                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                        <i class="lni lni-package product-image-fallback" style="display: none;"></i>` : 
                                        `<i class="lni lni-package product-image-fallback"></i>`
                                    }
                                </div>
                                <!-- Contenido del Producto -->
                                <div class="product-content">
                                    <h3 class="product-title">${productoNombre}</h3>
                                    <div class="product-meta">
                                        <span class="product-type">${esEmpresa ? 'Empresa' : 'Usuario'}</span>
                                    </div>
                                    ${esEmpresa ? `
                                    <div class="product-branches">
                                        <strong>Sucursales asignadas:</strong>
                                        ${producto.sucursales_asignadas && producto.sucursales_asignadas.length > 0 ? 
                                            `<ul class="branches-list">
                                                ${producto.sucursales_asignadas.map(sucursal => `<li>${sucursal.nombre}</li>`).join('')}
                                            </ul>` : 
                                            '<span class="no-branches">Sin sucursales asignadas</span>'
                                        }
                                    </div>` : ''}
                                </div>
                                <!-- Acciones del Producto -->
                                <div class="product-actions">
                                    <button class="action-btn btn-edit" data-bs-toggle="modal" data-bs-target="#EditProductModal"
                                            data-id="${productoId}"
                                            data-nombre="${productoNombre}"
                                            data-descripcion="${productoDescripcion || ''}"
                                            data-caracteristicas="${productoCaracteristicas || ''}"
                                            data-marca="${productoMarca || ''}"
                                            data-modelo="${productoModelo || ''}"
                                            data-categoria="${producto.categoria || ''}"
                                            data-imagen="${producto.imagen_url || ''}"
                                            data-user-type="${userType}"
                                            data-tooltip="Editar producto">
                                        <i class="lni lni-pencil"></i>
                                    </button>
                                    <button class="action-btn btn-delete" data-id="${productoId}" data-nombre="${productoNombre}" data-user-type="${userType}" data-tooltip="Eliminar producto">
                                        <i class="lni lni-trash-can"></i>
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
