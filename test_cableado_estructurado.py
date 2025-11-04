#!/usr/bin/env python3
"""
Script específico para probar "Cableado Estructurado" vs "servicio de Cableado Estructurado"
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from chatbot.gemini_service import GeminiService
from chatbot.database_service import DatabaseService

def test_exact_problem():
    """Prueba el problema exacto reportado por el usuario"""
    print("=== PRUEBA DEL PROBLEMA ESPECÍFICO ===")
    
    gemini_service = GeminiService()
    
    # Los dos casos exactos del usuario
    casos = [
        {
            'consulta': 'Cableado Estructurado',
            'deberia_funcionar': True,
            'problema_reportado': True
        },
        {
            'consulta': 'servicio de Cableado Estructurado', 
            'deberia_funcionar': True,
            'problema_reportado': False
        }
    ]
    
    print("\n1. Comparación directa de los casos problemáticos:")
    
    for i, caso in enumerate(casos, 1):
        consulta = caso['consulta']
        print(f"\n   Caso {i}: '{consulta}'")
        print(f"   Estado: {'❌ PROBLEMÁTICO' if caso['problema_reportado'] else '✅ FUNCIONA'}")
        
        try:
            # Probar la consulta completa a la base de datos
            informacion = gemini_service._consultar_base_datos(consulta)
            
            if informacion:
                claves = list(informacion.keys())
                print(f"   Resultado: ✅ Información encontrada: {claves}")
                
                # Verificar servicios específicamente
                if 'servicios_encontrados' in informacion:
                    servicios = informacion['servicios_encontrados']
                    print(f"   ✅ {len(servicios)} servicios encontrados:")
                    for j, serv in enumerate(servicios[:3], 1):
                        nombre = serv.get('nombre', 'N/A')
                        precio = serv.get('precio', 0)
                        proveedor = serv.get('proveedor', 'N/A')
                        print(f"     {j}. {nombre} - ${precio} - {proveedor}")
                else:
                    print(f"   ❌ No hay 'servicios_encontrados' en la información")
                    print(f"   Claves disponibles: {claves}")
            else:
                print(f"   ❌ No se encontró información")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_detection_step_by_step():
    """Prueba paso a paso la detección para 'Cableado Estructurado'"""
    print("\n=== ANÁLISIS PASO A PASO DE 'Cableado Estructurado' ===")
    
    consulta = "Cableado Estructurado"
    mensaje_lower = consulta.lower()
    
    print(f"\n2. Análisis de detección para: '{consulta}'")
    
    # Paso 1: Detección por palabra "servicio"
    es_consulta_servicio = any(palabra in mensaje_lower for palabra in ['servicio', 'servicios'])
    print(f"   Paso 1 - Contiene 'servicio': {'Sí' if es_consulta_servicio else 'No'}")
    
    # Paso 2: Detección por palabras clave
    palabras_servicios = [
        'diseño', 'desarrollo', 'reparacion', 'reparación', 'mantenimiento', 'instalacion', 'instalación',
        'limpieza', 'plomeria', 'plomería', 'electricidad', 'carpinteria', 'carpintería', 'pintura',
        'jardineria', 'jardinería', 'transporte', 'mudanza', 'delivery', 'consultoria', 'consultoría',
        'asesoría', 'capacitacion', 'capacitación', 'entrenamiento', 'clases', 'terapia', 'masaje',
        'peluqueria', 'peluquería', 'barberia', 'barbería', 'fotografia', 'fotografía', 'video',
        'marketing', 'publicidad', 'contabilidad', 'legal', 'abogado', 'medico', 'médico',
        'veterinario', 'seguridad', 'vigilancia', 'catering', 'eventos', 'organizacion', 'organización',
        # Servicios técnicos y especializados
        'cableado', 'estructurado', 'networking', 'redes', 'telecomunicaciones', 'fibra', 'optica',
        'soporte', 'tecnico', 'técnico', 'configuracion', 'configuración', 'programacion', 'programación',
        'software', 'hardware', 'sistemas', 'informatica', 'informática', 'web', 'hosting',
        'dominio', 'servidor', 'backup', 'respaldo', 'migracion', 'migración', 'actualizacion', 'actualización'
    ]
    
    if not es_consulta_servicio:
        palabras_encontradas = [palabra for palabra in palabras_servicios if palabra in mensaje_lower]
        es_consulta_servicio = len(palabras_encontradas) > 0
        print(f"   Paso 2 - Palabras clave encontradas: {palabras_encontradas}")
        print(f"   Paso 2 - Detectado como servicio: {'Sí' if es_consulta_servicio else 'No'}")
    
    # Paso 3: Búsqueda de respaldo
    print(f"   Paso 3 - ¿Necesita búsqueda de respaldo?: {'No' if es_consulta_servicio else 'Sí'}")
    
    if not es_consulta_servicio:
        print(f"   Paso 3 - Ejecutando búsqueda de respaldo...")
        try:
            db_service = DatabaseService()
            servicios_respaldo = db_service.buscar_servicios(consulta, limite=3)
            print(f"   Paso 3 - Servicios encontrados por respaldo: {len(servicios_respaldo)}")
        except Exception as e:
            print(f"   Paso 3 - Error en búsqueda de respaldo: {e}")

def test_database_direct_search():
    """Prueba búsqueda directa en la base de datos"""
    print("\n=== PRUEBA DE BÚSQUEDA DIRECTA EN BASE DE DATOS ===")
    
    db_service = DatabaseService()
    
    consultas = [
        "Cableado Estructurado",
        "cableado estructurado", 
        "CABLEADO",
        "estructurado",
        "cableado"
    ]
    
    print("\n3. Búsqueda directa de servicios en BD:")
    
    for consulta in consultas:
        print(f"\n   Consulta BD: '{consulta}'")
        
        try:
            servicios = db_service.buscar_servicios(consulta, limite=5)
            print(f"   Resultados: {len(servicios)} servicios")
            
            for i, serv in enumerate(servicios, 1):
                nombre = serv.get('nombre', 'N/A')
                print(f"     {i}. {nombre}")
                
        except Exception as e:
            print(f"   Error: {e}")

def test_search_intelligence():
    """Prueba el servicio de búsqueda inteligente"""
    print("\n=== PRUEBA DE BÚSQUEDA INTELIGENTE ===")
    
    from chatbot.search_intelligence_service import SearchIntelligenceService
    search_service = SearchIntelligenceService()
    
    print("\n4. Expansión de términos:")
    
    terminos = ["Cableado Estructurado", "cableado", "estructurado"]
    
    for termino in terminos:
        print(f"\n   Término: '{termino}'")
        try:
            variaciones = search_service.expandir_terminos_busqueda(termino)
            print(f"   Expansiones: {variaciones[:10]}...")  # Primeras 10
        except Exception as e:
            print(f"   Error: {e}")

def main():
    """Función principal"""
    print("DIAGNÓSTICO ESPECÍFICO: 'Cableado Estructurado' vs 'servicio de Cableado Estructurado'")
    print("=" * 80)
    
    try:
        test_exact_problem()
        test_detection_step_by_step()
        test_database_direct_search()
        test_search_intelligence()
        
        print("\n" + "=" * 80)
        print("DIAGNÓSTICO COMPLETADO")
        
        print("\nMEJORAS IMPLEMENTADAS:")
        print("✅ Agregada 'cableado' y 'estructurado' a palabras clave de servicios")
        print("✅ Búsqueda de respaldo cuando no se detecta como servicio")
        print("✅ Sinónimos específicos para 'cableado estructurado'")
        print("✅ Instrucciones mejoradas para Gemini sobre servicios")
        
        print("\nRESULTADO ESPERADO:")
        print("• 'Cableado Estructurado' → Ahora debería encontrar servicios")
        print("• 'servicio de Cableado Estructurado' → Sigue funcionando")
        
        print("\nSI AÚN NO FUNCIONA:")
        print("1. Verificar que existe un servicio con nombre 'Cableado Estructurado' en la BD")
        print("2. Verificar que el servicio esté activo (estatus='Activo')")
        print("3. Probar con términos más simples: 'cableado' o 'estructurado'")
        print("4. Revisar logs del servidor para errores específicos")
        
    except Exception as e:
        print(f"\nERROR EN EL DIAGNÓSTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
