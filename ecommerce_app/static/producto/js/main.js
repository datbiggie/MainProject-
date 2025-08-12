// Función para previsualizar la imagen
function previewImage(input) {
    console.log('Función previewImage llamada');
    const container = input.closest('.file-upload-container');
    const preview = document.getElementById('imagePreview');
    const file = input.files[0];
    
    console.log('Archivo seleccionado:', file);
    
    if (file) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            console.log('Imagen cargada en el reader');
            // Crear la imagen
            const img = document.createElement('img');
            img.src = e.target.result;
            img.alt = 'Preview';
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'contain';
            
            // Limpiar y agregar la imagen
            preview.innerHTML = '';
            preview.appendChild(img);
            
            // Mostrar la previsualización
            preview.style.display = 'block';
            container.classList.add('has-image');
            
            // Ocultar el placeholder
            const placeholder = container.querySelector('.file-upload-placeholder');
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            console.log('Previsualización actualizada');
        };
        
        reader.onerror = function(error) {
            console.error('Error al leer la imagen:', error);
            Swal.fire({
                title: 'Error',
                text: 'Error al cargar la imagen',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
        };
        
        reader.readAsDataURL(file);
    } else {
        console.log('No se seleccionó ningún archivo');
        preview.innerHTML = '';
        preview.style.display = 'none';
        container.classList.remove('has-image');
        
        // Mostrar el placeholder
        const placeholder = container.querySelector('.file-upload-placeholder');
        if (placeholder) {
            placeholder.style.display = 'flex';
        }
    }
}

// Código movido al bloque $(document).ready() para evitar conflictos

$(document).ready(function() {
    // Verificar que SweetAlert2 está cargado
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 no está cargado');
    } else {
        console.log('SweetAlert2 está cargado correctamente');
    }
    
    // Manejo de parámetros URL para mensajes
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
        Swal.fire({
            title: '¡Producto Registrado!',
            text: 'El producto ha sido creado correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    } else if (urlParams.has('updated')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'El producto ha sido actualizado correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('deleted')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'El producto ha sido eliminado correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('error')) {
        const errorMsg = urlParams.get('error_msg') || 'Ha ocurrido un error al procesar la solicitud';
        const errorField = urlParams.get('error_field');
        Swal.fire({
            title: 'Error',
            text: errorMsg,
            icon: 'error',
            confirmButtonText: 'Aceptar'
        }).then(() => {
            if (errorField) {
                const $el = document.getElementById(errorField);
                if ($el) $el.focus();
            }
        });
    }

    // Función para crear previsualización de imagen
    function createImagePreview(file, previewContainer) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewContainer.innerHTML = '';
            const img = document.createElement('img');
            img.src = e.target.result;
            img.style.width = '100%';
            img.style.maxWidth = '150px';
            img.style.height = '100px';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '8px';
            img.style.border = '2px solid #ddd';
            img.style.marginTop = '10px';
            previewContainer.appendChild(img);
        };
        reader.readAsDataURL(file);
    }
    
    // Configurar event listeners para cada input de imagen
    for (let i = 1; i <= 5; i++) {
        const input = document.getElementById(`imagen_${i}`);
        const preview = document.getElementById(`preview_${i}`);
        
        if (input && preview) {
            input.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    createImagePreview(file, preview);
                } else {
                    preview.innerHTML = '';
                }
            });
        }
    }
    
    // Función para verificar si al menos una imagen está seleccionada
    function hasAtLeastOneImage() {
        for (let i = 1; i <= 5; i++) {
            const input = document.getElementById(`imagen_${i}`);
            if (input && input.files.length > 0) {
                return true;
            }
        }
        return false;
    }

    // Manejar el envío del formulario
    const form = $('#productoForm');
    if (form.length === 0) {
        console.error('No se encontró el formulario con ID productoForm');
        return;
    }

    let isSubmitting = false;

    form.on('submit', function(e) {
        e.preventDefault();
        e.stopPropagation();

        if (isSubmitting) {
            console.log('Ya hay un envío en proceso');
            return false;
        }

        // Validar que al menos una imagen esté seleccionada
        if (!hasAtLeastOneImage()) {
            Swal.fire({
                title: 'Error',
                text: 'Debes seleccionar al menos una imagen para el producto',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            return false;
        }

        const submitButton = form.find('input[type="submit"]');
        submitButton.prop('disabled', true);
        isSubmitting = true;

        // Crear FormData personalizado para enviar las imágenes con el nombre correcto
        const formData = new FormData(this);
        
        // Remover los campos de imagen individuales
        formData.delete('imagen_1');
        formData.delete('imagen_2');
        formData.delete('imagen_3');
        formData.delete('imagen_4');
        formData.delete('imagen_5');
        
        // Agregar todas las imágenes seleccionadas con el nombre 'imagenes_producto'
        for (let i = 1; i <= 5; i++) {
            const imageInput = document.getElementById(`imagen_${i}`);
            if (imageInput && imageInput.files.length > 0) {
                formData.append('imagenes_producto', imageInput.files[0]);
            }
        }

        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log('Respuesta del servidor:', response);
                if (response.success) {
                    Swal.fire({
                        title: '¡Registro exitoso!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            form[0].reset();
                            const container = document.querySelector('.file-upload-container');
                            container.classList.remove('has-image');
                            document.getElementById('imagePreview').style.display = 'none';
                            
                            // Mostrar el placeholder nuevamente
                            const placeholder = container.querySelector('.file-upload-placeholder');
                            if (placeholder) {
                                placeholder.style.display = 'flex';
                            }
                            
                            setTimeout(function() {
                                window.location.reload();
                            }, 1500);
                        }
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: response.message,
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then(() => {
                        // Foco automático según el campo de error
                        if (response.field) {
                            const $el = document.getElementById(response.field);
                            if ($el) $el.focus();
                        }
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Error en la petición AJAX:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al procesar la solicitud',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
            },
            complete: function() {
                submitButton.prop('disabled', false);
                isSubmitting = false;
            }
        });

        return false;
    });
});
