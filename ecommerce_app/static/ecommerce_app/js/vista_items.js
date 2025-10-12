// JS extraído de vista_items.html - manejo de comentarios y funciones UI

(function() {
  // Contador y envío de comentarios
  const input = document.getElementById('comentario-input');
  const btn = document.getElementById('publicar-comentario-btn');
  const lista = document.getElementById('lista-comentarios');
  const counter = document.getElementById('comentario-counter');

  if (!input || !btn || !lista) return;

  // Actualizar contador de caracteres
  input.addEventListener('input', () => {
    counter.textContent = `${input.value.length}/1000`;
  });

  // Renderizar comentario en la lista (cliente)
  function renderComentario({autor, avatar, texto, fecha}) {
    const item = document.createElement('div');
    item.className = 'list-group-item';
    item.innerHTML = `
      <div class="d-flex gap-3">
        <img src="${avatar || '/static/avatars/Cartoon Style Robot.jpg'}" alt="avatar" style="width:48px;height:48px;object-fit:cover;border-radius:50%;">
        <div class="w-100">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <div class="comentario-autor">${autor || 'Usuario'}</div>
            <small class="text-muted">${fecha || ''}</small>
          </div>
          <div class="comentario-texto text-break">${texto}</div>
        </div>
      </div>
    `;
    lista.prepend(item);
  }

  // Manejar envío
  btn.addEventListener('click', () => {
    const texto = input.value.trim();
    if (!texto) {
      Swal.fire({title: 'Texto vacío', text: 'Escribe algo antes de publicar', icon: 'warning', confirmButtonColor: '#3085d6'});
      return;
    }

    // Datos básicos del item para asociar el comentario
    const params = new URLSearchParams(window.location.search);
    const itemId = params.get('id');
    const tipo = params.get('tipo');
    const origen = params.get('origen') || 'empresa';

    // Payload
    const data = {
      item_id: itemId,
      tipo: tipo,
      origen: origen,
      comentario: texto
    };

    // Deshabilitar botón mientras se envía
    btn.disabled = true;
    btn.textContent = 'Publicando...';

    fetch('/ecommerce/publicar_comentario/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken || ''
      },
      body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        // Renderizar localmente el comentario con la info devuelta o con datos por defecto
        renderComentario({autor: resp.autor || 'Usuario', avatar: resp.avatar || '/static/avatars/Cartoon Style Robot.jpg', texto: texto, fecha: resp.fecha || new Date().toLocaleString()});
        input.value = '';
        counter.textContent = '0/1000';
      } else {
        if (resp.message && resp.message.includes('autenticado')) {
          Swal.fire({title: 'Sesión requerida', text: 'Debes iniciar sesión para comentar', icon: 'warning', confirmButtonText: 'Iniciar sesión', confirmButtonColor: '#3b82f6'}).then((res) => {
            if (res.isConfirmed) window.location.href = '/ecommerce/iniciar_sesion/';
          });
        } else {
          Swal.fire({title: 'Error', text: resp.message || 'No se pudo publicar el comentario', icon: 'error', confirmButtonColor: '#ef4444'});
        }
      }
    })
    .catch(err => {
      console.error(err);
      Swal.fire({title: 'Error', text: 'Ocurrió un error al publicar el comentario', icon: 'error', confirmButtonColor: '#ef4444'});
    })
    .finally(() => {
      btn.disabled = false;
      btn.textContent = 'Publicar comentario';
    });
  });

  // TODO: cargar comentarios existentes desde servidor cuando se implemente el endpoint
})();
