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

document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    // Mensaje de éxito al crear producto
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
        // Si hay mensaje de error y parámetro de campo, enfocar el campo correspondiente
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
});

$(document).ready(function() {
    // Verificar que SweetAlert2 está cargado
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 no está cargado');
    } else {
        console.log('SweetAlert2 está cargado correctamente');
    }

    // Manejar la previsualización de la imagen
    $('#imagen_producto').on('change', function() {
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

        const submitButton = form.find('input[type="submit"]');
        submitButton.prop('disabled', true);
        isSubmitting = true;

        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: new FormData(this),
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
