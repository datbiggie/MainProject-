class AvatarSelector {
    constructor() {
        // Elementos del DOM
        this.avatarModal = document.getElementById('avatarModal');
    // Buscar inputs compatibles (empresa o usuario). Puede haber varios en la página.
    this.avatarInputs = document.querySelectorAll('#avatar_chatbot, #avatar_chatbot_empresa, input[name="avatar_chatbot"]');
    // Input principal (el primero) — usado para leer valor actual al abrir
    this.avatarInput = this.avatarInputs && this.avatarInputs.length ? this.avatarInputs[0] : null;
    this.avatarPreview = document.getElementById('avatarPreviewLarge');
    this.avatarNameElement = document.getElementById('selected_avatar_name');
    this.confirmBtn = document.getElementById('confirmAvatarBtn');
    // Puede haber varios botones para abrir el modal (empresa/usuario) — usar selector
    this.openModalBtn = document.querySelectorAll('#openAvatarModalBtn');
        this.avatarsGrid = document.getElementById('avatars-modal-grid');
        this.loadingElement = document.getElementById('avatars-loading');
        this.modalInstance = null;
        
        // Lista de avatares disponibles (se cargará dinámicamente)
        this.avatars = [];
        
        // Nombres amigables para los avatares
        this.avatarNames = {
            '1.png': 'Avatar 1',
            '2.png': 'Avatar 2',
            '3.png': 'Avatar 3',
            '4.png': 'Avatar 4',
            '5.png': 'Avatar 5',
            '6.png': 'Avatar 6',
            '7.jpg': 'Avatar 7',
            '7.svg': 'Avatar 8',
            'Cartoon Style Robot.jpg': 'Robot de Dibujos',
            'users-1.svg': 'Usuario 1',
            'users-2.svg': 'Usuario 2',
            'users-3.svg': 'Usuario 3',
            'users-4.svg': 'Usuario 4',
            'users-5.svg': 'Usuario 5',
            'users-6.svg': 'Usuario 6',
            'users-7.svg': 'Usuario 7',
            'users-8.svg': 'Usuario 8',
            'users-9.svg': 'Usuario 9',
            'users-10.svg': 'Usuario 10',
            'users-11.svg': 'Usuario 11',
            'users-12.svg': 'Usuario 12',
            'users-13.svg': 'Usuario 13',
            'users-14.svg': 'Usuario 14',
            'users-15.svg': 'Usuario 15',
            'users-16.svg': 'Usuario 16'
        };
        
        // Estado
        this.selectedAvatar = '';
        
        // Inicializar
        this.initialize();
    }
    
    initialize() {
        // Inicializar el modal de Bootstrap
        if (this.avatarModal) {
            this.modalInstance = new bootstrap.Modal(this.avatarModal);
            
            // Cargar avatares al abrir el modal
            this.avatarModal.addEventListener('show.bs.modal', () => this.loadAvatars());
        }
        
        // Configurar botón para abrir el modal
        if (this.openModalBtn && this.openModalBtn.length) {
            this.openModalBtn.forEach(btn => btn.addEventListener('click', () => this.openModal()));
        }
        
        // Configurar botón de confirmación
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => this.confirmSelection());
        }
        
        // Cargar avatar actual si existe (usar input principal si existe)
        if (this.avatarInput && this.avatarInput.value) {
            this.updatePreview(this.avatarInput.value);
        }
    }
    
    loadAvatars() {
        if (!this.avatarsGrid || !this.loadingElement) return;
        
        // Mostrar carga
        this.loadingElement.style.display = 'block';
        this.avatarsGrid.style.display = 'none';
        this.confirmBtn.disabled = true;
        
        // Obtener el avatar actual
        const currentAvatar = this.avatarInput ? this.avatarInput.value : '';
        const staticUrl = this.avatarsGrid.dataset.staticUrl || '';
        
        // Si ya tenemos los avatares cargados, solo renderizamos
        if (this.avatars.length > 0) {
            this.renderAvatars(currentAvatar, staticUrl);
            return;
        }
        
        // Obtener la lista de avatares del servidor
        fetch(`/ecommerce/api/get_avatars/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.avatars && data.avatars.length > 0) {
                    // Usar directamente los datos del servidor que ya vienen formateados
                    this.avatars = data.avatars.map(avatar => ({
                        path: avatar.path,
                        name: this.avatarNames[avatar.filename] || avatar.name
                    }));
                    
                    // Renderizar los avatares
                    this.renderAvatars(currentAvatar, staticUrl);
                } else {
                    this.showError('No se encontraron avatares disponibles.');
                }
            })
            .catch(error => {
                console.error('Error al cargar los avatares:', error);
                this.showError('Error al cargar los avatares. Por favor, intente nuevamente.');
            });
    }
    
    renderAvatars(currentAvatar, staticUrl) {
        if (!this.avatarsGrid) return;
        
        let html = '';
        this.avatars.forEach(avatar => {
            const isSelected = currentAvatar === avatar.path ? 'selected' : '';
            const imgSrc = `${staticUrl}${avatar.path}`;
            
            html += `
                <div class="col-6 col-sm-4 col-md-3 mb-3">
                    <div class="avatar-option text-center p-2 ${isSelected} position-relative" 
                         data-avatar="${avatar.path}" 
                         data-name="${avatar.name}">
                        <img src="${imgSrc}" 
                             alt="${avatar.name}" 
                             class="img-fluid rounded-circle mb-2" 
                             style="width: 100%; height: 100px; object-fit: cover;"
                             onerror="this.onerror=null;this.style.display='none';">
                        <p class="small mb-0 text-truncate" style="max-width: 100%;">${avatar.name}</p>
                        <div class="avatar-selected position-absolute top-0 end-0 bg-primary text-white rounded-circle p-1 m-1" style="display: ${isSelected ? 'block' : 'none'};">
                            <i class="fas fa-check"></i>
                        </div>
                    </div>
                </div>`;
        });
        
        // Actualizar la cuadrícula
        this.avatarsGrid.innerHTML = html;
        
        // Configurar eventos de los avatares
        this.setupAvatarEvents();
        
        // Ocultar carga y mostrar cuadrícula
        if (this.loadingElement) {
            this.loadingElement.style.display = 'none';
        }
        this.avatarsGrid.style.display = 'flex';
    }
    
    showError(message) {
        if (this.avatarsGrid) {
            this.avatarsGrid.innerHTML = `
                <div class="col-12 text-center py-4">
                    <i class="fas fa-exclamation-triangle text-warning mb-2" style="font-size: 2rem;"></i>
                    <p class="text-muted">${message}</p>
                </div>`;
        }
        
        if (this.loadingElement) {
            this.loadingElement.style.display = 'none';
        }
        
        if (this.avatarsGrid) {
            this.avatarsGrid.style.display = 'flex';
        }
    }
    
    setupAvatarEvents() {
        const options = this.avatarsGrid.querySelectorAll('.avatar-option');
        
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                // Deseleccionar todos
                options.forEach(opt => opt.classList.remove('selected'));
                
                // Seleccionar el actual
                option.classList.add('selected');
                this.selectedAvatar = option.dataset.avatar;
                this.confirmBtn.disabled = false;
                // Debug: log selección
                try { console.debug('[AvatarSelector] option clicked:', this.selectedAvatar, option.dataset.name); } catch (e) {}
                // Informar a cualquier integración externa que espere una API global
                try {
                    const staticUrl = this.avatarsGrid ? this.avatarsGrid.dataset.staticUrl || '' : '';
                    const src = (staticUrl || '') + this.selectedAvatar;
                    const name = option.dataset.name || '';
                    if (typeof window !== 'undefined' && typeof window.onAvatarSelected === 'function') {
                        window.onAvatarSelected({ id: this.selectedAvatar, src: src, name: name });
                    }
                    try { console.debug('[AvatarSelector] onAvatarSelected called with', { id: this.selectedAvatar, src: src, name: name }); } catch (e) {}
                } catch (err) {
                    // no bloquear en caso de error
                    console.warn('onAvatarSelected error', err);
                }
            });
        });
    }
    
    openModal() {
        if (this.modalInstance) {
            this.modalInstance.show();
        }
    }
    
    confirmSelection() {
        if (!this.selectedAvatar) return;

        // Actualizar todos los inputs ocultos encontrados en la página
        if (this.avatarInputs && this.avatarInputs.length) {
            this.avatarInputs.forEach(input => {
                try {
                    input.value = this.selectedAvatar;
                } catch (e) {
                    console.warn('No se pudo actualizar input avatar:', e);
                }
            });
        }

        // Actualizar vista previa
        this.updatePreview(this.selectedAvatar);
    try { console.debug('[AvatarSelector] confirmSelection:', this.selectedAvatar); } catch (e) {}

        // Cerrar modal
        if (this.modalInstance) {
            this.modalInstance.hide();
        }
    }
    
    updatePreview(avatarPath) {
        if (!this.avatarPreview || !this.avatarNameElement) return;
        
        const staticUrl = this.avatarsGrid ? this.avatarsGrid.dataset.staticUrl : '';
        const selectedAvatar = this.avatars.find(a => a.path === avatarPath);
        
        if (selectedAvatar) {
            this.avatarPreview.src = `${staticUrl}${avatarPath}`;
            this.avatarPreview.alt = selectedAvatar.name;
            this.avatarNameElement.textContent = selectedAvatar.name;
            this.avatarPreview.style.display = 'block';
            
            // Manejar error de carga de imagen
            this.avatarPreview.onerror = () => {
                this.avatarPreview.style.display = 'none';
                this.avatarNameElement.textContent = 'Avatar no disponible';
            };
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar el selector de avatares
    if (document.getElementById('avatarModal')) {
        new AvatarSelector();
    }
    
    // Inicializar tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Validación de formulario
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});
