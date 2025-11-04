#!/usr/bin/env python3
"""
Script para probar la funcionalidad de recuperación de contraseñas
"""

import os
import sys
import django
import json
from django.test import RequestFactory
from django.http import JsonResponse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

def test_password_recovery():
    """Prueba la funcionalidad de recuperación de contraseñas"""
    
    print("🔍 Probando recuperación de contraseñas...")
    print("=" * 50)
    
    # Importar después de configurar Django
    from ecommerce_app.views import request_password_reset
    from ecommerce_app.models import usuario, empresa
    
    # Verificar si existe el usuario con el email
    test_email = "luiseurdanetah@gmail.com"
    print(f"📧 Buscando usuario con email: {test_email}")
    
    # Buscar en usuarios
    user_obj = usuario.objects.filter(correo_usuario__iexact=test_email).first()
    if user_obj:
        print(f"✅ Usuario encontrado: {user_obj.nombre_usuario} (ID: {user_obj.id_usuario})")
    else:
        print("❌ No se encontró usuario con ese email")
        
        # Buscar en empresas
        empresa_obj = empresa.objects.filter(correo_empresa__iexact=test_email).first()
        if empresa_obj:
            print(f"✅ Empresa encontrada: {empresa_obj.nombre_empresa} (ID: {empresa_obj.id_empresa})")
        else:
            print("❌ No se encontró empresa con ese email")
            print("\n🔍 Usuarios disponibles:")
            for u in usuario.objects.all()[:5]:
                print(f"   - {u.nombre_usuario}: {u.correo_usuario}")
            print("\n🔍 Empresas disponibles:")
            for e in empresa.objects.all()[:5]:
                print(f"   - {e.nombre_empresa}: {e.correo_empresa}")
            return False
    
    print("\n📤 Probando envío de email de recuperación...")
    
    # Crear request simulado
    factory = RequestFactory()
    request_data = json.dumps({"email": test_email})
    request = factory.post(
        '/api/request_password_reset/',
        data=request_data,
        content_type='application/json'
    )
    
    try:
        # Llamar a la función de recuperación
        response = request_password_reset(request)
        
        if isinstance(response, JsonResponse):
            response_data = json.loads(response.content.decode('utf-8'))
            print(f"✅ Respuesta del servidor: {response_data}")
            
            if response_data.get('success'):
                print("✅ La función indica que el email fue enviado exitosamente")
                return True
            else:
                print(f"❌ Error en la respuesta: {response_data.get('message', 'Sin mensaje')}")
                return False
        else:
            print(f"❌ Respuesta inesperada: {type(response)}")
            return False
            
    except Exception as e:
        print(f"❌ Error al ejecutar request_password_reset: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_password_recovery()
    if success:
        print("\n🎉 Prueba completada exitosamente")
    else:
        print("\n💥 La prueba falló")
