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
            // Crear FormData para enviar los datos
            const formData = new FormData();
            formData.append('id_producto', idProducto);
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
            // Enviar solicitud de eliminación (URL hardcodeada)
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
                    // Éxito
                    Swal.fire({
                        icon: 'success',
                        title: '¡Producto Eliminado!',
                        text: data.message,
                        confirmButtonColor: '#3085d6',
                        confirmButtonText: 'Aceptar'
                    }).then((result) => {
                        // Recargar página para mostrar cambios
                        window.location.reload();
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
        
        if (e.target.closest('.btn-edit')) {
            console.log('Botón de editar encontrado');
            const button = e.target.closest('.btn-edit');
            
            // Obtener los datos del producto desde los atributos data-
            const id = button.getAttribute('data-id');
            const nombre = button.getAttribute('data-nombre');
            const marca = button.getAttribute('data-marca');
            const modelo = button.getAttribute('data-modelo');
            const categoria = button.getAttribute('data-categoria');
            const estatus = button.getAttribute('data-estatus');
            const descripcion = button.getAttribute('data-descripcion');
            const caracteristicas = button.getAttribute('data-caracteristicas');
            const imagen = button.getAttribute('data-imagen');
            
            console.log('Datos obtenidos:', { id, nombre, marca, modelo, categoria, estatus, descripcion, caracteristicas, imagen });
            
            // Debug detallado de todos los atributos data-
            console.log('=== DEBUG ATRIBUTOS DATA- ===');
            console.log('data-id:', id);
            console.log('data-nombre:', nombre);
            console.log('data-marca:', marca);
            console.log('data-modelo:', modelo);
            console.log('data-categoria:', categoria);
            console.log('data-estatus:', estatus);
            console.log('data-descripcion:', descripcion);
            console.log('data-caracteristicas:', caracteristicas);
            console.log('data-imagen:', imagen);
            
            // Cargar los datos en los campos del modal
            try {
                document.getElementById('edit_id_producto').value = id || '';
                document.getElementById('edit_nombre').value = nombre || '';
                document.getElementById('edit_marca').value = marca || '';
                document.getElementById('edit_modelo').value = modelo || '';
                
                // Asignar categoría
                const categoriaSelect = document.getElementById('edit_categoria');
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
                
                document.getElementById('edit_estatus').value = estatus || '';
                document.getElementById('edit_descripcion').value = descripcion || '';
                document.getElementById('edit_caracteristicas').value = caracteristicas || '';
                
                // Mostrar la imagen actual si existe
                const imagePreview = document.getElementById('edit_imagePreview');
                
                if (imagen && imagen !== '') {
                    // Mostrar la imagen actual en el preview del input
                    if (imagePreview) {
                        imagePreview.innerHTML = `
                            <img src="${imagen}" alt="Imagen actual" style="max-width: 150px; max-height: 150px; border-radius: 8px; border: 1px solid #ddd; margin-top: 10px;">
                        `;
                    }
                } else {
                    // Limpiar ambos elementos si no hay imagen
                    if (imagePreview) {
                        imagePreview.innerHTML = '';
                    }
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
                                // Cerrar modal
                                const modal = bootstrap.Modal.getInstance(document.getElementById('EditProductModal'));
                                if (modal) {
                                    modal.hide();
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
    
    // Limpiar el modal cuando se cierre
    const modal = document.getElementById('EditProductModal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            try {
                // Limpiar todos los campos
                document.getElementById('edit_id_producto').value = '';
                document.getElementById('edit_nombre').value = '';
                document.getElementById('edit_marca').value = '';
                document.getElementById('edit_modelo').value = '';
                document.getElementById('edit_categoria').value = '';
                document.getElementById('edit_estatus').value = '';
                document.getElementById('edit_descripcion').value = '';
                document.getElementById('edit_caracteristicas').value = '';
                document.getElementById('edit_imagen_producto').value = '';
                
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