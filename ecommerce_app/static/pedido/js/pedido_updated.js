// ===== PEDIDO JAVASCRIPT - ELEGANT FUNCTIONALITY =====

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the order system
    initializeOrderSystem();
});

// Also ensure calculation runs when window is fully loaded
window.addEventListener('load', function() {
    console.log('Window fully loaded, calculating vendor totals...');
    calculateVendorTotals();
});

function initializeOrderSystem() {
    // Calculate vendor totals
    calculateVendorTotals();
    
    // Setup payment method handlers
    setupPaymentMethodHandlers();
    
    // Setup individual order buttons
    setupIndividualOrderButtons();
    
    // Setup "Finalizar Todos" button
    setupFinalizarTodosButton();
    
    // Setup form validation
    setupFormValidation();
}

// Calculate totals for each vendor
function calculateVendorTotals() {
    console.log('=== CALCULATING VENDOR TOTALS ===');
    const vendorTotals = {};
    
    // Debug: Check if product items exist
    const productItems = document.querySelectorAll('.product-item-new');
    console.log(`Found ${productItems.length} product items`);
    
    if (productItems.length === 0) {
        console.log('No product items found, trying alternative selector');
        // Try alternative approach - look for vendor cards directly
        const vendorCards = document.querySelectorAll('.vendor-order-card');
        console.log(`Found ${vendorCards.length} vendor cards`);
        
        vendorCards.forEach(card => {
            const vendorForm = card.querySelector('.vendor-form');
            if (vendorForm) {
                const vendorId = vendorForm.getAttribute('data-vendor-id');
                console.log(`Processing vendor card for vendor ${vendorId}`);
                
                // Find all subtotals in this vendor card
                const subtotalElements = card.querySelectorAll('.col-md-2.text-end h6');
                console.log(`Found ${subtotalElements.length} subtotal elements for vendor ${vendorId}`);
                
                let vendorTotal = 0;
                subtotalElements.forEach(element => {
                    const subtotalText = element.textContent.replace('$', '').replace(',', '').trim();
                    const subtotal = parseFloat(subtotalText) || 0;
                    console.log(`Subtotal text: '${subtotalText}', parsed: ${subtotal}`);
                    vendorTotal += subtotal;
                });
                
                vendorTotals[vendorId] = vendorTotal;
                console.log(`Total for vendor ${vendorId}: ${vendorTotal}`);
            }
        });
    } else {
        // Original approach
        productItems.forEach(item => {
            const vendorCard = item.closest('.vendor-order-card');
            const vendorForm = vendorCard ? vendorCard.querySelector('.vendor-form') : null;
            
            if (!vendorForm) {
                console.log('No vendor form found for item:', item);
                return;
            }
            
            const vendorId = vendorForm.getAttribute('data-vendor-id');
            
            // Get subtotal from the product
            const subtotalElement = item.querySelector('.col-md-2.text-end h6');
            
            if (!subtotalElement) {
                console.log('No subtotal element found for item:', item);
                return;
            }
            
            const subtotalText = subtotalElement.textContent.replace('$', '').replace(',', '').trim();
            const subtotal = parseFloat(subtotalText) || 0;
            
            console.log(`Vendor ${vendorId}: Adding subtotal ${subtotal} from text '${subtotalText}'`);
            
            if (!vendorTotals[vendorId]) {
                vendorTotals[vendorId] = 0;
            }
            vendorTotals[vendorId] += subtotal;
        });
    }
    
    console.log('Final vendor totals calculated:', vendorTotals);
    
    // Update vendor total displays
    Object.keys(vendorTotals).forEach(vendorId => {
        const totalElement = document.querySelector(`.vendor-total-${vendorId}`);
        if (totalElement) {
            totalElement.textContent = vendorTotals[vendorId].toFixed(2);
            console.log(`✅ Updated total for vendor ${vendorId}: ${vendorTotals[vendorId].toFixed(2)}`);
        } else {
            console.log(`❌ Total element not found for vendor ${vendorId}`);
            // Debug: List all vendor total elements
            const allTotalElements = document.querySelectorAll('[class*="vendor-total-"]');
            console.log('Available total elements:', Array.from(allTotalElements).map(el => el.className));
        }
    });
    
    console.log('=== END CALCULATING VENDOR TOTALS ===');
}

