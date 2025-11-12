// Variables globales para manejar los datos del carrito
let productosUsuario = [];
let productosSucursal = [];
let totalUsuario = 0;
let totalSucursal = 0;

// Inicializar datos del carrito desde el contexto de Django
document.addEventListener('DOMContentLoaded', function() {
    // Cargar datos del carrito y calcular totales
    if (window.productosCarritoData) {
        calculateSucursalTotals();
    }
    
    // Mostrar/ocultar sección de comprobante según método de pago para cada vendedor
    const metodoPagoSelects = document.querySelectorAll('select[name="metodo_pago"]');
    
    metodoPagoSelects.forEach(function(metodoPago) {
        metodoPago.addEventListener('change', function() {
            // Encontrar la sección de comprobante correspondiente en el mismo formulario
            const form = this.closest('.vendor-form');
            const comprobanteSection = form.querySelector('.comprobante-section');
            const comprobantePago = form.querySelector('input[name="comprobante_pago"]');
            
            if (comprobanteSection) {
                if (this.value === 'transferencia' || this.value === 'paypal' || this.value === 'pago_movil') {
                    comprobanteSection.style.display = 'block';
                    comprobanteSection.classList.add('show');
                    if (comprobantePago) {
                        comprobantePago.required = true;
                    }
                } else {
                    comprobanteSection.style.display = 'none';
                    comprobanteSection.classList.remove('show');
                    if (comprobantePago) {
                        comprobantePago.required = false;
                        comprobantePago.value = ''; // Limpiar archivo seleccionado
                    }
                }
            }
        });
    });
    
    // Validación y envío de formularios individuales por vendedor
    const botonesFinalizarIndividual = document.querySelectorAll('.btn-finalizar-individual');
    
    botonesFinalizarIndividual.forEach(function(boton) {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const form = this.closest('.vendor-form');
            const vendorId = this.getAttribute('data-vendor-id');
            const vendorType = this.getAttribute('data-vendor-type');
            const vendorName = this.getAttribute('data-vendor-name');
            
            // Validar método de pago
            const metodoPagoSelect = form.querySelector('select[name="metodo_pago"]');
            const metodoPagoSeleccionado = metodoPagoSelect?.value;
            
            if (!metodoPagoSeleccionado) {
                // Usar SweetAlert en lugar de alert() para una mejor experiencia
                Swal.fire({
                    title: 'Método de pago requerido',
                    text: 'Por favor, seleccione un método de pago.',
                    icon: 'warning',
                    confirmButtonText: 'Entendido',
                    confirmButtonColor: '#f59e0b'
                }).then(() => {
                    try { metodoPagoSelect.focus(); } catch(e) {}
                });
                return;
            }
            
            // Validar comprobante si es requerido
            const comprobantePago = form.querySelector('input[name="comprobante_pago"]');
            if ((metodoPagoSeleccionado === 'transferencia' || metodoPagoSeleccionado === 'paypal' || metodoPagoSeleccionado === 'pago_movil')) {
                if (!comprobantePago?.files[0]) {
                    alert('Por favor, adjunte el comprobante de pago para ' + (metodoPagoSeleccionado === 'transferencia' ? 'transferencia bancaria' : 'PayPal') + '.');
                    comprobantePago.focus();
                    return;
                }
                
                // Validar tamaño del archivo (5MB máximo)
                const archivo = comprobantePago.files[0];
                if (archivo.size > 5 * 1024 * 1024) {
                    alert('El archivo es demasiado grande. El tamaño máximo permitido es 5MB.');
                    return;
                }
                
                // Validar tipo de archivo
                const tiposPermitidos = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
                if (!tiposPermitidos.includes(archivo.type)) {
                    alert('Tipo de archivo no permitido. Solo se aceptan archivos JPG, PNG y PDF.');
                    return;
                }
            }
            
            // Procesar pedido individual
            procesarPedidoIndividual(vendorId, vendorType, vendorName, metodoPagoSeleccionado, comprobantePago?.files[0]);
        });
    });
    
    // Mantener validación del formulario principal (si existe)
    const form = document.getElementById('orderForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validaciones básicas
            const nombre = document.getElementById('nombre')?.value.trim();
            const email = document.getElementById('email')?.value.trim();
            const telefono = document.getElementById('telefono')?.value.trim();
            const direccion = document.getElementById('direccionEntrega')?.value.trim();
            
            if (!nombre || !email || !telefono || !direccion) {
                alert('Por favor, complete todos los campos requeridos.');
                return;
            }
            
            // Validar que hay productos en el carrito
                // Validar que hay productos en el carrito
                if (productosUsuario.length === 0 && productosSucursal.length === 0) {
                    alert('No hay productos en el carrito para procesar.');
                    return;
                }
                // Confirmar antes de enviar
                let mensaje = 'Se procesarán los siguientes pedidos:\n\n';
                if (productosUsuario.length > 0) {
                    mensaje += `• Pedido de Usuarios: ${productosUsuario.length} productos - Total: $${totalUsuario.toFixed(2)}\n`;
                }
                if (productosSucursal.length > 0) {
                    mensaje += `• Pedido de Sucursal: ${productosSucursal.length} productos - Total: $${totalSucursal.toFixed(2)}\n`;
                }
                mensaje += '\n¿Desea continuar?';
            
            if (confirm(mensaje)) {
                // Mostrar indicador de carga
                const submitBtn = form.querySelector('button[type="submit"]');
                const originalText = submitBtn ? submitBtn.innerHTML : '';
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
                    submitBtn.disabled = true;
                }
                
                // Preparar datos del formulario
                const formData = new FormData(form);
                
                // Enviar petición AJAX
                fetch('/procesar_pedido/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                })
                .then(response => {
                    if (response.redirected) {
                        // Si la respuesta es una redirección, seguirla
                        window.location.href = response.url;
                        return;
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data) return; // Si fue redirección, data será undefined
                    
                    if (data.success) {
                        // Si hay una URL de redirección en la respuesta, usarla
                        if (data.redirect_url) {
                            window.location.href = data.redirect_url;
                        } else {
                            // Fallback: mostrar mensaje y redirigir al carrito
                            let mensajeExito = `¡Pedidos procesados exitosamente!\n\n`;
                            mensajeExito += `${data.message}\n\n`;
                            
                            if (data.pedidos && data.pedidos.length > 0) {
                                mensajeExito += 'Detalles de los pedidos:\n';
                                data.pedidos.forEach((pedido, index) => {
                                    mensajeExito += `${index + 1}. Pedido #${pedido.id} - Vendedor: ${pedido.vendedor} - Total: $${pedido.total.toFixed(2)}\n`;
                                });
                            }
                            
                            mensajeExito += `\nTotal general: $${data.total_general.toFixed(2)}`;
                            
                            alert(mensajeExito);
                            window.location.href = '/carrito/';
                        }
                    } else {
                        alert('Error al procesar el pedido: ' + (data.error || 'Error desconocido'));
                        
                        // Restaurar botón
                        if (submitBtn) {
                            submitBtn.innerHTML = originalText;
                            submitBtn.disabled = false;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error de conexión al procesar el pedido. Por favor, inténtelo de nuevo.');
                    
                    // Restaurar botón
                    if (submitBtn) {
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                    }
                });
            }
        });
    }
});

