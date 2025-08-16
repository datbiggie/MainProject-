import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from django.test import RequestFactory
from ecommerce_app.views import perfil_productos, is_user_authenticated, get_current_user
from ecommerce_app.models import usuario

# Crear una request factory
factory = RequestFactory()

# Simular una sesión de usuario autenticado
request = factory.get('/ecommerce/perfil_productos/')

# Verificar si hay usuarios en la base de datos
usuarios = usuario.objects.all()
print(f"Usuarios en la base de datos: {len(usuarios)}")
for u in usuarios:
    print(f"- ID: {u.id_usuario}, Nombre: {u.nombre_usuario}, Email: {u.correo_usuario}")

if usuarios.exists():
    # Simular sesión autenticada con el primer usuario
    primer_usuario = usuarios.first()
    request.session = {
        'is_authenticated': True,
        'user_id': primer_usuario.id_usuario,
        'account_type': 'usuario'
    }
    
    print(f"\nSimulando sesión para usuario: {primer_usuario.nombre_usuario}")
    print(f"Session data: {dict(request.session)}")
    
    # Verificar funciones de autenticación
    is_auth = is_user_authenticated(request)
    current_user = get_current_user(request)
    
    print(f"\nis_user_authenticated: {is_auth}")
    print(f"get_current_user: {current_user}")
    if current_user:
        print(f"Tipo de usuario: {type(current_user)}")
        print(f"Nombre: {current_user.nombre_usuario}")
        print(f"Email: {current_user.correo_usuario}")
    
    # Simular la lógica de perfil_productos
    account_type = request.session.get('account_type', 'usuario')
    user_info = {
        'is_authenticated': bool(current_user),
        'tipo': 'empresa' if account_type == 'empresa' else 'persona'
    }
    
    if current_user and account_type != 'empresa':
        user_info.update({
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'id': current_user.id_usuario
        })
    
    print(f"\nuser_info generado:")
    for key, value in user_info.items():
        print(f"  {key}: {value}")
else:
    print("No hay usuarios en la base de datos para probar.")