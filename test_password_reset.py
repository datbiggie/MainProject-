#!/usr/bin/env python3
"""
Script para probar la función de recuperación de contraseña
"""
import os
import sys
import django
import json
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from django.test import RequestFactory
from django.http import JsonResponse
from ecommerce_app.views import request_password_reset
from dotenv import load_dotenv

def test_password_reset():
    """Prueba la función de recuperación de contraseña"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("=== PRUEBA DE RECUPERACIÓN DE CONTRASEÑA ===")
    
    # Crear una request factory
    factory = RequestFactory()
    
    # Email a probar
    test_email = "luiseurdanetah@gmail.com"
    
    # Crear request POST con el email
    request_data = json.dumps({"email": test_email})
    request = factory.post(
        '/api/request_password_reset/',
        data=request_data,
        content_type='application/json'
    )
    
    print(f"📧 Probando recuperación para: {test_email}")
    
    try:
        # Llamar a la función de recuperación
        response = request_password_reset(request)
        
        if isinstance(response, JsonResponse):
            response_data = json.loads(response.content.decode('utf-8'))
            
            if response_data.get('success'):
                print("✅ Solicitud de recuperación procesada exitosamente!")
                print(f"📬 Mensaje: {response_data.get('message')}")
                print("\n🔍 VERIFICA:")
                print("1. Tu bandeja de entrada en Gmail")
                print("2. La carpeta de spam/correo no deseado")
                print("3. Que el correo provenga de: luiseurdanetah@gmail.com")
                
                return True
            else:
                print(f"❌ Error en la solicitud: {response_data.get('message')}")
                return False
        else:
            print("❌ Respuesta inesperada del servidor")
            return False
            
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {e}")
        print("\n🔧 POSIBLES CAUSAS:")
        print("1. El usuario no existe en la base de datos")
        print("2. Error en la configuración de email")
        print("3. Problema con el template de email")
        return False

def check_user_exists():
    """Verifica si el usuario existe en la base de datos"""
    try:
        from ecommerce_app.models import usuario, empresa
        
        test_email = "luiseurdanetah@gmail.com"
        
        print("\n=== VERIFICACIÓN DE USUARIO ===")
        
        # Buscar en usuarios
        user_obj = usuario.objects.filter(correo_usuario__iexact=test_email).first()
        if user_obj:
            print(f"✅ Usuario encontrado: {user_obj.nombre_usuario} (ID: {user_obj.id_usuario})")
            return True
        
        # Buscar en empresas
        empresa_obj = empresa.objects.filter(correo_empresa__iexact=test_email).first()
        if empresa_obj:
            print(f"✅ Empresa encontrada: {empresa_obj.nombre_empresa} (ID: {empresa_obj.id_empresa})")
            return True
        
        print(f"❌ No se encontró ningún usuario o empresa con el email: {test_email}")
        print("\n🔧 SOLUCIÓN:")
        print("1. Registra una cuenta con este email primero")
        print("2. O usa un email que ya esté registrado en el sistema")
        return False
        
    except Exception as e:
        print(f"❌ Error al verificar usuario: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de recuperación de contraseña...\n")
    
    # Verificar si el usuario existe
    user_exists = check_user_exists()
    
    if user_exists:
        # Probar la recuperación de contraseña
        success = test_password_reset()
        
        if success:
            print("\n🎉 ¡Prueba completada exitosamente!")
            print("📱 Revisa tu email para el enlace de recuperación")
        else:
            print("\n❌ La prueba falló")
    else:
        print("\n⚠️  No se puede probar la recuperación sin un usuario registrado")
