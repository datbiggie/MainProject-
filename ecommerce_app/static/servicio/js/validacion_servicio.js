// Validación de imagen obligatoria para el formulario de servicio
// Archivo: servicio/js/validacion_servicio.js

document.addEventListener('DOMContentLoaded', function() {
  var form = document.getElementById('servicioForm');
  if (!form) return;
  form.addEventListener('submit', function(e) {
    var imagenInput = document.getElementById('imagen_servicio');
    if (!imagenInput.files || imagenInput.files.length === 0) {
      e.preventDefault();
      Swal.fire({
        title: 'Imagen obligatoria',
        text: 'Debes seleccionar una imagen para el servicio.',
        icon: 'warning',
        confirmButtonColor: '#d33',
      });
      return false;
    }
  });
});