// Setup payment method change handlers
function setupPaymentMethodHandlers() {
    document.querySelectorAll('.vendor-form select[name="metodo_pago"]').forEach(select => {
        select.addEventListener('change', function() {
            const comprobanteSection = this.closest('.vendor-form').querySelector('.comprobante-section');
            const comprobanteInput = comprobanteSection.querySelector('input[type="file"]');
            
            if (['transferencia', 'pago_movil', 'paypal'].includes(this.value)) {
                comprobanteSection.style.display = 'block';
                comprobanteSection.classList.add('show');
                comprobanteInput.required = true;
            } else {
                comprobanteSection.style.display = 'none';
                comprobanteSection.classList.remove('show');
                comprobanteInput.required = false;
                comprobanteInput.value = '';
            }
        });
    });
}

// Setup individual order buttons
function setupIndividualOrderButtons() {
    document.querySelectorAll('.btn-finalizar-individual').forEach(button => {
        button.addEventListener('click', function() {
            const vendorId = this.getAttribute('data-vendor-id');
            const vendorType = this.getAttribute('data-vendor-type');
            const vendorName = this.getAttribute('data-vendor-name');
            
            processIndividualOrder(vendorId, vendorType, vendorName, this);
        });
    });
}

// Setup "Finalizar Todos" button
function setupFinalizarTodosButton() {
    const finalizarTodosBtn = document.getElementById('finalizarTodos');
    if (finalizarTodosBtn) {
        finalizarTodosBtn.addEventListener('click', function() {
            processAllOrders(this);
        });
    }
}

// Función para finalizar pedido individual
function finalizarPedidoIndividual(vendedorId, vendedorTipo) {
    console.log('Finalizando pedido individual:', vendedorId, vendedorTipo);
    
    // Validar datos generales
    if (!validarDatosGenerales()) {
        return;
    }
    
    // Obtener datos del formulario general
    const datosGenerales = obtenerDatosGenerales();
    
    // Obtener método de pago específico del vendedor
    const metodoPagoElement = document.querySelector(`#metodo-pago-${vendedorTipo}-${vendedorId}`);
    if (!metodoPagoElement || !metodoPagoElement.value) {
        mostrarError('Por favor selecciona un método de pago para este vendedor.');
        return;
    }
    
    const metodoPago = metodoPagoElement.value;
    
    // Crear objeto de datos para enviar
    const datosEnvio = {
        ...datosGenerales,
        metodoPago: metodoPago,
        vendedoresSeleccionados: JSON.stringify([`${vendedorTipo}_${vendedorId}`]),
        finalizarTodos: 'false'
    };
    
    enviarPedido(datosEnvio, `pedido-${vendedorTipo}-${vendedorId}`);
}

// Función para enviar pedido
function enviarPedido(datosEnvio, identificador) {
    console.log('Enviando pedido:', identificador, datosEnvio);
    
    // Mostrar indicador de carga
    const loadingElement = mostrarCarga('Procesando pedido...');
    
    // Obtener el token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Crear FormData para enviar los datos
    const formData = new FormData();
    Object.keys(datosEnvio).forEach(key => {
        formData.append(key, datosEnvio[key]);
    });
    formData.append('csrfmiddlewaretoken', csrfToken);
    
    // Enviar petición AJAX
    fetch('/procesar_pedido/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        ocultarCarga(loadingElement);
        
        if (data.success) {
            mostrarExito('¡Pedido procesado exitosamente!');
            
            // Opcional: redirigir o actualizar la página después de un tiempo
            setTimeout(() => {
                window.location.href = '/carrito/';
            }, 2000);
        } else {
            mostrarError(data.error || 'Error al procesar el pedido');
        }
    })
    .catch(error => {
        ocultarCarga(loadingElement);
        console.error('Error:', error);
        mostrarError('Error de conexión. Por favor intenta nuevamente.');
    });
}

