// solicitud_servicio.js
// JS para la página de solicitud de servicio

document.addEventListener('DOMContentLoaded', function() {
    // Preseleccionar sucursal si hay una marcada como selected
    var preselected = document.querySelector('.sucursal-card.selected');
    if (preselected) {
        var sucursalId = preselected.getAttribute('data-sucursal-id');
        document.getElementById('sucursal_id').value = sucursalId;
        document.getElementById('sucursal-nombre').textContent = preselected.querySelector('h6').textContent;
        document.getElementById('sucursal-seleccionada').style.display = 'block';
        // Importante: establecer la variable global
        sucursalSeleccionada = sucursalId;
    }
    
    // Si hay un campo sucursal_id con valor (sucursal preseleccionada desde backend)
    const sucursalIdInput = document.getElementById('sucursal_id');
    if (sucursalIdInput && sucursalIdInput.value) {
        sucursalSeleccionada = sucursalIdInput.value;
    }

    // Establecer fecha mínima como hoy
    const fechaInput = document.getElementById('fecha_preferida');
    if (fechaInput) {
        const today = new Date().toISOString().split('T')[0];
        fechaInput.min = today;
    }
});

let sucursalSeleccionada = null;

function seleccionarSucursal(sucursalId) {
    // Remover selección anterior
    document.querySelectorAll('.sucursal-card').forEach(card => {
        card.classList.remove('selected');
    });
    // Seleccionar nueva sucursal
    const sucursalCard = document.querySelector(`[data-sucursal-id="${sucursalId}"]`);
    if (sucursalCard) {
        sucursalCard.classList.add('selected');
        sucursalSeleccionada = sucursalId;
        // Actualizar campo oculto
        document.getElementById('sucursal_id').value = sucursalId;
        // Mostrar sucursal seleccionada
        const sucursalNombre = sucursalCard.querySelector('h6').textContent;
        document.getElementById('sucursal-nombre').textContent = sucursalNombre;
        document.getElementById('sucursal-seleccionada').style.display = 'block';
    }
}

document.getElementById('solicitudForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    // Validar sucursal si es necesario
    const tipoServicio = document.querySelector('input[name="tipo_propietario"]').value;
    if (tipoServicio === 'empresa' && !sucursalSeleccionada) {
        Swal.fire({
            icon: 'warning',
            title: 'Sucursal requerida',
            text: 'Por favor seleccione una sucursal antes de continuar.',
            confirmButtonText: 'Entendido'
        });
        return;
    }
    // Validar descripción
    const descripcion = document.getElementById('descripcion_solicitud').value.trim();
    if (!descripcion) {
        Swal.fire({
            icon: 'warning',
            title: 'Descripción requerida',
            text: 'Por favor proporcione una descripción de su solicitud.',
            confirmButtonText: 'Entendido'
        });
        return;
    }
    // Validar dirección
    const direccion = document.getElementById('direccion').value.trim();
    if (!direccion) {
        Swal.fire({
            icon: 'warning',
            title: 'Dirección requerida',
            text: 'Por favor proporcione la dirección donde se requiere el servicio.',
            confirmButtonText: 'Entendido'
        });
        return;
    }
    // Mostrar loading
    Swal.fire({
        title: 'Enviando solicitud...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    // Enviar formulario
    const formData = new FormData(this);
    fetch(window.location.href, {
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
                icon: 'success',
                title: '¡Solicitud enviada!',
                text: data.message,
                confirmButtonText: 'Continuar'
            }).then(() => {
                window.location.href = solicitudRedirectUrl;
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message,
                confirmButtonText: 'Intentar de nuevo'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'No se pudo enviar la solicitud. Por favor intente de nuevo.',
            confirmButtonText: 'Intentar de nuevo'
        });
    });
});

// Variable global para redirección
const solicitudRedirectUrl = document.getElementById('solicitudForm')?.getAttribute('data-redirect-url') || '/';
