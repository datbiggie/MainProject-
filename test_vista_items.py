#!/usr/bin/env python3
"""
Script de prueba para verificar la función vista_items
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import *
from ecommerce_app.views import vista_items
from django.test import RequestFactory

def test_vista_items():
    """Prueba la función vista_items con diferentes parámetros"""
    
    # Crear un request factory
    factory = RequestFactory()
    
    # Casos de prueba
    test_cases = [
        {
            'name': 'Producto empresa por producto_sucursal',
            'params': {'id': '1', 'tipo': 'producto', 'origen': 'empresa'}
        },
        {
            'name': 'Producto empresa por producto_empresa',
            'params': {'id': '1', 'tipo': 'producto', 'origen': 'empresa'}
        },
        {
            'name': 'Producto usuario',
            'params': {'id': '1', 'tipo': 'producto', 'origen': 'usuario'}
        },
        {
            'name': 'Servicio empresa por servicio_sucursal',
            'params': {'id': '1', 'tipo': 'servicio', 'origen': 'empresa'}
        },
        {
            'name': 'Servicio empresa por servicio_empresa',
            'params': {'id': '1', 'tipo': 'servicio', 'origen': 'empresa'}
        },
        {
            'name': 'Servicio usuario',
            'params': {'id': '1', 'tipo': 'servicio', 'origen': 'usuario'}
        }
    ]
    
    print("=== PRUEBAS DE VISTA_ITEMS ===\n")
    
    for test_case in test_cases:
        print(f"Probando: {test_case['name']}")
        print(f"Parámetros: {test_case['params']}")
        
        try:
            # Crear request
            request = factory.get('/vista_items/', test_case['params'])
            
            # Llamar a la función
            response = vista_items(request)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {type(response)}")
            
            if hasattr(response, 'content'):
                print(f"Content length: {len(response.content)}")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            print("-" * 50)

def check_models():
    """Verifica que los modelos existan y tengan datos"""
    
    print("=== VERIFICACIÓN DE MODELOS ===\n")
    
    models_to_check = [
        ('producto_sucursal', producto_sucursal),
        ('producto_empresa', producto_empresa),
        ('producto_usuario', producto_usuario),
        ('servicio_sucursal', servicio_sucursal),
        ('servicio_empresa', servicio_empresa),
        ('servicio_usuario', servicio_usuario),
    ]
    
    for model_name, model_class in models_to_check:
        try:
            count = model_class.objects.count()
            print(f"{model_name}: {count} registros")
            
            if count > 0:
                # Mostrar el primer registro
                first = model_class.objects.first()
                print(f"  Primer registro ID: {first.pk}")
                
                # Mostrar campos disponibles
                fields = [f.name for f in model_class._meta.fields]
                print(f"  Campos: {fields[:5]}...")  # Solo los primeros 5
                
        except Exception as e:
            print(f"{model_name}: ERROR - {str(e)}")
        
        print()

if __name__ == '__main__':
    print("Iniciando pruebas...\n")
    
    # Verificar modelos primero
    check_models()
    
    # Probar vista_items
    test_vista_items()
    
    print("Pruebas completadas.")
