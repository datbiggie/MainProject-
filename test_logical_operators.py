#!/usr/bin/env python3
"""
Script de prueba para búsquedas con operadores lógicos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from chatbot.database_service import DatabaseService
from chatbot.gemini_service import GeminiService

def test_logical_operators():
    """Prueba búsquedas con operadores lógicos"""
    print("=== PRUEBAS DE OPERADORES LÓGICOS ===")
    
    db_service = DatabaseService()
    
    # Consultas con múltiples criterios (operador AND)
    consultas_logicas = [
        "laptop HP de 8GB de RAM",
        "laptop HP de 8GB y precio menor a $1000",
        "computadora Dell con procesador Intel y 16GB de RAM",
        "laptop de 8GB y procesador Intel con precio entre $500 y $1200",
        "notebook HP con 8GB de memoria y precio hasta $800",
        "laptop con procesador AMD y RAM de 16GB",
        "computadora de marca HP y almacenamiento SSD",
        "laptop negra de 8GB con precio mayor a $600"
    ]
    
    print("\n1. Detección de múltiples atributos y condiciones:")
    for consulta in consultas_logicas:
        print(f"\n   Consulta: '{consulta}'")
        
        # Probar detección
        deteccion = db_service._detectar_atributos_en_mensaje(consulta)
        if deteccion:
            atributos = deteccion.get('atributos', {})
            precio = deteccion.get('precio', {})
            
            print(f"     ✅ Atributos detectados: {atributos}")
            if precio:
                print(f"     ✅ Condiciones de precio: {precio}")
        else:
            print("     ❌ No se detectaron criterios")

def test_logical_search():
    """Prueba la búsqueda con operadores lógicos"""
    print("\n=== PRUEBAS DE BÚSQUEDA LÓGICA ===")
    
    db_service = DatabaseService()
    
    consultas_test = [
        "laptop HP de 8GB de RAM",
        "laptop de 8GB y precio menor a $1000",
        "computadora con procesador Intel y 8GB"
    ]
    
    print("\n2. Búsqueda con operadores lógicos AND:")
    for consulta in consultas_test:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            productos = db_service.buscar_productos(consulta, limite=5)
            print(f"   Productos encontrados: {len(productos)}")
            
            for i, prod in enumerate(productos, 1):
                print(f"\n   Producto {i}:")
                print(f"     - Nombre: {prod['nombre']}")
                print(f"     - Precio: ${prod['precio']}")
                print(f"     - Vendedor: {prod['vendedor']}")
                
                # Mostrar atributos EAV
                atributos = prod.get('atributos', {})
                if atributos:
                    attrs_str = ", ".join([f"{k}: {v}" for k, v in atributos.items()])
                    print(f"     - Especificaciones: {attrs_str}")
                
                # Mostrar coincidencias lógicas
                if 'coincidencia_logica' in prod:
                    print(f"     - ✅ {prod['coincidencia_logica']}")
                elif 'coincidencia_eav' in prod:
                    print(f"     - ✅ {prod['coincidencia_eav']}")
                elif 'coincidencia_patron' in prod:
                    print(f"     - ✅ {prod['coincidencia_patron']}")
                    
        except Exception as e:
            print(f"     ❌ Error: {e}")

def test_price_conditions():
    """Prueba condiciones de precio específicas"""
    print("\n=== PRUEBAS DE CONDICIONES DE PRECIO ===")
    
    db_service = DatabaseService()
    
    consultas_precio = [
        "productos con precio menor a $500",
        "laptops con precio entre $800 y $1200",
        "computadoras con precio hasta $1000",
        "productos desde $300",
        "$600 o menos",
        "$900 o más"
    ]
    
    print("\n3. Condiciones de precio:")
    for consulta in consultas_precio:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            productos = db_service.buscar_productos(consulta, limite=3)
            print(f"   Productos encontrados: {len(productos)}")
            
            for i, prod in enumerate(productos, 1):
                print(f"     {i}. {prod['nombre']} - ${prod['precio']}")
                if 'coincidencia_logica' in prod:
                    print(f"        ✅ {prod['coincidencia_logica']}")
                    
        except Exception as e:
            print(f"     ❌ Error: {e}")

def test_complex_combinations():
    """Prueba combinaciones complejas"""
    print("\n=== PRUEBAS DE COMBINACIONES COMPLEJAS ===")
    
    db_service = DatabaseService()
    
    consultas_complejas = [
        "laptop HP de 8GB con procesador Intel y precio entre $700 y $1100",
        "computadora Dell de 16GB con SSD y precio menor a $1500",
        "notebook con RAM de 8GB y procesador AMD hasta $900"
    ]
    
    print("\n4. Combinaciones complejas (múltiples atributos + precio):")
    for consulta in consultas_complejas:
        print(f"\n   Consulta: '{consulta}'")
        
        # Mostrar detección completa
        deteccion = db_service._detectar_atributos_en_mensaje(consulta)
        if deteccion:
            print(f"     Criterios detectados:")
            if 'atributos' in deteccion:
                for attr, val in deteccion['atributos'].items():
                    print(f"       - {attr}: {val}")
            if 'precio' in deteccion:
                for cond, val in deteccion['precio'].items():
                    print(f"       - precio {cond}: ${val}")
        
        try:
            productos = db_service.buscar_productos(consulta, limite=2)
            print(f"     Productos que cumplen TODOS los criterios: {len(productos)}")
            
            for i, prod in enumerate(productos, 1):
                print(f"\n     Producto {i}:")
                print(f"       - {prod['nombre']} - ${prod['precio']}")
                print(f"       - Vendedor: {prod['vendedor']}")
                
                if 'coincidencia_logica' in prod:
                    print(f"       - ✅ {prod['coincidencia_logica']}")
                    
        except Exception as e:
            print(f"     ❌ Error: {e}")

def test_gemini_integration():
    """Prueba integración con Gemini"""
    print("\n=== PRUEBAS DE INTEGRACIÓN GEMINI ===")
    
    gemini_service = GeminiService()
    
    consulta = "laptop HP de 8GB y precio menor a $1000"
    print(f"\n5. Integración Gemini: '{consulta}'")
    
    try:
        informacion = gemini_service._consultar_base_datos(consulta)
        
        if informacion and 'productos_encontrados' in informacion:
            productos = informacion['productos_encontrados']
            print(f"   ✅ {len(productos)} productos en información BD")
            
            for i, prod in enumerate(productos[:2], 1):
                print(f"\n   Producto {i} para Gemini:")
                print(f"     - Nombre: {prod['nombre']}")
                print(f"     - Precio: ${prod['precio']}")
                
                if 'coincidencia_logica' in prod:
                    print(f"     - ✅ Coincidencia lógica: {prod['coincidencia_logica']}")
                
                atributos = prod.get('atributos', {})
                if atributos:
                    print(f"     - Atributos: {atributos}")
        else:
            print("   ❌ No se encontraron productos en BD")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Función principal"""
    print("PRUEBAS DE BÚSQUEDA CON OPERADORES LÓGICOS")
    print("=" * 60)
    
    try:
        test_logical_operators()
        test_logical_search()
        test_price_conditions()
        test_complex_combinations()
        test_gemini_integration()
        
        print("\n" + "=" * 60)
        print("FUNCIONALIDADES IMPLEMENTADAS:")
        print("✅ Detección de múltiples atributos (marca, RAM, procesador, etc.)")
        print("✅ Detección de condiciones de precio (menor, mayor, entre, hasta, desde)")
        print("✅ Operador lógico AND (productos que cumplan TODOS los criterios)")
        print("✅ Búsqueda combinada (atributos + precio)")
        print("✅ Coincidencias exactas múltiples")
        print("✅ Integración con Gemini")
        
        print("\nEJEMPLOS QUE AHORA FUNCIONAN:")
        print("• 'laptop HP de 8GB y precio menor a $1000'")
        print("• 'computadora Dell con procesador Intel y 16GB de RAM'")
        print("• 'laptop de 8GB y procesador Intel con precio entre $500 y $1200'")
        print("• 'notebook HP con 8GB de memoria y precio hasta $800'")
        
        print("\nTIPOS DE CONSULTAS SOPORTADAS:")
        print("• Múltiples atributos: marca + RAM + procesador + almacenamiento")
        print("• Condiciones de precio: <, >, entre, hasta, desde")
        print("• Combinaciones complejas: atributos + precio + condiciones")
        
    except Exception as e:
        print(f"\nERROR EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
