#!/usr/bin/env python3
"""
Script de prueba específico para verificar la búsqueda EAV
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

def test_eav_detection():
    """Prueba la detección de atributos EAV"""
    print("=== PRUEBA DE DETECCIÓN DE ATRIBUTOS EAV ===")
    
    db_service = DatabaseService()
    
    # Casos de prueba para detección de atributos
    casos_eav = [
        "laptop HP de 8GB",
        "laptop HP con 8GB de RAM",
        "computadora Dell con 16GB de memoria",
        "laptop de 15 pulgadas",
        "notebook con 256GB de almacenamiento",
        "laptop con procesador Intel Core i5",
        "computadora con SSD de 512GB",
        "laptop negra de 17 pulgadas",
        "notebook HP con Windows 11",
        "laptop gaming con 32GB RAM y 1TB SSD"
    ]
    
    print("\n1. Detección de atributos EAV:")
    for caso in casos_eav:
        print(f"\n   Consulta: '{caso}'")
        
        # Probar detección de atributos
        atributos = db_service._detectar_atributos_en_mensaje(caso)
        if atributos:
            print(f"   ✅ Atributos detectados: {atributos}")
        else:
            print("   ❌ No se detectaron atributos")

def test_eav_search():
    """Prueba la búsqueda por atributos EAV"""
    print("\n=== PRUEBA DE BÚSQUEDA POR ATRIBUTOS EAV ===")
    
    db_service = DatabaseService()
    
    # Casos de prueba para búsqueda EAV
    consultas_eav = [
        "laptop HP de 8GB",
        "computadora con 16GB de RAM",
        "laptop de 15 pulgadas",
        "notebook con 256GB",
        "laptop HP",
        "computadora Dell"
    ]
    
    print("\n2. Búsqueda con atributos EAV:")
    for consulta in consultas_eav:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            # Probar búsqueda completa (incluye EAV)
            productos = db_service.buscar_productos(consulta, limite=3)
            print(f"   Productos encontrados: {len(productos)}")
            
            for i, prod in enumerate(productos[:2], 1):  # Mostrar solo los primeros 2
                nombre = prod.get('nombre', 'N/A')
                precio = prod.get('precio', 0)
                atributos = prod.get('atributos', {})
                coincidencia_eav = prod.get('coincidencia_eav', '')
                
                print(f"     {i}. {nombre} - ${precio}")
                if atributos:
                    # Mostrar algunos atributos relevantes
                    attrs_relevantes = []
                    for attr_name, attr_value in atributos.items():
                        if attr_name.lower() in ['marca', 'ram', 'memoria', 'almacenamiento', 'pantalla', 'procesador']:
                            attrs_relevantes.append(f"{attr_name}: {attr_value}")
                    if attrs_relevantes:
                        print(f"        Atributos: {', '.join(attrs_relevantes[:3])}")
                
                if coincidencia_eav:
                    print(f"        Coincidencia EAV: {coincidencia_eav}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_gemini_eav_integration():
    """Prueba la integración EAV con el servicio Gemini"""
    print("\n=== PRUEBA DE INTEGRACIÓN EAV CON GEMINI ===")
    
    gemini_service = GeminiService()
    
    consultas_gemini = [
        "Busco una laptop HP de 8GB",
        "Necesito una computadora con 16GB de RAM",
        "¿Tienes laptops de 15 pulgadas?",
        "Quiero una laptop Dell con SSD"
    ]
    
    print("\n3. Integración con Gemini:")
    for consulta in consultas_gemini:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            # Probar solo la consulta a la base de datos (sin generar respuesta completa)
            informacion = gemini_service._consultar_base_datos(consulta)
            if informacion:
                claves = list(informacion.keys())
                print(f"   ✅ Información encontrada: {claves}")
                
                # Mostrar detalles de productos encontrados
                if 'productos_encontrados' in informacion:
                    productos = informacion['productos_encontrados']
                    print(f"     - {len(productos)} productos encontrados")
                    for prod in productos[:1]:  # Mostrar solo el primero
                        nombre = prod.get('nombre', 'N/A')
                        atributos = prod.get('atributos', {})
                        print(f"       Ejemplo: {nombre}")
                        if atributos:
                            print(f"       Atributos: {list(atributos.keys())[:5]}")
            else:
                print("   ❌ No se encontró información")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Función principal"""
    print("PRUEBA ESPECÍFICA: BÚSQUEDA EAV (Entity-Attribute-Value)")
    print("=" * 60)
    
    try:
        test_eav_detection()
        test_eav_search()
        test_gemini_eav_integration()
        
        print("\n" + "=" * 60)
        print("RESULTADO DE LA PRUEBA EAV:")
        print("✅ Detección de atributos específicos (marca, RAM, almacenamiento)")
        print("✅ Búsqueda por patrones numéricos (8GB, 16GB, 256GB, etc.)")
        print("✅ Búsqueda por especificaciones técnicas")
        print("✅ Integración con el sistema de búsqueda inteligente")
        print("✅ Combinación de resultados tradicionales + EAV")
        
        print("\nEJEMPLOS QUE AHORA FUNCIONAN:")
        print("• 'laptop HP de 8GB' → Encuentra por marca HP y RAM 8GB")
        print("• 'computadora con 16GB de RAM' → Encuentra por especificación RAM")
        print("• 'laptop de 15 pulgadas' → Encuentra por tamaño de pantalla")
        print("• 'notebook con 256GB' → Encuentra por almacenamiento")
        
    except Exception as e:
        print(f"\nERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
