#!/usr/bin/env python
import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from chatbot.gemini_service import GeminiService
from chatbot.database_service import DatabaseService

print("=== Probando respuesta del chatbot para 'Decandido' ===")

# Crear instancias de los servicios
gemini_service = GeminiService()
db_service = DatabaseService()

# Mensaje del usuario
mensaje_usuario = "busca la empresa Decandido"
print(f"\nMensaje del usuario: {mensaje_usuario}")

# Simular el proceso completo del chatbot
print("\n1. Consultando base de datos...")
informacion_bd = gemini_service._consultar_base_datos(mensaje_usuario)
print(f"Información encontrada en BD: {json.dumps(informacion_bd, ensure_ascii=False, indent=2) if informacion_bd else 'None'}")

# Generar respuesta completa
print("\n2. Generando respuesta con Gemini...")
respuesta = gemini_service.generar_respuesta(mensaje_usuario)
print(f"\nRespuesta del chatbot:\n{respuesta}")

# Probar también con diferentes variaciones del mensaje
mensajes_prueba = [
    "¿está registrada la empresa Decandido?",
    "me puedes decir si Decandido está en el sistema?",
    "información sobre la empresa Decandido",
    "Decandido empresa"
]

print("\n=== Probando variaciones del mensaje ===")
for i, mensaje in enumerate(mensajes_prueba, 1):
    print(f"\n{i}. Mensaje: {mensaje}")
    informacion = gemini_service._consultar_base_datos(mensaje)
    if informacion:
        print(f"   BD encontró: {list(informacion.keys())}")
        respuesta = gemini_service.generar_respuesta(mensaje)
        print(f"   Respuesta: {respuesta[:200]}..." if len(respuesta) > 200 else f"   Respuesta: {respuesta}")
    else:
        print("   No se encontró información en BD")

print("\n=== Fin de la prueba ===")