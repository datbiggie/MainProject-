
$(document).ready(function() {
  // Inicializar Select2 para países
  $('#country').select2({
    theme: 'bootstrap-5',
    width: '100%',
    placeholder: 'Selecciona un país',
    allowClear: true,
    language: {
      noResults: function() {
        return "No se encontraron resultados";
      },
      searching: function() {
        return "Buscando...";
      }
    }
  });

  // Inicializar Select2 para estados
  $('#state').select2({
    theme: 'bootstrap-5',
    width: '100%',
    placeholder: 'Selecciona un estado',
    allowClear: true,
    disabled: true,
    language: {
      noResults: function() {
        return "No se encontraron resultados";
      },
      searching: function() {
        return "Buscando...";
      }
    }
  });

  // Inicializar Select2 para tipo de empresa
  $('#tipo_empresa').select2({
    theme: 'bootstrap-5',
    width: '100%',
    placeholder: 'Selecciona el tipo de empresa',
    allowClear: true,
    language: {
      noResults: function() {
        return "No se encontraron resultados";
      },
      searching: function() {
        return "Buscando...";
      }
    }
  });

  // Agregar solo Venezuela al select de países
  $('#country').append(new Option('Venezuela', 'VE'));

  // Manejar cambio de país
  $('#country').on('change', function() {
    const countryCode = $(this).val();
    const stateSelect = $('#state');
    
    if (countryCode === 'VE') {
      stateSelect.prop('disabled', false);
      stateSelect.select2('enable');
    } else {
      stateSelect.prop('disabled', true);
      stateSelect.select2('disable');
      stateSelect.val('').trigger('change');
    }
  });
});

