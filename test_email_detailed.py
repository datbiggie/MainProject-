#!/usr/bin/env python3
"""
Script detallado para probar el envío de emails de recuperación
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

def test_email_sending():
    """Prueba detallada del envío de emails"""
    
    print("🔍 Prueba detallada de envío de emails...")
    print("=" * 50)
    
    # Importar después de configurar Django
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    from django.core import signing
    from ecommerce_app.models import usuario
    
    # Verificar configuración de email
    print("📧 Configuración de email:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"   EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NO CONFIGURADO'}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Obtener usuario
    test_email = "luiseurdanetah@gmail.com"
    user_obj = usuario.objects.filter(correo_usuario__iexact=test_email).first()
    
    if not user_obj:
        print(f"❌ No se encontró usuario con email: {test_email}")
        return False
    
    print(f"\n✅ Usuario encontrado: {user_obj.nombre_usuario}")
    
    # Generar token como lo hace la función real
    payload = {'type': 'usuario', 'id': user_obj.id_usuario}
    token = signing.dumps(payload, salt='password-reset')
    
    # Generar link
    base_url = 'http://localhost:8000'  # URL base por defecto
    reset_link = f"{base_url}/ecommerce/confirmar_recuperacion/?token={token}"
    
    print(f"\n🔗 Link de recuperación generado:")
    print(f"   {reset_link}")
    
    # Renderizar template de email
    try:
        html_message = render_to_string('ecommerce_app/emails/password_reset.html', {
            'reset_link': reset_link, 
            'user': user_obj
        })
        plain_message = strip_tags(html_message)
        
        print(f"\n📝 Template renderizado exitosamente")
        print(f"   Longitud HTML: {len(html_message)} caracteres")
        print(f"   Longitud texto plano: {len(plain_message)} caracteres")
        
    except Exception as e:
        print(f"❌ Error renderizando template: {str(e)}")
        return False
    
    # Intentar enviar email
    subject = 'Recuperación de contraseña'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [test_email]
    
    print(f"\n📤 Intentando enviar email...")
    print(f"   De: {from_email}")
    print(f"   Para: {recipient_list}")
    print(f"   Asunto: {subject}")
    
    try:
        result = send_mail(
            subject, 
            plain_message, 
            from_email, 
            recipient_list, 
            html_message=html_message, 
            fail_silently=False
        )
        
        print(f"✅ Email enviado exitosamente!")
        print(f"   Resultado: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {str(e)}")
        print(f"   Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_sending()
    if success:
        print("\n🎉 Prueba de email completada exitosamente")
        print("📬 Revisa tu bandeja de entrada (y carpeta de spam)")
    else:
        print("\n💥 La prueba de email falló")
