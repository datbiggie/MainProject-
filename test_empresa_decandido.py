#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import empresa
from chatbot.database_service import DatabaseService
from chatbot.gemini_service import GeminiService

print("=== Verificando empresa 'Decandido' ===")

# Buscar directamente en la base de datos
print("\n1. Búsqueda directa en la base de datos:")
empresas_decandido = empresa.objects.filter(nombre_empresa__icontains='Decandido')
print(f"Empresas encontradas con 'Decandido': {empresas_decandido.count()}")

for emp in empresas_decandido:
    print(f"  - ID: {emp.id_empresa}")
    print(f"  - Nombre: {emp.nombre_empresa}")
    print(f"  - Email: {emp.correo_empresa}")
    print(f"  - Descripción: {emp.descripcion_empresa}")
    print(f"  - Fecha registro: {emp.fecha_registro_empresa}")
    print()

# Probar con DatabaseService
print("\n2. Prueba con DatabaseService:")
db_service = DatabaseService()
resultado_busqueda = db_service.buscar_empresas('Decandido')
print(f"Resultado de buscar_empresas('Decandido'): {len(resultado_busqueda)} empresas")
for emp in resultado_busqueda:
    print(f"  - {emp['nombre']} (ID: {emp['id']})")

# Probar búsqueda específica
print("\n3. Prueba con buscar_empresa específica:")
resultado_especifico = db_service.buscar_empresa('Decandido')
if resultado_especifico:
    print(f"Empresa encontrada: {resultado_especifico['nombre']}")
    print(f"Email: {resultado_especifico['email']}")
else:
    print("No se encontró la empresa específica")

# Probar extracción de criterio
print("\n4. Prueba de extracción de criterio:")
gemini_service = GeminiService()
criterio = gemini_service._extraer_criterio_busqueda_empresa("busca la empresa Decandido")
print(f"Criterio extraído de 'busca la empresa Decandido': '{criterio}'")

# Listar todas las empresas para verificar
print("\n5. Todas las empresas registradas:")
todas_empresas = empresa.objects.all()
print(f"Total de empresas: {todas_empresas.count()}")
for emp in todas_empresas:
    print(f"  - {emp.nombre_empresa} (ID: {emp.id_empresa})")

print("\n=== Fin de la verificación ===")