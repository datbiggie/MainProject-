// ===== JAVASCRIPT PERSONALIZADO PARA INICIO DE SESIÓN =====

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

    // Código existente para el manejo del email y contraseña
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const emailField = document.getElementById('emailField');
    const passwordField = document.getElementById('passwordField');
    const nextButton = document.getElementById('nextButton');
    const backButton = document.getElementById('backButton');
    const createAccountDropdown = document.getElementById('createAccountDropdown');
    const loginForm = document.getElementById('loginForm');
    const title = document.querySelector('.login100-form-title');

    // Función para validar campos obligatorios
    function validateRequiredField(field) {
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

    // Aplicar validación en tiempo real para contraseña
    passwordInput.addEventListener('blur', function() {
        validateRequiredField(this);
    });

    passwordInput.addEventListener('input', function() {
        if (this.value.trim()) {
            this.classList.remove('required-error');
            this.removeAttribute('title');
        }
    });

    nextButton.addEventListener('click', function() {
        const email = emailInput.value.trim();
        
        // Validar que el email no esté vacío
        if (!email) {
            Swal.fire({
                title: 'Campo obligatorio',
                text: 'Por favor ingrese su correo electrónico',
                icon: 'warning',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
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
                confirmButtonColor: '#3b82f6'
            });
            emailInput.focus();
            return;
        }

        // Asegurar que el campo de contraseña esté oculto antes de validar
        passwordField.style.display = 'none';
        passwordField.classList.add('hidden');
        passwordField.classList.remove('visible');

        fetch('/ecommerce/validate-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ email: email })
        })
        .then(response => response.json())
        .then(data => {
            if (data.exists) {
                title.classList.add('slide-up');
                emailField.classList.add('hidden');
                // Ocultar inmediatamente el campo de correo
                emailField.style.display = 'none';
                
                setTimeout(() => {
                    passwordField.style.display = 'block';
                    passwordField.classList.remove('hidden');
                    passwordField.classList.add('visible');
                    nextButton.textContent = 'Entrar';
                    nextButton.type = 'submit';
                    createAccountDropdown.style.display = 'none';
                    backButton.style.display = 'block';
                }, 300);
            } else {
                Swal.fire({
                    title: 'Usuario no encontrado',
                    text: 'El correo electrónico no está registrado en nuestro sistema',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
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
                confirmButtonColor: '#3b82f6'
            });
        });
    });

    // Manejar el botón de regresar
    backButton.addEventListener('click', function() {
        title.classList.remove('slide-up');
        passwordField.classList.remove('visible');
        passwordField.classList.add('hidden');
        // Ocultar inmediatamente el campo de contraseña
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
            document.getElementById('password').value = '';
        }, 300);
    });

    // Manejar el envío del formulario (cuando se hace clic en "Entrar")
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();
        
        // Validar campos antes de enviar
        if (!email) {
            Swal.fire({
                title: 'Campo obligatorio',
                text: 'Por favor ingrese su correo electrónico',
                icon: 'warning',
                confirmButtonText: 'Aceptar',
                confirmButtonColor: '#3b82f6'
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
                confirmButtonColor: '#3b82f6'
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
                confirmButtonColor: '#3b82f6'
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
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
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
                    confirmButtonColor: '#3b82f6'
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
                    confirmButtonColor: '#3b82f6'
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
                confirmButtonColor: '#3b82f6'
            });
        });
    });
});

