#!/usr/bin/env python3
"""
Script para probar el mensaje de advertencia cuando un producto no tiene coordenadas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import producto_usuario
from django.db.models import Q

# Buscar un producto sin coordenadas
producto_sin_coordenadas = producto_usuario.objects.filter(
    Q(latitud_entrega_producto__isnull=True) | 
    Q(longitud_entrega_producto__isnull=True)
).first()

if producto_sin_coordenadas:
    print(f"Producto encontrado para prueba:")
    print(f"ID: {producto_sin_coordenadas.id_producto_usuario}")
    print(f"Nombre: {producto_sin_coordenadas.nombre_producto_usuario}")
    print(f"Latitud: {producto_sin_coordenadas.latitud_entrega_producto}")
    print(f"Longitud: {producto_sin_coordenadas.longitud_entrega_producto}")
    
    # Simular la lógica de JavaScript
    lat = producto_sin_coordenadas.latitud_entrega_producto
    lng = producto_sin_coordenadas.longitud_entrega_producto
    
    print(f"\nSimulando lógica JavaScript:")
    print(f"lat = {lat}")
    print(f"lng = {lng}")
    print(f"lat is None: {lat is None}")
    print(f"lng is None: {lng is None}")
    
    # Condiciones que deberían activar el mensaje
    should_show_warning = (
        lat is None or lng is None or 
        (isinstance(lat, str) and lat.lower() == 'none') or
        (isinstance(lng, str) and lng.lower() == 'none')
    )
    
    print(f"\nDebería mostrar advertencia: {should_show_warning}")
    
    if should_show_warning:
        print("✅ El mensaje de advertencia DEBERÍA aparecer para este producto")
    else:
        print("❌ El mensaje de advertencia NO debería aparecer")
else:
    print("No se encontraron productos sin coordenadas")