// Función para mostrar indicador de carga
function mostrarCarga(mensaje) {
    const loadingElement = document.createElement('div');
    loadingElement.id = 'loading-message';
    loadingElement.className = 'alert alert-info';
    loadingElement.style.marginTop = '10px';
    loadingElement.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            ${mensaje}
        </div>
    `;
    
    const container = document.querySelector('.pedido-container');
    if (container) {
        container.insertBefore(loadingElement, container.firstChild);
    }
    
    return loadingElement;
}

// Función para ocultar indicador de carga
function ocultarCarga(loadingElement) {
    if (loadingElement && loadingElement.parentNode) {
        loadingElement.parentNode.removeChild(loadingElement);
    }
}

// Función para mostrar mensajes de éxito
function mostrarExito(mensaje) {
    // Crear o actualizar el elemento de éxito
    let successElement = document.getElementById('success-message');
    if (!successElement) {
        successElement = document.createElement('div');
        successElement.id = 'success-message';
        successElement.className = 'alert alert-success';
        successElement.style.marginTop = '10px';
        
        // Insertar al inicio del contenedor principal
        const container = document.querySelector('.pedido-container');
        if (container) {
            container.insertBefore(successElement, container.firstChild);
        }
    }
    
    successElement.textContent = mensaje;
    successElement.style.display = 'block';
    
    // Ocultar el mensaje después de 5 segundos
    setTimeout(() => {
        successElement.style.display = 'none';
    }, 5000);
    
    // Scroll hacia arriba para mostrar el éxito
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Process individual order
function processIndividualOrder(vendorId, vendorType, vendorName, button) {
    // Validate general info first
    if (!validateGeneralInfo()) {
        showAlert('Por favor, complete la información general antes de continuar.', 'warning');
        return;
    }
    
    // Validate vendor form
    const vendorForm = button.closest('.vendor-form');
    if (!validateVendorForm(vendorForm)) {
        showAlert('Por favor, complete todos los campos requeridos para este vendedor.', 'warning');
        return;
    }
    
    // Show loading state
    setButtonLoading(button, true);
    
    // Collect order data
    const orderData = collectOrderData([vendorId], [vendorType]);
    
    // Create FormData for backend compatibility
    const formData = new FormData();
    formData.append('nombre', orderData.general_info.nombre);
    formData.append('email', orderData.general_info.email);
    formData.append('telefono', orderData.general_info.telefono);
    formData.append('direccion_envio', orderData.general_info.direccion_envio);
    formData.append('notas_adicionales', orderData.general_info.notas_pedido);
    formData.append('vendedoresSeleccionados', JSON.stringify(orderData.selected_vendors));
    formData.append('finalizarTodos', 'false');
    
    // Add vendor-specific data
    if (orderData.vendor_data.length > 0) {
        formData.append('metodoPago', orderData.vendor_data[0].metodo_pago);
    }
    
    // Send order
    fetch('/ecommerce/procesar_pedido/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        setButtonLoading(button, false);
        
        if (data.success) {
            showOrderSuccess(vendorId, data.orders[0], button);
            showAlert(`¡Pedido de ${vendorName} procesado exitosamente!`, 'success');
        } else {
            showAlert(data.message || 'Error al procesar el pedido', 'error');
        }
    })
    .catch(error => {
        setButtonLoading(button, false);
        console.error('Error:', error);
        showAlert('Error de conexión. Intente nuevamente.', 'error');
    });
}

// Función para finalizar todos los pedidos
function finalizarTodosPedidos() {
    console.log('Finalizando todos los pedidos');
    
    // Validar datos generales
    if (!validarDatosGenerales()) {
        return;
    }
    
    // Validar que todos los vendedores tengan método de pago seleccionado
    const metodosPagoElements = document.querySelectorAll('[id^="metodo-pago-"]');
    let todosTienenMetodoPago = true;
    
    metodosPagoElements.forEach(select => {
        if (!select.value) {
            todosTienenMetodoPago = false;
        }
    });
    
    if (!todosTienenMetodoPago) {
        mostrarError('Por favor selecciona un método de pago para todos los vendedores.');
        return;
    }
    
    // Obtener datos del formulario general
    const datosGenerales = obtenerDatosGenerales();
    
    // Para "finalizar todos", usamos el primer método de pago como referencia
    // (el backend procesará todos los vendedores independientemente)
    const primerMetodoPago = metodosPagoElements[0]?.value || 'efectivo';
    
    // Crear objeto de datos para enviar
    const datosEnvio = {
        ...datosGenerales,
        metodoPago: primerMetodoPago,
        finalizarTodos: 'true'
    };
    
    enviarPedido(datosEnvio, 'todos-pedidos');
}

// Process all orders
function processAllOrders(button) {
    // Validate general info
    if (!validateGeneralInfo()) {
        showAlert('Por favor, complete la información general antes de continuar.', 'warning');
        return;
    }
    
    // Validate all vendor forms
    const vendorForms = document.querySelectorAll('.vendor-form');
    let allValid = true;
    
    vendorForms.forEach(form => {
        if (!validateVendorForm(form)) {
            allValid = false;
        }
    });
    
    if (!allValid) {
        showAlert('Por favor, complete todos los campos requeridos para todos los vendedores.', 'warning');
        return;
    }
    
    // Show loading state
    setButtonLoading(button, true);
    
    // Collect all vendor IDs and types
    const vendorIds = [];
    const vendorTypes = [];
    
    vendorForms.forEach(form => {
        vendorIds.push(form.getAttribute('data-vendor-id'));
        vendorTypes.push(form.getAttribute('data-vendor-type'));
    });
    
    // Collect order data
    const orderData = collectOrderData(vendorIds, vendorTypes);
    
    // Send orders
    fetch('/ecommerce/procesar_pedido/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        setButtonLoading(button, false);
        
        if (data.success) {
            // Show success for all orders
            data.orders.forEach((order, index) => {
                const vendorId = vendorIds[index];
                const vendorButton = document.querySelector(`[data-vendor-id="${vendorId}"].btn-finalizar-individual`);
                showOrderSuccess(vendorId, order, vendorButton);
            });
            
            showAlert(`¡Todos los pedidos (${data.orders.length}) han sido procesados exitosamente!`, 'success');
            
            // Redirect after a delay
            setTimeout(() => {
                window.location.href = '/ecommerce/mis_pedidos/';
            }, 3000);
        } else {
            showAlert(data.message || 'Error al procesar los pedidos', 'error');
        }
    })
    .catch(error => {
        setButtonLoading(button, false);
        console.error('Error:', error);
        showAlert('Error de conexión. Intente nuevamente.', 'error');
    });
}

// Collect order data
function collectOrderData(vendorIds, vendorTypes) {
    const generalInfo = {
        nombre: document.getElementById('nombre_general').value,
        email: document.getElementById('email_general').value,
        telefono: document.getElementById('telefono_general').value,
        direccion_envio: document.getElementById('direccion_general').value,
        notas_pedido: document.getElementById('notas_general').value
    };
    
    const vendorData = [];
    
    vendorIds.forEach((vendorId, index) => {
        const vendorForm = document.querySelector(`[data-vendor-id="${vendorId}"].vendor-form`);
        const metodoPago = vendorForm.querySelector('select[name="metodo_pago"]').value;
        const comprobantePago = vendorForm.querySelector('input[name="comprobante_pago"]').files[0];
        
        vendorData.push({
            vendor_id: vendorId,
            vendor_type: vendorTypes[index],
            metodo_pago: metodoPago,
            comprobante_pago: comprobantePago ? comprobantePago.name : null
        });
    });
    
    // Format vendor IDs with type prefix for backend compatibility
    const formattedVendorIds = vendorIds.map((vendorId, index) => {
        return `${vendorTypes[index]}_${vendorId}`;
    });
    
    return {
        general_info: generalInfo,
        vendor_data: vendorData,
        selected_vendors: formattedVendorIds
    };
}

// Validate general info
function validateGeneralInfo() {
    const requiredFields = ['nombre_general', 'email_general', 'telefono_general', 'direccion_general'];
    
    for (let fieldId of requiredFields) {
        const field = document.getElementById(fieldId);
        if (!field.value.trim()) {
            field.focus();
            field.classList.add('is-invalid');
            return false;
        } else {
            field.classList.remove('is-invalid');
        }
    }
    
    return true;
}

// Validate vendor form
function validateVendorForm(form) {
    const metodoPago = form.querySelector('select[name="metodo_pago"]');
    const comprobanteInput = form.querySelector('input[name="comprobante_pago"]');
    
    // Check payment method
    if (!metodoPago.value) {
        metodoPago.focus();
        metodoPago.classList.add('is-invalid');
        return false;
    } else {
        metodoPago.classList.remove('is-invalid');
    }
    
    // Check comprobante if required
    if (comprobanteInput.required && !comprobanteInput.files.length) {
        comprobanteInput.focus();
        comprobanteInput.classList.add('is-invalid');
        return false;
    } else {
        comprobanteInput.classList.remove('is-invalid');
    }
    
    return true;
}

// Setup form validation
function setupFormValidation() {
    // Real-time validation for general info
    document.querySelectorAll('#generalInfoForm input, #generalInfoForm textarea').forEach(field => {
        field.addEventListener('blur', function() {
            if (this.required && !this.value.trim()) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid') && this.value.trim()) {
                this.classList.remove('is-invalid');
            }
        });
    });
    
    // Real-time validation for vendor forms
    document.querySelectorAll('.vendor-form select, .vendor-form input').forEach(field => {
        field.addEventListener('change', function() {
            if (this.required && !this.value) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });
}

// Show order success
function showOrderSuccess(vendorId, orderData, button) {
    const vendorCard = button.closest('.vendor-order-card');
    const orderStatus = vendorCard.querySelector('.order-status');
    const orderIdSpan = orderStatus.querySelector('.order-id');
    
    // Update order ID
    orderIdSpan.textContent = orderData.numero_pedido || orderData.id;
    
    // Show success status
    orderStatus.classList.remove('d-none');
    
    // Hide button and show processed state
    button.style.display = 'none';
    vendorCard.classList.add('order-processed');
    
    // Disable form
    const vendorForm = vendorCard.querySelector('.vendor-form');
    vendorForm.querySelectorAll('input, select').forEach(field => {
        field.disabled = true;
    });
}

// Set button loading state
function setButtonLoading(button, loading) {
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner-border');
    
    if (loading) {
        button.disabled = true;
        button.classList.add('processing');
        btnText.textContent = 'Procesando...';
        spinner.classList.remove('d-none');
    } else {
        button.disabled = false;
        button.classList.remove('processing');
        btnText.textContent = button.classList.contains('btn-finalizar-todos') ? 'Finalizar Todos los Pedidos' : 'Finalizar Pedido';
        spinner.classList.add('d-none');
    }
}

// Show alert
function showAlert(message, type) {
    // Remove existing alerts
    document.querySelectorAll('.alert-custom').forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show alert-custom`;
    alertDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'times-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Get CSRF token
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Función para obtener datos generales del formulario
function obtenerDatosGenerales() {
    return {
        nombre: document.getElementById('nombre').value,
        email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value,
        direccionEntrega: document.getElementById('direccion_envio').value,
        notasAdicionales: document.getElementById('notas_pedido').value
    };
}

// Función para validar datos generales
function validarDatosGenerales() {
    const nombre = document.getElementById('nombre').value.trim();
    const email = document.getElementById('email').value.trim();
    const telefono = document.getElementById('telefono').value.trim();
    const direccion = document.getElementById('direccion_envio').value.trim();
    
    if (!nombre) {
        mostrarError('Por favor ingresa tu nombre completo.');
        return false;
    }
    
    if (!email) {
        mostrarError('Por favor ingresa tu email.');
        return false;
    }
    
    // Validación básica de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        mostrarError('Por favor ingresa un email válido.');
        return false;
    }
    
    if (!telefono) {
        mostrarError('Por favor ingresa tu número de teléfono.');
        return false;
    }
    
    if (!direccion) {
        mostrarError('Por favor ingresa la dirección de entrega.');
        return false;
    }
    
    return true;
}

// Función para mostrar errores
function mostrarError(mensaje) {
    // Crear o actualizar el elemento de error
    let errorElement = document.getElementById('error-message');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = 'error-message';
        errorElement.className = 'alert alert-danger';
        errorElement.style.marginTop = '10px';
        
        // Insertar al inicio del contenedor principal
        const container = document.querySelector('.pedido-container');
        if (container) {
            container.insertBefore(errorElement, container.firstChild);
        }
    }
    
    errorElement.textContent = mensaje;
    errorElement.style.display = 'block';
    
    // Ocultar el mensaje después de 5 segundos
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
    
    // Scroll hacia arriba para mostrar el error
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-VE', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

// Initialize tooltips if Bootstrap is available
if (typeof bootstrap !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    });
}