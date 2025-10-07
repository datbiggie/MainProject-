# Script para agregar funciones de avatar a registrar_empresa

avatar_js_code = '''

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
            fileUploadArea.addEventListener(eventName', function() {
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
'''

# Leer el archivo de registrar_empresa
with open(r'c:\GitHub\MainProject-\ecommerce_app\static\registrar_empresa\js\main.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si las funciones ya están
if 'function openAvatarModal()' not in content:
    # Agregar el código al final
    with open(r'c:\GitHub\MainProject-\ecommerce_app\static\registrar_empresa\js\main.js', 'a', encoding='utf-8') as f:
        f.write(avatar_js_code)
    print("✓ Funciones de avatar agregadas exitosamente a registrar_empresa")
else:
    print("✓ Las funciones de avatar ya existen en registrar_empresa")
