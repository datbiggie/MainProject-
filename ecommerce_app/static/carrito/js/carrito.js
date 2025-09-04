// Funciones para manejar el carrito
function increaseQuantity(itemId) {
    const quantityInput = document.getElementById('quantity-' + itemId);
    let currentValue = parseInt(quantityInput.value);
    quantityInput.value = currentValue + 1;
    // Aquí se puede agregar lógica para actualizar en el servidor
}

function decreaseQuantity(itemId) {
    const quantityInput = document.getElementById('quantity-' + itemId);
    let currentValue = parseInt(quantityInput.value);
    if (currentValue > 1) {
        quantityInput.value = currentValue - 1;
        // Aquí se puede agregar lógica para actualizar en el servidor
    }
}

function removeItem(itemId, type) {
    if (confirm('¿Estás seguro de que deseas eliminar este elemento del carrito?')) {
        // Aquí se puede agregar lógica para eliminar del servidor
        console.log('Eliminando item:', itemId, 'tipo:', type);
    }
}

function clearCart() {
    if (confirm('¿Estás seguro de que deseas limpiar todo el carrito?')) {
        // Aquí se puede agregar lógica para limpiar el carrito en el servidor
        console.log('Limpiando carrito');
    }
}

function proceedToCheckout() {
    // Aquí se puede agregar lógica para proceder al checkout
    console.log('Procediendo al checkout');
}

function viewItem(itemId) {
    // Aquí se puede agregar lógica para ver los detalles del producto
    console.log('Viendo detalles del producto:', itemId);
    // Ejemplo: redirigir a la página de detalles del producto
    // window.location.href = '/ecommerce/producto/' + itemId;
}

function verDetalleCarrito() {
    // Redirigir a la página de detalle del carrito
    console.log('Viendo detalle del carrito');
    window.location.href = '/ecommerce/detalle_carrito/';
}

// Manejar selección de todos los productos
// Comentado porque el elemento 'selectAllProducts' no existe en este template
/*
document.getElementById('selectAllProducts').addEventListener('change', function() {
    const checkboxes = document.querySelectorAll('.product-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = this.checked;
    });
});
*/

// Función para mostrar notificaciones de cambios de precio
function mostrarCambiosPrecios(cambiosPrecios) {
    if (cambiosPrecios && cambiosPrecios.length > 0) {
        let cambiosTexto = '';
        cambiosPrecios.forEach(function(cambio) {
            // Acceder a las propiedades del objeto cambio
            const producto = cambio.fields ? cambio.fields.producto : (cambio.producto || 'Producto');
            const precioOriginal = cambio.fields ? cambio.fields.precio_original : (cambio.precio_original || '0');
            const precioActual = cambio.fields ? cambio.fields.precio_actual : (cambio.precio_actual || '0');
            
            cambiosTexto += '• ' + producto + ': $' + precioOriginal + ' → $' + precioActual + '\n';
        });
        
        Swal.fire({
            title: '¡Precios Actualizados!',
            text: 'Algunos productos en tu carrito han cambiado de precio:\n\n' + cambiosTexto + '\nLos precios y totales se han actualizado automáticamente.',
            icon: 'info',
            confirmButtonText: 'Entendido',
            confirmButtonColor: '#007bff',
            allowOutsideClick: false,
            customClass: {
                popup: 'swal-wide'
            }
        });
    }
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Aquí se pueden agregar más inicializaciones si es necesario
    console.log('Carrito JavaScript cargado correctamente');
});