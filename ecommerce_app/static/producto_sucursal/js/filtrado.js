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
        // Si el campo está vacío, pedir todos los productos (sin filtro)
        let url = '/ecommerce/api/filtrar_productos/';
        if (textoBusqueda !== '') {
            url += `?nombre=${encodeURIComponent(textoBusqueda)}`;
        }
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('Respuesta del servidor:', data); // Debug
                // Siempre limpiar el contenedor primero
                contenedorProductos.innerHTML = '';
                
                if (data.success === false) {
                    console.error('Error del servidor:', data.message);
                    contenedorProductos.innerHTML = '<div class="text-center w-100 py-4"><p>Error al cargar productos.</p></div>';
                    return;
                }
                
                if (!data.productos || data.productos.length === 0) {
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
                    const productoCategoria = producto.categoria_producto || 'Sin categoría';
                    const imagenUrl = producto.imagen_url || '/static/images/default-product.png';

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
                                ${esEmpresa ? `
                                <div class="product-meta">
                                    <span class="product-type">Empresa</span>
                                </div>
                                <div class="product-branches">
                                    <strong>Sucursales asignadas:</strong>
                                    ${producto.sucursales_asignadas && producto.sucursales_asignadas.length > 0 ? 
                                        `<ul class="branches-list">
                                            ${producto.sucursales_asignadas.map(sucursal => `<li>${sucursal.nombre}</li>`).join('')}
                                        </ul>` : 
                                        '<span class="no-branches">Sin sucursales asignadas</span>'
                                    }
                                </div>` : `
                                <div class="product-details">
                                    <div class="product-info-item">
                                        <strong>Estado:</strong>
                                        <span class="status-badge status-${(producto.estatus_producto_usuario || 'activo').toLowerCase()}">${producto.estatus_producto_usuario || 'Activo'}</span>
                                    </div>
                                    <div class="product-info-item price-item">
                                        <strong>Precio:</strong>
                                        <span class="product-price">$${producto.precio_producto_usuario || '0'}</span>
                                    </div>
                                </div>`}
                            </div>
                            <!-- Acciones del Producto -->
                            <div class="product-actions">
                                <button class="action-btn btn-edit" data-bs-toggle="modal" data-bs-target="#EditProductModal"
                                        data-id="${productoId}"
                                        data-nombre="${productoNombre}"
                                        data-descripcion="${productoDescripcion || ''}"
                                        data-caracteristicas="${productoCaracteristicas || ''}"
                                        data-categoria="${producto.categoria_producto || ''}"
                                        data-imagen="${producto.imagen_url || ''}"
                                        data-user-type="${userType}"
                                        ${esUsuario ? `
                                        data-stock="${producto.stock_producto_usuario || '0'}"
                                        data-precio="${producto.precio_producto_usuario || '0'}"
                                        data-condicion="${producto.condicion_producto_usuario || 'Nuevo'}"
                                        data-estatus="${producto.estatus_producto_usuario || 'Activo'}"
                                        data-latitud="${producto.latitud_producto_usuario || ''}"
                                        data-longitud="${producto.longitud_producto_usuario || ''}"` : ''}
                                        data-tooltip="Editar producto">
                                    <i class="lni lni-pencil"></i>
                                </button>
                                <button class="action-btn btn-delete" data-id="${productoId}" data-nombre="${productoNombre}" data-user-type="${userType}" data-tooltip="Eliminar producto">
                                    <i class="lni lni-trash-can"></i>
                                </button>
                                <button class="action-btn btn-assign-branch" data-id="${productoId}" data-nombre="${productoNombre}" data-user-type="${userType}" data-tooltip="Asignar por sucursal">
                                    <i class="lni lni-map-marker"></i>
                                </button>
                            </div>
                        </div>
                    </div>`;
                    contenedorProductos.innerHTML += productoHTML;
                });
            })
            .catch(error => {
                console.error('Error al filtrar productos:', error);
                contenedorProductos.innerHTML = '<div class="text-center w-100 py-4"><p>Error al cargar productos. Por favor, intente nuevamente.</p></div>';
            });
    }
});
