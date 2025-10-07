// ===== MODERN LOGIN PAGE JAVASCRIPT =====
// Solución implementada para corregir errores de compatibilidad entre navegadores
// Problema original: "TypeError: Cannot read properties of null (reading 'classList')"
// Solución: Verificaciones de seguridad para elementos del DOM

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el dropdown
    const dropdownElementList = document.querySelectorAll('.dropdown-toggle');
    const dropdownList = [...dropdownElementList].map(dropdownToggleEl => new bootstrap.Dropdown(dropdownToggleEl));

    // Manejar clics en los items del dropdown
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href) {
                window.location.href = href;
            }
        });
    });

    // Función de utilidad para obtener elementos del DOM de forma segura
    // Esta función evita errores cuando elementos no están disponibles en algunos navegadores
    function getElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.error(`Elemento con id '${id}' no encontrado en el DOM`);
            return null;
        }
        return element;
    }

    // Elementos del formulario con verificaciones de seguridad
    const emailInput = getElement('email');
    const passwordInput = getElement('password');
    const emailField = getElement('emailField');
    const passwordField = getElement('passwordField');
    const nextButton = getElement('nextButton');
    const backButton = getElement('backButton');
    const createAccountDropdown = getElement('createAccountDropdown');
    const loginForm = getElement('loginForm');
    const title = document.querySelector('.login-title');

    // Verificar que todos los elementos críticos estén presentes
    // Si faltan elementos críticos, mostrar error y recargar la página
    if (!emailInput || !passwordInput || !emailField || !passwordField || !nextButton || !loginForm) {
        console.error('Algunos elementos críticos del formulario no están disponibles');
        Swal.fire({
            title: 'Error de carga',
            text: 'No se pudieron cargar correctamente los elementos del formulario. Por favor, recargue la página.',
            icon: 'error',
            confirmButtonText: 'Recargar',
            confirmButtonColor: '#2196F3'
        }).then(() => {
            window.location.reload();
        });
        return; // Detener la ejecución si faltan elementos críticos
    }

    // Función para validar campos obligatorios
    function validateRequiredField(field) {
        if (!field) return;
        const value = field.value.trim();
        if (!value) {
            field.classList.add('required-error');
            field.setAttribute('title', 'Este campo es obligatorio');
        } else {
            field.classList.remove('required-error');
            field.removeAttribute('title');
        }
    }

    // Función para validar formato de email
    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Aplicar validación en tiempo real para email
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            validateRequiredField(this);
            if (this.value.trim() && !validateEmail(this.value)) {
                this.classList.add('error-input');
                this.setAttribute('title', 'Ingrese un correo electrónico válido');
            } else {
                this.classList.remove('error-input');
                this.removeAttribute('title');
            }
        });

        emailInput.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('required-error');
                this.removeAttribute('title');
            }
            if (this.value.trim() && validateEmail(this.value)) {
                this.classList.remove('error-input');
                this.removeAttribute('title');
            }
        });
    }

    // Aplicar validación en tiempo real para contraseña
    if (passwordInput) {
        passwordInput.addEventListener('blur', function() {
            validateRequiredField(this);
        });

        passwordInput.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('required-error');
                this.removeAttribute('title');
            }
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', function() {
            if (!emailInput) return;
            const email = emailInput.value.trim();
            
            // Validar que el email no esté vacío
            if (!email) {
                Swal.fire({
                    title: 'Campo obligatorio',
                    text: 'Por favor ingrese su correo electrónico',
                    icon: 'warning',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#2196F3'
                });
                emailInput.focus();
                return;
            }
            
            // Validar formato de email
            if (!validateEmail(email)) {
                Swal.fire({
                    title: 'Formato inválido',
                    text: 'Por favor ingrese un correo electrónico válido',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#2196F3'
                });
                emailInput.focus();
                return;
            }

            // Asegurar que el campo de contraseña esté oculto antes de validar
            if (passwordField) {
                passwordField.style.display = 'none';
                passwordField.classList.add('hidden');
                passwordField.classList.remove('visible');
            }

            fetch('/ecommerce/validate-email/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : ''
                },
                body: JSON.stringify({ email: email })
            })
            .then(response => response.json())
            .then(data => {
                if (data.exists) {
                    if (emailField && passwordField && nextButton && createAccountDropdown && backButton) {
                        emailField.classList.add('hidden');
                        emailField.style.display = 'none';
                        
                        setTimeout(() => {
                            passwordField.style.display = 'block';
                            passwordField.classList.remove('hidden');
                            passwordField.classList.add('visible');
                            nextButton.textContent = 'Entrar';
                            nextButton.type = 'submit';
                            createAccountDropdown.style.display = 'none';
                            backButton.style.display = 'flex';
                        }, 300);
                    }
                } else {
                    Swal.fire({
                        title: 'Usuario no encontrado',
                        text: 'El correo electrónico no está registrado en nuestro sistema',
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#2196F3'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error de conexión',
                    text: 'Ocurrió un error al validar el correo. Por favor, inténtelo de nuevo.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#2196F3'
                });
            });
        });
    }

    // Manejar el botón de regresar
    if (backButton) {
        backButton.addEventListener('click', function() {
            if (passwordField && emailField && nextButton && createAccountDropdown) {
                passwordField.classList.remove('visible');
                passwordField.classList.add('hidden');
                passwordField.style.display = 'none';
                
                setTimeout(() => {
                    emailField.style.display = 'block';
                    emailField.classList.remove('hidden');
                    emailField.classList.add('visible');
                    nextButton.textContent = 'Siguiente';
                    nextButton.type = 'button';
                    createAccountDropdown.style.display = 'block';
                    backButton.style.display = 'none';
                    // Limpiar el campo de contraseña
                    if (passwordInput) {
                        passwordInput.value = '';
                    }
                }, 300);
            }
        });
    }

    // Manejar el envío del formulario (cuando se hace clic en "Entrar")
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!emailInput || !passwordInput) return;
            
            const email = emailInput.value.trim();
            const password = passwordInput.value.trim();
            
            // Validar campos antes de enviar
            if (!email) {
                Swal.fire({
                    title: 'Campo obligatorio',
                    text: 'Por favor ingrese su correo electrónico',
                    icon: 'warning',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#2196F3'
                });
                emailInput.focus();
                return false;
            }
            
            if (!validateEmail(email)) {
                Swal.fire({
                    title: 'Formato inválido',
                    text: 'Por favor ingrese un correo electrónico válido',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#2196F3'
                });
                emailInput.focus();
                return false;
            }
            
            if (!password) {
                Swal.fire({
                    title: 'Campo obligatorio',
                    text: 'Por favor ingrese su contraseña',
                    icon: 'warning',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#2196F3'
                });
                passwordInput.focus();
                return false;
            }
            
            // Si todo está válido, enviar el formulario
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : ''
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: '¡Inicio de sesión exitoso!',
                        text: data.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#2196F3'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            window.location.href = data.redirect_url || '/ecommerce/';
                        }
                    });
                } else {
                    Swal.fire({
                        title: 'Error de autenticación',
                        text: data.message || 'Credenciales incorrectas',
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#2196F3'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error de conexión',
                    text: 'Ocurrió un error al procesar la solicitud. Por favor, inténtelo de nuevo.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#2196F3'
                });
            });
        });
    }
});
