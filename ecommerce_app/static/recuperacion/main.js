// JS para recuperación de clave
// Flujo: enviar email -> backend verifica existencia y envía código por email -> mostrar confirmación al usuario

document.addEventListener('DOMContentLoaded', function(){
  const form = document.getElementById('recoverForm');
  const btn = document.getElementById('btnSendCode');

  form.addEventListener('submit', async function(e){
    e.preventDefault();
    // Validación básica HTML5
    if (!form.checkValidity()){
      form.classList.add('was-validated');
      return;
    }

    const email = document.getElementById('email').value.trim();
    if (!email) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';

    try{
      const resp = await fetch('/ecommerce/api/request_password_reset/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ email })
      });

      const data = await resp.json();
      if (data.success){
        // Mostrar mensaje y redirigir a la pantalla para ingresar código / nueva password
        Swal.fire({
          icon: 'success',
          title: 'Código enviado',
          text: 'Si existe una cuenta asociada a ese correo, hemos enviado un código a su bandeja de entrada.',
          confirmButtonText: 'Aceptar'
        }).then(()=>{
          // Redirigir a la página de confirmar (puede ser la misma o otra ruta)
          window.location.href = '/ecommerce/confirmar_recuperacion/';
        });
      } else {
        Swal.fire({ icon: 'info', title: 'Hecho', text: 'Si existe una cuenta asociada a ese correo, hemos enviado un código a su bandeja de entrada.'});
      }

    }catch(err){
      console.error(err);
      Swal.fire({ icon: 'error', title: 'Error', text: 'Ocurrió un error al enviar el correo. Intenta de nuevo.' });
    }finally{
      btn.disabled = false;
      btn.innerHTML = 'Enviar código';
    }
  });

});

// Helper to read cookie (CSRF)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
