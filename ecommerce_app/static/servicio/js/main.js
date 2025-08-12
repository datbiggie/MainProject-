$(document).ready(function() {
    // Verificar que SweetAlert2 está cargado
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 no está cargado');
    } else {
        console.log('SweetAlert2 está cargado correctamente');
    }

    // Manejar la previsualización de la imagen
    $('#imagen_servicio').on('change', function() {
        console.log('Cambio detectado en el input de imagen');
        const input = this;
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

    // Función para crear previsualización de imagen
    function createImagePreview(input, previewId) {
        const file = input.files[0];
        const preview = document.getElementById(previewId);
        
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="width: 100%; height: 150px; object-fit: cover; border-radius: 5px;">`;
            };
            reader.readAsDataURL(file);
        } else {
            preview.innerHTML = '';
        }
    }

    // Event listeners para las 5 imágenes de servicio
    for (let i = 1; i <= 5; i++) {
        const imageInput = document.getElementById(`imagen_servicio_${i}`);
        if (imageInput) {
            imageInput.addEventListener('change', function() {
                createImagePreview(this, `preview_servicio_${i}`);
            });
        }
    }
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
    });

    // Manejar el envío del formulario
    const form = $('#servicioForm');
    if (form.length === 0) {
        console.error('No se encontró el formulario con ID servicioForm');
        return;
    }

    let isSubmitting = false;

    // Función para verificar si al menos una imagen está seleccionada
    function hasAtLeastOneImage() {
        for (let i = 1; i <= 5; i++) {
            const imageInput = document.getElementById(`imagen_servicio_${i}`);
            if (imageInput && imageInput.files.length > 0) {
                return true;
            }
        }
        return false;
    }

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
                text: 'Debes seleccionar al menos una imagen para el servicio',
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
        formData.delete('imagen_servicio_1');
        formData.delete('imagen_servicio_2');
        formData.delete('imagen_servicio_3');
        formData.delete('imagen_servicio_4');
        formData.delete('imagen_servicio_5');
        
        // Agregar todas las imágenes seleccionadas con el nombre 'imagenes_servicio'
        for (let i = 1; i <= 5; i++) {
            const imageInput = document.getElementById(`imagen_servicio_${i}`);
            if (imageInput && imageInput.files.length > 0) {
                formData.append('imagenes_servicio', imageInput.files[0]);
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
                            
                            // Limpiar todas las previsualizaciones de imágenes
                            for (let i = 1; i <= 5; i++) {
                                const preview = document.getElementById(`preview_servicio_${i}`);
                                if (preview) {
                                    preview.innerHTML = '';
                                }
                            }
                            
                            setTimeout(function() {
                                window.location.reload();
                            }, 1500);
                        }
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: response.message || 'Error al guardar el servicio',
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
                    text: 'Error al guardar el servicio',
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
    });
});

    // Manejar parámetros URL para mostrar mensajes
    const urlParams = new URLSearchParams(window.location.search);
    
    // Mensaje de éxito al crear servicio
    if (urlParams.get('success') === 'true') {
        Swal.fire({
            title: '¡Servicio Registrado!',
            text: 'El servicio ha sido creado correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    } else if (urlParams.has('updated')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'El servicio ha sido actualizado correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('deleted')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'El servicio ha sido eliminado correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('error')) {
        Swal.fire({
            title: 'Error',
            text: 'Ha ocurrido un error al procesar la solicitud.',
            icon: 'error',
            confirmButtonText: 'Aceptar'
        });
    }

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
