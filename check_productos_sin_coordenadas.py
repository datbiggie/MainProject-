#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import producto_usuario
from django.db.models import Q

# Buscar productos sin coordenadas (solo valores NULL)
productos_sin_coordenadas = producto_usuario.objects.filter(
    Q(latitud_entrega_producto__isnull=True) | 
    Q(longitud_entrega_producto__isnull=True)
)

print(f"Productos sin coordenadas encontrados: {productos_sin_coordenadas.count()}")

# Mostrar los primeros 5
for producto in productos_sin_coordenadas[:5]:
    print(f"ID: {producto.id_producto_usuario}, Nombre: {producto.nombre_producto_usuario}")
    print(f"  Latitud: {producto.latitud_entrega_producto}")
    print(f"  Longitud: {producto.longitud_entrega_producto}")
    print("---")

# Mostrar también algunos productos con coordenadas para comparar
print("\nPrimeros 10 productos (para debug):")
todos_productos = producto_usuario.objects.all()[:10]
for producto in todos_productos:
    print(f"ID: {producto.id_producto_usuario}, Nombre: {producto.nombre_producto_usuario}")
    print(f"  Latitud: {producto.latitud_entrega_producto}")
    print(f"  Longitud: {producto.longitud_entrega_producto}")
    print("---")