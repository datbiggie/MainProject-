import os
import django
import sys

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import usuario

def check_passwords():
    print("Verificando usuarios y contraseñas en la base de datos...")
    print("-" * 50)
    
    users = usuario.objects.all()
    for user in users:
        print(f"Usuario: {user.correo_usuario}")
        print(f"Contraseña almacenada: {user.password_usuario}")
        print(f"¿Está hasheada?: {'Sí' if user.password_usuario.startswith('pbkdf2_sha256$') else 'No'}")
        print("-" * 50)

if __name__ == "__main__":
    check_passwords() 