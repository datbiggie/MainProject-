#!/usr/bin/env python
"""
Script de prueba para verificar el proceso de recuperación de contraseña
Ejecutar con: python manage.py shell < test_password_reset.py
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MainProject.settings')
    django.setup()

from django.core import signing
from django.contrib.auth.hashers import make_password, check_password
from ecommerce_app.models import usuario, empresa

def test_token_generation_and_validation():
    """Prueba la generación y validación de tokens"""
    print("=== PRUEBA DE TOKENS ===")
    
    # Crear payload de prueba
    payload = {'type': 'usuario', 'id': 1}
    
    # Generar token
    token = signing.dumps(payload, salt='password-reset')
    print(f"Token generado: {token[:50]}...")
    
    # Validar token
    try:
        decoded_payload = signing.loads(token, salt='password-reset', max_age=60 * 60 * 2)
        print(f"Token válido. Payload: {decoded_payload}")
        return True
    except signing.BadSignature as e:
        print(f"Error validando token: {e}")
        return False

def test_password_hashing():
    """Prueba el hash de contraseñas"""
    print("\n=== PRUEBA DE HASH DE CONTRASEÑAS ===")
    
    password = "nueva_password_123"
    hashed = make_password(password)
    print(f"Contraseña original: {password}")
    print(f"Hash generado: {hashed[:50]}...")
    
    # Verificar que el hash es válido
    is_valid = check_password(password, hashed)
    print(f"Verificación del hash: {'✓ VÁLIDO' if is_valid else '✗ INVÁLIDO'}")
    
    return is_valid

def test_user_lookup():
    """Prueba la búsqueda de usuarios y empresas"""
    print("\n=== PRUEBA DE BÚSQUEDA DE USUARIOS ===")
    
    # Buscar primer usuario
    try:
        user = usuario.objects.first()
        if user:
            print(f"Usuario encontrado: {user.nombre_usuario} ({user.correo_usuario})")
            print(f"ID: {user.id_usuario}")
            return user
        else:
            print("No se encontraron usuarios en la base de datos")
    except Exception as e:
        print(f"Error buscando usuarios: {e}")
    
    # Buscar primera empresa
    try:
        emp = empresa.objects.first()
        if emp:
            print(f"Empresa encontrada: {emp.nombre_empresa} ({emp.correo_empresa})")
            print(f"ID: {emp.id_empresa}")
            return emp
        else:
            print("No se encontraron empresas en la base de datos")
    except Exception as e:
        print(f"Error buscando empresas: {e}")
    
    return None

def test_password_update_simulation():
    """Simula la actualización de contraseña"""
    print("\n=== SIMULACIÓN DE ACTUALIZACIÓN DE CONTRASEÑA ===")
    
    # Buscar un usuario de prueba
    test_user = usuario.objects.first()
    if not test_user:
        print("No hay usuarios para probar")
        return False
    
    print(f"Usuario de prueba: {test_user.nombre_usuario}")
    
    # Guardar contraseña original
    original_password = test_user.password_usuario
    print(f"Contraseña original (hash): {original_password[:30]}...")
    
    # Generar nueva contraseña
    new_password = "test_nueva_password_123"
    new_hashed = make_password(new_password)
    
    # Simular actualización (sin guardar realmente)
    print(f"Nueva contraseña (hash): {new_hashed[:30]}...")
    print("✓ Simulación exitosa - No se guardó en la base de datos")
    
    return True

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("INICIANDO PRUEBAS DEL SISTEMA DE RECUPERACIÓN DE CONTRASEÑA")
    print("=" * 60)
    
    results = []
    
    # Prueba 1: Tokens
    results.append(test_token_generation_and_validation())
    
    # Prueba 2: Hash de contraseñas
    results.append(test_password_hashing())
    
    # Prueba 3: Búsqueda de usuarios
    user_found = test_user_lookup()
    results.append(user_found is not None)
    
    # Prueba 4: Simulación de actualización
    if user_found:
        results.append(test_password_update_simulation())
    else:
        print("\n⚠️  Saltando prueba de actualización - No hay usuarios")
        results.append(False)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS:")
    tests = [
        "Generación y validación de tokens",
        "Hash de contraseñas",
        "Búsqueda de usuarios/empresas",
        "Simulación de actualización"
    ]
    
    for i, (test_name, result) in enumerate(zip(tests, results)):
        status = "✓ PASÓ" if result else "✗ FALLÓ"
        print(f"{i+1}. {test_name}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nResultado final: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema debería funcionar correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar la configuración.")

if __name__ == "__main__":
    run_all_tests()
