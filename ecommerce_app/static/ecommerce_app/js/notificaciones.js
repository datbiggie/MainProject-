// Función para redireccionar según el tipo de notificación (definida globalmente)
function redirectToNotification(notificationElement) {
    const tipo = $(notificationElement).data('tipo');
    const solicitudId = $(notificationElement).data('solicitud-id');
    const pedidoId = $(notificationElement).data('pedido-id');
    const notificacionId = $(notificationElement).data('id');
    const tituloNotificacion = $(notificationElement).find('h6').text() || '';
    
    // Debug: mostrar los valores recibidos
    console.log('Datos de notificación:', {
        tipo: tipo,
        solicitudId: solicitudId,
        pedidoId: pedidoId,
        accountType: window.accountType
    });
    
    let redirectUrl = '';
    
    // Determinar la URL de redirección según el tipo de notificación
    if (tipo === 'solicitud_servicio') {
        // Nueva solicitud de servicio (eres el proveedor) -> ir a ventas pendientes
        redirectUrl = '/ecommerce/servicios_ventas_pendientes/';
    } else if (tipo === 'servicio' || tipo === 'servicio_cotizado' || 
        tipo === 'servicio_aceptado' || tipo === 'servicio_completado') {
        // Actualizaciones de tus propias solicitudes -> ir a gestión de servicios
        redirectUrl = '/ecommerce/gestion_servicio/';
    } else if (tipo === 'servicio_pagado' || /pago recibido/i.test(tituloNotificacion)) {
        // Cuando se recibe el pago por una solicitud, llevar a la vista de servicios confirmados
        redirectUrl = '/ecommerce/servicios_ventas_confirmadas/';
    } else if (tipo === 'pedido_confirmado' || tipo === 'venta_confirmada') {
        // Para notificaciones de pedido/venta confirmada llevar a la vista de pedidos confirmados
        // Nota: para empresas la vista usa el tipo 'venta_confirmada' en backend
        redirectUrl = '/ecommerce/pedidos_confirmados/';
    } else if (tipo === 'nuevo_pedido' || tipo === 'pago') {
        if (pedidoId) {
            // Redireccionar a mis pedidos o ventas pendientes según el tipo de usuario
            if (window.accountType === 'empresa') {
                // La ruta correcta en el proyecto es /ecommerce/ventas_pendientes/
                redirectUrl = '/ecommerce/ventas_pendientes/';
            } else {
                redirectUrl = '/ecommerce/mis_pedidos/';
            }
        }
    }
    
    // Realizar la redirección si se encontró una URL válida
    if (redirectUrl) {
        // Si la notificación está sin leer, marcarla como leída antes de redirigir (no bloquear la navegación)
        if (notificacionId) {
            const esEmpresa = window.accountType === 'empresa';
            $.ajax({
                url: marcarNotificacionUrl,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    'notificacion_id': notificacionId,
                    'es_empresa': esEmpresa
                }),
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }).always(function() {
                // Navegar aunque falle la petición de marcado
                window.location.href = redirectUrl;
            });
        } else {
            window.location.href = redirectUrl;
        }
    } else {
        console.warn('No se pudo determinar la URL de redirección para esta notificación');
    }
}

// JavaScript para el manejo de notificaciones
$(document).ready(function() {
    // Event listener para los botones de marcar como leída
    $('.mark-read-btn').on('click', function() {
        const notificacionId = $(this).data('notificacion-id');
        marcarComoLeida(notificacionId);
    });

    // Manejar clics en notificaciones para redirección
    $('.clickable-notification').on('click', function() {
        redirectToNotification(this);
    });
});

function marcarComoLeida(notificacionId) {
    // Detectar si es empresa basado en el tipo de cuenta
    const esEmpresa = window.accountType === 'empresa';
    
    $.ajax({
        url: marcarNotificacionUrl, // Esta variable debe ser definida en el template
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            'notificacion_id': notificacionId,
            'es_empresa': esEmpresa
        }),
        headers: {
            'X-CSRFToken': csrfToken, // Esta variable debe ser definida en el template
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            if (response.success) {
                // Actualizar la tarjeta de notificación
                const card = $(`.notification-card[data-id="${notificacionId}"]`);
                card.removeClass('unread').addClass('read');
                card.find('.mark-read-btn').remove();
                
                // Agregar indicador de leída
                const now = new Date();
                const fechaLeida = now.toLocaleDateString('es-ES') + ' ' + now.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'});
                card.find('.notification-time').parent().append(
                    `<small class="text-success">
                        <i class="fas fa-check-circle me-1"></i>
                        Leída el ${fechaLeida}
                    </small>`
                );
                
                // Mostrar mensaje de éxito
                Swal.fire({
                    icon: 'success',
                    title: 'Notificación marcada como leída',
                    showConfirmButton: false,
                    timer: 1500
                });
                
                // Actualizar contador si existe
                updateNotificationCounter();
            }
        },
        error: function() {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo marcar la notificación como leída'
            });
        }
    });
}

function updateNotificationCounter() {
    // Contar notificaciones no leídas restantes
    const unreadCount = $('.notification-card.unread').length;
    
    // Actualizar el texto del header
    const headerText = $('.notification-header p');
    if (unreadCount > 0) {
        headerText.text(`Tienes ${unreadCount} notificación${unreadCount > 1 ? 'es' : ''} sin leer`);
    } else {
        headerText.text('Todas las notificaciones están al día');
    }
}