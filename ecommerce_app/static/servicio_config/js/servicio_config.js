function filtrarProductos() {
    const textoBusqueda = busquedaInput.value.trim();
    let url = `/ecommerce/api/filtrar_servicios/?nombre=${encodeURIComponent(textoBusqueda)}`;
    if (estadoActual && estadoActual !== 'todos') {
        url += `&estatus=${encodeURIComponent(estadoActual)}`;
    }
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                contenedorProductos.innerHTML = '';
                if (data.servicios.length === 0) {
                    contenedorProductos.innerHTML = '<div class="text-center w-100 py-4"><p>No se encontraron servicios.</p></div>';
                    return;
                }
                data.servicios.forEach(servicio => {
                    const servicioHTML = `
                    <div class="col-lg-4 col-md-6 col-12 wow fadeInUp" data-wow-delay=".2s">
                        <div class="single-featuer" style="max-width: 240px; min-width: 180px; width: 100%; border-radius: 0.7rem; padding: 0.7rem 0.7rem 0.5rem 0.7rem; margin: 0 auto; box-shadow: 0 2px 12px rgba(0,0,0,0.07);">
                            <img class="shape" src="/static/servicio_config/images/features/shape.svg" alt="#" style="max-width: 32px;">
                            <img class="shape2" src="/static/servicio_config/images/features/shape2.svg" alt="#" style="max-width: 32px;">
                            <span class="serial" style="font-size: 0.95rem;">${servicio.serial}</span>
                            <div style="display: flex; align-items: center; justify-content: center; width: 100%; margin-bottom: 8px;">
                                ${servicio.imagen_url ? `<img src="${servicio.imagen_url}" alt="Imagen del servicio" class="img-producto-hover" style="width: 60px; height: 60px; object-fit: cover; border-radius: 0.7rem; background: #f8f9fa; border: 1.5px solid #e0e0e0; box-shadow: 0 1px 6px rgba(0,0,0,0.08); display: block;">` : `<i class="lni lni-microphone" style="font-size: 2rem; color: #b0b0b0;"></i>`}
                            </div>
                            <h3 style="font-size: 1rem; margin-bottom: 0.5rem; margin-top: 0.2rem; text-align: center;">${servicio.nombre_servicio}</h3>
                            <div class="feature-buttons" style="display: flex; justify-content: center; gap: 0.3rem;">
                                <button href="#EditProductModal" class="btn btn-edit" data-bs-toggle="modal" data-bs-target="#EditProductModal"
                                        data-id="${servicio.id_servicio}"
                                        data-nombre="${servicio.nombre_servicio}"
                                        data-categoria="${servicio.categoria_servicio || ''}"
                                        data-descripcion="${servicio.descripcion_servicio || ''}"
                                        data-imagen="${servicio.imagen_url || ''}">
                                    <i class="lni lni-pencil"></i> Editar
                                </button>
                                <button class="btn btn-delete" data-id="${servicio.id_servicio}" data-nombre="${servicio.nombre_servicio}">
                                    <i class="lni lni-trash"></i> Eliminar
                                </button>
                            </div>
                        </div>
                    </div>
                    `;
                    contenedorProductos.innerHTML += servicioHTML;
                });
            } else {
                contenedorProductos.innerHTML = '<div class="text-center w-100 py-4"><p>Error al filtrar servicios.</p></div>';
            }
        })
        .catch(() => {
            contenedorProductos.innerHTML = '<div class="text-center w-100 py-4"><p>Error de conexión.</p></div>';
        });
}