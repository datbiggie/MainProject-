/**
 * Interacciones Modernas para Configuración de Categorías de Productos
 * Maneja animaciones, efectos y funcionalidades del nuevo diseño
 */

class ModernCategoryManager {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.initAnimations();
    }

    init() {
        // Inicializar componentes cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
    }

    onDOMReady() {
        this.setupIntersectionObserver();
        this.initParallaxEffect();
        this.setupSearchEnhancements();
        this.initStatsCounter();
        this.setupCardHoverEffects();
    }

    setupEventListeners() {
        // Mejorar la búsqueda con debounce
        const searchInput = document.getElementById('busqueda');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 300);
            });
        }

        // Mejorar el filtro de estatus
        const statusFilter = document.getElementById('filtroEstatus');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterByStatus(e.target.value);
            });
        }

        // Agregar efectos de clic a los botones
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modern-btn')) {
                this.createRippleEffect(e);
            }
        });
    }

    setupIntersectionObserver() {
        // Animaciones de entrada para las tarjetas
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Observar todas las tarjetas de categoría
        document.querySelectorAll('.category-card').forEach(card => {
            observer.observe(card);
        });
    }

    initParallaxEffect() {
        // Efecto parallax sutil para el fondo
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.modern-container::before');
            
            parallaxElements.forEach(element => {
                const speed = 0.5;
                element.style.transform = `translateY(${scrolled * speed}px)`;
            });
        });
    }

    setupSearchEnhancements() {
        const searchInput = document.getElementById('busqueda');
        if (!searchInput) return;

        // Efectos de focus
        const searchContainer = searchInput.parentElement;
        searchInput.addEventListener('focus', () => {
            searchContainer.classList.add('search-focused');
        });

        searchInput.addEventListener('blur', () => {
            searchContainer.classList.remove('search-focused');
        });
    }

    performSearch(query) {
        const cards = document.querySelectorAll('.category-card');
        const searchQuery = query.toLowerCase().trim();

        cards.forEach(card => {
            const title = card.querySelector('.category-title');
            const description = card.querySelector('.category-description');
            
            if (title && description) {
                const titleText = title.textContent.toLowerCase();
                const descText = description.textContent.toLowerCase();
                
                const matches = titleText.includes(searchQuery) || descText.includes(searchQuery);
                
                if (matches || searchQuery === '') {
                    card.style.display = 'block';
                    card.classList.add('search-match');
                } else {
                    card.style.display = 'none';
                    card.classList.remove('search-match');
                }
            }
        });

        this.updateSearchResults(searchQuery);
    }

    filterByStatus(status) {
        const cards = document.querySelectorAll('.category-card');
        
        cards.forEach(card => {
            const statusBadge = card.querySelector('.status-badge');
            if (!statusBadge) return;

            const cardStatus = statusBadge.classList.contains('status-active') ? 'activo' : 'inactivo';
            
            if (status === 'todos' || status === cardStatus) {
                card.style.display = 'block';
                card.classList.add('status-match');
            } else {
                card.style.display = 'none';
                card.classList.remove('status-match');
            }
        });
    }

    updateSearchResults(query) {
        // Función simplificada sin contador de resultados
    }

    initStatsCounter() {
        // Contador animado para estadísticas
        const statsNumbers = document.querySelectorAll('.stats-number');
        
        const animateCounter = (element, target) => {
            let current = 0;
            const increment = target / 50;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                element.textContent = Math.floor(current);
            }, 30);
        };

        // Observar cuando las estadísticas entren en vista
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = parseInt(entry.target.textContent);
                    animateCounter(entry.target, target);
                    statsObserver.unobserve(entry.target);
                }
            });
        });

        statsNumbers.forEach(stat => {
            statsObserver.observe(stat);
        });
    }

    setupCardHoverEffects() {
        const cards = document.querySelectorAll('.category-card');
        
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                // Efecto de elevación suave
                card.style.transform = 'translateY(-8px) scale(1.02)';
                
                // Animar el icono
                const icon = card.querySelector('.category-icon');
                if (icon) {
                    icon.style.transform = 'scale(1.1) rotate(5deg)';
                }
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
                
                const icon = card.querySelector('.category-icon');
                if (icon) {
                    icon.style.transform = 'scale(1) rotate(0deg)';
                }
            });
        });
    }

    createRippleEffect(event) {
        const button = event.target;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    // Método para actualizar estadísticas dinámicamente
    updateStats() {
        const totalCards = document.querySelectorAll('.category-card').length;
        const activeCards = document.querySelectorAll('.status-active').length;
        const inactiveCards = totalCards - activeCards;
        
        // Actualizar contadores si existen
        const totalStat = document.querySelector('[data-stat="total"]');
        const activeStat = document.querySelector('[data-stat="active"]');
        const inactiveStat = document.querySelector('[data-stat="inactive"]');
        
        if (totalStat) totalStat.textContent = totalCards;
        if (activeStat) activeStat.textContent = activeCards;
        if (inactiveStat) inactiveStat.textContent = inactiveCards;
    }

    // Método para mostrar notificaciones modernas
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `modern-notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="lni lni-${type === 'success' ? 'checkmark' : type === 'error' ? 'cross' : 'information'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Remover después de 3 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Método para inicializar tooltips modernos
    initTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'modern-tooltip';
                tooltip.textContent = e.target.getAttribute('data-tooltip');
                document.body.appendChild(tooltip);
                
                const rect = e.target.getBoundingClientRect();
                tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
                
                setTimeout(() => tooltip.classList.add('show'), 100);
            });
            
            element.addEventListener('mouseleave', () => {
                const tooltip = document.querySelector('.modern-tooltip');
                if (tooltip) {
                    tooltip.classList.remove('show');
                    setTimeout(() => tooltip.remove(), 200);
                }
            });
        });
    }

    initAnimations() {
        // Inicializar animaciones generales
        const animatedElements = document.querySelectorAll('.category-card, .stats-card, .glass-card');
        
        animatedElements.forEach((element, index) => {
            // No modificar el background, solo aplicar animaciones de posición y opacidad
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
                // No aplicar estilos de background aquí para evitar efectos visuales
            }, index * 100);
        });
    }
}

// Inicializar cuando el script se carga
const modernCategoryManager = new ModernCategoryManager();

// Exponer métodos globalmente para compatibilidad
window.modernCategoryManager = modernCategoryManager;

// Estilos CSS adicionales para efectos JavaScript
const additionalStyles = `
<style>
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s linear;
    pointer-events: none;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}





.modern-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
    padding: 1rem 1.5rem;
    z-index: 1000;
    transform: translateX(100%);
    transition: transform 0.3s ease;
    border-left: 4px solid var(--primary-blue);
}

.modern-notification.show {
    transform: translateX(0);
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.modern-tooltip {
    position: absolute;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    font-size: 0.8rem;
    z-index: 1000;
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: none;
}

.modern-tooltip.show {
    opacity: 1;
}

.modern-tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: rgba(0, 0, 0, 0.8);
}
</style>
`;

// Inyectar estilos adicionales
document.head.insertAdjacentHTML('beforeend', additionalStyles);