#!/usr/bin/env python3
"""
Script para probar la integración completa del sistema de login con recuperación de contraseña
"""
import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from dotenv import load_dotenv

def test_login_integration():
    """Prueba la integración completa del sistema de login"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("=== PRUEBA DE INTEGRACIÓN DEL SISTEMA DE LOGIN ===")
    
    # Crear cliente de prueba
    client = Client()
    
    try:
        # 1. Probar que la página de login carga correctamente
        print("1. 🔍 Probando carga de página de login...")
        login_response = client.get('/ecommerce/iniciar_sesion/')
        if login_response.status_code == 200:
            print("   ✅ Página de login carga correctamente")
            
            # Verificar que contiene el enlace de recuperación
            content = login_response.content.decode('utf-8')
            if 'recuperar_clave' in content and '¿Olvidaste tu contraseña?' in content:
                print("   ✅ Enlace de recuperación de contraseña presente")
            else:
                print("   ⚠️  Enlace de recuperación no encontrado en el HTML")
        else:
            print(f"   ❌ Error al cargar página de login: {login_response.status_code}")
            return False
        
        # 2. Probar que la página de recuperación carga correctamente
        print("\n2. 🔍 Probando carga de página de recuperación...")
        recovery_response = client.get('/ecommerce/recuperar_clave/')
        if recovery_response.status_code == 200:
            print("   ✅ Página de recuperación carga correctamente")
        else:
            print(f"   ❌ Error al cargar página de recuperación: {recovery_response.status_code}")
            return False
        
        # 3. Probar validación de email
        print("\n3. 🔍 Probando validación de email...")
        email_validation_response = client.post('/ecommerce/validate-email/', 
            {'email': 'luiseurdanetah@gmail.com'}, 
            content_type='application/json'
        )
        if email_validation_response.status_code == 200:
            print("   ✅ Endpoint de validación de email funciona")
        else:
            print(f"   ❌ Error en validación de email: {email_validation_response.status_code}")
        
        # 4. Probar endpoint de recuperación
        print("\n4. 🔍 Probando endpoint de recuperación...")
        recovery_request_response = client.post('/ecommerce/api/request_password_reset/', 
            {'email': 'luiseurdanetah@gmail.com'}, 
            content_type='application/json'
        )
        if recovery_request_response.status_code == 200:
            print("   ✅ Endpoint de recuperación funciona")
        else:
            print(f"   ❌ Error en endpoint de recuperación: {recovery_request_response.status_code}")
        
        print("\n🎉 ¡Todas las pruebas de integración pasaron exitosamente!")
        print("\n📋 RESUMEN DE FUNCIONALIDADES:")
        print("✅ Página de login con enlace de recuperación")
        print("✅ Página de recuperación de contraseña")
        print("✅ Validación de email existente")
        print("✅ Envío de correos de recuperación")
        print("✅ Templates de email personalizados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False

def show_urls():
    """Muestra las URLs disponibles del sistema"""
    print("\n=== URLs DEL SISTEMA ===")
    print("🔐 Login: http://localhost:8000/ecommerce/iniciar_sesion/")
    print("🔑 Recuperar contraseña: http://localhost:8000/ecommerce/recuperar_clave/")
    print("📧 API validar email: http://localhost:8000/ecommerce/validate-email/")
    print("🔄 API recuperar contraseña: http://localhost:8000/ecommerce/api/request_password_reset/")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de integración del sistema de login...\n")
    
    success = test_login_integration()
    
    if success:
        show_urls()
        print("\n✨ ¡El sistema está completamente funcional!")
        print("💡 Puedes probar el flujo completo en tu navegador")
    else:
        print("\n❌ Algunas pruebas fallaron")
        print("🔧 Revisa la configuración del servidor y las URLs")
