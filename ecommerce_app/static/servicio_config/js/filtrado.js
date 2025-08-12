// filtrado.js para productos - búsqueda y filtrado con peticiones al servidor

// Función para cargar imágenes existentes del servicio
function cargarImagenesExistentesServicio(idServicio) {
    const container = document.getElementById('current_images_container_servicio');
    if (!container) return;
    
    // Mostrar loading
    container.innerHTML = '<div class="col-12"><p>Cargando imágenes...</p></div>';
    
    fetch(`/ecommerce/api/obtener_imagenes_servicio/?id_servicio=${idServicio}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarImagenesExistentesServicio(data.imagenes);
            } else {
                container.innerHTML = '<div class="col-12"><p class="text-muted">No se pudieron cargar las imágenes.</p></div>';
            }
        })
        .catch(error => {
            console.error('Error al cargar imágenes:', error);
            container.innerHTML = '<div class="col-12"><p class="text-muted">Error al cargar las imágenes.</p></div>';
        });
}

// Función para mostrar las imágenes existentes del servicio
function mostrarImagenesExistentesServicio(imagenes) {
    const container = document.getElementById('current_images_container_servicio');
    if (!container) return;
    
    if (imagenes.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-muted">No hay imágenes registradas para este servicio.</p></div>';
        return;
    }
    
    let html = '';
    imagenes.forEach(imagen => {
        html += `
            <div class="col-md-4 col-sm-6 col-6 mb-2" id="imagen_servicio_${imagen.id_imagen}">
                <div class="card" style="border-radius: 8px; overflow: hidden;">
                    <img src="${imagen.url}" class="card-img-top" style="height: 80px; object-fit: cover;" alt="Imagen del servicio">
                    <div class="card-body p-1">
                        <button type="button" class="btn btn-danger btn-sm w-100" style="font-size: 11px; padding: 4px 8px;" onclick="eliminarImagenServicio(${imagen.id_imagen})">
                            <i class="fas fa-trash" style="font-size: 10px;"></i> Eliminar
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Función para eliminar una imagen específica del servicio
function eliminarImagenServicio(idImagen) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            const formData = new FormData();
            formData.append('id_imagen', idImagen);
            
            fetch('/ecommerce/api/eliminar_imagen_servicio/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remover la imagen del DOM
                    const imagenElement = document.getElementById(`imagen_servicio_${idImagen}`);
                    if (imagenElement) {
                        imagenElement.remove();
                    }
                    
                    Swal.fire({
                        title: 'Eliminada',
                        text: data.message,
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: data.message,
                        icon: 'error'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'Error de conexión al eliminar la imagen',
                    icon: 'error'
                });
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const busquedaInput = document.getElementById('busqueda-producto');
    const contenedorProductos = document.getElementById('contenedor-productos');
    const filtroBtns = document.querySelectorAll('.filtro-estado-producto');
    let estadoActual = 'todos';

    if (!busquedaInput || !contenedorProductos) return;


    let timeout = null;
    busquedaInput.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            filtrarServicios();
        }, 350);
    });

