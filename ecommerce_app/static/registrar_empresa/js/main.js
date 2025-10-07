// Función para previsualizar la imagen
function previewImage(input) {
    const preview = document.getElementById('imagePreview');
    const file = input.files[0];
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '';
        preview.style.display = 'none';
    }
}

// Manejar errores de carga de la API de Google Maps
window.onerror = function(msg, url, lineNo, columnNo, error) {
    if (msg.includes('Google Maps')) {
        document.getElementById('map').innerHTML = `
            <div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border-radius: 8px;">
                <h3>Error al cargar el mapa</h3>
                <p>Por favor, verifica tu conexión a internet y recarga la página.</p>
                <p>Si el problema persiste, contacta al administrador.</p>
            </div>
        `;
    }
    return false;
};

// Inicialización cuando el documento está listo
$(document).ready(function() {
    // ===== VALIDACIÓN SOLO NÚMEROS EN TELÉFONO =====
    $('#phone').on('input', function() {
        // Eliminar cualquier carácter que no sea número
        this.value = this.value.replace(/[^0-9]/g, '');
    });

    // ===== FUNCIONALIDAD DE ACORDEÓN =====
    $('.accordion-header').on('click', function() {
        const section = $(this).parent('.accordion-section');
        const isActive = section.hasClass('active');
        
        // Cerrar todas las secciones
        $('.accordion-section').removeClass('active');
        
        // Abrir la sección clickeada si no estaba activa
        if (!isActive) {
            section.addClass('active');
        }
    });
    
    // Abrir la primera sección por defecto
    $('.accordion-section').first().addClass('active');

    // Inicializar Select2 para estados
    $('#state').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Selecciona un estado',
        allowClear: true,
        language: {
            noResults: function() {
                return "No se encontraron resultados";
            },
            searching: function() {
                return "Buscando...";
            }
        },
        dropdownCssClass: 'select2-dropdown-custom'
    });

    // Asegurar que el contenedor de Select2 tenga la misma altura
    $('.select2-container').css('height', '45px');
    $('.select2-selection').css('height', '45px');
    $('.select2-selection__rendered').css('line-height', '45px');

    // Evento para enfocar el campo de búsqueda cuando se abre el select
    $('#state').on('select2:open', function() {
        setTimeout(function() {
            document.querySelector('.select2-search__field').focus();
        }, 0);
    });

    // Inicializar Select2 para tipo de empresa
    $('#tipo_empresa').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Selecciona el tipo de empresa',
        allowClear: true,
        minimumResultsForSearch: -1,
        language: {
            noResults: function() {
                return "No se encontraron resultados";
            },
            searching: function() {
                return "Buscando...";
            }
        },
        dropdownCssClass: 'select2-dropdown-custom'
    });

    // Inicializar Select2 para sector de empresa
    $('#sector_empresa').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Selecciona el sector de la empresa',
        allowClear: true,
        minimumResultsForSearch: -1,
        language: {
            noResults: function() {
                return "No se encontraron resultados";
            },
            searching: function() {
                return "Buscando...";
            }
        },
        dropdownCssClass: 'select2-dropdown-custom'
    });

    // Manejar cambio de país
    $('#country').on('change', function() {
        const countryCode = $(this).val();
        const stateSelect = $('#state');
        
        if (countryCode === 'VE') {
            stateSelect.prop('disabled', false);
            stateSelect.select2('enable');
        } else {
            stateSelect.prop('disabled', true);
            stateSelect.select2('disable');
            stateSelect.val('').trigger('change');
        }
        
        // Validar campo obligatorio
        validateRequiredField(this);
    });

    // Validación en tiempo real para campos obligatorios
    function validateRequiredField(field) {
        const value = $(field).val().trim();
        if (!value) {
            $(field).addClass('required-error');
            $(field).attr('title', 'Este campo es obligatorio');
        } else {
            $(field).removeClass('required-error');
            $(field).removeAttr('title');
        }
    }

    // Aplicar validación a todos los campos obligatorios
    $('#firstname, #email, #phone, #descripcion_empresa, #direccion_empresa').on('blur input', function() {
        validateRequiredField(this);
    });

    // Validación especial para textarea
    $('#descripcion_empresa').on('blur input', function() {
        validateRequiredField(this);
    });

    // Validación especial para selects
    $('#state, #tipo_empresa').on('change', function() {
        const value = $(this).val();
        if (!value) {
            $(this).addClass('required-error');
            $(this).attr('title', 'Debe seleccionar una opción');
        } else {
            $(this).removeClass('required-error');
            $(this).removeAttr('title');
        }
    });

    // Validación para checkbox de términos
    $('#supportCheckbox').on('change', function() {
        if (!$(this).is(':checked')) {
            $(this).addClass('required-error');
            $(this).attr('title', 'Debe aceptar los términos y condiciones');
        } else {
            $(this).removeClass('required-error');
            $(this).removeAttr('title');
        }
    });

    // Manejar el envío SOLO del formulario de registro de empresa, no el de login
    var empresaForm = $("#step2 form");
    if (empresaForm.length) {
        empresaForm.on('submit', function(e) {
            // Solo validar si el formulario está visible (step2 activo)
            if (!$('#step2').hasClass('active')) {
                return true;
            }
            e.preventDefault();

            // Validar campos obligatorios antes de enviar
            const nombre_empresa = $('#firstname').val().trim();
            const descripcion_empresa = $('#descripcion_empresa').val().trim();
            const pais_empresa = $('#country').val();
            const estado_empresa = $('#state').val();
            const tipo_empresa = $('#tipo_empresa').val();
            const direccion_empresa = $('#direccion_empresa').val().trim();

            // Validar checkbox de términos y condiciones
            const checkbox = $('#supportCheckbox').is(':checked');

            // Validar campos vacíos
            if (!nombre_empresa || !descripcion_empresa || !pais_empresa || !estado_empresa || !tipo_empresa || !direccion_empresa) {
                Swal.fire({
                    title: 'Campos obligatorios',
                    text: 'Todos los campos son obligatorios. Por favor complete todos los campos.',
                    icon: 'warning',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
                return false;
            }

            // Validar checkbox de términos y condiciones
            if (!checkbox) {
                Swal.fire({
                    title: 'Términos y condiciones',
                    text: 'Debe aceptar los términos y condiciones para continuar.',
                    icon: 'warning',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
                $('#supportCheckbox').focus();
                return false;
            }

            // Si pasa validación, enviar el formulario con AJAX
            const formData = new FormData(this);
            
            $.ajax({
                url: $(this).attr('action') || window.location.pathname,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        Swal.fire({
                            title: '¡Registro exitoso!',
                            text: response.message || 'Empresa registrada correctamente',
                            icon: 'success',
                            confirmButtonText: 'Continuar',
                            confirmButtonColor: '#3b82f6'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                // Redirigir a la página de sucursal
                                window.location.href = response.redirect_url || '/ecommerce/sucursal/';
                            }
                        });
                    } else {
                        Swal.fire({
                            title: 'Error en el registro',
                            text: response.message || 'Ocurrió un error al registrar la empresa',
                            icon: 'error',
                            confirmButtonText: 'Aceptar',
                            confirmButtonColor: '#3b82f6'
                        });
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error en la petición AJAX:', error);
                    Swal.fire({
                        title: 'Error de conexión',
                        text: 'No se pudo conectar con el servidor. Por favor, inténtelo de nuevo.',
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    });
                }
            });
        });
    }
});