// Función para procesar pedido individual por vendedor
function procesarPedidoIndividual(vendorId, vendorType, vendorName, metodoPago, archivoComprobante) {
    console.log('Procesando pedido individual:', {
        vendorId: vendorId,
        vendorType: vendorType,
        vendorName: vendorName,
        metodoPago: metodoPago,
        tieneComprobante: !!archivoComprobante
    });
    
    // Encontrar el botón concreto (priorizar el botón individual) y mostrar estado de carga
    let boton = document.querySelector(`button.btn-finalizar-individual[data-vendor-id="${vendorId}"]`);
    if (!boton) {
        // Fallback: buscar cualquier elemento con ese data-vendor-id
        boton = document.querySelector(`[data-vendor-id="${vendorId}"]`);
    }

    if (!boton) {
        console.error('No se encontró el botón para vendorId:', vendorId);
        Swal.fire({
            title: 'Error',
            text: 'No se encontró el botón de finalizar para este vendedor. Por favor, recargue la página e inténtelo de nuevo.',
            icon: 'error',
            confirmButtonColor: '#d33'
        });
        return;
    }

    const spinner = boton.querySelector('.spinner-border');
    const btnText = boton.querySelector('.btn-text');
    const vendorForm = boton.closest('.vendor-form');
    const orderStatus = vendorForm ? vendorForm.querySelector('.order-status') : null;

    // Mostrar estado de carga (con comprobaciones)
    boton.disabled = true;
    if (spinner) spinner.classList.remove('d-none');
    if (btnText) btnText.textContent = 'Procesando...';
    
    // Crear FormData para envío
    const formData = new FormData();
    formData.append('vendor_id', vendorId);
    formData.append('vendor_type', vendorType);
    formData.append('vendor_name', vendorName);
    formData.append('metodo_pago', metodoPago);
    
    if (archivoComprobante) {
        formData.append('comprobante_pago', archivoComprobante);
    }
    
    // Agregar datos del cliente al FormData
    const form = boton.closest('.vendor-form');
    const mainForm = document.querySelector('#pedidoForm');
    if (mainForm) {
        formData.append('nombre', mainForm.querySelector('[name="nombre"]')?.value || '');
        formData.append('email', mainForm.querySelector('[name="email"]')?.value || '');
        formData.append('telefono', mainForm.querySelector('[name="telefono"]')?.value || '');
        formData.append('direccion_envio', mainForm.querySelector('[name="direccion_envio"]')?.value || '');
        formData.append('notas_pedido', mainForm.querySelector('[name="notas_pedido"]')?.value || '');
    }
    
    // Agregar usuario vendedor seleccionado (solo este usuario)
    let vendedoresSeleccionados;
    if (vendorType === 'usuario') {
        vendedoresSeleccionados = [`usuario_${vendorId}`];
    } else {
        vendedoresSeleccionados = [`sucursal_${vendorId}`];
    }
    formData.append('vendedores_seleccionados', JSON.stringify(vendedoresSeleccionados));
    formData.append('finalizar_todos', 'false');
    
    // Realizar llamada AJAX real al servidor
    fetch('/ecommerce/procesar_pedido/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (response.redirected) {
            // Si la respuesta es una redirección, seguirla
            window.location.href = response.url;
            return;
        }
        return response.json();
    })
    .then(data => {
        if (!data) return; // Si fue redirección, data será undefined
        
        if (data.success) {
            // Mostrar SweetAlert de éxito
            Swal.fire({
                title: '¡Pedido Realizado Exitosamente!',
                text: data.message || 'Su pedido ha sido procesado correctamente.',
                icon: 'success',
                confirmButtonText: 'Ver Confirmación',
                confirmButtonColor: '#28a745'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Si hay una URL de redirección en la respuesta, usarla
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    }
                }
            });
            
            if (!data.redirect_url) {
                // Mostrar estado de éxito
                if (boton) {
                    boton.classList.remove('btn-success');
                    boton.classList.add('btn-outline-success');
                }
                if (btnText) btnText.textContent = '¡Procesado!';
                if (spinner) spinner.classList.add('d-none');

                // Mostrar mensaje de éxito
                if (orderStatus) {
                    orderStatus.classList.remove('d-none');
                    const orderIdEl = orderStatus.querySelector('.order-id');
                    if (orderIdEl) {
                        if (data.pedidos && data.pedidos.length > 0) {
                            orderIdEl.textContent = `Pedido #${data.pedidos[0].id}`;
                        } else {
                            orderIdEl.textContent = `Pedido procesado`;
                        }
                    }
                }

                // Deshabilitar el formulario
                if (form) {
                    const inputs = form.querySelectorAll('select, input, button');
                    inputs.forEach(input => {
                        if (input !== boton) {
                            input.disabled = true;
                        }
                    });
                }
                
                console.log('Pedido procesado exitosamente para vendedor:', vendorName);
            }
        } else {
            // Manejar error
            if (boton) boton.disabled = false;
            if (spinner) spinner.classList.add('d-none');
            if (btnText) btnText.textContent = 'Finalizar Pedido';
            alert('Error al procesar el pedido: ' + (data.error || 'Error desconocido'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Manejar error
        if (boton) boton.disabled = false;
        if (spinner) spinner.classList.add('d-none');
        if (btnText) btnText.textContent = 'Finalizar Pedido';
        alert('Error de conexión al procesar el pedido. Por favor, inténtelo de nuevo.');
    });
}

