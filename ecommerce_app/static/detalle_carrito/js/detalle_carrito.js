// Variables globales para el modal
let productoActualId = null;
let precioUnitarioActual = 0;

// Función para mostrar el modal de editar cantidad
function mostrarModalEditar(productoId) {
    // Obtener datos del producto desde la fila de la tabla
    const fila = document.querySelector(`button[data-producto-id="${productoId}"]`).closest('tr');
    const imagen = fila.querySelector('img')?.src || '';
    const nombre = fila.querySelector('strong').textContent;
    const sucursal = fila.querySelector('.text-muted').textContent.replace('Sucursal: ', '');
    const cantidadActual = parseInt(fila.querySelector('.badge').textContent);
    const precioTexto = fila.querySelectorAll('strong')[1].textContent;
    const precio = parseFloat(precioTexto.replace('$', '').replace(',', ''));
    
    // Guardar datos globales
    productoActualId = productoId;
    precioUnitarioActual = precio;
    
    // Llenar el modal con los datos
    document.getElementById('modal-producto-imagen').src = imagen;
    document.getElementById('modal-producto-nombre').textContent = nombre;
    document.getElementById('modal-producto-sucursal').textContent = `Sucursal: ${sucursal}`;
    document.getElementById('nueva-cantidad').value = cantidadActual;
    document.getElementById('modal-precio-unitario').textContent = precio.toFixed(2);
    
    // Calcular y mostrar el subtotal inicial
    actualizarSubtotal();
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('editarCantidadModal'));
    modal.show();
}

// Función para actualizar el subtotal en el modal
function actualizarSubtotal() {
    const cantidad = parseInt(document.getElementById('nueva-cantidad').value) || 1;
    const subtotal = cantidad * precioUnitarioActual;
    document.getElementById('modal-nuevo-subtotal').textContent = subtotal.toFixed(2);
}

// Función para actualizar cantidad en el servidor
function actualizarCantidad(productoId, nuevaCantidad) {
    fetch('/ecommerce/actualizar_cantidad_carrito/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({
            producto_id: productoId,
            cantidad: nuevaCantidad
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                title: '¡Actualizado!',
                text: data.message,
                icon: 'success',
                timer: 2000,
                showConfirmButton: false
            }).then(() => {
                // Recargar la página para actualizar el carrito
                location.reload();
            });
        } else {
            Swal.fire({
                title: 'Error',
                text: data.message,
                icon: 'error'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            title: 'Error',
            text: 'Ocurrió un error al actualizar la cantidad',
            icon: 'error'
        });
    });
}

function eliminarDetalle(productoId) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: '¿Deseas eliminar este producto del carrito?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Realizar la petición al servidor para eliminar el producto
            fetch('/ecommerce/eliminar_del_carrito/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                producto_id: productoId
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: '¡Eliminado!',
                        text: data.message,
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        // Recargar la página para actualizar el carrito
                        location.reload();
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: data.message,
                        icon: 'error'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'Ocurrió un error al eliminar el producto',
                    icon: 'error'
                });
            });
        }
    });
}



function procederCompra() {
    // Verificar que hay productos en el carrito
    const productosEnCarrito = document.querySelectorAll('tbody tr').length;
    
    if (productosEnCarrito === 0) {
        Swal.fire({
            title: 'Carrito vacío',
            text: 'No hay productos en el carrito para proceder con la compra',
            icon: 'warning'
        });
        return;
    }
    
    // Confirmar antes de proceder
    Swal.fire({
        title: '¿Proceder a la compra?',
        text: '¿Desea proceder con la compra de todos los productos en el carrito?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, proceder',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Redirigir a la página de pedido
            window.location.href = '/ecommerce/pedido/';
        }
    });
}

// Función auxiliar para obtener el token CSRF
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

// Inicializar tooltips de Bootstrap y event listeners
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Event listeners para botones de editar
    document.querySelectorAll('.btn-editar').forEach(function(button) {
        button.addEventListener('click', function() {
            const productoId = this.getAttribute('data-producto-id');
            mostrarModalEditar(productoId);
        });
    });
    
    // Event listeners para el modal de editar cantidad
    const btnDecrementar = document.getElementById('btn-decrementar');
    const btnIncrementar = document.getElementById('btn-incrementar');
    const inputCantidad = document.getElementById('nueva-cantidad');
    const btnGuardar = document.getElementById('btn-guardar-cantidad');
    
    if (btnDecrementar) {
        btnDecrementar.addEventListener('click', function() {
            const cantidadActual = parseInt(inputCantidad.value) || 1;
            if (cantidadActual > 1) {
                inputCantidad.value = cantidadActual - 1;
                actualizarSubtotal();
            }
        });
    }
    
    if (btnIncrementar) {
        btnIncrementar.addEventListener('click', function() {
            const cantidadActual = parseInt(inputCantidad.value) || 1;
            if (cantidadActual < 99) {
                inputCantidad.value = cantidadActual + 1;
                actualizarSubtotal();
            }
        });
    }
    
    if (inputCantidad) {
        inputCantidad.addEventListener('input', function() {
            actualizarSubtotal();
        });
    }
    
    if (btnGuardar) {
        btnGuardar.addEventListener('click', function() {
            const nuevaCantidad = parseInt(inputCantidad.value);
            if (nuevaCantidad && nuevaCantidad > 0 && productoActualId) {
                // Cerrar el modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editarCantidadModal'));
                modal.hide();
                
                // Actualizar cantidad
                actualizarCantidad(productoActualId, nuevaCantidad);
            } else {
                Swal.fire({
                    title: 'Error',
                    text: 'Por favor ingrese una cantidad válida',
                    icon: 'error'
                });
            }
        });
    }
    
    // Event listeners para botones de eliminar
    document.querySelectorAll('.btn-eliminar').forEach(function(button) {
        button.addEventListener('click', function() {
            const detalleId = this.getAttribute('data-producto-id');
            eliminarDetalle(detalleId);
        });
    });
});