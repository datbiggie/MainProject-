// ========================= Producto Config Modal JavaScript =========================

// Variables globales
let currentProductId = null;
let userType = null;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Obtener el tipo de usuario del contenedor
    const container = document.querySelector('[data-user-type]');
    if (container) {
        userType = container.getAttribute('data-user-type');
    }
    
    // Inicializar eventos
    initializeModalEvents();
    initializeDeleteEvents();
    initializeImagePreview();
    initializeFormSubmission();
});

// ========================= Modal Events =========================
function initializeModalEvents() {
    const editModal = document.getElementById('EditProductModal');
    if (!editModal) return;
    
    // Evento cuando se abre el modal
    editModal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        if (!button) return;
        
        // Obtener datos del producto
        const productData = {
            id: button.getAttribute('data-id'),
            nombre: button.getAttribute('data-nombre'),
            marca: button.getAttribute('data-marca'),
            modelo: button.getAttribute('data-modelo'),
            categoria: button.getAttribute('data-categoria'),
            descripcion: button.getAttribute('data-descripcion'),
            caracteristicas: button.getAttribute('data-caracteristicas'),
            imagen: button.getAttribute('data-imagen')
        };
        
        // Para usuarios tipo 'persona', obtener campos adicionales
        if (userType === 'persona') {
            productData.stock = button.getAttribute('data-stock');
            productData.precio = button.getAttribute('data-precio');
            productData.condicion = button.getAttribute('data-condicion');
            productData.estatus = button.getAttribute('data-estatus');
            productData.latitud = button.getAttribute('data-latitud');
            productData.longitud = button.getAttribute('data-longitud');
        }
        
        // Llenar el formulario
        populateEditForm(productData);
        
        // Cargar imágenes actuales
        loadCurrentImages(productData.id);
        
        // Guardar ID actual
        currentProductId = productData.id;
    });
    
    // Limpiar modal al cerrarse
    editModal.addEventListener('hidden.bs.modal', function() {
        clearModalForm();
        currentProductId = null;
    });
}

// ========================= Populate Form =========================
function populateEditForm(data) {
    // Campos comunes
    setFieldValue('edit_nombre', data.nombre);
    setFieldValue('edit_marca', data.marca);
    setFieldValue('edit_modelo', data.modelo);
    setFieldValue('edit_descripcion', data.descripcion);
    setFieldValue('edit_caracteristicas', data.caracteristicas);
    
    // ID del producto
    if (userType === 'empresa') {
        setFieldValue('edit_id_producto_empresa', data.id);
    } else {
        setFieldValue('edit_id_producto_usuario', data.id);
    }
    
    // Categoría
    const categoriaSelect = document.getElementById('edit_categoria');
    if (categoriaSelect && data.categoria) {
        // Buscar la opción que coincida con el nombre de la categoría
        for (let option of categoriaSelect.options) {
            if (option.text === data.categoria) {
                option.selected = true;
                break;
            }
        }
    }
    
    // Campos específicos para usuarios tipo 'persona'
    if (userType === 'persona') {
        setFieldValue('edit_stock', data.stock);
        setFieldValue('edit_precio', data.precio);
        setSelectValue('edit_condicion', data.condicion);
        setSelectValue('edit_estatus', data.estatus);
        
        // Inicializar mapa con coordenadas guardadas
        if (typeof initializeEditMapOnModalShow === 'function') {
            initializeEditMapOnModalShow(data.latitud, data.longitud);
        }
    }
}

// ========================= Utility Functions =========================
function setFieldValue(fieldId, value) {
    const field = document.getElementById(fieldId);
    if (field && value) {
        field.value = value;
    }
}

function setSelectValue(fieldId, value) {
    const field = document.getElementById(fieldId);
    if (field && value) {
        field.value = value;
    }
}

// ========================= Load Current Images =========================
function loadCurrentImages(productId) {
    const container = document.getElementById('current_images_container');
    if (!container) return;
    
    // Mostrar loading
    container.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Cargando imágenes...</div>';
    
    // Hacer petición AJAX para obtener las imágenes
    fetch(`/ecommerce/get_product_images/${productId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.images) {
            displayCurrentImages(data.images);
        } else {
            container.innerHTML = '<p class="text-muted">No hay imágenes disponibles</p>';
        }
    })
    .catch(error => {
        console.error('Error loading images:', error);
        container.innerHTML = '<p class="text-danger">Error al cargar las imágenes</p>';
    });
}

// ========================= Display Current Images =========================
function displayCurrentImages(images) {
    const container = document.getElementById('current_images_container');
    if (!container) return;
    
    if (images.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay imágenes disponibles</p>';
        return;
    }
    
    let html = '';
    images.forEach((image, index) => {
        html += `
            <div class="col-4 mb-2">
                <div class="position-relative">
                    <img src="${image.url}" alt="Imagen ${index + 1}" class="img-fluid" style="width: 100%; height: 80px; object-fit: cover; border-radius: 0.5rem; border: 2px solid #e1e5e9;">
                    <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1 delete-image-btn" 
                            data-image-id="${image.id}" 
                            style="padding: 0.2rem 0.4rem; font-size: 0.7rem; border-radius: 50%;">
                        <i class="lni lni-close"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Agregar eventos para eliminar imágenes
    container.querySelectorAll('.delete-image-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const imageId = this.getAttribute('data-image-id');
            deleteProductImage(imageId);
        });
    });
}