// Función para inicializar los datos del carrito (llamada desde el template)
function initializeCartData(productosUsuarioData, productosEmpresaData, totalUsuarioData, totalEmpresaData) {
    productosUsuario = productosUsuarioData || [];
    productosSucursal = productosEmpresaData || [];
    totalUsuario = totalUsuarioData || 0;
    totalSucursal = totalEmpresaData || 0;
    
    // Llenar campos ocultos con los datos
    const productosUsuarioField = document.getElementById('productos_usuario');
    const productosSucursalField = document.getElementById('productos_sucursal');
    const totalUsuarioField = document.getElementById('total_usuario');
    const totalSucursalField = document.getElementById('total_sucursal');
    
    if (productosUsuarioField) productosUsuarioField.value = JSON.stringify(productosUsuario);
    if (productosSucursalField) productosSucursalField.value = JSON.stringify(productosSucursal);
    if (totalUsuarioField) totalUsuarioField.value = totalUsuario;
    if (totalSucursalField) totalSucursalField.value = totalSucursal;
}

// Función para procesar datos del carrito desde Django template
function processCartDataFromTemplate(productosUsuarioTemplate, productosEmpresaTemplate, totalUsuarioTemplate, totalEmpresaTemplate) {
    // Esta función será llamada desde el template HTML con los datos de Django
    initializeCartData(productosUsuarioTemplate, productosEmpresaTemplate, totalUsuarioTemplate, totalEmpresaTemplate);
}

