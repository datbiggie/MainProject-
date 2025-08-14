import os
import sys
import django

# Configurar Django
sys.path.append('c:\\GitHub\\MainProject-')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import empresa, usuario

print("=== Debug de valores de rol ===\n")

# Verificar empresas
print("EMPRESAS:")
empresas = empresa.objects.all()[:5]
for emp in empresas:
    print(f"ID: {emp.id_empresa}, Nombre: {emp.nombre_empresa}, Rol: '{emp.rol_empresa}'")

print("\nUSUARIOS:")
usuarios = usuario.objects.all()[:5]
for usr in usuarios:
    print(f"ID: {usr.id_usuario}, Nombre: {usr.nombre_usuario}, Rol: '{usr.rol_usuario}'")

print("\n=== Opciones de rol en modelos ===\n")
print("Opciones empresa:", empresa.OPCIONES_ROL)
print("Opciones usuario:", usuario.OPCIONES_ROL)

print("\n=== Fin del debug ===")