// Funcionalidad adicional para acordeones de categorías

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar acordeones
    initializeAccordions();
    
    // Agregar funcionalidad de búsqueda rápida
    addSearchFunctionality();
    
    // Agregar animaciones suaves
    addSmoothAnimations();
});

function initializeAccordions() {
    const accordionButtons = document.querySelectorAll('.accordion-button');
    
    accordionButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Agregar clase de animación al hacer clic
            this.classList.add('clicking');
            
            setTimeout(() => {
                this.classList.remove('clicking');
            }, 200);
        });
    });
}

function addSearchFunctionality() {
    // Crear barra de búsqueda si no existe
    const accordionContainer = document.querySelector('.accordion');
    if (!accordionContainer) return;
    
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container mb-3';
    searchContainer.innerHTML = `
        <div class="input-group">
            <span class="input-group-text">
                <i class="fas fa-search"></i>
            </span>
            <input type="text" class="form-control" id="categorySearch" placeholder="Buscar en categorías...">
            <button class="btn btn-outline-secondary" type="button" id="clearSearch">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    accordionContainer.parentNode.insertBefore(searchContainer, accordionContainer);
    
    // Funcionalidad de búsqueda
    const searchInput = document.getElementById('categorySearch');
    const clearButton = document.getElementById('clearSearch');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterCategories(this.value.toLowerCase());
        });
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            searchInput.value = '';
            filterCategories('');
        });
    }
}

function filterCategories(searchTerm) {
    const accordionItems = document.querySelectorAll('.accordion-item');
    
    accordionItems.forEach(item => {
        const categoryName = item.querySelector('.accordion-button strong').textContent.toLowerCase();
        const itemCards = item.querySelectorAll('.ml-horizontal-card');
        
        let hasMatchingItems = false;
        
        // Buscar en nombres de categoría
        if (categoryName.includes(searchTerm)) {
            hasMatchingItems = true;
        } else {
            // Buscar en nombres de productos/servicios
            itemCards.forEach(card => {
                const itemName = card.querySelector('.ml-horizontal-card-title')?.textContent.toLowerCase() || '';
                const itemDescription = card.querySelector('.ml-horizontal-card-description')?.textContent.toLowerCase() || '';
                
                if (itemName.includes(searchTerm) || itemDescription.includes(searchTerm)) {
                    hasMatchingItems = true;
                }
            });
        }
        
        // Mostrar/ocultar categoría
        if (hasMatchingItems || searchTerm === '') {
            item.style.display = 'block';
            item.style.animation = 'fadeInUp 0.3s ease forwards';
        } else {
            item.style.display = 'none';
        }
    });
    
    // Mostrar mensaje si no hay resultados
    showNoResultsMessage(searchTerm);
}

function showNoResultsMessage(searchTerm) {
    const accordionContainer = document.querySelector('.accordion');
    let noResultsMsg = document.getElementById('noResultsMessage');
    
    if (searchTerm && !document.querySelector('.accordion-item[style*="block"]')) {
        if (!noResultsMsg) {
            noResultsMsg = document.createElement('div');
            noResultsMsg.id = 'noResultsMessage';
            noResultsMsg.className = 'alert alert-info text-center';
            noResultsMsg.innerHTML = `
                <i class="fas fa-search mb-2" style="font-size: 2rem; opacity: 0.5;"></i>
                <h5>No se encontraron resultados</h5>
                <p class="mb-0">No hay categorías o elementos que coincidan con "<strong>${searchTerm}</strong>"</p>
            `;
            accordionContainer.parentNode.appendChild(noResultsMsg);
        }
        noResultsMsg.style.display = 'block';
    } else {
        if (noResultsMsg) {
            noResultsMsg.style.display = 'none';
        }
    }
}

function addSmoothAnimations() {
    // Observador de intersección para animaciones de entrada
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Observar elementos del acordeón
    document.querySelectorAll('.accordion-item').forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(item);
    });
}

// Función para expandir/contraer todas las categorías
function toggleAllCategories(expand = true) {
    const accordionButtons = document.querySelectorAll('.accordion-button');
    
    accordionButtons.forEach(button => {
        const isExpanded = !button.classList.contains('collapsed');
        
        if (expand && button.classList.contains('collapsed')) {
            button.click();
        } else if (!expand && !button.classList.contains('collapsed')) {
            button.click();
        }
    });
}

// Agregar botones de control global
function addGlobalControls() {
    const accordionContainer = document.querySelector('.accordion');
    if (!accordionContainer) return;
    
    const controlsContainer = document.createElement('div');
    controlsContainer.className = 'accordion-controls mb-3 text-end';
    controlsContainer.innerHTML = `
        <div class="btn-group" role="group">
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="toggleAllCategories(true)">
                <i class="fas fa-expand-alt"></i> Expandir Todo
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="toggleAllCategories(false)">
                <i class="fas fa-compress-alt"></i> Contraer Todo
            </button>
        </div>
    `;
    
    accordionContainer.parentNode.insertBefore(controlsContainer, accordionContainer);
}

// Inicializar controles globales cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    addGlobalControls();
});

// Función para contar elementos en cada categoría
function updateCategoryCounters() {
    const accordionItems = document.querySelectorAll('.accordion-item');
    
    accordionItems.forEach(item => {
        const badge = item.querySelector('.badge');
        const cards = item.querySelectorAll('.ml-horizontal-card');
        
        if (badge && cards.length > 0) {
            badge.textContent = cards.length;
        }
    });
}

// Actualizar contadores al cargar la página
document.addEventListener('DOMContentLoaded', updateCategoryCounters);

// Estilos CSS adicionales para la funcionalidad
const additionalStyles = `
<style>
.search-container .input-group {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    overflow: hidden;
}

.search-container .form-control {
    border: none;
    box-shadow: none;
}

.search-container .form-control:focus {
    box-shadow: none;
    border-color: transparent;
}

.accordion-button.clicking {
    transform: scale(0.98);
    transition: transform 0.1s ease;
}

.accordion-controls .btn {
    font-size: 0.875rem;
    padding: 0.375rem 0.75rem;
}

@media (max-width: 768px) {
    .accordion-controls {
        text-align: center;
    }
    
    .accordion-controls .btn {
        font-size: 0.8rem;
        padding: 0.25rem 0.5rem;
    }
}
</style>
`;

// Agregar estilos adicionales al head
document.addEventListener('DOMContentLoaded', function() {
    document.head.insertAdjacentHTML('beforeend', additionalStyles);
});