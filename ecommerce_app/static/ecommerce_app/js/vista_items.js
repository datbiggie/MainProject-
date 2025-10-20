// JS extraído de vista_items.html - manejo de comentarios y funciones UI

(function() {
  document.addEventListener('DOMContentLoaded', () => {
    // Contador y envío de comentarios
    const input = document.getElementById('comentario-input');
    const btn = document.getElementById('publicar-comentario-btn');
    const lista = document.getElementById('lista-comentarios');
    const counter = document.getElementById('comentario-counter');

    if (!lista) return;

    // Actualizar contador de caracteres si existe el input
    if (input && counter) {
      input.addEventListener('input', () => {
        counter.textContent = `${input.value.length}/1000`;
      });
    }

  // Renderizar comentario en la lista (cliente)
  // Renderizar comentario en la lista (cliente)
  // Accepts id and is_author to show edit/delete actions immediately
  function renderComentario({id, autor, avatar, texto, fecha, is_author}) {
    const item = document.createElement('div');
    item.className = 'list-group-item';
    item.innerHTML = `
      <div class="comentario-card" data-comentario-id="${id || ''}">
        <img class="comentario-avatar" src="${avatar || '/static/avatars/Cartoon Style Robot.jpg'}" alt="avatar">
        <div class="w-100">
          <div class="comentario-meta">
            <div class="comentario-autor">${autor || 'Usuario'}</div>
            <div class="comentario-fecha">${fecha || ''}</div>
          </div>
          <div class="comentario-texto">${texto}</div>
        </div>
          ${is_author ? '<div class="comentario-actions ms-2"><button class="editar-comentario-btn btn-icon" title="Editar comentario" aria-label="Editar comentario"><i class="fa fa-pen" aria-hidden="true"></i></button><button class="eliminar-comentario-btn btn-icon ms-1" title="Eliminar comentario" aria-label="Eliminar comentario"><i class="fa fa-trash" aria-hidden="true"></i></button></div>' : ''}
      </div>
    `;
    // Prepend to show newest first
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
        const newComment = {
          id: resp.id || null,
          is_author: resp.is_author === true,
          autor: resp.autor || 'Usuario',
          avatar: resp.avatar || '/static/avatars/Cartoon Style Robot.jpg',
          texto: texto,
          fecha: resp.fecha || new Date().toLocaleString()
        };
        renderComentario(newComment);
        input.value = '';
        counter.textContent = '0/1000';
        // Update total count and subtitle
        try{
          const total = parseInt(window.commentsTotalCount || '0');
          window.commentsTotalCount = String((isNaN(total) ? 0 : total) + 1);
          const btn = document.getElementById('cargar-mas-comentarios-btn') || document.querySelector('.load-more-control');
          if (btn) updateLoadMoreSubtitle(btn);
        }catch(e){/* ignore */}
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
  // --- CARGA INICIAL Y 'CARGAR MÁS' ---
  const COMMENTS_BATCH = 5;
  let commentsOffset = 0;
  let commentsHasMore = true;
  // Use server-rendered initial comments if present to avoid duplicate fetch
  const serverRenderedCount = (function(){
    try{
      const listItems = lista.querySelectorAll('.list-group-item');
      return listItems ? listItems.length : 0;
    }catch(e){return 0}
  })();

  if (serverRenderedCount > 0) {
    commentsOffset = serverRenderedCount;
  }

  function renderComentariosList(comments, append = true) {
    // Si append es false, limpiar lista
    if (!append) lista.innerHTML = '';
    comments.forEach(c => {
      const item = document.createElement('div');
      item.className = 'list-group-item';
      // Render comment card; if comment has is_author flag, include delete action
      item.innerHTML = `
        <div class="comentario-card" data-comentario-id="${c.id}">
          <img class="comentario-avatar" src="${c.avatar || '/static/avatars/Cartoon Style Robot.jpg'}" alt="avatar">
          <div class="w-100">
            <div class="comentario-meta">
              <div class="comentario-autor">${c.autor || 'Usuario'}</div>
              <div class="comentario-fecha">${c.fecha || ''}</div>
            </div>
            <div class="comentario-texto">${c.texto}</div>
          </div>
          ${c.is_author ? '<div class="comentario-actions ms-2"><button class="btn btn-sm btn-outline-secondary editar-comentario-btn" title="Editar comentario">✎</button><button class="btn btn-sm btn-outline-danger eliminar-comentario-btn ms-1" title="Eliminar comentario">✖</button></div>' : ''}
        </div>
      `;
      // Agregar al final para mantener orden cronológico descendente
      lista.appendChild(item);
    });
  }

  function updateLoadMoreSubtitle(btn) {
    try {
      const subtitle = btn.querySelector('.load-more-subtitle');
      if (!subtitle) return;
      const total = parseInt(window.commentsTotalCount || '0');
      const remaining = Math.max(0, total - commentsOffset);
      if (total && remaining > 0) subtitle.textContent = `Ver ${remaining} más`;
      else subtitle.textContent = '';
    } catch (e) { /* ignore */ }
  }

  function createLoadMoreBtn() {
    // Prefer existing element by id (template may have inserted it), then by class
    let btn = document.getElementById('cargar-mas-comentarios-btn') || document.querySelector('.load-more-control');
    if (btn) {
      // Attach listener once if not already attached
      if (!btn._hasLoadMoreListener) {
        btn.addEventListener('click', loadMoreComments);
        // keyboard accessibility
        btn.addEventListener('keydown', (ev) => {
          if (ev.key === 'Enter' || ev.key === ' ') {
            ev.preventDefault();
            loadMoreComments();
          }
        });
        btn._hasLoadMoreListener = true;
      }
      // keep subtitle up-to-date
      updateLoadMoreSubtitle(btn);
      return btn;
    }

    // Fallback: create a more sophisticated non-button control (div with role=button)
    btn = document.createElement('div');
    btn.id = 'cargar-mas-comentarios-btn';
    btn.className = 'load-more-control load-more-btn';
    btn.setAttribute('role', 'button');
    btn.setAttribute('tabindex', '0');
    btn.style.display = 'block';
    btn.style.margin = '12px auto 0';
    btn.innerHTML = `
      <div class="load-more-left">
        <span class="load-more-label">Ver más</span>
        <small class="load-more-subtitle" aria-hidden="true"></small>
      </div>
      <div class="load-more-right">
        <svg class="load-more-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
        <span class="load-more-spinner" style="display:none;">\n          <svg width="18" height="18" viewBox="0 0 50 50"><circle cx="25" cy="25" r="20" stroke="currentColor" stroke-width="5" fill="none" stroke-linecap="round"/></svg>
        </span>
      </div>
    `;

    btn.addEventListener('click', loadMoreComments);
    // keyboard accessibility
    btn.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        loadMoreComments();
      }
    });
    btn._hasLoadMoreListener = true;
    lista.parentNode.appendChild(btn);
    updateLoadMoreSubtitle(btn);
    return btn;
  }

  function loadMoreComments() {
    if (!commentsHasMore) return;
    const btn = createLoadMoreBtn();
    // UI: show loading state
    btn.classList.add('loading');
    const chevron = btn.querySelector('.load-more-chevron');
    const spinner = btn.querySelector('.load-more-spinner');
    if (chevron) chevron.style.opacity = '0';
    if (spinner) spinner.style.display = 'inline-block';

    const params = new URLSearchParams(window.location.search);
    params.set('offset', commentsOffset);
    params.set('limit', COMMENTS_BATCH);
    fetch(`/ecommerce/obtener_comentarios/?${params.toString()}`)
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          renderComentariosList(data.comments, true);
          commentsOffset = data.next_offset || (commentsOffset + data.comments.length);
          commentsHasMore = data.has_more;
          // Update subtitle and visibility
          updateLoadMoreSubtitle(btn);
          if (!commentsHasMore) btn.style.display = 'none';
        }
      })
      .catch(err => {
        // no debug logs here but restore UI
      })
      .finally(() => {
        btn.classList.remove('loading');
        if (chevron) chevron.style.opacity = '';
        if (spinner) spinner.style.display = 'none';
      });
  }

  // Cargar los primeros comentarios al iniciar
  function loadInitialComments() {
    // Si ya hay comentarios renderizados por el servidor, no refetchear esa primera tanda
    if (serverRenderedCount > 0) {
      // Comprobar si hay más comentarios en el servidor usando comments_total_count si está disponible
      try{
        const total = parseInt(window.commentsTotalCount || '0');
        commentsHasMore = commentsOffset < total;
        const btn = createLoadMoreBtn();
        btn.style.display = commentsHasMore ? 'block' : 'none';
        return;
      }catch(e){/* fallthrough: intentar fetch si no hay total */}
    }

    // Si no hay datos renderizados en servidor, obtener la primera tanda desde la API
    commentsOffset = 0;
    commentsHasMore = true;
    const params = new URLSearchParams(window.location.search);
    params.set('offset', 0);
    params.set('limit', COMMENTS_BATCH);
    fetch(`/ecommerce/obtener_comentarios/?${params.toString()}`)
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          renderComentariosList(data.comments, false);
          commentsOffset = data.next_offset || data.comments.length;
          commentsHasMore = data.has_more;
          const btn = createLoadMoreBtn();
          btn.style.display = commentsHasMore ? 'block' : 'none';
          updateLoadMoreSubtitle(btn);
        }
      })
      .catch(err => console.error('Error cargando comentarios iniciales:', err));
  }

  // Ejecutar carga inicial
  loadInitialComments();

  // Delegated handler for delete buttons inside the comments list
  lista.addEventListener('click', (ev) => {
    const deleteBtn = ev.target.closest && ev.target.closest('.eliminar-comentario-btn');
      if (!deleteBtn) return;
    // Find the comentario card parent to get id
      const card = deleteBtn.closest('.comentario-card');
    if (!card) return;
    const comentarioId = card.getAttribute('data-comentario-id');
    if (!comentarioId) return;

    // Confirm deletion
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        title: '¿Eliminar comentario?',
        text: 'Esta acción no se puede deshacer.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Eliminar',
        cancelButtonText: 'Cancelar'
      }).then((result) => {
        if (result.isConfirmed) {
          performDeleteComment(comentarioId, card);
        }
      });
    } else {
      if (confirm('¿Eliminar comentario?')) performDeleteComment(comentarioId, card);
    }
  });

  // Delegated handler for edit buttons
  lista.addEventListener('click', (ev) => {
    const editBtn = ev.target.closest && ev.target.closest('.editar-comentario-btn');
    if (!editBtn) return;
    const card = editBtn.closest('.comentario-card');
    if (!card) return;
    const comentarioId = card.getAttribute('data-comentario-id');
    if (!comentarioId) return;

    enterEditMode(card, comentarioId);
  });

  function enterEditMode(card, comentarioId) {
    const textoEl = card.querySelector('.comentario-texto');
    if (!textoEl) return;
    const originalText = textoEl.textContent || textoEl.innerText || '';
    // Replace the text node with a textarea in-place so the editor appears
    // exactly where the original text was and can be wider.
    const editArea = document.createElement('div');
    editArea.className = 'comentario-edit-area';
    editArea.innerHTML = `
      <textarea class="form-control comentario-edit-text" rows="4">${originalText.trim()}</textarea>
      <div class="d-flex gap-2 mt-2">
        <button class="btn btn-sm btn-primary guardar-comentario-btn">Guardar</button>
        <button class="btn btn-sm btn-secondary cancelar-comentario-btn">Cancelar</button>
      </div>
    `;

    const actions = card.querySelector('.comentario-actions');
    // Hide the existing actions while editing
    if (actions) actions.style.display = 'none';

    // Insert editArea right after the textoEl and hide the original textoEl
    textoEl.style.display = 'none';
    textoEl.parentNode.insertBefore(editArea, textoEl.nextSibling);

    // Handlers
    const guardarBtn = editArea.querySelector('.guardar-comentario-btn');
    const cancelarBtn = editArea.querySelector('.cancelar-comentario-btn');

    cancelarBtn.addEventListener('click', () => {
      editArea.remove();
      textoEl.style.display = '';
      if (actions) actions.style.display = '';
    });

    guardarBtn.addEventListener('click', () => {
      const nueva = editArea.querySelector('.comentario-edit-text').value.trim();
      if (!nueva) {
        if (typeof Swal !== 'undefined') Swal.fire({title: 'Texto vacío', text: 'Escribe algo antes de guardar', icon: 'warning'});
        else alert('Escribe algo antes de guardar');
        return;
      }
      // Call API to save
      const payload = { comentario_id: comentarioId, texto: nueva };
      guardarBtn.disabled = true;
      fetch('/ecommerce/editar_comentario/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': window.csrfToken || ''
        },
        body: JSON.stringify(payload)
      })
      .then(r => r.json())
      .then(resp => {
        if (resp.success) {
          // Update text and cleanup
          textoEl.textContent = resp.texto || nueva;
          if (resp.fecha) {
            const fechaEl = card.querySelector('.comentario-fecha');
            if (fechaEl) fechaEl.textContent = resp.fecha;
          }
          editArea.remove();
          textoEl.style.display = '';
          if (actions) actions.style.display = '';
        } else {
          if (resp.message) {
            if (typeof Swal !== 'undefined') Swal.fire({title: 'Error', text: resp.message, icon: 'error'});
            else alert(resp.message);
          }
        }
      })
      .catch(err => {
        console.error('Error editando comentario:', err);
      })
      .finally(() => { guardarBtn.disabled = false; });
    });
  }

  function performDeleteComment(comentarioId, cardElement) {
    const url = '/ecommerce/eliminar_comentario/';
    const payload = { comentario_id: comentarioId };
    // Show a temporary loading state on the card
    cardElement.style.opacity = '0.6';
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken || ''
      },
      body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        // Remove the list item wrapper (list-group-item)
        const listItem = cardElement.closest('.list-group-item');
        if (listItem) listItem.remove();
        // Update counts and subtitle
        try{
          const total = parseInt(window.commentsTotalCount || '0');
          if (!isNaN(total) && total > 0) {
            window.commentsTotalCount = String(Math.max(0, total - 1));
            const btn = document.getElementById('cargar-mas-comentarios-btn') || document.querySelector('.load-more-control');
            if (btn) updateLoadMoreSubtitle(btn);
          }
        }catch(e){/* ignore */}
      } else {
        if (resp.message) {
          if (typeof Swal !== 'undefined') Swal.fire({title: 'Error', text: resp.message, icon: 'error'});
          else alert(resp.message);
        }
        cardElement.style.opacity = '';
      }
    })
    .catch(err => {
      console.error('Error eliminando comentario:', err);
      cardElement.style.opacity = '';
    });
  }

  }); // end DOMContentLoaded

})();
