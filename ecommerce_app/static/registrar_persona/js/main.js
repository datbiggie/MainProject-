$(document).ready(function() {
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
    
    // Inicializar Select2
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
        }
    });

    // Validación para nombre y apellido (solo letras y espacios)
    function validateName(input) {
        const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
        return nameRegex.test(input);
    }

    // Validación para teléfono (solo números)
    function validatePhone(input) {
        const phoneRegex = /^[0-9]+$/;
        return phoneRegex.test(input);
    }

    // Aplicar validación en tiempo real para nombre
    $('#nombre_usuario').on('input', function() {
        const value = $(this).val();
        if (value && !validateName(value)) {
            $(this).addClass('error-input');
            $(this).attr('title', 'Solo se permiten letras y espacios');
        } else {
            $(this).removeClass('error-input');
            $(this).removeAttr('title');
        }
    });

    // Aplicar validación en tiempo real para apellido
    $('#apellido').on('input', function() {
        const value = $(this).val();
        if (value && !validateName(value)) {
            $(this).addClass('error-input');
            $(this).attr('title', 'Solo se permiten letras y espacios');
        } else {
            $(this).removeClass('error-input');
            $(this).removeAttr('title');
        }
    });

    // Aplicar validación en tiempo real para teléfono - solo números
    $('#telefono').on('input', function() {
        // Eliminar cualquier carácter que no sea número
        this.value = this.value.replace(/[^0-9]/g, '');
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
    $('#nombre_usuario, #apellido, #email, #password, #telefono, #fecha_nacimiento, #country').on('blur', function() {
        validateRequiredField(this);
    });

    // Validación especial para el select de estado
    $('#state').on('change', function() {
        const value = $(this).val();
        if (!value) {
            $(this).addClass('required-error');
            $(this).attr('title', 'Debe seleccionar un estado');
        } else {
            $(this).removeClass('required-error');
            $(this).removeAttr('title');
        }
    });

    // Evento para enfocar el campo de búsqueda cuando se abre el select
    $('#state').on('select2:open', function() {
        setTimeout(function() {
            document.querySelector('.select2-search__field').focus();
        }, 0);
    });

    // Manejar el envío del formulario
    $('form').on('submit', function(e) {
        e.preventDefault();
        
        // Validar campos antes de enviar
        const nombre = $('#nombre_usuario').val();
        const apellido = $('#apellido').val();
        const telefono = $('#telefono').val();
        
        // Validar nombre
        if (!validateName(nombre)) {
            Swal.fire({
                title: 'Error de validación',
                text: 'El nombre solo puede contener letras y espacios',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            $('#nombre_usuario').focus();
            return false;
        }
        
        // Validar apellido
        if (!validateName(apellido)) {
            Swal.fire({
                title: 'Error de validación',
                text: 'El apellido solo puede contener letras y espacios',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            $('#apellido').focus();
            return false;
        }
        
        // Validar teléfono
        if (!validatePhone(telefono)) {
            Swal.fire({
                title: 'Error de validación',
                text: 'El teléfono solo puede contener números',
                icon: 'error',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
            });
            $('#telefono').focus();
            return false;
        }
        
        // Validar que todos los campos estén completos
        const email = $('#email').val().trim();
        const password = $('#password').val().trim();
        const fecha_nacimiento = $('#fecha_nacimiento').val();
        const pais = $('#country').val().trim();
        const estado = $('#state').val();
        const checkbox = $('#supportCheckbox').is(':checked');
        
        // Validar campos vacíos
        if (!nombre || !apellido || !email || !password || !telefono || !fecha_nacimiento || !pais || !estado) {
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
        
        $.ajax({
            url: $(this).attr('action'),
            method: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                if (response.success) {
                    Swal.fire({
                        title: '¡Registro exitoso!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Si hay una URL de redirección en la respuesta, usarla
                            if (response.redirect_url) {
                                window.location.href = response.redirect_url;
                            } else {
                                // Limpiar el formulario y recargar la página
                                $('form')[0].reset();
                                window.location.href = window.location.pathname;
                            }
                        }
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: response.message,
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    });
                }
            },
            error: function() {
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al procesar la solicitud',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
            }
        });
    });
});


// ===== CÓDIGO MOVIDO DESDE HTML (MODAL DE AVATARES) =====
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
    if (!modal) return;

    // Move modal to document.body to avoid positioning issues when ancestors have transforms
    if (modal.parentNode !== document.body) {
        document.body.appendChild(modal);
    }

    // Compute header height (fixed top bar) to avoid overlapping it
    const header = document.querySelector('.top-bar-ecommerce');
    const headerHeight = header ? Math.ceil(header.getBoundingClientRect().height) : 0;

    modal.style.paddingTop = Math.max(10, headerHeight + 10) + 'px';
    modal.style.paddingBottom = '10px';

    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    loadAvatars();
}

// Función para cerrar el modal
function closeAvatarModal() {
    const modal = document.getElementById('avatarModal');
    if (!modal) return;

    modal.classList.remove('show');
    modal.style.removeProperty('padding-top');
    modal.style.removeProperty('padding-bottom');
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

// JavaScript para manejar la selección de avatares
document.addEventListener('DOMContentLoaded', function() {
    // Manejar clicks en las tarjetas del modal
    const avatarModalCards = document.querySelectorAll('.avatar-modal-card');
    avatarModalCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remover selección anterior
            avatarModalCards.forEach(c => c.classList.remove('selected'));
            
            // Agregar selección al avatar clickeado
            this.classList.add('selected');
            
            // Actualizar datos del avatar seleccionado
            selectedAvatarData = {
                path: this.getAttribute('data-avatar'),
                name: this.getAttribute('data-name')
            };
        });
    });
    
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
    
    // Seleccionar el primer avatar por defecto
    const firstAvatar = document.querySelector('.avatar-modal-card');
    if (firstAvatar) {
        firstAvatar.classList.add('selected');
    }
    
    const avatarOptions = document.querySelectorAll('input[name="avatar_option"]');
    const customUploadSection = document.getElementById('custom_upload_section');
    const avatarFileInput = document.getElementById('avatar_chatbot');
    
    avatarOptions.forEach(option => {
        option.addEventListener('change', function() {
            if (this.value === 'custom') {
                customUploadSection.style.display = 'block';
                avatarFileInput.required = false;
            } else {
                customUploadSection.style.display = 'none';
                avatarFileInput.value = '';
                avatarFileInput.required = false;
            }
        });
    });
    
    // Manejar la subida de archivos con drag & drop
    const fileUploadArea = document.querySelector('.file-upload-area');
    const fileInput = document.getElementById('avatar_chatbot');
    const uploadPlaceholder = document.querySelector('.upload-placeholder');
    
    if (fileUploadArea && fileInput) {
        // Prevenir comportamiento por defecto del drag & drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Resaltar área de drop
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            fileUploadArea.style.borderColor = '#667eea';
            fileUploadArea.style.background = '#f0f4ff';
        }
        
        function unhighlight(e) {
            fileUploadArea.style.borderColor = '#cbd5e0';
            fileUploadArea.style.background = 'white';
        }
        
        // Manejar archivos soltados
        fileUploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        }
        
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
    
    // Los avatares se cargan automáticamente cuando se abre el modal
    
    // Agregar animaciones suaves a las tarjetas de avatar
    const avatarCards = document.querySelectorAll('.avatar-card');
    avatarCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.style.animation = 'fadeInUp 0.6s ease forwards';
    });
    
    // Agregar animación CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .avatar-card {
            opacity: 0;
        }
    `;
    document.head.appendChild(style);
});
