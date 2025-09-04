// Configuración de categorías de servicios - JavaScript principal

// Variables globales para el manejo de sesión
window.USER_INFO = {
    account_type: document.querySelector('meta[name="account-type"]').getAttribute('content'),
    user_id: document.querySelector('meta[name="user-id"]').getAttribute('content'),
    is_authenticated: document.querySelector('meta[name="is-authenticated"]').getAttribute('content')
};
window.CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

// Función para abrir modal de edición
function abrirModalEditar(id, nombre, descripcion, estatus) {
    document.getElementById('edit_id_categoria').value = id;
    document.getElementById('edit_nombre_categoria').value = nombre;
    document.getElementById('edit_descripcion_categoria').value = descripcion;
    document.getElementById('edit_estatus_categoria').value = estatus;
    
    const modal = new bootstrap.Modal(document.getElementById('editCategoriaModal'));
    modal.show();
}

// Función para confirmar eliminación
function confirmarEliminacion(id) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            eliminarCategoria(id);
        }
    });
}

// Función para eliminar categoría
function eliminarCategoria(id) {
    const formData = new FormData();
    formData.append('id_categoriaservicio', id);
    
    fetch('/ecommerce/eliminar_categoria_servicio/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': CSRF_TOKEN
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire('Eliminado', data.message, 'success').then(() => {
                location.reload();
            });
        } else {
            Swal.fire('Error', data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire('Error', 'Ocurrió un error al eliminar la categoría', 'error');
    });
}

// Función para filtrar categorías
function filtrarCategorias() {
    const busqueda = document.getElementById('busqueda');
    const filtroEstatus = document.getElementById('filtroEstatus');
    const categorias = document.querySelectorAll('.category-card');
    
    const textoBusqueda = busqueda.value.toLowerCase();
    const estatusFiltro = filtroEstatus.value.toLowerCase();

    categorias.forEach(categoria => {
        const nombre = categoria.dataset.nombre;
        const estatus = categoria.dataset.estatus;
        
        const coincideTexto = nombre.includes(textoBusqueda);
        const coincideEstatus = estatusFiltro === 'todos' || estatus === estatusFiltro;
        
        if (coincideTexto && coincideEstatus) {
            categoria.style.display = 'block';
        } else {
            categoria.style.display = 'none';
        }
    });
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Configurar filtrado en tiempo real
    const busqueda = document.getElementById('busqueda');
    const filtroEstatus = document.getElementById('filtroEstatus');
    
    if (busqueda) {
        busqueda.addEventListener('input', filtrarCategorias);
    }
    
    if (filtroEstatus) {
        filtroEstatus.addEventListener('change', filtrarCategorias);
    }
    
    // Manejo del formulario de edición
    const editForm = document.getElementById('editCategoriaForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Éxito', data.message, 'success').then(() => {
                        location.reload();
                    });
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error', 'Ocurrió un error al guardar los cambios', 'error');
            });
        });
    }
});

// Exponer funciones globalmente para uso en HTML
window.abrirModalEditar = abrirModalEditar;
window.confirmarEliminacion = confirmarEliminacion;