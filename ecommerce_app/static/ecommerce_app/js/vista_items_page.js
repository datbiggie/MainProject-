// Funciones de comportamiento para la vista de items
// Estas funciones usan window.vistaItemsConfig y window.csrfToken, definidos en la plantilla

(function(){
  const cfg = window.vistaItemsConfig || {};
  const CSRF = window.csrfToken || '';

  // Cambiar imagen principal
  window.changeMainImage = function(imageSrc, thumbnailElement) {
    const main = document.getElementById('mainImage');
    if (main) main.src = imageSrc;

    document.querySelectorAll('.thumbnail-img').forEach(img => img.classList.remove('active'));
    if (thumbnailElement && thumbnailElement.classList) thumbnailElement.classList.add('active');
  };

  // Agregar al carrito (sin cantidad)
  window.agregarAlCarrito = function(productoId, tipoPropietario) {
    const data = {
      producto_id: productoId,
      tipo_propietario: tipoPropietario
    };

    fetch(cfg.agregarAlCarritoUrl || '/ecommerce/agregar_al_carrito/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': CSRF
      },
      body: new URLSearchParams(data)
    }).then(resp => resp.json())
      .then(data => {
        if (data.success) {
          Swal.fire({title: '¡Éxito!', text: data.message, icon: 'success', confirmButtonText: 'Continuar', confirmButtonColor: '#10b981'});
          if (data.total_items !== undefined && typeof updateCartBadge === 'function') updateCartBadge(data.total_items);
        } else {
          if (data.message === 'Usuario no autenticado') {
            Swal.fire({title: 'Sesión requerida', text: 'Debes iniciar sesión para agregar productos al carrito', icon: 'warning', showCancelButton: true, confirmButtonText: 'Iniciar sesión', cancelButtonText: 'Cancelar', confirmButtonColor: '#3b82f6'})
              .then(result => { if (result.isConfirmed) window.location.href = cfg.iniciarSesionUrl || '/ecommerce/iniciar_sesion/'; });
          } else if (data.stock_insuficiente) {
            Swal.fire({title: 'Stock insuficiente', text: data.message, icon: 'warning', confirmButtonText: 'Entendido', confirmButtonColor: '#f59e0b'});
          } else {
            Swal.fire({title: 'Error', text: data.message, icon: 'error', confirmButtonText: 'Entendido', confirmButtonColor: '#ef4444'});
          }
        }
      })
      .catch(err => { console.error(err); Swal.fire({title:'Error', text:'Ocurrió un error al agregar el producto al carrito', icon:'error', confirmButtonText:'Entendido'}); });
  };

  // Redirigir a solicitud de servicio
  window.solicitarServicio = function(itemId, tipoPropietario) {
    const url = `/ecommerce/solicitud_servicio/?servicio_id=${itemId}&tipo_propietario=${tipoPropietario}`;
    window.location.href = url;
  };

  // Control cantidad
  window.incrementarCantidad = function() {
    const cantidadInput = document.getElementById('cantidad');
    if (!cantidadInput) return;
    const maxStock = parseInt(cantidadInput.getAttribute('max')) || 999;
    const currentValue = parseInt(cantidadInput.value) || 1;
    if (currentValue < maxStock) cantidadInput.value = currentValue + 1;
    else Swal.fire({title: 'Límite de stock alcanzado', text: `No puedes agregar más unidades. Stock disponible: ${maxStock} unidades`, icon: 'info', confirmButtonText: 'Entendido', confirmButtonColor: '#3085d6', timer: 3000, timerProgressBar: true});
  };

  window.decrementarCantidad = function() {
    const cantidadInput = document.getElementById('cantidad');
    if (!cantidadInput) return;
    const currentValue = parseInt(cantidadInput.value) || 1;
    if (currentValue > 1) cantidadInput.value = currentValue - 1;
  };

  // Agregar al carrito con cantidad
  window.agregarAlCarritoConCantidad = function(productoId, tipoPropietario) {
    const cantidadInput = document.getElementById('cantidad');
    const cantidad = cantidadInput ? parseInt(cantidadInput.value) || 1 : 1;
    const stockDisponible = cantidadInput ? parseInt(cantidadInput.getAttribute('max')) || 999 : 999;

    if (cantidad > stockDisponible) {
      Swal.fire({title: 'Cantidad no disponible', text: `La cantidad solicitada (${cantidad}) excede el stock disponible (${stockDisponible} unidades)`, icon: 'warning', confirmButtonText: 'Entendido', confirmButtonColor: '#f59e0b'});
      return;
    }

    const data = { producto_id: productoId, tipo_propietario: tipoPropietario, cantidad: cantidad };

    fetch(cfg.agregarAlCarritoUrl || '/ecommerce/agregar_al_carrito/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': CSRF
      },
      body: new URLSearchParams(data)
    }).then(r => r.json()).then(data => {
      if (data.success) {
        Swal.fire({title: '¡Éxito!', text: data.message, icon: 'success', confirmButtonText: 'Continuar', confirmButtonColor: '#10b981'});
        if (data.total_items !== undefined && typeof updateCartBadge === 'function') updateCartBadge(data.total_items);
      } else {
        if (data.message === 'Usuario no autenticado') {
          Swal.fire({title: 'Sesión requerida', text: 'Debes iniciar sesión para agregar productos al carrito', icon: 'warning', showCancelButton: true, confirmButtonText: 'Iniciar sesión', cancelButtonText: 'Cancelar', confirmButtonColor: '#3b82f6'}).then(result => { if (result.isConfirmed) window.location.href = cfg.iniciarSesionUrl || '/ecommerce/iniciar_sesion/'; });
        } else if (data.stock_insuficiente) {
          Swal.fire({title: 'Stock insuficiente', text: data.message, icon: 'warning', confirmButtonText: 'Entendido', confirmButtonColor: '#f59e0b'});
        } else {
          Swal.fire({title: 'Error', text: data.message, icon: 'error', confirmButtonText: 'Entendido', confirmButtonColor: '#ef4444'});
        }
      }
    }).catch(err => { console.error(err); Swal.fire({title:'Error', text:'Ocurrió un error al agregar el producto al carrito', icon:'error', confirmButtonText:'Entendido'}); });
  };

  // Agregar a favoritos
  window.agregarAFavoritos = function(itemId, tipoPropietario) {
    const tipoItem = window.location.href.includes('tipo=servicio') ? 'servicio' : 'producto';
    const data = { item_id: itemId, tipo_propietario: tipoPropietario, tipo_item: tipoItem };

    fetch(cfg.agregarFavoritoUrl || '/ecommerce/agregar_quitar_favorito/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF
      },
      body: JSON.stringify(data)
    }).then(r => r.json()).then(data => {
      if (data.success) {
        const icon = data.action === 'added' ? 'success' : 'info';
        const title = data.action === 'added' ? '¡Agregado a favoritos!' : 'Eliminado de favoritos';
        Swal.fire({title: title, text: data.message, icon: icon, confirmButtonText: 'Continuar', confirmButtonColor: '#10b981'});
        const botonFavorito = document.querySelector(`button[onclick*="agregarAFavoritos('${itemId}', '${tipoPropietario}')"]`);
        if (botonFavorito) {
          const icono = botonFavorito.querySelector('i');
          if (data.action === 'added') {
            icono.style.color = '#ef4444';
            botonFavorito.innerHTML = "<i class='fas fa-heart me-1' style='color: #ef4444;'></i>Quitar de favoritos";
          } else {
            icono.style.color = '';
            botonFavorito.innerHTML = "<i class='fas fa-heart me-1'></i>Agregar a favoritos";
          }
        }
      } else {
        if (data.message === 'Debes iniciar sesión para agregar favoritos') {
          Swal.fire({title: 'Sesión requerida', text: 'Debes iniciar sesión para agregar productos a favoritos', icon: 'warning', showCancelButton: true, confirmButtonText: 'Iniciar sesión', cancelButtonText: 'Cancelar', confirmButtonColor: '#3b82f6'}).then(result => { if (result.isConfirmed) window.location.href = cfg.iniciarSesionUrl || '/ecommerce/iniciar_sesion/'; });
        } else Swal.fire({title: 'Error', text: data.message, icon: 'error', confirmButtonText: 'Entendido', confirmButtonColor: '#ef4444'});
      }
    }).catch(err => { console.error(err); Swal.fire({title:'Error', text:'Ocurrió un error al procesar la solicitud', icon:'error', confirmButtonText:'Entendido'}); });
  };

})();
