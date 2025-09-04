// Función para confirmar eliminación de producto (sin variables globales)
function confirmarEliminacionProducto(idProducto, nombreProducto) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: `¿Realmente quieres eliminar el producto "${nombreProducto}"? Esta acción no se puede deshacer.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Detectar el tipo de usuario desde el contenedor principal
            const userTypeElement = document.querySelector('[data-user-type]');
            const userType = userTypeElement?.getAttribute('data-user-type') || 'empresa';
                

                
            
            console.log('=== DEBUG ELIMINACIÓN PRODUCTO ===');
            console.log('ID Producto:', idProducto);
            console.log('Nombre Producto:', nombreProducto);
            console.log('Tipo de usuario detectado:', userType);
            
            // Crear FormData para enviar los datos
            const formData = new FormData();
            
            // Enviar el parámetro correcto según el tipo de usuario
            if (userType.toLowerCase() === 'persona') {
                formData.append('id_producto_usuario', idProducto);
                console.log('Enviando como id_producto_usuario:', idProducto);
            } else {
                formData.append('id_producto_empresa', idProducto);
                console.log('Enviando como id_producto_empresa:', idProducto);
            }
            
            // Obtener el token CSRF del primer input oculto del DOM
            const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (csrfInput) {
                formData.append('csrfmiddlewaretoken', csrfInput.value);
            }
            // Mostrar indicador de carga
            Swal.fire({
                title: 'Eliminando...',
                text: 'Por favor espera mientras se elimina el producto',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Enviar solicitud de eliminación
            fetch('/ecommerce/eliminar_producto/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfInput ? csrfInput.value : ''
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Producto Eliminado!',
                        text: data.message,
                        confirmButtonColor: '#3085d6',
                        confirmButtonText: 'Aceptar'
                    }).then((result) => {
                        window.location.reload();
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message,
                        confirmButtonColor: '#d33',
                        confirmButtonText: 'Aceptar'
                    });
                }
            })
            .catch(error => {
                console.error('Error al eliminar producto:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Error al eliminar el producto. Por favor, inténtalo de nuevo.',
                    confirmButtonColor: '#d33',
                    confirmButtonText: 'Aceptar'
                });
            });
        }
    });
}

// Función para cargar imágenes existentes del producto con retry automático
function cargarImagenesExistentes(idProducto, userType = 'empresa', intentos = 0) {
    const container = document.getElementById('current_images_container');
    if (!container) {
        console.error('❌ Container current_images_container no encontrado');
        return;
    }
    
    // Debug: Verificar parámetros recibidos
    console.log('🔍 cargarImagenesExistentes - idProducto:', idProducto, 'userType:', userType, 'intento:', intentos + 1);
    
    // Validar que tenemos un ID válido
    if (!idProducto || idProducto === 'undefined' || idProducto === 'null') {
        console.error('❌ ID de producto inválido:', idProducto);
        container.innerHTML = '<div class="col-12"><p class="text-danger">Error: ID de producto inválido.</p></div>';
        return;
    }
    
    // Mostrar loading con indicador de intento
    const loadingText = intentos > 0 ? `Reintentando cargar imágenes... (${intentos + 1}/3)` : 'Cargando imágenes...';
    container.innerHTML = `<div class="col-12"><p>${loadingText}</p></div>`;
    
    // Determinar el parámetro correcto según el tipo de usuario
    let urlParam;
    if (userType === 'persona') {
        urlParam = `id_producto_usuario=${idProducto}`;
        console.log('🔍 Usando parámetro para persona:', urlParam);
    } else if (userType === 'empresa') {
        urlParam = `id_producto_empresa=${idProducto}`;
        console.log('🔍 Usando parámetro para empresa:', urlParam);
    } else {
        // Fallback para compatibilidad
        urlParam = `id_producto_empresa=${idProducto}`;
        console.log('🔍 Usando parámetro para empresa (fallback):', urlParam);
    }
    
    const url = `/ecommerce/api/obtener_imagenes_producto/?${urlParam}`;
    console.log('🌐 Haciendo fetch a:', url);
    
    // Configurar timeout para la petición
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 segundos timeout
    
    fetch(url, {
        signal: controller.signal,
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    })
        .then(response => {
            clearTimeout(timeoutId);
            console.log('📡 Response status:', response.status);
            console.log('📡 Response ok:', response.ok);
            console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return response.json();
        })
        .then(data => {
            console.log('📦 Data recibida:', data);
            
            if (data.success) {
                console.log('✅ Éxito - Mostrando imágenes:', data.imagenes.length);
                mostrarImagenesExistentes(data.imagenes, userType);
            } else {
                console.log('❌ Error en data.success:', data.error || 'Sin mensaje de error');
                
                // Retry automático si es el primer o segundo intento
                if (intentos < 2) {
                    console.log(`🔄 Reintentando en 1 segundo... (intento ${intentos + 2}/3)`);
                    setTimeout(() => {
                        cargarImagenesExistentes(idProducto, userType, intentos + 1);
                    }, 1000);
                } else {
                    container.innerHTML = '<div class="col-12"><p class="text-muted">No se pudieron cargar las imágenes después de 3 intentos.</p></div>';
                }
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.error('💥 Error completo al cargar imágenes:', error);
            console.error('💥 Error stack:', error.stack);
            console.error('💥 Error name:', error.name);
            
            // Retry automático si es el primer o segundo intento y no es un error de abort
            if (intentos < 2 && error.name !== 'AbortError') {
                console.log(`🔄 Reintentando en 2 segundos... (intento ${intentos + 2}/3)`);
                setTimeout(() => {
                    cargarImagenesExistentes(idProducto, userType, intentos + 1);
                }, 2000);
            } else {
                let errorMsg = 'Error al cargar las imágenes.';
                if (error.name === 'AbortError') {
                    errorMsg = 'Timeout: La carga de imágenes tardó demasiado.';
                } else if (intentos >= 2) {
                    errorMsg = 'Error al cargar las imágenes después de 3 intentos.';
                }
                
                container.innerHTML = `<div class="col-12"><p class="text-danger">${errorMsg}</p><button class="btn btn-sm btn-outline-primary mt-2" onclick="cargarImagenesExistentes('${idProducto}', '${userType}', 0)">Reintentar</button></div>`;
            }
        });
}

// Función para mostrar las imágenes existentes
function mostrarImagenesExistentes(imagenes, userType = 'empresa') {
    const container = document.getElementById('current_images_container');
    if (!container) return;
    
    if (imagenes.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-muted">No hay imágenes registradas para este producto.</p></div>';
        return;
    }
    
    let html = '';
    imagenes.forEach(imagen => {
        // Determinar el ID de imagen según el tipo de usuario
        let imagenId, imagenIdField;
        if (userType.toLowerCase() === 'persona') {
            imagenId = imagen.id_imagen_producto_usuario;
            imagenIdField = 'id_imagen_producto_usuario';
        } else {
            imagenId = imagen.id_imagen_producto_empresa;
            imagenIdField = 'id_imagen_producto_empresa';
        }
        
        html += `
            <div class="col-md-4 col-sm-6 col-6 mb-2" id="imagen_${imagenId}">
                <div class="card" style="border-radius: 8px; overflow: hidden;">
                    <img src="${imagen.url}" class="card-img-top" style="height: 80px; object-fit: cover;" alt="Imagen del producto">
                    <div class="card-body p-1">
                        <button type="button" class="btn btn-danger btn-sm w-100" style="font-size: 11px; padding: 4px 8px;" onclick="eliminarImagen(${imagenId}, 'producto', '${userType}')">
                            <i class="fas fa-trash" style="font-size: 10px;"></i> Eliminar
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Función para eliminar una imagen específica
function eliminarImagen(idImagen, tipo, userType = 'empresa') {
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
            
            // Determinar el nombre del parámetro según el tipo y usuario
            let paramName;
            if (tipo === 'producto') {
                paramName = (userType.toLowerCase() === 'persona') ? 'id_imagen_producto_usuario' : 'id_imagen_producto_empresa';
            } else {
                paramName = (userType.toLowerCase() === 'persona') ? 'id_imagen_servicio_usuario' : 'id_imagen_servicio_empresa';
            }
            
            formData.append(paramName, idImagen);
            
            const endpoint = tipo === 'producto' ? '/ecommerce/api/eliminar_imagen_producto/' : '/ecommerce/api/eliminar_imagen_servicio/';
            
            fetch(endpoint, {
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
                    const imagenElement = document.getElementById(`imagen_${idImagen}`);
                    if (imagenElement) {
                        imagenElement.remove();
                        
                        // Verificar si no quedan más imágenes y mostrar mensaje
                        const container = document.getElementById('current_images_container');
                        if (container && container.children.length === 0) {
                            container.innerHTML = '<div class="col-12"><p class="text-muted">No hay imágenes registradas para este producto.</p></div>';
                        }
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
                    text: 'Error al eliminar la imagen',
                    icon: 'error'
                });
            });
        }
    });
}

