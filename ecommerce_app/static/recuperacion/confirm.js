// JavaScript para confirmar recuperación de contraseña
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('confirmForm');
    const btn = document.getElementById('btnConfirm');
    const passwordInput = document.getElementById('password');
    const password2Input = document.getElementById('password2');
    const tokenInput = document.getElementById('token');

    if (!form || !btn) {
        console.error('Error: No se encontraron los elementos del formulario');
        return;
    }

    // Validación en tiempo real de contraseñas
    function validatePasswords() {
        const password = passwordInput.value;
        const password2 = password2Input.value;
        
        // Limpiar clases previas
        passwordInput.classList.remove('is-invalid', 'is-valid');
        password2Input.classList.remove('is-invalid', 'is-valid');
        
        // Validar longitud mínima
        if (password.length < 6) {
            passwordInput.classList.add('is-invalid');
            return false;
        } else {
            passwordInput.classList.add('is-valid');
        }
        
        // Validar que las contraseñas coincidan
        if (password2 && password !== password2) {
            password2Input.classList.add('is-invalid');
            return false;
        } else if (password2) {
            password2Input.classList.add('is-valid');
        }
        
        return password.length >= 6 && password === password2;
    }

    // Eventos de validación
    passwordInput.addEventListener('input', validatePasswords);
    password2Input.addEventListener('input', validatePasswords);

    // Manejar envío del formulario
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const password = passwordInput.value.trim();
        const password2 = password2Input.value.trim();
        const token = tokenInput.value;

        // Validaciones
        if (!password || password.length < 6) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'La contraseña debe tener al menos 6 caracteres.'
            });
            return;
        }

        if (password !== password2) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Las contraseñas no coinciden.'
            });
            return;
        }

        if (!token) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Token de recuperación no válido.'
            });
            return;
        }

        // Obtener CSRF token
        const csrfToken = getCookie('csrftoken');

        // Deshabilitar botón y mostrar loading
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Actualizando...';

        try {
            const response = await fetch('/ecommerce/confirmar_recuperacion/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    token: token,
                    password: password
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Contraseña actualizada!',
                    text: 'Tu contraseña ha sido actualizada correctamente. Ahora puedes iniciar sesión con tu nueva contraseña.',
                    confirmButtonText: 'Ir a Iniciar Sesión'
                }).then(() => {
                    window.location.href = '/ecommerce/iniciar_sesion/';
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message || 'No se pudo actualizar la contraseña. Intenta de nuevo.'
                });
            }

        } catch (error) {
            console.error('Error en la petición:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'Ocurrió un error al actualizar la contraseña. Verifica tu conexión e intenta de nuevo.'
            });
        } finally {
            // Restaurar botón
            btn.disabled = false;
            btn.innerHTML = 'Actualizar contraseña';
        }
    });
});

// Helper para obtener cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
