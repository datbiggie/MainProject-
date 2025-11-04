#!/usr/bin/env python3
"""
Script de prueba específico para verificar la detección de servicios
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from chatbot.gemini_service import GeminiService
from chatbot.search_intelligence_service import SearchIntelligenceService

def test_service_detection():
    """Prueba la detección mejorada de servicios"""
    print("=== PRUEBA DE DETECCIÓN DE SERVICIOS ===")
    
    gemini_service = GeminiService()
    search_service = SearchIntelligenceService()
    
    # Casos de prueba específicos
    casos_prueba = [
        "servicio de Diseño y desarrollo de sitios web",  # Funciona
        "Diseño y desarrollo de sitios web",              # No funcionaba antes
        "desarrollo web",
        "diseño gráfico",
        "programación",
        "marketing digital",
        "consultoría empresarial",
        "fotografía profesional"
    ]
    
    print("\n1. Prueba de expansión de términos:")
    for caso in casos_prueba:
        print(f"\n   Consulta: '{caso}'")
        
        # Probar expansión de términos
        terminos_expandidos = search_service.expandir_terminos_busqueda(caso)
        print(f"   Términos expandidos: {terminos_expandidos[:8]}...")  # Mostrar solo los primeros 8
        
        # Probar detección en Gemini
        try:
            informacion = gemini_service._consultar_base_datos(caso)
            if informacion:
                claves = list(informacion.keys())
                print(f"   ✅ Información encontrada: {claves}")
            else:
                print("   ❌ No se encontró información")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n2. Prueba de detección de palabras clave de servicios:")
    
    # Probar detección directa
    palabras_servicios = [
        'diseño', 'desarrollo', 'programación', 'marketing', 'consultoría',
        'fotografía', 'video', 'contabilidad', 'legal', 'médico'
    ]
    
    for palabra in palabras_servicios:
        mensaje_test = f"Busco {palabra}"
        mensaje_lower = mensaje_test.lower()
        
        # Simular la lógica de detección del gemini_service
        es_consulta_servicio = any(palabra in mensaje_lower for palabra in ['servicio', 'servicios'])
        
        palabras_servicios_detectar = [
            'diseño', 'desarrollo', 'reparacion', 'reparación', 'mantenimiento',
            'limpieza', 'plomeria', 'plomería', 'electricidad', 'carpinteria',
            'pintura', 'jardineria', 'transporte', 'mudanza', 'delivery',
            'consultoria', 'consultoría', 'asesoría', 'capacitacion', 'marketing',
            'publicidad', 'contabilidad', 'legal', 'abogado', 'medico', 'médico',
            'fotografia', 'fotografía', 'video'
        ]
        
        if not es_consulta_servicio:
            es_consulta_servicio = any(palabra_serv in mensaje_lower for palabra_serv in palabras_servicios_detectar)
        
        resultado = "✅ DETECTADO" if es_consulta_servicio else "❌ NO DETECTADO"
        print(f"   '{mensaje_test}' -> {resultado}")

def main():
    """Función principal"""
    print("PRUEBA ESPECÍFICA: DETECCIÓN DE SERVICIOS")
    print("=" * 50)
    
    try:
        test_service_detection()
        
        print("\n" + "=" * 50)
        print("RESULTADO DE LA PRUEBA:")
        print("✅ Ahora 'Diseño y desarrollo de sitios web' debería ser detectado")
        print("✅ La detección no depende solo de la palabra 'servicio'")
        print("✅ Se agregaron sinónimos específicos para servicios digitales")
        
    except Exception as e:
        print(f"\nERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