// Script para cargar datos en el modal de producto_config
document.addEventListener('DOMContentLoaded', function() {
    console.log('Script cargado - buscando botones de editar y eliminar');
    
    // Event listener para el botón de eliminar
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-delete')) {
            console.log('Botón de eliminar encontrado');
            const button = e.target.closest('.btn-delete');
            const idProducto = button.getAttribute('data-id');
            const nombreProducto = button.getAttribute('data-nombre');
            
            console.log('Datos para eliminar:', { idProducto, nombreProducto });
            
            // Llamar a la función de confirmación
            confirmarEliminacionProducto(idProducto, nombreProducto);
        }
    });
    
    // Event listener para el botón de editar
    document.addEventListener('click', function(e) {
        console.log('Click detectado en:', e.target);
        console.log('Clases del elemento clickeado:', e.target.className);
        console.log('Elemento padre más cercano:', e.target.parentElement);
        
        if (e.target.closest('.btn-edit')) {
            console.log('✅ Botón de editar encontrado');
            const button = e.target.closest('.btn-edit');
            console.log('Botón encontrado:', button);
            console.log('Atributos del botón:', button.attributes);
            
            // Obtener los datos del producto desde los atributos data-
            const id = button.getAttribute('data-id');
            const nombre = button.getAttribute('data-nombre');
            const marca = button.getAttribute('data-marca');
            const modelo = button.getAttribute('data-modelo');
            const categoria = button.getAttribute('data-categoria');
            const estatus = button.getAttribute('data-estatus');
            const descripcion = button.getAttribute('data-descripcion');
            const caracteristicas = button.getAttribute('data-caracteristicas');
            const stock = button.getAttribute('data-stock');
            const precio = button.getAttribute('data-precio');
            const condicion = button.getAttribute('data-condicion');
            const estatusUsuario = button.getAttribute('data-estatus');
            const imagen = button.getAttribute('data-imagen');
            
            console.log('Datos obtenidos:', { id, nombre, marca, modelo, categoria, estatus, descripcion, caracteristicas, stock, precio, condicion, estatusUsuario, imagen });
            
            // Debug detallado de todos los atributos data-
            console.log('=== DEBUG ATRIBUTOS DATA- ===');
            console.log('data-id:', id);
            console.log('data-nombre:', nombre);
            console.log('data-stock:', stock);
            console.log('data-precio:', precio);
            console.log('data-condicion:', condicion);
            console.log('data-estatus:', estatusUsuario);
            console.log('data-marca:', marca);
            console.log('data-modelo:', modelo);
            console.log('data-categoria:', categoria);
            console.log('data-estatus:', estatus);
            console.log('data-descripcion:', descripcion);
            console.log('data-caracteristicas:', caracteristicas);
            console.log('data-imagen:', imagen);
            
            // Cargar los datos en los campos del modal
            try {
                // Función para detectar el tipo de usuario de manera robusta
                function detectarTipoUsuario() {
                    // Método 1: Desde el current_images_container
                    const userTypeElement = document.getElementById('current_images_container');
                    console.log('🔍 Elemento current_images_container:', userTypeElement);
                    
                    if (userTypeElement) {
                        const rawUserType = userTypeElement.getAttribute('data-user-type');
                        console.log('🔍 Valor RAW de data-user-type:', rawUserType);
                        
                        if (rawUserType && rawUserType.trim()) {
                            console.log('✅ Tipo de usuario detectado desde data-user-type:', rawUserType.trim());
                            return rawUserType.trim();
                        }
                    }
                    
                    // Método 2: Detectar desde los campos del formulario
                    const stockField = document.getElementById('edit_stock');
                    const precioField = document.getElementById('edit_precio');
                    const condicionField = document.getElementById('edit_condicion');
                    
                    if (stockField || precioField || condicionField) {
                        console.log('✅ Campos de usuario persona detectados, usando tipo: persona');
                        return 'persona';
                    }
                    
                    // Método 3: Detectar desde el ID del producto en el botón
                    if (id && (button.getAttribute('data-id') || '').includes('usuario')) {
                        console.log('✅ ID contiene "usuario", usando tipo: persona');
                        return 'persona';
                    }
                    
                    // Método 4: Fallback por defecto
                    console.log('⚠️ No se pudo detectar el tipo de usuario, usando fallback: empresa');
                    return 'empresa';
                }
                
                const userType = detectarTipoUsuario();
                console.log('🔍 userType FINAL:', userType);
                
                console.log('Tipo de usuario detectado:', userType);
                
                // Asignar ID según el tipo de usuario
                if (userType === 'empresa') {
                    const idField = document.getElementById('edit_id_producto_empresa');
                    console.log('Campo ID empresa encontrado:', idField);
                    if (idField) {
                        idField.value = id || '';
                        console.log('✅ ID de producto empresa asignado:', id);
                    } else {
                        console.log('❌ Campo edit_id_producto_empresa no encontrado');
                    }
                } else if (userType === 'persona') {
                    const idField = document.getElementById('edit_id_producto_usuario');
                    console.log('Campo ID usuario encontrado:', idField);
                    if (idField) {
                        idField.value = id || '';
                        console.log('✅ ID de producto usuario asignado:', id);
                    } else {
                        console.log('❌ Campo edit_id_producto_usuario no encontrado');
                    }
                }
                
                // Asignar valores a los campos del modal
                const nombreField = document.getElementById('edit_nombre');
                const marcaField = document.getElementById('edit_marca');
                const modeloField = document.getElementById('edit_modelo');
                
                if (nombreField) {
                    nombreField.value = nombre || '';
                    console.log('✅ Nombre asignado:', nombre);
                } else {
                    console.log('❌ Campo edit_nombre no encontrado');
                }
                
                if (marcaField) {
                    marcaField.value = marca || '';
                    console.log('✅ Marca asignada:', marca);
                } else {
                    console.log('❌ Campo edit_marca no encontrado');
                }
                
                if (modeloField) {
                    modeloField.value = modelo || '';
                    console.log('✅ Modelo asignado:', modelo);
                } else {
                    console.log('❌ Campo edit_modelo no encontrado');
                }
                
                // Asignar categoría
                const categoriaSelect = document.getElementById('edit_categoria');
                console.log('Select de categoría encontrado:', categoriaSelect);
                if (categoriaSelect && categoria) {
                    console.log('=== DEBUG CATEGORÍA ===');
                    console.log('Categoría obtenida del botón:', categoria);
                    console.log('Elemento select encontrado:', categoriaSelect);
                    
                    // Mostrar todas las opciones disponibles
                    const options = Array.from(categoriaSelect.options);
                    console.log('Opciones disponibles en el select:');
                    options.forEach((option, index) => {
                        console.log(`Opción ${index}: value="${option.value}", text="${option.text}"`);
                    });
                    
                    // Buscar la opción por texto (nombre de categoría)
                    const matchingOption = options.find(option => 
                        option.text.trim().toLowerCase() === categoria.trim().toLowerCase()
                    );
                    
                    if (matchingOption) {
                        categoriaSelect.value = matchingOption.value;
                        console.log('✅ Categoría asignada correctamente:', matchingOption.value, '->', matchingOption.text);
                    } else {
                        console.log('❌ No se encontró la categoría:', categoria);
                        console.log('Categorías disponibles:', options.map(opt => opt.text).join(', '));
                    }
                } else {
                    console.log('❌ No se pudo obtener el select de categoría o la categoría está vacía');
                }
                
                // Asignar descripción y características
                const descripcionField = document.getElementById('edit_descripcion');
                const caracteristicasField = document.getElementById('edit_caracteristicas');
                
                if (descripcionField) {
                    descripcionField.value = descripcion || '';
                    console.log('✅ Descripción asignada:', descripcion);
                } else {
                    console.log('❌ Campo edit_descripcion no encontrado');
                }
                
                if (caracteristicasField) {
                    caracteristicasField.value = caracteristicas || '';
                    console.log('✅ Características asignadas:', caracteristicas);
                } else {
                    console.log('❌ Campo edit_caracteristicas no encontrado');
                }
                
                // Asignar campos adicionales para usuarios tipo persona
                if (userType === 'persona') {
                    const stockField = document.getElementById('edit_stock');
                    const precioField = document.getElementById('edit_precio');
                    const condicionField = document.getElementById('edit_condicion');
                    const estatusField = document.getElementById('edit_estatus');
                    
                    if (stockField) {
                        stockField.value = stock || '0';
                        console.log('✅ Stock asignado:', stock);
                    } else {
                        console.log('❌ Campo edit_stock no encontrado');
                    }
                    
                    if (precioField) {
                        precioField.value = precio || '0';
                        console.log('✅ Precio asignado:', precio);
                    } else {
                        console.log('❌ Campo edit_precio no encontrado');
                    }
                    
                    if (condicionField) {
                        condicionField.value = condicion || 'Nuevo';
                        console.log('✅ Condición asignada:', condicion);
                    } else {
                        console.log('❌ Campo edit_condicion no encontrado');
                    }
                    
                    if (estatusField) {
                        estatusField.value = estatusUsuario || 'Activo';
                        console.log('✅ Estatus asignado:', estatusUsuario);
                    } else {
                        console.log('❌ Campo edit_estatus no encontrado');
                    }
                }
                
                // Cargar imágenes existentes del producto
                cargarImagenesExistentes(id, userType);
                
                // Limpiar preview de nuevas imágenes
                const imagePreview = document.getElementById('edit_imagePreview');
                if (imagePreview) {
                    imagePreview.innerHTML = '';
                }
                
                console.log('Datos cargados exitosamente en el modal');
                
            } catch (error) {
                console.error('Error al cargar datos en el modal:', error);
            }
        }
    });
    
    // Manejar el envío del formulario
    setTimeout(() => {
        const editProductoForm = document.getElementById('editProductoForm');
        console.log('Buscando formulario de edición:', editProductoForm);
        
        if (editProductoForm) {
            console.log('Formulario encontrado, agregando event listener');
            
            // Remover el onsubmit por defecto
            editProductoForm.onsubmit = null;
            
            editProductoForm.addEventListener('submit', function(e) {
                console.log('Evento submit capturado');
                e.preventDefault();
                e.stopPropagation();
                console.log('Envío tradicional prevenido');
                
                // Crear FormData para enviar archivos
                const formData = new FormData(this);
                
                // Debug: Mostrar todos los datos que se van a enviar
                console.log('=== DEBUG DATOS DEL FORMULARIO ===');
                for (let [key, value] of formData.entries()) {
                    console.log(`${key}: ${value}`);
                }
                
                // Mostrar indicador de carga
                const submitButton = this.querySelector('button[type="submit"]');
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="lni lni-spinner"></i> Guardando...';
                submitButton.disabled = true;
                
                console.log('Enviando formulario via AJAX a:', this.action);
                
                // Enviar formulario via AJAX
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                })
                .then(response => {
                    console.log('Status de respuesta:', response.status);
                    return response.text(); // Primero obtener como texto
                })
                .then(text => {
                    console.log('Respuesta en texto:', text);
                    
                    try {
                        const data = JSON.parse(text); // Intentar parsear como JSON
                        console.log('Respuesta parseada:', data);
                        
                        if (data.success) {
                            // Éxito
                            Swal.fire({
                                icon: 'success',
                                title: '¡Éxito!',
                                text: data.message,
                                confirmButtonColor: '#3085d6',
                                confirmButtonText: 'Aceptar'
                            }).then((result) => {
                                // Cerrar modal correctamente
                                const modalElement = document.getElementById('EditProductModal');
                                const modal = bootstrap.Modal.getInstance(modalElement);
                                if (modal) {
                                    modal.hide();
                                } else {
                                    // Si no hay instancia, crear una y cerrarla
                                    const newModal = new bootstrap.Modal(modalElement);
                                    newModal.hide();
                                }
                                
                                // Recargar página para mostrar cambios
                                setTimeout(() => {
                                    window.location.reload();
                                }, 500);
                            });
                            
                        } else {
                            // Error
                            Swal.fire({
                                icon: 'error',
                                title: 'Error',
                                text: data.message,
                                confirmButtonColor: '#d33',
                                confirmButtonText: 'Aceptar'
                            });
                        }
                    } catch (e) {
                        console.error('Error al parsear JSON:', e);
                        console.log('Respuesta no es JSON válido:', text);
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'Error en la respuesta del servidor',
                            confirmButtonColor: '#d33',
                            confirmButtonText: 'Aceptar'
                        });
                    }
                })
                .catch(error => {
                    console.error('Error al enviar formulario:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Error al enviar el formulario. Por favor, inténtalo de nuevo.',
                        confirmButtonColor: '#d33',
                        confirmButtonText: 'Aceptar'
                    });
                })
                .finally(() => {
                    // Restaurar botón
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                });
                
                return false; // Prevenir envío adicional
            });
            
            console.log('Event listener agregado al formulario');
        } else {
            console.error('❌ No se encontró el formulario editProductoForm');
        }
    }, 100); // Pequeño delay para asegurar que el DOM esté listo
    
    // Configurar el modal para evitar problemas de aria-hidden
    const modal = document.getElementById('EditProductModal');
    if (modal) {
        // Configurar opciones del modal para mejor accesibilidad
        modal.addEventListener('show.bs.modal', function() {
            // Remover aria-hidden cuando el modal se muestra
            this.removeAttribute('aria-hidden');
        });
        
        modal.addEventListener('shown.bs.modal', function() {
            // Asegurar que el modal no tenga aria-hidden cuando está visible
            this.removeAttribute('aria-hidden');
        });
        
        modal.addEventListener('hide.bs.modal', function() {
            // Manejar el cierre del modal correctamente
            const focusedElement = document.activeElement;
            if (focusedElement && this.contains(focusedElement)) {
                focusedElement.blur();
            }
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            try {
                // Limpiar todos los campos
                // Limpiar campos según el tipo de usuario
            const empresaIdField = document.getElementById('edit_id_producto_empresa');
            const usuarioIdField = document.getElementById('edit_id_producto_usuario');
            if (empresaIdField) empresaIdField.value = '';
            if (usuarioIdField) usuarioIdField.value = '';
            
            document.getElementById('edit_nombre').value = '';
            document.getElementById('edit_marca').value = '';
                document.getElementById('edit_modelo').value = '';
                document.getElementById('edit_categoria').value = '';
                document.getElementById('edit_descripcion').value = '';
                document.getElementById('edit_caracteristicas').value = '';
                document.getElementById('edit_imagenes_producto').value = '';
                
                // Limpiar previsualizaciones
                const imagePreview = document.getElementById('edit_imagePreview');
                if (imagePreview) imagePreview.innerHTML = '';
                
                console.log('Modal cerrado - campos limpiados');
            } catch (error) {
                console.error('Error al limpiar el modal:', error);
            }
        });
    }
});