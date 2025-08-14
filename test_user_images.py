#!/usr/bin/env python
"""
Script para probar la carga de imágenes para usuarios no-empresa
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MainProject.settings')
django.setup()

from ecommerce_app.models import (
    usuario, producto_usuario, imagen_producto_usuario,
    empresa, producto_empresa, imagen_producto_empresa
)

print("=== VERIFICACIÓN DE IMÁGENES PARA USUARIOS NO-EMPRESA ===")
print()

# Verificar usuarios registrados
print("1. USUARIOS REGISTRADOS:")
usuarios = usuario.objects.all()
for user in usuarios:
    print(f"   - ID: {user.id_usuario}, Nombre: {user.nombre_usuario}, Rol: {user.rol_usuario}")
print()

# Verificar productos de usuario
print("2. PRODUCTOS DE USUARIO:")
productos_usuario = producto_usuario.objects.all()
for producto in productos_usuario:
    print(f"   - ID: {producto.id_producto_usuario}, Nombre: {producto.nombre_producto_usuario}")
    
    # Verificar imágenes de este producto
    imagenes = imagen_producto_usuario.objects.filter(id_producto_usuario_fk=producto)
    print(f"     Imágenes: {imagenes.count()}")
    for img in imagenes:
        print(f"       * ID: {img.id_imagen_producto_usuario}, Ruta: {img.ruta_imagen_producto_usuario}")
print()

# Verificar empresas registradas
print("3. EMPRESAS REGISTRADAS:")
empresas = empresa.objects.all()
for emp in empresas:
    print(f"   - ID: {emp.id_empresa}, Nombre: {emp.nombre_empresa}, Rol: {emp.rol_empresa}")
print()

# Verificar productos de empresa
print("4. PRODUCTOS DE EMPRESA:")
productos_empresa = producto_empresa.objects.all()
for producto in productos_empresa:
    print(f"   - ID: {producto.id_producto_empresa}, Nombre: {producto.nombre_producto_empresa}")
    
    # Verificar imágenes de este producto
    imagenes = imagen_producto_empresa.objects.filter(id_producto_empresa_fk=producto)
    print(f"     Imágenes: {imagenes.count()}")
    for img in imagenes:
        print(f"       * ID: {img.id_imagen_producto_empresa}, Ruta: {img.ruta_imagen_producto_empresa}")
print()

print("=== RESUMEN ===")
print(f"Total usuarios: {usuarios.count()}")
print(f"Total productos de usuario: {productos_usuario.count()}")
print(f"Total empresas: {empresas.count()}")
print(f"Total productos de empresa: {productos_empresa.count()}")

# Verificar si hay productos de usuario con imágenes
productos_con_imagenes = 0
for producto in productos_usuario:
    if imagen_producto_usuario.objects.filter(id_producto_usuario_fk=producto).exists():
        productos_con_imagenes += 1

print(f"Productos de usuario con imágenes: {productos_con_imagenes}")
print()
print("=== FIN DE LA VERIFICACIÓN ===")