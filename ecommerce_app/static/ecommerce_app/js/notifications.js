// Sistema de Notificaciones - Versión segura sin polling automático
// Solo carga notificaciones una vez al inicializar la página

(function() {
    'use strict';
    
    // Prevenir múltiples ejecuciones del script
    if (window.NotificationSystemInitialized) {
        console.log('Sistema de notificaciones ya inicializado');
        return;
    }
    window.NotificationSystemInitialized = true;
    
    class SafeNotificationManager {
        constructor() {
            this.isLoaded = false;
            this.init();
        }
        
        init() {
            if (this.isLoaded) {
                return;
            }
            
            console.log('Inicializando SafeNotificationManager');
            
            // Verificar autenticación
            const isAuthenticated = document.querySelector('meta[name="user-authenticated"]')?.content === 'true';
            console.log('Usuario autenticado:', isAuthenticated);
            
            if (isAuthenticated) {
                this.isLoaded = true;
                
                // Cargar notificaciones solo una vez al inicializar
                this.loadNotificationsOnce();
                
                // Configurar eventos para marcar como leídas
                this.setupMarkAsReadEvents();
                


            } else {
                console.log('Usuario no autenticado, no se cargarán notificaciones');
            }
            

        }
        
        async loadNotificationsOnce() {
            try {
                console.log('Cargando notificaciones (una sola vez)...');
                const response = await fetch('/ecommerce/obtener_notificaciones/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('DATOS COMPLETOS RECIBIDOS:', data);
                    console.log('total_no_leidas:', data.total_no_leidas);
                    console.log('ventas_pendientes_count:', data.ventas_pendientes_count);
                    console.log('notificaciones length:', data.notificaciones ? data.notificaciones.length : 0);
                    console.log('ventas_pendientes length:', data.ventas_pendientes ? data.ventas_pendientes.length : 0);
                    
                    this.updateNotificationBadge(data.total_no_leidas || 0);
                    console.log('Notificaciones cargadas exitosamente:', data.total_no_leidas || 0);
                } else {
                    console.warn('Error al cargar notificaciones:', response.status);
                    console.log('Response text:', await response.text());
                }
            } catch (error) {
                console.error('Error en loadNotificationsOnce:', error);
            }
        }
        
        updateNotificationBadge(count) {
            // Buscar badges por clase e ID
            const badgesByClass = document.querySelectorAll('.notification-badge, .badge-notification');
            const badgeById = document.getElementById('notification-badge');
            const allBadges = [...badgesByClass];
            if (badgeById && !allBadges.includes(badgeById)) {
                allBadges.push(badgeById);
            }
            
            const bellLink = document.querySelector('a[title="Mis Notificaciones"]');
            const bellSvg = bellLink ? bellLink.querySelector('svg') : null;
            
            console.log('Actualizando notificaciones - Count:', count);
            
            // Actualizar todos los badges
            allBadges.forEach((badge, index) => {
                if (count > 0) {
                    badge.textContent = count;
                    badge.style.display = 'inline';
                    badge.classList.add('show');
                } else {
                    badge.style.display = 'none';
                    badge.classList.remove('show');
                }
            });
            
            // Cambiar el estilo del icono usando clases CSS
            if (bellLink) {
                console.log('Aplicando/removiendo clases CSS al enlace');
                if (count > 0) {
                    bellLink.classList.add('notification-active', 'bell-shake');
                    console.log('Clases aplicadas: notification-active, bell-shake');
                    
                    // Remover la animación de sacudida inicial después de que termine
                    setTimeout(() => {
                        bellLink.classList.remove('bell-shake');
                        console.log('Clase bell-shake removida');
                    }, 800);
                    
                    // Agregar vibración periódica cada 10 segundos
                    this.startPeriodicShake(bellLink);
                    
                } else {
                    bellLink.classList.remove('notification-active', 'bell-shake');
                    console.log('Clases removidas: notification-active, bell-shake');
                    
                    // Detener vibración periódica
                    this.stopPeriodicShake();
                }
            } else {
                console.log('No se pudo encontrar el enlace de notificaciones');
            }
            console.log('=== FIN DEBUG ===');
        }
        

        
        setupMarkAsReadEvents() {
            document.addEventListener('click', (e) => {
                if (e.target.classList.contains('mark-read-btn') || 
                    e.target.closest('.mark-read-btn')) {
                    const button = e.target.classList.contains('mark-read-btn') ? 
                                 e.target : e.target.closest('.mark-read-btn');
                    const notificationId = button.getAttribute('data-notificacion-id');
                    if (notificationId) {
                        this.markAsRead(notificationId, button);
                    }
                }
            });
        }
        
        async markAsRead(notificationId, button) {
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                                window.csrfToken || 
                                document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
                
                // Detectar si es empresa basado en el tipo de cuenta
                const esEmpresa = window.accountType === 'empresa';
                
                const response = await fetch(window.marcarNotificacionUrl || '/ecommerce/marcar_notificacion_leida/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        notificacion_id: notificationId,
                        es_empresa: esEmpresa
                    })
                });
                
                if (response.ok) {
                    // Marcar visualmente como leída
                    const notificationCard = button.closest('.notification-card');
                    if (notificationCard) {
                        notificationCard.classList.remove('unread');
                        notificationCard.classList.add('read');
                        button.remove();
                    }
                    
                    // Recargar notificaciones una sola vez
                    this.loadNotificationsOnce();
                    
                    console.log('Notificación marcada como leída');
                } else {
                    console.error('Error al marcar notificación como leída');
                }
            } catch (error) {
                console.error('Error en markAsRead:', error);
            }
        }
        
        // Método para iniciar vibración periódica
        startPeriodicShake(bellLink) {
            // Limpiar cualquier intervalo anterior
            this.stopPeriodicShake();
            
            // Crear nuevo intervalo para vibración cada 10 segundos
            this.shakeInterval = setInterval(() => {
                if (bellLink && bellLink.classList.contains('notification-active')) {
                    bellLink.classList.add('bell-shake');
                    
                    // Remover la clase después de la animación
                    setTimeout(() => {
                        bellLink.classList.remove('bell-shake');
                    }, 800);
                }
            }, 10000); // 10 segundos
            
            console.log('Vibración periódica iniciada');
        }
        
        // Método para detener vibración periódica
        stopPeriodicShake() {
            if (this.shakeInterval) {
                clearInterval(this.shakeInterval);
                this.shakeInterval = null;
                console.log('Vibración periódica detenida');
            }
        }
    }
    
    // Función para verificar autenticación
    function isUserAuthenticated() {
        const metaAuth = document.querySelector('meta[name="user-authenticated"]');
        return metaAuth && metaAuth.getAttribute('content') === 'true';
    }
    
    // Inicialización segura
    function initSafeNotificationSystem() {
        if (!isUserAuthenticated()) {
            console.log('Usuario no autenticado, no iniciando sistema de notificaciones');
            return;
        }
        
        if (window.safeNotificationManager) {
            console.log('Sistema de notificaciones seguro ya inicializado');
            return;
        }
        
        window.safeNotificationManager = new SafeNotificationManager();
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSafeNotificationSystem);
    } else {
        initSafeNotificationSystem();
    }
    
})();