// Function to reload the page clearing cache
function reloadPageWithCacheClear() {
    console.log('Reloading page clearing cache...');
    window.location.reload(true);
}

// Manejar mensajes de URL al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);

    // Mensaje de éxito al crear empresa
    if (urlParams.get('success') === 'true') {
        Swal.fire({
            title: '¡Empresa Registrada!',
            text: 'La empresa ha sido creada correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    } else if (urlParams.has('updated')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La empresa ha sido actualizada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('deleted')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La empresa ha sido eliminada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('error')) {
        Swal.fire({
            title: 'Error',
            text: 'Ha ocurrido un error al procesar la solicitud',
            icon: 'error',
            confirmButtonText: 'Aceptar'
        });
    }
    
   
});


// ===== CÓDIGO PARA MODAL DE AVATARES =====
// Variables globales para el modal de avatares
let selectedAvatarData = {
    path: 'avatars/Cartoon Style Robot.jpg',
    name: 'Robot Cartoon'
};

// Función para cargar avatares dinámicamente
function loadAvatars() {
    fetch('/ecommerce/api/get_avatars/')
        .then(response => response.json())
        .then(data => {
            const loadingDiv = document.getElementById('avatars-loading');
            const gridDiv = document.getElementById('avatars-modal-grid');
            
            if (data.success && data.avatars) {
                // Ocultar mensaje de carga
                loadingDiv.style.display = 'none';
                
                // Limpiar grid
                gridDiv.innerHTML = '';
                
                // Crear tarjetas de avatares dinámicamente
                data.avatars.forEach(avatar => {
                    const avatarCard = document.createElement('div');
                    avatarCard.className = 'avatar-modal-card';
                    avatarCard.setAttribute('data-avatar', avatar.path);
                    avatarCard.setAttribute('data-name', avatar.name);
                    
                    avatarCard.innerHTML = `
                        <div class="avatar-modal-image">
                            <img src="/static/${avatar.path}" alt="${avatar.name}">
                            <div class="avatar-modal-overlay">
                                <div class="check-icon">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="white"/>
                                    </svg>
                                </div>
                            </div>
                        </div>
                        <span class="avatar-modal-name">${avatar.name}</span>
                    `;
                    
                    // Agregar event listener para selección
                    avatarCard.addEventListener('click', function() {
                        // Remover selección anterior
                        document.querySelectorAll('.avatar-modal-card').forEach(c => c.classList.remove('selected'));
                        
                        // Agregar selección al avatar clickeado
                        this.classList.add('selected');
                        
                        // Actualizar datos del avatar seleccionado
                        selectedAvatarData = {
                            path: this.getAttribute('data-avatar'),
                            name: this.getAttribute('data-name')
                        };
                    });
                    
                    gridDiv.appendChild(avatarCard);
                });
                
                // Mostrar grid
                gridDiv.classList.add('show');
            } else {
                loadingDiv.innerHTML = 'Error al cargar avatares';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('avatars-loading').innerHTML = 'Error al cargar avatares';
        });
}

// Función para abrir el modal
function openAvatarModal() {
    const modal = document.getElementById('avatarModal');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    loadAvatars();
}

// Función para cerrar el modal
function closeAvatarModal() {
    const modal = document.getElementById('avatarModal');
    modal.classList.remove('show');
    document.body.style.overflow = 'auto';
}

// Función para confirmar la selección
function confirmAvatarSelection() {
    // Actualizar el preview en el formulario principal
    const previewImage = document.getElementById('selected_avatar_preview');
    const previewName = document.getElementById('selected_avatar_name');
    const hiddenInput = document.getElementById('selected_avatar_input');
    
    if (previewImage) previewImage.src = "/static/" + selectedAvatarData.path;
    if (previewName) previewName.textContent = selectedAvatarData.name;
    if (hiddenInput) hiddenInput.value = selectedAvatarData.path;
    
    // Cerrar el modal
    closeAvatarModal();
}

// Inicialización de avatares
document.addEventListener('DOMContentLoaded', function() {
    // Cerrar modal al hacer click fuera de él
    const modal = document.getElementById('avatarModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeAvatarModal();
            }
        });
    }
    
    // Cerrar modal con tecla Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAvatarModal();
        }
    });
    
    // Manejar opciones de avatar (predefinido vs custom)
    const avatarOptions = document.querySelectorAll('input[name="avatar_option"]');
    const customUploadSection = document.getElementById('custom_upload_section');
    const avatarFileInput = document.getElementById('avatar_chatbot');
    
    if (avatarOptions.length > 0 && customUploadSection) {
        avatarOptions.forEach(option => {
            option.addEventListener('change', function() {
                if (this.value === 'custom') {
                    customUploadSection.style.display = 'block';
                } else {
                    customUploadSection.style.display = 'none';
                    if (avatarFileInput) {
                        avatarFileInput.value = '';
                    }
                }
            });
        });
    }
    
    // Manejar la subida de archivos con drag & drop
    const fileUploadArea = document.querySelector('.file-upload-area');
    const fileInput = document.getElementById('avatar_chatbot');
    const uploadPlaceholder = document.querySelector('.upload-placeholder');
    
    if (fileUploadArea && fileInput && uploadPlaceholder) {
        // Prevenir comportamiento por defecto del drag & drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });
        
        // Resaltar área de drop
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, function() {
                fileUploadArea.style.borderColor = '#667eea';
                fileUploadArea.style.background = '#f0f4ff';
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, function() {
                fileUploadArea.style.borderColor = '#cbd5e0';
                fileUploadArea.style.background = 'white';
            }, false);
        });
        
        // Manejar archivos soltados
        fileUploadArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        }, false);
        
        // Manejar selección de archivo
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
        
        function handleFileSelect(file) {
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    uploadPlaceholder.innerHTML = `
                        <div style="display: flex; flex-direction: column; align-items: center;">
                            <img src="${e.target.result}" alt="Preview" style="width: 80px; height: 80px; object-fit: cover; border-radius: 50%; margin-bottom: 10px; border: 3px solid #667eea;">
                            <span style="color: #667eea; font-weight: 600;">${file.name}</span>
                            <small style="color: #a0aec0;">Imagen seleccionada correctamente</small>
                        </div>
                    `;
                };
                reader.readAsDataURL(file);
            }
        }
    }
});
