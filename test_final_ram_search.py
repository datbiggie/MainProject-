#!/usr/bin/env python3
"""
Prueba final para verificar que la búsqueda de laptops con 8GB RAM funcione
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

def test_ram_detection():
    """Prueba la detección de RAM en diferentes formatos"""
    print("=== PRUEBA DE DETECCIÓN DE RAM ===")
    
    db_service = DatabaseService()
    
    consultas_ram = [
        "necesito una laptop de 8gb de ram",
        "laptop con 8GB RAM",
        "computadora de 8 GB",
        "laptop HP de 8gb",
        "busco laptop con 8gb de memoria",
        "laptop 8GB",
        "8gb laptop"
    ]
    
    print("\n1. Detección de atributos RAM:")
    for consulta in consultas_ram:
        print(f"\n   Consulta: '{consulta}'")
        atributos = db_service._detectar_atributos_en_mensaje(consulta)
        if atributos and 'ram' in atributos:
            print(f"   ✅ RAM detectada: {atributos['ram']}")
        else:
            print(f"   ❌ RAM no detectada. Atributos: {atributos}")

def test_comprehensive_search():
    """Prueba búsqueda completa con múltiples métodos"""
    print("\n=== PRUEBA DE BÚSQUEDA COMPLETA ===")
    
    db_service = DatabaseService()
    consulta = "necesito una laptop de 8gb de ram"
    
    print(f"\n2. Búsqueda completa para: '{consulta}'")
    
    try:
        # Búsqueda completa
        productos = db_service.buscar_productos(consulta, limite=10)
        print(f"   Total productos encontrados: {len(productos)}")
        
        if productos:
            print("\n   Productos encontrados:")
            for i, prod in enumerate(productos, 1):
                print(f"\n   {i}. {prod['nombre']} - ${prod['precio']}")
                print(f"      Vendedor: {prod['vendedor']}")
                print(f"      Stock: {prod['stock']}")
                
                # Mostrar atributos
                atributos = prod.get('atributos', {})
                if atributos:
                    attrs_importantes = []
                    for attr_name, attr_value in atributos.items():
                        if any(keyword in attr_name.lower() for keyword in ['ram', 'memoria', 'marca', 'procesador', 'almacenamiento']):
                            attrs_importantes.append(f"{attr_name}: {attr_value}")
                    
                    if attrs_importantes:
                        print(f"      Especificaciones: {', '.join(attrs_importantes)}")
                    else:
                        print(f"      Atributos disponibles: {list(atributos.keys())[:5]}")
                else:
                    print("      Sin atributos EAV")
                
                # Mostrar coincidencias
                if 'coincidencia_eav' in prod:
                    print(f"      ✅ Coincidencia EAV: {prod['coincidencia_eav']}")
                if 'coincidencia_patron' in prod:
                    print(f"      ✅ Coincidencia Patrón: {prod['coincidencia_patron']}")
        else:
            print("   ❌ No se encontraron productos")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_gemini_integration():
    """Prueba la integración completa con Gemini"""
    print("\n=== PRUEBA DE INTEGRACIÓN GEMINI ===")
    
    gemini_service = GeminiService()
    consulta = "necesito una laptop de 8gb de ram"
    
    print(f"\n3. Consulta Gemini: '{consulta}'")
    
    try:
        # Solo probar la consulta a la BD (sin generar respuesta completa)
        informacion = gemini_service._consultar_base_datos(consulta)
        
        if informacion:
            print(f"   ✅ Información de BD obtenida. Claves: {list(informacion.keys())}")
            
            if 'productos_encontrados' in informacion:
                productos = informacion['productos_encontrados']
                print(f"   ✅ {len(productos)} productos en la información de BD")
                
                # Verificar que los productos tengan la información necesaria
                for i, prod in enumerate(productos[:3], 1):
                    print(f"\n   Producto {i} para Gemini:")
                    print(f"     Nombre: {prod.get('nombre', 'N/A')}")
                    print(f"     Precio: ${prod.get('precio', 0)}")
                    print(f"     Vendedor: {prod.get('vendedor', 'N/A')}")
                    
                    atributos = prod.get('atributos', {})
                    if atributos:
                        print(f"     ✅ Atributos disponibles: {len(atributos)}")
                        # Buscar RAM específicamente
                        ram_attrs = {k: v for k, v in atributos.items() if 'ram' in k.lower() or 'memoria' in k.lower()}
                        if ram_attrs:
                            print(f"     🎯 RAM encontrada: {ram_attrs}")
                        else:
                            print(f"     Otros atributos: {list(atributos.keys())[:3]}")
                    else:
                        print(f"     ❌ Sin atributos EAV")
                    
                    if 'coincidencia_eav' in prod:
                        print(f"     ✅ Coincidencia EAV: {prod['coincidencia_eav']}")
                    if 'coincidencia_patron' in prod:
                        print(f"     ✅ Coincidencia Patrón: {prod['coincidencia_patron']}")
            else:
                print("   ❌ No hay 'productos_encontrados' en la información de BD")
                print(f"   Claves disponibles: {list(informacion.keys())}")
        else:
            print("   ❌ No se obtuvo información de la BD")
            
    except Exception as e:
        print(f"   ❌ Error en Gemini: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Función principal"""
    print("PRUEBA FINAL: BÚSQUEDA DE LAPTOPS CON 8GB RAM")
    print("=" * 60)
    
    try:
        # Ejecutar todas las pruebas
        test_ram_detection()
        test_comprehensive_search()
        test_gemini_integration()
        
        print("\n" + "=" * 60)
        print("DIAGNÓSTICO COMPLETO REALIZADO")
        
        print("\nMEJORAS IMPLEMENTADAS:")
        print("✅ Detección mejorada de patrones de RAM")
        print("✅ Búsqueda en nombre/descripción por patrones específicos")
        print("✅ Búsqueda de respaldo por patrones múltiples")
        print("✅ Instrucciones mejoradas para Gemini")
        print("✅ Combinación de múltiples métodos de búsqueda")
        
        print("\nSI AÚN NO FUNCIONA, POSIBLES CAUSAS:")
        print("• No hay productos con '8gb', '8GB', 'RAM 8gb' en nombre/descripción")
        print("• No hay atributos EAV configurados para RAM")
        print("• Los productos están inactivos o no existen")
        print("• Los datos están en un formato no detectado")
        
        print("\nPRÓXIMOS PASOS:")
        print("1. Ejecutar: python debug_eav_search.py")
        print("2. Verificar que existan productos con RAM en la BD")
        print("3. Revisar el formato de los datos de RAM")
        print("4. Probar con consultas más simples como 'laptop'")
        
    except Exception as e:
        print(f"\nERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
