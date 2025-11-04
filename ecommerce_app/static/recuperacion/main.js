// JS para recuperación de clave
// Flujo: enviar email -> backend verifica existencia y envía código por email -> mostrar confirmación al usuario

document.addEventListener('DOMContentLoaded', function(){
  const form = document.getElementById('recoverForm');
  const btn = document.getElementById('btnSendCode');

  if (!form || !btn) {
    console.error('Error: No se encontraron los elementos del formulario');
    return;
  }

  form.addEventListener('submit', async function(e){
    e.preventDefault();
    
    // Validación básica HTML5
    if (!form.checkValidity()){
      form.classList.add('was-validated');
      return;
    }

    const email = document.getElementById('email').value.trim();
    if (!email) return;

    // Obtener CSRF token
    const csrfToken = getCookie('csrftoken');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';

    try{
      const resp = await fetch('/ecommerce/api/request_password_reset/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ email })
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
      }

      const data = await resp.json();
      
      if (data.success){
        // Mostrar mensaje y redirigir a la pantalla para ingresar código / nueva password
        Swal.fire({
          icon: 'success',
          title: 'Email enviado',
          text: 'Si existe una cuenta asociada a ese correo, hemos enviado un enlace de recuperación. Revisa tu bandeja de entrada y haz clic en el enlace para restablecer tu contraseña.',
          confirmButtonText: 'Ir a Iniciar Sesión'
        }).then(()=>{
          // Redirigir a iniciar sesión para que el usuario pueda usar el link del email
          window.location.href = '/ecommerce/iniciar_sesion/';
        });
      } else {
        Swal.fire({ 
          icon: 'info', 
          title: 'Hecho', 
          text: 'Si existe una cuenta asociada a ese correo, hemos enviado un enlace de recuperación. Revisa tu bandeja de entrada.',
          confirmButtonText: 'Aceptar'
        }).then(()=>{
          window.location.href = '/ecommerce/iniciar_sesion/';
        });
      }

    }catch(err){
      console.error('Error en petición AJAX:', err);
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
