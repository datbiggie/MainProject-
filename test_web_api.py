#!/usr/bin/env python3
"""
Script para probar la API web de recuperación de contraseñas
"""

import os
import sys
import django
import json
from django.test import Client, RequestFactory
from django.urls import reverse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

def test_web_api():
    """Prueba la API web como lo haría el navegador"""
    
    print("🌐 Probando API web de recuperación...")
    print("=" * 50)
    
    # Crear cliente de prueba
    client = Client()
    
    # Primero, obtener la página para conseguir el CSRF token
    print("1️⃣ Obteniendo página de recuperación...")
    response = client.get('/ecommerce/recuperar_clave/')
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo la página: {response.status_code}")
        return False
    
    # Extraer CSRF token
    csrf_token = None
    if hasattr(response, 'context') and response.context:
        csrf_token = response.context.get('csrf_token')
    
    if not csrf_token:
        # Intentar extraer del contenido HTML
        content = response.content.decode('utf-8')
        import re
        csrf_match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', content)
        if csrf_match:
            csrf_token = csrf_match.group(1)
    
    print(f"   CSRF Token: {'✅ Obtenido' if csrf_token else '❌ No encontrado'}")
    
    # Probar la API
    print("\n2️⃣ Probando API de recuperación...")
    
    test_email = "luiseurdanetah@gmail.com"
    
    # Método 1: POST con JSON (como hace el JavaScript)
    print("   Método 1: POST con JSON...")
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    } if csrf_token else {'Content-Type': 'application/json'}
    
    try:
        response = client.post(
            '/ecommerce/api/request_password_reset/',
            data=json.dumps({'email': test_email}),
            content_type='application/json',
            **({'HTTP_X_CSRFTOKEN': csrf_token} if csrf_token else {})
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.content.decode('utf-8'))
                print(f"   Respuesta: {data}")
                
                if data.get('success'):
                    print("   ✅ API respondió exitosamente")
                    return True
                else:
                    print(f"   ❌ API indicó fallo: {data.get('message', 'Sin mensaje')}")
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ Error decodificando JSON: {e}")
                print(f"   Contenido crudo: {response.content}")
                
        elif response.status_code == 403:
            print("   ❌ Error 403: Problema con CSRF token")
            
        elif response.status_code == 404:
            print("   ❌ Error 404: URL no encontrada")
            
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            print(f"   Contenido: {response.content}")
            
    except Exception as e:
        print(f"   ❌ Excepción: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Método 2: POST con form data (alternativo)
    print("\n   Método 2: POST con form data...")
    try:
        response = client.post(
            '/ecommerce/api/request_password_reset/',
            {'email': test_email},
            **({'HTTP_X_CSRFTOKEN': csrf_token} if csrf_token else {})
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.content.decode('utf-8'))
                print(f"   Respuesta: {data}")
                
                if data.get('success'):
                    print("   ✅ API respondió exitosamente (form data)")
                    return True
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ Error decodificando JSON: {e}")
                
    except Exception as e:
        print(f"   ❌ Excepción: {str(e)}")
    
    return False

def check_urls():
    """Verificar que las URLs estén configuradas correctamente"""
    print("\n🔗 Verificando URLs...")
    
    from django.urls import reverse
    
    try:
        url1 = reverse('ecommerce_app:recuperar_clave')
        print(f"   recuperar_clave: {url1}")
    except Exception as e:
        print(f"   ❌ Error con recuperar_clave: {e}")
    
    try:
        url2 = reverse('ecommerce_app:request_password_reset')
        print(f"   request_password_reset: {url2}")
    except Exception as e:
        print(f"   ❌ Error con request_password_reset: {e}")

if __name__ == "__main__":
    check_urls()
    success = test_web_api()
    
    if success:
        print("\n🎉 Prueba de API web exitosa")
        print("📬 Deberías haber recibido un email de recuperación")
    else:
        print("\n💥 La prueba de API web falló")
        print("🔍 Revisa los logs para más detalles")
