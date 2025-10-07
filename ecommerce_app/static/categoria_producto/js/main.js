// Verificar que jQuery esté cargado
if (typeof jQuery != 'undefined') {
    console.log('jQuery está cargado');
} else {
    console.error('jQuery no está cargado');
}

// Verificar que SweetAlert2 esté cargado
if (typeof Swal != 'undefined') {
    console.log('SweetAlert2 está cargado');
} else {
    console.error('SweetAlert2 no está cargado');
}

document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Mensaje de éxito al crear categoría
    if (urlParams.get('success') === 'true') {
        Swal.fire({
            title: '¡Categoría Registrada!',
            text: 'La categoría ha sido creada correctamente.',
            icon: 'success',
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#3b82f6'
        });
    } else if (urlParams.has('updated')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La categoría ha sido actualizada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('deleted')) {
        Swal.fire({
            title: '¡Éxito!',
            text: 'La categoría ha sido eliminada correctamente',
            icon: 'success',
            confirmButtonText: 'Aceptar'
        });
    } else if (urlParams.has('error')) {
        Swal.fire({
            title: 'Error',
            text: 'Ha ocurrido un error al procesar la solicitud',
            icon: 'error',
            confirmButtonText: 'Aceptar'
        });
    }
});

/* ----- Funciones movidas desde el template categoria_producto.html ----- */
let contadorAtributos = 0;

$(document).ready(function() {
    var $select = $('#atributos_existentes');
    var $listaContainer = $('#atributos-seleccionados-lista');
    var $lista = $('#lista-atributos');

    if ($select.length) {
        // Inicializar Select2 para atributos existentes
        $select.select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Buscar y seleccionar atributos...',
            allowClear: true,
            closeOnSelect: true,
            language: {
                noResults: function() { return "No se encontraron atributos"; },
                searching: function() { return "Buscando atributos..."; },
                inputTooShort: function() { return "Escribe para buscar atributos"; },
                maximumSelected: function(e) { return "Solo puedes seleccionar " + e.maximum + " atributos"; }
            },
            templateResult: function(option) {
                if (!option.id) return option.text;
                var $option = $(
                    '<div class="select2-result-atributo">' +
                        '<div class="select2-result-atributo__title">' + option.text + '</div>' +
                    '</div>'
                );
                return $option;
            },
            templateSelection: function(option) { return option && option.id ? option.text : option.text; }
        });

        // Función para actualizar la lista de atributos seleccionados
        function actualizarListaAtributos() {
            var valoresSeleccionados = $select.val() || [];
            $lista.empty();

            if (valoresSeleccionados.length === 0) {
                $listaContainer.hide();
                return;
            }

            $listaContainer.show();

            valoresSeleccionados.forEach(function(valor) {
                var $option = $select.find('option[value="' + valor + '"]');
                var nombreAtributo = $option.text();

                var $atributoTag = $('<div class="atributo-seleccionado">' +
                    '<span>' + nombreAtributo + '</span>' +
                    '<button type="button" class="remove-btn" data-value="' + valor + '">×</button>' +
                    '</div>');

                $lista.append($atributoTag);
            });
        }

        // Eventos
        $select.on('change', actualizarListaAtributos);

        $lista.on('click', '.remove-btn', function(e) {
            e.preventDefault();
            var valorARemover = $(this).data('value');
            var valoresActuales = $select.val() || [];
            var nuevosValores = valoresActuales.filter(function(valor) { return valor !== valorARemover.toString(); });
            $select.val(nuevosValores).trigger('change');
        });

        $select.on('select2:open', function() {
            setTimeout(function() { document.querySelector('.select2-search__field')?.focus(); }, 0);
        });

        actualizarListaAtributos();
    }
});

