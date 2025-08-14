import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone
from ecommerce_app.models import usuario, empresa

print("=== DEBUG: Verificando sesiones activas ===")

# Obtener todas las sesiones activas
active_sessions = Session.objects.filter(expire_date__gte=timezone.now())

print(f"Total de sesiones activas: {active_sessions.count()}")

for session in active_sessions:
    session_data = session.get_decoded()
    print(f"\n--- Sesión ID: {session.session_key[:10]}... ---")
    print(f"Expira: {session.expire_date}")
    
    if 'is_authenticated' in session_data:
        print(f"Autenticado: {session_data.get('is_authenticated')}")
        print(f"Tipo de cuenta: {session_data.get('account_type')}")
        print(f"ID de usuario: {session_data.get('user_id')}")
        print(f"Email: {session_data.get('user_email')}")
        print(f"Nombre: {session_data.get('user_name')}")
        print(f"Tipo de usuario: {session_data.get('user_type')}")
        
        # Verificar qué usuario/empresa corresponde
        user_id = session_data.get('user_id')
        account_type = session_data.get('account_type', 'usuario')
        
        if user_id:
            try:
                if account_type == 'empresa':
                    emp = empresa.objects.get(id_empresa=user_id)
                    print(f"Empresa encontrada: {emp.nombre_empresa} (Rol: {emp.rol_empresa})")
                else:
                    usr = usuario.objects.get(id_usuario=user_id)
                    print(f"Usuario encontrado: {usr.nombre_usuario} (Rol: {usr.rol_usuario})")
            except (usuario.DoesNotExist, empresa.DoesNotExist):
                print("Usuario/Empresa no encontrado en la base de datos")
    else:
        print("Sesión no autenticada")
        
print("\n=== Fin del debug de sesiones ===")