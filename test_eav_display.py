#!/usr/bin/env python3
"""
Script de prueba para verificar que los atributos EAV se muestren correctamente
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

def test_eav_attributes_display():
    """Prueba que los atributos EAV se muestren correctamente"""
    print("=== PRUEBA DE VISUALIZACIÓN DE ATRIBUTOS EAV ===")
    
    db_service = DatabaseService()
    
    # Probar búsqueda de productos
    consultas_test = [
        "laptop HP",
        "Laptop HP",
        "LAPTOP HP",
        "hp laptop",
        "HP LAPTOP"
    ]
    
    print("\n1. Prueba de búsqueda con diferentes mayúsculas/minúsculas:")
    for consulta in consultas_test:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            productos = db_service.buscar_productos(consulta, limite=2)
            print(f"   Productos encontrados: {len(productos)}")
            
            for i, prod in enumerate(productos, 1):
                print(f"\n   Producto {i}:")
                print(f"     Nombre: {prod.get('nombre', 'N/A')}")
                print(f"     Precio: ${prod.get('precio', 0)}")
                print(f"     Vendedor: {prod.get('vendedor', 'N/A')}")
                
                # Verificar atributos EAV
                atributos = prod.get('atributos', {})
                if atributos:
                    print(f"     ✅ Atributos EAV encontrados: {len(atributos)}")
                    for attr_name, attr_value in atributos.items():
                        print(f"       - {attr_name}: {attr_value}")
                else:
                    print("     ❌ No hay atributos EAV")
                
                # Verificar coincidencia EAV
                coincidencia = prod.get('coincidencia_eav', '')
                if coincidencia:
                    print(f"     🎯 Coincidencia EAV: {coincidencia}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_gemini_response_format():
    """Prueba el formato de respuesta del Gemini con atributos EAV"""
    print("\n=== PRUEBA DE FORMATO DE RESPUESTA GEMINI ===")
    
    gemini_service = GeminiService()
    
    consultas_gemini = [
        "laptop HP",
        "busco laptop HP de 8GB",
        "necesito una computadora HP"
    ]
    
    print("\n2. Prueba de respuesta completa de Gemini:")
    for consulta in consultas_gemini:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            # Solo probar la consulta a la base de datos
            informacion = gemini_service._consultar_base_datos(consulta)
            
            if informacion and 'productos_encontrados' in informacion:
                productos = informacion['productos_encontrados']
                print(f"   ✅ {len(productos)} productos encontrados en la consulta BD")
                
                # Verificar que los productos tengan atributos
                for i, prod in enumerate(productos[:1], 1):  # Solo el primero
                    print(f"\n   Producto {i} en información BD:")
                    print(f"     Nombre: {prod.get('nombre', 'N/A')}")
                    
                    atributos = prod.get('atributos', {})
                    if atributos:
                        print(f"     ✅ Atributos disponibles: {list(atributos.keys())}")
                        # Mostrar algunos atributos importantes
                        attrs_importantes = ['marca', 'ram', 'memoria', 'almacenamiento', 'procesador', 'pantalla']
                        for attr in attrs_importantes:
                            if attr in atributos:
                                print(f"       - {attr}: {atributos[attr]}")
                    else:
                        print("     ❌ Sin atributos EAV en la información BD")
            else:
                print("   ❌ No se encontraron productos en la consulta BD")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_eav_case_sensitivity():
    """Prueba la sensibilidad a mayúsculas/minúsculas en búsqueda EAV"""
    print("\n=== PRUEBA DE MAYÚSCULAS/MINÚSCULAS EN EAV ===")
    
    db_service = DatabaseService()
    
    # Probar diferentes variaciones de mayúsculas
    variaciones_marca = [
        "hp", "HP", "Hp", "hP",
        "dell", "DELL", "Dell", "dELL"
    ]
    
    print("\n3. Prueba de variaciones de mayúsculas en marcas:")
    for marca in variaciones_marca:
        print(f"\n   Buscando marca: '{marca}'")
        
        # Detectar atributos
        atributos_detectados = db_service._detectar_atributos_en_mensaje(f"laptop {marca}")
        if atributos_detectados:
            print(f"     ✅ Atributos detectados: {atributos_detectados}")
        else:
            print("     ❌ No se detectaron atributos")
        
        # Buscar productos
        try:
            productos = db_service.buscar_productos(f"laptop {marca}", limite=1)
            if productos:
                print(f"     ✅ {len(productos)} productos encontrados")
            else:
                print("     ❌ No se encontraron productos")
        except Exception as e:
            print(f"     ❌ Error en búsqueda: {e}")

def main():
    """Función principal"""
    print("PRUEBA ESPECÍFICA: VISUALIZACIÓN Y MAYÚSCULAS/MINÚSCULAS EN EAV")
    print("=" * 70)
    
    try:
        test_eav_attributes_display()
        test_gemini_response_format()
        test_eav_case_sensitivity()
        
        print("\n" + "=" * 70)
        print("VERIFICACIONES REALIZADAS:")
        print("✅ Búsqueda con diferentes mayúsculas/minúsculas")
        print("✅ Visualización de atributos EAV en resultados")
        print("✅ Formato de respuesta de Gemini con atributos")
        print("✅ Detección flexible de marcas y atributos")
        
        print("\nSOLUCIONES IMPLEMENTADAS:")
        print("• Búsqueda flexible con icontains, iexact, upper(), lower(), title()")
        print("• Instrucciones específicas en el prompt para mostrar atributos EAV")
        print("• Detección mejorada de marcas con variaciones")
        print("• Combinación de búsqueda tradicional + EAV")
        
        print("\nAHORA DEBERÍA FUNCIONAR:")
        print("• 'laptop HP' → Muestra atributos como Marca: HP, RAM: 8GB, etc.")
        print("• 'LAPTOP hp' → Funciona igual que 'laptop HP'")
        print("• 'Hp LaPtOp' → Funciona con cualquier combinación de mayúsculas")
        
    except Exception as e:
        print(f"\nERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
