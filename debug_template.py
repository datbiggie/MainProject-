import os
import django
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.views import producto_config_funcion, get_current_user
from ecommerce_app.models import usuario, empresa

print("=== DEBUG: Simulando request de producto_config ===")

# Crear un request simulado
factory = RequestFactory()
request = factory.get('/ecommerce/producto_config/')

# Agregar middleware de sesión
middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
request.session.save()

# Simular sesión de usuario persona (Luis urdaneta)
request.session['is_authenticated'] = True
request.session['user_id'] = 6
request.session['account_type'] = 'usuario'  # o None
request.session['user_email'] = 'luiseurdanetah@gmail.com'
request.session['user_name'] = 'Luis urdaneta'
request.session['user_type'] = 'persona'
request.session.save()

print("Datos de sesión configurados:")
print(f"- is_authenticated: {request.session.get('is_authenticated')}")
print(f"- user_id: {request.session.get('user_id')}")
print(f"- account_type: {request.session.get('account_type')}")
print(f"- user_type: {request.session.get('user_type')}")

# Probar get_current_user
current_user = get_current_user(request)
print(f"\nUsuario obtenido: {current_user}")
if current_user:
    print(f"Tipo de objeto: {type(current_user)}")
    if hasattr(current_user, 'rol_usuario'):
        print(f"Rol usuario: {current_user.rol_usuario}")
    if hasattr(current_user, 'rol_empresa'):
        print(f"Rol empresa: {current_user.rol_empresa}")

# Verificar account_type en producto_config_funcion
account_type = request.session.get('account_type', 'usuario')
print(f"\nAccount type para comparación: '{account_type}'")
print(f"¿Es empresa? {account_type == 'empresa'}")
print(f"¿Es usuario? {account_type != 'empresa'}")

print("\n=== Fin del debug ===")