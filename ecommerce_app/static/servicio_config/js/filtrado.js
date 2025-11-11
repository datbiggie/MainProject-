// filtrado.js para productos - búsqueda y filtrado con peticiones al servidor

// Función para cargar imágenes existentes del servicio
function cargarImagenesExistentesServicio(idServicio, userType) {
    const container = document.getElementById('current_images_container_servicio');
    if (!container) return;
    
    // Detectar userType si no se proporciona
    if (!userType) {
        const containerElement = document.querySelector('.container[data-user-type]');
        userType = containerElement?.getAttribute('data-user-type') || 'empresa';
    }
    
    console.log('=== DEBUG CARGA IMÁGENES SERVICIO ===');
    console.log('ID del servicio:', idServicio);
    console.log('Tipo de usuario:', userType);
    
    // Mostrar loading
    container.innerHTML = '<div class="col-12"><p>Cargando imágenes...</p></div>';
    
    // Construir URL según el tipo de usuario
    let url;
    if (userType === 'persona') {
        url = `/ecommerce/api/obtener_imagenes_servicio/?id_servicio_usuario=${idServicio}`;
    } else {
        url = `/ecommerce/api/obtener_imagenes_servicio/?id_servicio_empresa=${idServicio}`;
    }
    
    console.log('URL de la API:', url);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarImagenesExistentesServicio(data.imagenes, userType);
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
function mostrarImagenesExistentesServicio(imagenes, userType) {
    const container = document.getElementById('current_images_container_servicio');
    if (!container) return;
    
    if (imagenes.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-muted">No hay imágenes registradas para este servicio.</p></div>';
        return;
    }
    
    let html = '';
    imagenes.forEach(imagen => {
        // Determinar el ID de imagen según el tipo de usuario
        let imagenId, imagenIdField;
        if (userType === 'persona') {
            imagenId = imagen.id_imagen_servicio_usuario;
            imagenIdField = 'id_imagen_servicio_usuario';
        } else {
            imagenId = imagen.id_imagen_servicio_empresa;
            imagenIdField = 'id_imagen_servicio_empresa';
        }
        
        html += `
            <div class="col-md-4 col-sm-6 col-6 mb-2" id="imagen_servicio_${imagenId}">
                <div class="card" style="border-radius: 8px; overflow: hidden;">
                    <img src="${imagen.url}" class="card-img-top" style="height: 80px; object-fit: cover;" alt="Imagen del servicio">
                    <div class="card-body p-1">
                        <button type="button" class="btn btn-danger btn-sm w-100" style="font-size: 11px; padding: 4px 8px;" onclick="eliminarImagenServicio('${imagenId}', '${imagenIdField}')">
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
function eliminarImagenServicio(idImagen, imagenIdField) {
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
            formData.append(imagenIdField, idImagen);
            
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

    // Configurar el modal de servicios para evitar problemas de aria-hidden
    const serviceModal = document.getElementById('EditServiceModal');
    if (serviceModal) {
        // Configurar opciones del modal para mejor accesibilidad
        serviceModal.addEventListener('show.bs.modal', function() {
            // Remover aria-hidden cuando el modal se muestra
            this.removeAttribute('aria-hidden');
        });
        
        serviceModal.addEventListener('shown.bs.modal', function() {
            // Asegurar que el modal no tenga aria-hidden cuando está visible
            this.removeAttribute('aria-hidden');
        });
        
        serviceModal.addEventListener('hide.bs.modal', function() {
            // Manejar el cierre del modal correctamente
            const focusedElement = document.activeElement;
            if (focusedElement && this.contains(focusedElement)) {
                focusedElement.blur();
            }
        });
        
        serviceModal.addEventListener('hidden.bs.modal', function() {
            // Limpiar campos del modal cuando se cierre
            try {
                const empresaIdField = document.getElementById('edit_id_servicio_empresa');
                const usuarioIdField = document.getElementById('edit_id_servicio_usuario');
                if (empresaIdField) empresaIdField.value = '';
                if (usuarioIdField) usuarioIdField.value = '';
                
                const nombreField = document.getElementById('edit_nombre_servicio');
                const descripcionField = document.getElementById('edit_descripcion_servicio');
                const categoriaField = document.getElementById('edit_categoria_servicio');
                const imagenesField = document.getElementById('edit_imagenes_servicio');
                
                if (nombreField) nombreField.value = '';
                if (descripcionField) descripcionField.value = '';
                if (categoriaField) categoriaField.value = '';
                if (imagenesField) imagenesField.value = '';
                
                // Limpiar previsualizaciones
                const imagePreview = document.getElementById('edit_imagePreview_servicio');
                if (imagePreview) imagePreview.innerHTML = '';
                
                console.log('Modal de servicio cerrado - campos limpiados');
            } catch (error) {
                console.error('Error al limpiar el modal de servicio:', error);
            }
        });
    }

};


document.addEventListener('DOMContentLoaded', function() {
    const busquedaInput = document.getElementById('busqueda-producto');
    const contenedorProductos = document.getElementById('contenedor-productos');

    if (!busquedaInput || !contenedorProductos) return;

    let timeout = null;
    busquedaInput.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            filtrarServicios();
        }, 350);
    });

// Función para cargar imágenes existentes del servicio
function cargarImagenesExistentesServicio(idServicio, userType) {
    const container = document.getElementById('current_images_container_servicio');
    if (!container) return;
    
    console.log('=== CARGANDO IMÁGENES DE SERVICIO ===');
    console.log('ID del servicio:', idServicio);
    console.log('Tipo de usuario:', userType);
    
    // Mostrar loading
    container.innerHTML = '<div class="col-12"><p>Cargando imágenes...</p></div>';
    
    // Construir URL según el tipo de usuario
    let apiUrl;
    if (userType === 'persona') {
        apiUrl = `/ecommerce/api/obtener_imagenes_servicio/?id_servicio_usuario=${idServicio}`;
    } else {
        apiUrl = `/ecommerce/api/obtener_imagenes_servicio/?id_servicio_empresa=${idServicio}`;
    }
    
    console.log('URL de la API:', apiUrl);
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta de la API:', data);
            if (data.success) {
                mostrarImagenesExistentesServicio(data.imagenes, userType);
            } else {
                container.innerHTML = '<div class="col-12"><p class="text-muted">No se pudieron cargar las imágenes.</p></div>';
            }
        })
        .catch(error => {
            console.error('Error al cargar imágenes:', error);
            container.innerHTML = '<div class="col-12"><p class="text-danger">Error al cargar las imágenes.</p></div>';
        });
}



    // Lógica para abrir el modal y llenar los campos con los datos del servicio
    document.addEventListener('click', function(e) {
        console.log('Click detectado en servicio:', e.target);
        console.log('Clases del elemento:', e.target.className);
        
        if (e.target.classList.contains('btn-edit') || e.target.closest('.btn-edit')) {
            const btn = e.target.closest('.btn-edit');
            if (!btn) return;
            console.log('✅ Botón de editar servicio encontrado');
            console.log('Botón que activó el modal:', btn);
            console.log('Atributos del botón:', btn.attributes);
            // Determinar el tipo de usuario desde el botón o el contexto
            let userType = btn.getAttribute('data-user-type');
            let userTypeElement = null;
            if (!userType) {
                userTypeElement = btn.closest('.container').querySelector('[data-user-type]');
                userType = userTypeElement?.getAttribute('data-user-type') || 'empresa';
            }
            const serviceId = btn.getAttribute('data-id');
            
            console.log('=== DEBUG TIPO DE USUARIO SERVICIO ===');
            console.log('Elemento con data-user-type:', userTypeElement);
            console.log('Tipo de usuario detectado:', userType);
            console.log('ID del servicio obtenido:', serviceId);
            
            // Asignar ID según el tipo de usuario
            if (userType === 'empresa') {
                const idField = document.getElementById('edit_id_servicio_empresa');
                console.log('Campo ID servicio empresa encontrado:', idField);
                if (idField) {
                    idField.value = serviceId || '';
                    console.log('✅ ID de servicio empresa asignado:', serviceId);
                } else {
                    console.log('❌ Campo edit_id_servicio_empresa no encontrado');
                }
            } else {
                const idField = document.getElementById('edit_id_servicio_usuario');
                console.log('Campo ID servicio usuario encontrado:', idField);
                if (idField) {
                    idField.value = serviceId || '';
                    console.log('✅ ID de servicio usuario asignado:', serviceId);
                } else {
                    console.log('❌ Campo edit_id_servicio_usuario no encontrado');
                }
            }
            
            // Asignar valores a los campos del modal
            const nombreField = document.getElementById('edit_nombre_servicio');
            const descripcionField = document.getElementById('edit_descripcion_servicio');
            
            if (nombreField) {
                nombreField.value = btn.getAttribute('data-nombre') || '';
                console.log('✅ Nombre del servicio asignado:', btn.getAttribute('data-nombre'));
            } else {
                console.log('❌ Campo edit_nombre_servicio no encontrado');
            }
            
            if (descripcionField) {
                descripcionField.value = btn.getAttribute('data-descripcion') || '';
                console.log('✅ Descripción del servicio asignada:', btn.getAttribute('data-descripcion'));
            } else {
                console.log('❌ Campo edit_descripcion_servicio no encontrado');
            }
            
            // Asignar campos adicionales para usuarios tipo persona
            if (userType === 'persona') {
                const precioField = document.getElementById('edit_precio_servicio');
                const estatusField = document.getElementById('edit_estatus_servicio');
                
                if (precioField) {
                    precioField.value = btn.getAttribute('data-precio') || '0';
                    console.log('✅ Precio del servicio asignado:', btn.getAttribute('data-precio'));
                } else {
                    console.log('❌ Campo edit_precio_servicio no encontrado');
                }
                
                if (estatusField) {
                    estatusField.value = btn.getAttribute('data-estatus') || 'Activo';
                    console.log('✅ Estatus del servicio asignado:', btn.getAttribute('data-estatus'));
                } else {
                    console.log('❌ Campo edit_estatus_servicio no encontrado');
                }
            }
            
            // Ya no establecemos el valor de estatus_servicio porque el campo se ha eliminado
            // Seleccionar la categoría correcta
            const categoria = btn.getAttribute('data-categoria') || '';
            const selectCategoria = document.getElementById('edit_categoria_servicio');
            console.log('Select de categoría de servicio encontrado:', selectCategoria);
            
            if (selectCategoria) {
                console.log('Valor de categoría obtenido:', categoria);
                console.log('Opciones disponibles en el select:');
                // Priorizar data-categoria-id si está presente (valor de la option)
                const categoriaId = btn.getAttribute('data-categoria-id');
                if (categoriaId) {
                    // Intentar seleccionar por value directamente
                    const optionByValue = Array.from(selectCategoria.options).find(opt => opt.value.trim() === categoriaId.trim());
                    if (optionByValue) {
                        selectCategoria.value = categoriaId.trim();
                        console.log('✅ Categoría asignada por ID:', categoriaId);
                    } else {
                        console.log('⚠️ data-categoria-id proporcionado pero no coincide con ningún value del select:', categoriaId);
                    }
                }
                for (let i = 0; i < selectCategoria.options.length; i++) {
                    console.log(`Opción ${i}: value="${selectCategoria.options[i].value}", text="${selectCategoria.options[i].text}"`);
                }
                
                // Si no se asignó por ID anteriormente, intentar asignar por texto/valor
                if (!categoriaId && categoria) {
                    let categoriaEncontrada = false;
                    for (let i = 0; i < selectCategoria.options.length; i++) {
                        // Comparación más robusta: trim y comparación case-insensitive
                        const optionText = selectCategoria.options[i].text.trim();
                        const optionValue = selectCategoria.options[i].value.trim();
                        const categoriaToCompare = categoria.trim();
                        
                        if (optionText.toLowerCase() === categoriaToCompare.toLowerCase() || 
                            optionValue === categoriaToCompare) {
                            selectCategoria.selectedIndex = i;
                            console.log('✅ Categoría de servicio asignada:', categoria, 'en índice', i);
                            categoriaEncontrada = true;
                            break;
                        }
                    }
                    if (!categoriaEncontrada) {
                        console.log('❌ No se encontró coincidencia para la categoría:', categoria);
                    }
                } else {
                    console.log('❌ No se encontró valor de categoría en data-categoria ni data-categoria-id');
                }
            } else {
                console.log('❌ Campo edit_categoria_servicio no encontrado');
            }
            // Cargar imágenes existentes del servicio
            const idServicio = btn.getAttribute('data-id');
            cargarImagenesExistentesServicio(idServicio, userType);
            
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
        console.log('=== ENVÍO DE FORMULARIO DE SERVICIO ===');
        const form = e.target;
        const formData = new FormData(form);
        
        // Debug: Mostrar todos los datos que se van a enviar
        console.log('=== DEBUG DATOS DEL FORMULARIO DE SERVICIO ===');
        for (let [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }
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
                // Cerrar modal correctamente
                const modalElement = document.getElementById('EditServiceModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                } else {
                    // Si no hay instancia, crear una y cerrarla
                    const newModal = new bootstrap.Modal(modalElement);
                    newModal.hide();
                }
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
        // Aceptar clicks tanto sobre el botón como sobre elementos internos (p. ej. el icono)
        if (e.target.classList.contains('btn-delete') || e.target.closest('.btn-delete')) {
            const btn = e.target.classList.contains('btn-delete') ? e.target : e.target.closest('.btn-delete');
            const id = btn.getAttribute('data-id');
            const nombre = btn.getAttribute('data-nombre');
            
            // Determinar el tipo de usuario desde el contexto
            let userType = btn.getAttribute('data-user-type');
            if (!userType) {
                const userTypeElement = btn.closest('.container').querySelector('[data-user-type]');
                userType = userTypeElement?.getAttribute('data-user-type') || 'empresa';
            }
            
            console.log('=== DEBUG ELIMINACIÓN SERVICIO ===');
            console.log('ID del servicio:', id);
            console.log('Tipo de usuario:', userType);
            
            Swal.fire({
                title: '¿Eliminar servicio?',
                text: `¿Seguro que deseas eliminar el servicio "${nombre}"?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Construir el cuerpo de la petición según el tipo de usuario
                    let requestBody;
                    if (userType === 'persona') {
                        requestBody = `id_servicio_usuario=${encodeURIComponent(id)}`;
                    } else {
                        requestBody = `id_servicio_empresa=${encodeURIComponent(id)}`;
                    }
                    
                    console.log('Cuerpo de la petición:', requestBody);
                    
                    fetch('/ecommerce/eliminar_servicio/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        },
                        body: requestBody
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
                            // Determinar si es servicio de empresa o usuario
                            const esEmpresa = servicio.hasOwnProperty('id_servicio_empresa');
                            const esUsuario = servicio.hasOwnProperty('id_servicio_usuario');
                            
                            // Obtener valores según el tipo de servicio
                            const servicioId = esEmpresa ? servicio.id_servicio_empresa : servicio.id_servicio_usuario;
                            const servicioNombre = esEmpresa ? servicio.nombre_servicio_empresa : servicio.nombre_servicio_usuario;
                            const servicioDescripcion = esEmpresa ? servicio.descripcion_servicio_empresa : servicio.descripcion_servicio_usuario;
                            const servicioCaracteristicas = esEmpresa ? servicio.caracteristicas_generales_empresa : servicio.caracteristicas_generales_usuario;
                            const userType = esEmpresa ? 'empresa' : 'persona';
                            
                            // Construir atributos adicionales para usuarios tipo persona
                            let additionalAttributes = '';
                            if (userType === 'persona') {
                                additionalAttributes = `
                                                data-precio="${servicio.precio_servicio_usuario || '0'}"
                                                data-estatus="${servicio.estatus_servicio_usuario || 'Activo'}"`;
                            }
                            
                            const servicioHTML = `
                            <div class="product-card animate-card" data-nombre="${servicioNombre ? servicioNombre.toLowerCase() : ''}">
                                <div class="modern-product-wrapper">
                                    <!-- Número de Servicio -->
                                    <div class="product-number">${servicio.serial || ''}</div>
                                    <!-- Contenedor de Imagen Mejorado -->
                                    <div class="product-image-container">
                                        ${servicio.imagen_url && servicio.imagen_url !== '' ? 
                                            `<img src="${servicio.imagen_url}" alt="${servicioNombre || 'Imagen del servicio'}" class="product-image loaded" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"><i class="lni lni-package product-image-fallback" style="display: none;"></i>` : 
                                            `<i class="lni lni-package product-image-fallback"></i>`
                                        }
                                    </div>
                                    <!-- Información del Servicio -->
                                    <div class="product-content">
                                        <h3 class="product-title">${servicioNombre || ''}</h3>
                                        <div class="product-meta">
                                            <span class="product-type">${userType === 'empresa' ? 'Empresa' : 'Usuario'}</span>
                                        </div>
                                        ${userType === 'empresa' ? `
                                        <div class="product-branches">
                                            <strong>Sucursales asignadas:</strong>
                                            ${servicio.sucursales_asignadas && servicio.sucursales_asignadas.length > 0 ? 
                                                `<ul class="branches-list">
                                                    ${servicio.sucursales_asignadas.map(sucursal => `<li>${sucursal.nombre}</li>`).join('')}
                                                </ul>` : 
                                                '<span class="no-branches">Sin sucursales asignadas</span>'
                                            }
                                        </div>` : ''}
                                    </div>
                                    <!-- Acciones del Servicio -->
                                    <div class="product-actions">
                                        <button class="action-btn btn-edit" data-bs-toggle="modal" data-bs-target="#EditServiceModal"
                                                data-id="${servicioId}"
                                                data-nombre="${servicioNombre || ''}"
                                                data-descripcion="${servicioDescripcion || ''}"
                                                data-caracteristicas="${servicioCaracteristicas || ''}"
                                                data-categoria="${servicio.categoria || ''}"
                                                data-categoria-id="${servicio.categoria_servicio_id || ''}"
                                                data-imagen="${servicio.imagen_url || ''}"
                                                data-user-type="${userType}"${additionalAttributes}
                                                data-tooltip="Editar servicio">
                                            <i class="lni lni-pencil"></i>
                                        </button>
                                        <button class="action-btn btn-delete" data-id="${servicioId}" data-nombre="${servicioNombre}" data-user-type="${userType}" data-tooltip="Eliminar servicio">
                                            <i class="lni lni-trash-can"></i>
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
