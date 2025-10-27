document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('confirmForm');
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const password = document.getElementById('password').value.trim();
        const password2 = document.getElementById('password2').value.trim();
        const token = document.getElementById('token').value.trim();
        if (!password || !password2) {
            Swal.fire('Error', 'Completa ambos campos', 'warning');
            return;
        }
        if (password !== password2) {
            Swal.fire('Error', 'Las contraseñas no coinciden', 'error');
            return;
        }
        try {
            const resp = await fetch('/ecommerce/confirmar_recuperacion/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token: token, password: password})
            });
            const data = await resp.json();
            if (data.success) {
                Swal.fire('Éxito', data.message || 'Contraseña actualizada', 'success').then(() => {
                    window.location.href = '/ecommerce/iniciar_sesion/';
                });
            } else {
                Swal.fire('Error', data.message || 'No fue posible actualizar la contraseña', 'error');
            }
        } catch (err) {
            Swal.fire('Error', 'Error de red', 'error');
        }
    });
});