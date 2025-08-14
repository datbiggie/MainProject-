#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import producto_empresa, imagen_producto_empresa, producto_usuario, imagen_producto_usuario, usuario, empresa

print("=== DEBUG: Verificando productos y sus imágenes ===")
print()

# Listar todos los productos de empresa
productos_empresa = producto_empresa.objects.all()
print(f"Total de productos de empresa: {productos_empresa.count()}")

for producto in productos_empresa:
    print(f"ID: {producto.id_producto_empresa}")
    print(f"Nombre: {producto.nombre_producto_empresa}")
    print(f"Empresa: {producto.id_empresa_fk.nombre_empresa}")
    
    # Verificar imágenes asociadas
    imagenes = imagen_producto_empresa.objects.filter(id_producto_fk=producto)
    print(f"Imágenes asociadas: {imagenes.count()}")
    print("-" * 30)

print()
# Listar todos los productos de usuario
productos_usuario = producto_usuario.objects.all()
print(f"Total de productos de usuario: {productos_usuario.count()}")

for producto in productos_usuario:
    print(f"ID: {producto.id_producto_usuario}")
    print(f"Nombre: {producto.nombre_producto_usuario}")
    print(f"Usuario: {producto.id_usuario_fk.nombre_usuario}")
    
    # Verificar imágenes asociadas
    imagenes = imagen_producto_usuario.objects.filter(id_producto_fk=producto)
    print(f"Imágenes asociadas: {imagenes.count()}")
    
    if imagenes.exists():
        for img in imagenes:
            print(f"  - Imagen ID: {img.id_imagen_producto_usuario}")
            print(f"  - Ruta: {img.ruta_imagen_producto_usuario}")
    print("-" * 30)

print()
print("=== Verificando usuarios y empresas ===")
usuarios = usuario.objects.all()
empresas = empresa.objects.all()
print(f"Total usuarios: {usuarios.count()}")
print(f"Total empresas: {empresas.count()}")

print()
print("=== Usuarios registrados ===")
for user in usuarios:
    print(f"ID: {user.id_usuario}, Nombre: {user.nombre_usuario}, Email: {user.correo_usuario}, Rol: {user.rol_usuario}")

print()
print("=== Empresas registradas ===")
for emp in empresas:
    print(f"ID: {emp.id_empresa}, Nombre: {emp.nombre_empresa}, Email: {emp.correo_empresa}, Rol: {emp.rol_empresa}")