// Función para cargar imágenes existentes del servicio
function cargarImagenesExistentesServicio(idServicio) {
    const container = document.getElementById('current_images_container_servicio');
    if (!container) return;
    
    // Mostrar loading
    container.innerHTML = '<div class="col-12"><p>Cargando imágenes...</p></div>';
    
    fetch(`/ecommerce/api/obtener_imagenes_servicio/?id_servicio=${idServicio}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarImagenesExistentesServicio(data.imagenes);
            } else {
                container.innerHTML = '<div class="col-12"><p class="text-muted">No se pudieron cargar las imágenes.</p></div>';
            }
        })
        .catch(error => {
            console.error('Error al cargar imágenes:', error);
            container.innerHTML = '<div class="col-12"><p class="text-danger">Error al cargar las imágenes.</p></div>';
        });
}

    filtroBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            filtroBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            estadoActual = this.getAttribute('data-estado');
            filtrarServicios();
        });
    });

    // Lógica para abrir el modal y llenar los campos con los datos del servicio
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-edit')) {
            const btn = e.target.closest('.btn-edit');
            if (!btn) return;
            document.getElementById('edit_id_servicio').value = btn.getAttribute('data-id') || '';
            document.getElementById('edit_nombre_servicio').value = btn.getAttribute('data-nombre') || '';
            document.getElementById('edit_descripcion_servicio').value = btn.getAttribute('data-descripcion') || '';
            // Ya no establecemos el valor de estatus_servicio porque el campo se ha eliminado
            // Seleccionar la categoría correcta
            const categoria = btn.getAttribute('data-categoria') || '';
            const selectCategoria = document.getElementById('edit_categoria_servicio');
            if (selectCategoria) {
                for (let i = 0; i < selectCategoria.options.length; i++) {
                    if (selectCategoria.options[i].text === categoria || selectCategoria.options[i].value === categoria) {
                        selectCategoria.selectedIndex = i;
                        break;
                    }
                }
            }
            // Cargar imágenes existentes del servicio
            const idServicio = btn.getAttribute('data-id');
            cargarImagenesExistentesServicio(idServicio);
            
            // Limpiar preview de nuevas imágenes
            const imgPreview = document.getElementById('edit_imagePreview_servicio');
            if (imgPreview) {
                imgPreview.innerHTML = '';
            }
        }
    });


    // Enviar formulario de edición de servicio por AJAX
    document.getElementById('editServiceForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        fetch('/ecommerce/editar_servicio/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cerrar modal y recargar lista
                const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('EditServiceModal'));
                modal.hide();
                filtrarServicios();
                Swal.fire('¡Éxito!', data.message || 'Servicio actualizado', 'success');
            } else {
                Swal.fire('Error', data.message || 'No se pudo actualizar el servicio', 'error');
            }
        })
        .catch(() => {
            Swal.fire('Error', 'Error de conexión', 'error');
        });
    });

    // Eliminar servicio por AJAX
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-delete')) {
            const btn = e.target.closest('.btn-delete');
            const id = btn.getAttribute('data-id');
            const nombre = btn.getAttribute('data-nombre');
            Swal.fire({
                title: '¿Eliminar servicio?',
                text: `¿Seguro que deseas eliminar el servicio "${nombre}"?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch('/ecommerce/eliminar_servicio/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        },
                        body: `id_servicio=${encodeURIComponent(id)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            filtrarServicios();
                            Swal.fire('¡Eliminado!', data.message || 'Servicio eliminado', 'success');
                        } else {
                            Swal.fire('Error', data.message || 'No se pudo eliminar el servicio', 'error');
                        }
                    })
                    .catch(() => {
                        Swal.fire('Error', 'Error de conexión', 'error');
                    });
                }
            });
        }
    });

    function filtrarServicios() {
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
                        if (!data.servicios || data.servicios.length === 0) {
                            contenedorProductos.innerHTML = '<div class="text-center w-100 py-4"><p>No se encontraron servicios.</p></div>';
                            return;
                        }
                        data.servicios.forEach(servicio => {
                            const servicioHTML = `
                            <div class="col-lg-4 col-md-6 col-12 wow fadeInUp" data-wow-delay=".2s">
                                <div class="single-featuer" style="max-width: 240px; min-width: 180px; width: 100%; border-radius: 0.7rem; padding: 0.7rem 0.7rem 0.5rem 0.7rem; margin: 0 auto; box-shadow: 0 2px 12px rgba(0,0,0,0.07);">
                                    <img class="shape" src="/static/servicio_config/images/features/shape.svg" alt="#" style="max-width: 32px;">
                                    <img class="shape2" src="/static/servicio_config/images/features/shape2.svg" alt="#" style="max-width: 32px;">
                                    <span class="serial" style="font-size: 0.95rem;">${servicio.serial || ''}</span>
                                    <div style="display: flex; align-items: center; justify-content: center; width: 100%; margin-bottom: 8px;">
                                        ${servicio.imagen_url && servicio.imagen_url !== '' ? `<img src="${servicio.imagen_url}" alt="Imagen del servicio" class="img-servicio-hover" style="width: 60px; height: 60px; object-fit: cover; border-radius: 0.7rem; background: #f8f9fa; border: 1.5px solid #e0e0e0; box-shadow: 0 1px 6px rgba(0,0,0,0.08); display: block;">` : `<i class=\"lni lni-customer\" style=\"font-size: 2rem; color: #b0b0b0;\"></i>`}
                                    </div>
                                    <h3 style="font-size: 1rem; margin-bottom: 0.5rem; margin-top: 0.2rem; text-align: center;">${servicio.nombre_servicio || ''}</h3>
                                    <div class="feature-buttons" style="display: flex; justify-content: center; gap: 0.3rem;">
                                        <button href="#EditServiceModal" class="btn btn-edit" data-bs-toggle="modal" data-bs-target="#EditServiceModal"
                                                data-id="${servicio.id_servicio}"
                                                data-nombre="${servicio.nombre_servicio || ''}"
                                                data-categoria="${servicio.categoria_servicio || ''}"
                                                data-descripcion="${servicio.descripcion_servicio || ''}"
                                                data-caracteristicas="${servicio.caracteristicas_generales || ''}"
                                                data-imagen="${servicio.imagen_url || ''}">
                                            <i class="lni lni-pencil"></i> Editar
                                        </button>
                                        <button class="btn btn-delete" data-id="${servicio.id_servicio}" data-nombre="${servicio.nombre_servicio}">
                                            <i class="lni lni-trash"></i> Eliminar
                                        </button>
                                    </div>
                                </div>
                            </div>`;
                            contenedorProductos.innerHTML += servicioHTML;
                        });
                    }
                });
        }
});
