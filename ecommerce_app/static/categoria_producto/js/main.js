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