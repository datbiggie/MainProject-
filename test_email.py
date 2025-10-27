#!/usr/bin/env python3
"""
Script para probar la configuración de email de Django
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

from django.core.mail import send_mail
from django.conf import settings
from dotenv import load_dotenv

def test_email_configuration():
    """Prueba la configuración de email enviando un correo de prueba"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("=== CONFIGURACIÓN DE EMAIL ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NO CONFIGURADO'}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    # Verificar que las variables estén configuradas
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("❌ ERROR: EMAIL_HOST_USER o EMAIL_HOST_PASSWORD no están configurados")
        return False
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("⚠️  ADVERTENCIA: Usando console backend - los emails se mostrarán en consola")
        return False
    
    # Intentar enviar email de prueba
    try:
        print("📧 Enviando email de prueba...")
        
        subject = 'Prueba de configuración de email'
        message = '''
        Este es un email de prueba para verificar que la configuración de email funciona correctamente.
        
        Si recibes este mensaje, la configuración está funcionando.
        
        Saludos,
        Sistema de E-commerce
        '''
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.EMAIL_HOST_USER]  # Enviar a ti mismo
        
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False
        )
        
        print("✅ Email enviado exitosamente!")
        print(f"📬 Revisa tu bandeja de entrada en: {settings.EMAIL_HOST_USER}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR al enviar email: {e}")
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("1. Verifica que la contraseña de aplicación sea correcta")
        print("2. Asegúrate de que la autenticación de 2 factores esté habilitada en Gmail")
        print("3. Verifica que las variables de entorno estén cargadas correctamente")
        return False

if __name__ == "__main__":
    test_email_configuration()