// ========================= Delete Product Image =========================
function deleteProductImage(imageId) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta imagen?')) {
        return;
    }
    
    fetch(`/ecommerce/delete_product_image/${imageId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Recargar las imágenes
            loadCurrentImages(currentProductId);
            showAlert('Imagen eliminada correctamente', 'success');
        } else {
            showAlert('Error al eliminar la imagen: ' + (data.message || 'Error desconocido'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al eliminar la imagen', 'error');
    });
}

// ========================= Image Preview =========================
function initializeImagePreview() {
    const fileInput = document.getElementById('edit_imagenes_producto');
    const previewContainer = document.getElementById('edit_imagePreview');
    
    if (!fileInput || !previewContainer) return;
    
    fileInput.addEventListener('change', function() {
        previewContainer.innerHTML = '';
        
        if (this.files.length === 0) return;
        
        Array.from(this.files).forEach((file, index) => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.cssText = 'width: 60px; height: 60px; object-fit: cover; border-radius: 0.5rem; border: 2px solid #e1e5e9; margin: 0.2rem;';
                    previewContainer.appendChild(img);
                };
                reader.readAsDataURL(file);
            }
        });
    });
}

// ========================= Form Submission =========================
function initializeFormSubmission() {
    const form = document.getElementById('editProductoForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validar formulario
        if (!validateForm()) {
            return;
        }
        
        // Mostrar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
        submitBtn.disabled = true;
        
        // Crear FormData
        const formData = new FormData(form);
        
        // Enviar formulario
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Producto actualizado correctamente', 'success');
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('EditProductModal'));
                modal.hide();
                // Recargar página para mostrar cambios
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showAlert('Error al actualizar el producto: ' + (data.message || 'Error desconocido'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al actualizar el producto', 'error');
        })
        .finally(() => {
            // Restaurar botón
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });
}

// ========================= Form Validation =========================
function validateForm() {
    const requiredFields = [
        'edit_nombre',
        'edit_categoria',
        'edit_caracteristicas'
    ];
    
    let isValid = true;
    
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field && !field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else if (field) {
            field.classList.remove('is-invalid');
        }
    });
    
    if (!isValid) {
        showAlert('Por favor, completa todos los campos requeridos', 'warning');
    }
    
    return isValid;
}

// ========================= Delete Events =========================
function initializeDeleteEvents() {
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-delete') || e.target.closest('.btn-delete')) {
            e.preventDefault();
            
            const btn = e.target.classList.contains('btn-delete') ? e.target : e.target.closest('.btn-delete');
            const productId = btn.getAttribute('data-id');
            const productName = btn.getAttribute('data-nombre');
            
            deleteProduct(productId, productName);
        }
    });
}

// ========================= Delete Product =========================
function deleteProduct(productId, productName) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: `¿Quieres eliminar el producto "${productName}"? Esta acción no se puede deshacer.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Realizar eliminación
            const formData = new FormData();
            
            // Determinar el tipo de usuario y agregar el ID correspondiente
            if (userType === 'persona') {
                formData.append('id_producto_usuario', productId);
            } else if (userType === 'empresa') {
                formData.append('id_producto_empresa', productId);
            }
            
            fetch('/ecommerce/eliminar_producto/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken()
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: '¡Eliminado!',
                        text: 'El producto ha sido eliminado correctamente.',
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: 'Error al eliminar el producto: ' + (data.message || 'Error desconocido'),
                        icon: 'error'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'Error al eliminar el producto',
                    icon: 'error'
                });
            });
        }
    });
}

// ========================= Clear Modal Form =========================
function clearModalForm() {
    const form = document.getElementById('editProductoForm');
    if (form) {
        form.reset();
        
        // Limpiar preview de imágenes
        const previewContainer = document.getElementById('edit_imagePreview');
        if (previewContainer) {
            previewContainer.innerHTML = '';
        }
        
        // Limpiar contenedor de imágenes actuales
        const currentImagesContainer = document.getElementById('current_images_container');
        if (currentImagesContainer) {
            currentImagesContainer.innerHTML = '';
        }
        
        // Remover clases de validación
        form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        
        // Limpiar mapa para usuarios persona
        if (userType === 'persona' && typeof clearEditMapState === 'function') {
            clearEditMapState();
        }
    }
}

// ========================= Utility Functions =========================
function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

function showAlert(message, type = 'info') {
    let icon = 'info';
    let title = 'Información';
    
    switch(type) {
        case 'success':
            icon = 'success';
            title = '¡Éxito!';
            break;
        case 'error':
            icon = 'error';
            title = 'Error';
            break;
        case 'warning':
            icon = 'warning';
            title = 'Advertencia';
            break;
    }
    
    Swal.fire({
        title: title,
        text: message,
        icon: icon,
        timer: 3000,
        showConfirmButton: false,
        toast: true,
        position: 'top-end'
    });
}

// ========================= Search Functionality =========================
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('busqueda-producto');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            filterProducts(searchTerm);
        });
    }
});

function filterProducts(searchTerm) {
    const productCards = document.querySelectorAll('#contenedor-productos .col-lg-4');
    
    productCards.forEach(card => {
        const productName = card.querySelector('h3');
        if (productName) {
            const name = productName.textContent.toLowerCase();
            if (name.includes(searchTerm)) {
                card.style.display = 'block';
                card.classList.add('fadeInUp');
            } else {
                card.style.display = 'none';
                card.classList.remove('fadeInUp');
            }
        }
    });
    
    // Mostrar mensaje si no hay resultados
    const visibleCards = document.querySelectorAll('#contenedor-productos .col-lg-4[style="display: block;"]');
    const container = document.getElementById('contenedor-productos');
    
    // Remover mensaje anterior si existe
    const existingMessage = container.querySelector('.no-results-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    if (visibleCards.length === 0 && searchTerm !== '') {
        const noResultsMessage = document.createElement('div');
        // Mensaje eliminado por solicitud del usuario
    }
}