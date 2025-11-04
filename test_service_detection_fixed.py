#!/usr/bin/env python3
"""
Script de prueba para verificar la detección mejorada de servicios
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
from chatbot.search_intelligence_service import SearchIntelligenceService

def test_service_keyword_detection():
    """Prueba la detección de palabras clave de servicios"""
    print("=== PRUEBA DE DETECCIÓN DE PALABRAS CLAVE DE SERVICIOS ===")
    
    # Casos problemáticos específicos
    casos_servicios = [
        "Cableado Estructurado",  # Caso problemático
        "servicio de Cableado Estructurado",  # Funciona
        "Diseño y desarrollo de sitios web",  # Caso anterior
        "servicio de Diseño y desarrollo de sitios web",  # Funciona
        "Reparación de computadoras",
        "Mantenimiento preventivo",
        "Soporte técnico",
        "Configuración de redes",
        "Instalación de software",
        "Migración de datos",
        "Networking empresarial",
        "Telecomunicaciones"
    ]
    
    print("\n1. Detección directa de servicios (sin palabra 'servicio'):")
    
    # Simular la lógica de detección del gemini_service
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
    
    for caso in casos_servicios:
        mensaje_lower = caso.lower()
        
        # Detección por palabra "servicio"
        es_consulta_servicio = any(palabra in mensaje_lower for palabra in ['servicio', 'servicios'])
        
        # Detección por palabras clave
        if not es_consulta_servicio:
            es_consulta_servicio = any(palabra in mensaje_lower for palabra in palabras_servicios)
        
        resultado = "✅ DETECTADO" if es_consulta_servicio else "❌ NO DETECTADO"
        print(f"   '{caso}' -> {resultado}")

def test_service_search_intelligence():
    """Prueba la expansión de términos para servicios"""
    print("\n=== PRUEBA DE EXPANSIÓN DE TÉRMINOS PARA SERVICIOS ===")
    
    search_service = SearchIntelligenceService()
    
    terminos_test = [
        "Cableado Estructurado",
        "cableado",
        "estructurado", 
        "redes",
        "soporte técnico",
        "configuración"
    ]
    
    print("\n2. Expansión de términos de servicios:")
    for termino in terminos_test:
        print(f"\n   Término: '{termino}'")
        variaciones = search_service.obtener_variaciones_termino(termino)
        print(f"   Variaciones: {variaciones[:8]}...")  # Mostrar solo las primeras 8

def test_database_service_search():
    """Prueba la búsqueda directa en DatabaseService"""
    print("\n=== PRUEBA DE BÚSQUEDA DIRECTA DE SERVICIOS ===")
    
    db_service = DatabaseService()
    
    consultas_directas = [
        "Cableado Estructurado",
        "cableado estructurado",
        "CABLEADO ESTRUCTURADO",
        "Diseño y desarrollo de sitios web",
        "reparación",
        "mantenimiento"
    ]
    
    print("\n3. Búsqueda directa de servicios:")
    for consulta in consultas_directas:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            servicios = db_service.buscar_servicios(consulta, limite=3)
            print(f"   Servicios encontrados: {len(servicios)}")
            
            for i, serv in enumerate(servicios, 1):
                print(f"     {i}. {serv.get('nombre', 'N/A')} - ${serv.get('precio', 0)}")
                print(f"        Proveedor: {serv.get('proveedor', 'N/A')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_gemini_service_integration():
    """Prueba la integración completa con GeminiService"""
    print("\n=== PRUEBA DE INTEGRACIÓN CON GEMINI SERVICE ===")
    
    gemini_service = GeminiService()
    
    consultas_gemini = [
        "Cableado Estructurado",  # Caso problemático
        "servicio de Cableado Estructurado",  # Funciona
        "Diseño y desarrollo de sitios web",
        "Reparación de computadoras",
        "Soporte técnico"
    ]
    
    print("\n4. Consultas completas a Gemini:")
    for consulta in consultas_gemini:
        print(f"\n   Consulta: '{consulta}'")
        
        try:
            # Solo probar la consulta a la base de datos
            informacion = gemini_service._consultar_base_datos(consulta)
            
            if informacion:
                claves = list(informacion.keys())
                print(f"   ✅ Información encontrada: {claves}")
                
                if 'servicios_encontrados' in informacion:
                    servicios = informacion['servicios_encontrados']
                    print(f"     - {len(servicios)} servicios encontrados")
                    for serv in servicios[:2]:  # Mostrar solo los primeros 2
                        print(f"       • {serv.get('nombre', 'N/A')}")
                else:
                    print("     - No hay 'servicios_encontrados' en la información")
            else:
                print("   ❌ No se encontró información")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_backup_search():
    """Prueba la búsqueda de respaldo"""
    print("\n=== PRUEBA DE BÚSQUEDA DE RESPALDO ===")
    
    gemini_service = GeminiService()
    
    # Simular consultas que no se detectan como servicios inicialmente
    consultas_respaldo = [
        "Cableado Estructurado",
        "Networking empresarial", 
        "Infraestructura de red",
        "Sistemas de telecomunicaciones"
    ]
    
    print("\n5. Búsqueda de respaldo para servicios:")
    for consulta in consultas_respaldo:
        print(f"\n   Consulta: '{consulta}'")
        
        # Simular la lógica de detección
        mensaje_lower = consulta.lower()
        es_consulta_servicio = any(palabra in mensaje_lower for palabra in ['servicio', 'servicios'])
        
        palabras_servicios = [
            'cableado', 'estructurado', 'networking', 'redes', 'telecomunicaciones',
            'soporte', 'tecnico', 'técnico', 'configuracion', 'configuración'
        ]
        
        if not es_consulta_servicio:
            es_consulta_servicio = any(palabra in mensaje_lower for palabra in palabras_servicios)
        
        print(f"   Detectado como servicio: {'Sí' if es_consulta_servicio else 'No'}")
        
        # Si no se detecta, probar búsqueda de respaldo
        if not es_consulta_servicio:
            try:
                servicios_respaldo = gemini_service.db_service.buscar_servicios(consulta, limite=3)
                if servicios_respaldo:
                    print(f"   ✅ Búsqueda de respaldo encontró: {len(servicios_respaldo)} servicios")
                else:
                    print(f"   ❌ Búsqueda de respaldo no encontró servicios")
            except Exception as e:
                print(f"   ❌ Error en búsqueda de respaldo: {e}")

def main():
    """Función principal"""
    print("PRUEBA ESPECÍFICA: DETECCIÓN MEJORADA DE SERVICIOS")
    print("=" * 60)
    
    try:
        test_service_keyword_detection()
        test_service_search_intelligence()
        test_database_service_search()
        test_gemini_service_integration()
        test_backup_search()
        
        print("\n" + "=" * 60)
        print("MEJORAS IMPLEMENTADAS:")
        print("✅ Agregadas palabras clave: 'cableado', 'estructurado', 'networking', etc.")
        print("✅ Búsqueda de respaldo cuando no se detecta como servicio")
        print("✅ Sinónimos específicos para servicios técnicos")
        print("✅ Detección mejorada sin dependencia de palabra 'servicio'")
        
        print("\nAHORA DEBERÍA FUNCIONAR:")
        print("• 'Cableado Estructurado' → Detectado como servicio")
        print("• 'Diseño y desarrollo de sitios web' → Detectado como servicio")
        print("• 'Reparación de computadoras' → Detectado como servicio")
        print("• 'Soporte técnico' → Detectado como servicio")
        
        print("\nSI AÚN NO FUNCIONA:")
        print("• Verificar que existan servicios con esos nombres en la BD")
        print("• Revisar que los servicios estén activos")
        print("• Probar con búsqueda más simple como 'cableado'")
        
    except Exception as e:
        print(f"\nERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