// Función para formatear números como moneda
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-VE', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Variable global para el total del carrito
window.totalCarrito = 0;

// Función para calcular totales por sucursal
function calculateSucursalTotals() {
    console.log('Calculando totales por sucursal...');
    
    if (!window.productosCarritoData || !window.productosCarritoData.productos_por_sucursal) {
        console.log('No hay datos de productos disponibles');
        return;
    }
    
    const productosPorSucursal = window.productosCarritoData.productos_por_sucursal;
    console.log('Datos de productos:', productosPorSucursal);
    
    // Calcular totales por sucursal
    for (const [sucursalKey, productos] of Object.entries(productosPorSucursal)) {
        if (productos && productos.length > 0) {
            const primerProducto = productos[0];
            const sucursalId = primerProducto.sucursal_id;
            
            // Calcular total para esta sucursal
            let totalSucursal = 0;
            productos.forEach(producto => {
                const subtotal = parseFloat(producto.subtotal) || 0;
                totalSucursal += subtotal;
                console.log(`Producto: ${producto.nombre}, Subtotal: $${subtotal}`);
            });
            
            console.log(`Total para sucursal ${sucursalId}: $${totalSucursal.toFixed(2)}`);
            
            // Actualizar el elemento en el DOM
            const totalElement = document.querySelector(`.sucursal-total-${sucursalId}`);
            if (totalElement) {
                totalElement.textContent = totalSucursal.toFixed(2);
                console.log(`Actualizado total para sucursal ${sucursalId}: $${totalSucursal.toFixed(2)}`);
            } else {
                console.log(`No se encontró elemento .sucursal-total-${sucursalId}`);
            }
        }
    }
}