function agregarNuevoAtributo() {
    contadorAtributos++;
    const container = document.getElementById('nuevos-atributos');
    if (!container) return;

    const atributoDiv = document.createElement('div');
    atributoDiv.className = 'border p-3 mb-3';
    atributoDiv.id = `nuevo-atributo-${contadorAtributos}`;

    atributoDiv.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <label class="form-label">Nombre del Atributo *</label>
                <input type="text" class="form-control" name="nuevo_atributo_nombre_${contadorAtributos}" placeholder="Ej: Color, Tamaño, Marca" required onblur="validarNombreAtributo(this, ${contadorAtributos})">
                <div id="error-nombre-${contadorAtributos}" class="text-danger small" style="display: none;"></div>
            </div>
            <div class="col-md-3">
                <label class="form-label">Tipo de Dato *</label>
                <select class="form-control" name="nuevo_atributo_tipo_${contadorAtributos}" onchange="manejarTipoAtributo(${contadorAtributos}, this.value)" required>
                    <option value="">Seleccionar</option>
                    <option value="texto">Texto</option>
                    <option value="numero">Número</option>
                    <option value="decimal">Decimal</option>
                    <option value="fecha">Fecha</option>
                    <option value="booleano">Booleano</option>
                    <option value="lista">Lista de opciones</option>
                </select>
            </div>
            <div class="col-md-2">
                <label class="form-label">Obligatorio</label>
                <div class="form-check mt-2">
                    <input class="form-check-input" type="checkbox" name="nuevo_atributo_obligatorio_${contadorAtributos}" value="1">
                    <label class="form-check-label">Sí</label>
                </div>
            </div>
            <div class="col-md-2">
                <label class="form-label">&nbsp;</label>
                <button type="button" class="btn btn-danger btn-sm d-block" onclick="eliminarAtributo(${contadorAtributos})">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
        </div>
        <div class="row mt-2">
            <div class="col-md-8">
                <label class="form-label">Descripción</label>
                <textarea class="form-control" name="nuevo_atributo_descripcion_${contadorAtributos}" rows="2" placeholder="Descripción opcional del atributo"></textarea>
            </div>
            <div class="col-md-4" id="opciones-container-${contadorAtributos}" style="display: none;">
                <label class="form-label">Opciones (separadas por coma)</label>
                <textarea class="form-control" name="nuevo_atributo_opciones_${contadorAtributos}" rows="2" placeholder="Opción1, Opción2, Opción3"></textarea>
            </div>
        </div>
    `;

    container.appendChild(atributoDiv);
}

function manejarTipoAtributo(id, tipo) {
    const opcionesContainer = document.getElementById(`opciones-container-${id}`);
    if (!opcionesContainer) return;
    opcionesContainer.style.display = tipo === 'lista' ? 'block' : 'none';
}

function eliminarAtributo(id) {
    const elemento = document.getElementById(`nuevo-atributo-${id}`);
    if (elemento) elemento.remove();
}

function validarNombreAtributo(input, id) {
    const nombre = input.value.trim();
    const errorDiv = document.getElementById(`error-nombre-${id}`);
    if (!errorDiv) return;

    if (!nombre) {
        errorDiv.style.display = 'none';
        return;
    }

    // Verificar duplicados en atributos existentes
    const atributosExistentes = document.querySelectorAll('input[name^="atributo_"]');
    let duplicadoEncontrado = false;

    atributosExistentes.forEach(function(atributoInput) {
        if (atributoInput.checked) {
            const labelElement = document.querySelector(`label[for="${atributoInput.id}"]`);
            if (labelElement && labelElement.textContent.trim().toLowerCase() === nombre.toLowerCase()) {
                duplicadoEncontrado = true;
            }
        }
    });

    // Verificar duplicados en otros nuevos atributos
    const nuevosAtributos = document.querySelectorAll('input[name^="nuevo_atributo_nombre_"]');
    nuevosAtributos.forEach(function(nuevoInput) {
        if (nuevoInput !== input && nuevoInput.value.trim().toLowerCase() === nombre.toLowerCase()) {
            duplicadoEncontrado = true;
        }
    });

    if (duplicadoEncontrado) {
        errorDiv.textContent = 'Ya existe un atributo con este nombre';
        errorDiv.style.display = 'block';
        input.classList.add('is-invalid');
    } else {
        errorDiv.style.display = 'none';
        input.classList.remove('is-invalid');
    }
}

function validarFormularioCompleto() {
    let hayErrores = false;
    const nuevosAtributos = document.querySelectorAll('input[name^="nuevo_atributo_nombre_"]');
    nuevosAtributos.forEach(function(input) {
        const parts = input.name.split('_');
        const id = parts[parts.length - 1];
        validarNombreAtributo(input, id);
        const errorDiv = document.getElementById(`error-nombre-${id}`);
        if (errorDiv && errorDiv.style.display !== 'none') hayErrores = true;
    });
    return !hayErrores;
}

/* Fin de funciones movidas */


document.addEventListener('DOMContentLoaded', function () {
    const fechaInput = document.getElementById('fecha_creacion');
    if (fechaInput) {
      flatpickr(fechaInput, {
        dateFormat: "d/m/Y",
        locale: "es",
        altInput: true,
        altFormat: "d/m/Y",
        disableMobile: true,
        minDate: "today",
        maxDate: new Date().fp_incr(365),
        defaultDate: "today" // 👉 Esta línea pone la fecha de hoy por defecto
      });
    }
  });

// Función para mostrar mensajes de éxito
function mostrarMensajeExito(mensaje) {
    Swal.fire({
        title: '¡Éxito!',
        text: mensaje,
        icon: 'success',
        confirmButtonText: 'Aceptar',
        confirmButtonColor: '#3b82f6'
    });
}

// Función para mostrar mensajes de error
function mostrarMensajeError(mensaje) {
    Swal.fire({
        title: 'Error',
        text: mensaje,
        icon: 'error',
        confirmButtonText: 'Aceptar',
        confirmButtonColor: '#3b82f6'
    });
}

// Esperar a que el documento esté listo
$(document).ready(function() {
    // Verificar que jQuery y SweetAlert2 estén cargados
    if (typeof $ === 'undefined') {
        console.error('jQuery no está cargado');
        return;
    }
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 no está cargado');
        return;
    }

    console.log('jQuery version:', $.fn.jquery);
    console.log('SweetAlert2 version:', Swal.version);

    // Inicializar flatpickr
    if (typeof flatpickr !== 'undefined') {
        flatpickr("#fecha_creacion", {
            dateFormat: "d/m/Y",
            locale: "es",
            allowInput: true,
            altInput: true,
            altFormat: "d/m/Y",
            disableMobile: "true",
            minDate: "today",
            maxDate: new Date().fp_incr(365),
            enableTime: false,
            time_24hr: true,
            showMonths: 1,
            static: true,
            position: "auto",
            monthSelectorType: "static",
            prevArrow: "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M15 18L9 12L15 6' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>",
            nextArrow: "<svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M9 18L15 12L9 6' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>",
            onOpen: function(selectedDates, dateStr, instance) {
                instance.set("position", "auto");
            }
        });
    }

    // Manejar el envío del formulario
    const form = $('#categoriaForm');
    if (form.length === 0) {
        console.error('No se encontró el formulario con ID categoriaForm');
        return;
    }

    let isSubmitting = false;

    form.on('submit', function(e) {
        e.preventDefault();
        e.stopPropagation();

        if (isSubmitting) {
            console.log('Ya hay un envío en proceso');
            return false;
        }

        // Validar atributos duplicados antes del envío
        if (typeof validarFormularioCompleto === 'function' && !validarFormularioCompleto()) {
            Swal.fire({
                title: 'Error de validación',
                text: 'Por favor, corrija los errores en los nombres de atributos antes de continuar.',
                icon: 'error',
                confirmButtonText: 'Entendido'
            });
            return false;
        }

        const submitButton = form.find('input[type="submit"]');
        submitButton.prop('disabled', true);
        isSubmitting = true;

        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: form.serialize(),
            success: function(response) {
                console.log('Respuesta del servidor:', response);
                if (response.success) {
                    Swal.fire({
                        title: '¡Registro exitoso!',
                        text: response.message,
                        icon: 'success',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            form[0].reset();
                            setTimeout(function() {
                                window.location.reload();
                            }, 1500);
                        }
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: response.message,
                        icon: 'error',
                        confirmButtonText: 'Aceptar',
                        confirmButtonColor: '#3b82f6'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            let fieldToFocus = null;
                            if (response.message && response.message.toLowerCase().includes('nombre')) {
                                fieldToFocus = $('#nombre_categoria');
                            } else if (response.message && response.message.toLowerCase().includes('estatus')) {
                                fieldToFocus = $('#estatus_categoria');
                            } else if (response.message && response.message.toLowerCase().includes('descrip')) {
                                fieldToFocus = $('#descripcion_categoria');
                            }

                            if (fieldToFocus && fieldToFocus.length) {
                                const section = fieldToFocus.closest('.accordion-section');
                                if (section.length && !section.hasClass('active')) {
                                    section.find('.accordion-header').click();
                                }
                                setTimeout(() => fieldToFocus.focus(), 300); // Pequeño delay para asegurar que la sección se abra
                            }
                        }
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Error en la petición AJAX:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'Ha ocurrido un error al procesar la solicitud',
                    icon: 'error',
                    confirmButtonText: 'Aceptar',
                    confirmButtonColor: '#3b82f6'
                });
            },
            complete: function() {
                submitButton.prop('disabled', false);
                isSubmitting = false;
            }
        });

        return false;
    });
});

    // ----- Comportamiento del acordeón para categoria_producto -----
    document.addEventListener('DOMContentLoaded', function() {
        // Cuando se hace clic en el header de una sección, alternar su estado
        document.querySelectorAll('.accordion-header').forEach(function(header) {
            header.addEventListener('click', function() {
                var section = header.closest('.accordion-section');
                var isActive = section.classList.contains('active');

                // Cerrar todas
                document.querySelectorAll('.accordion-section').forEach(function(s) {
                    s.classList.remove('active');
                });

                // Si no estaba activa, abrirla
                if (!isActive) section.classList.add('active');
            });
        });

        /*
        // Abrir la primera sección por defecto si no hay ninguna activa
        if (!document.querySelector('.accordion-section.active')) {
            var first = document.querySelector('.accordion-section');
            if (first) first.classList.add('active');
        }
        */
    });