#!/usr/bin/env python3
"""
Script de diagnóstico para encontrar por qué no se encuentran laptops con 8GB RAM
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from ecommerce_app.models import AtributoProducto, ValorAtributoProducto, producto_usuario, producto_empresa
from chatbot.database_service import DatabaseService
from django.db.models import Q

def debug_eav_structure():
    """Diagnostica la estructura EAV actual"""
    print("=== DIAGNÓSTICO DE ESTRUCTURA EAV ===")
    
    # 1. Verificar qué atributos existen
    print("\n1. Atributos disponibles en la base de datos:")
    atributos = AtributoProducto.objects.all()
    for attr in atributos:
        print(f"   - {attr.nombre} ({attr.tipo_dato}) - {attr.descripcion}")
    
    if not atributos:
        print("   ❌ NO HAY ATRIBUTOS EAV CONFIGURADOS")
        return False
    
    # 2. Buscar atributos relacionados con RAM/memoria
    print("\n2. Atributos relacionados con RAM/memoria:")
    ram_attrs = AtributoProducto.objects.filter(
        Q(nombre__icontains='ram') |
        Q(nombre__icontains='memoria') |
        Q(descripcion__icontains='ram') |
        Q(descripcion__icontains='memoria')
    )
    
    for attr in ram_attrs:
        print(f"   ✅ {attr.nombre} ({attr.tipo_dato}) - {attr.descripcion}")
        
        # Ver valores de este atributo
        valores = ValorAtributoProducto.objects.filter(atributo=attr)[:5]
        print(f"      Valores ejemplo:")
        for valor in valores:
            val_texto = valor.valor_texto or valor.valor_numero or valor.valor_decimal or "N/A"
            print(f"        - {val_texto}")
    
    if not ram_attrs:
        print("   ❌ NO HAY ATRIBUTOS DE RAM/MEMORIA")
    
    # 3. Buscar productos con laptops
    print("\n3. Productos que contienen 'laptop':")
    productos_laptop_usuario = producto_usuario.objects.filter(
        Q(nombre_producto_usuario__icontains='laptop') |
        Q(descripcion_producto_usuario__icontains='laptop')
    )[:3]
    
    productos_laptop_empresa = producto_empresa.objects.filter(
        Q(nombre_producto_empresa__icontains='laptop') |
        Q(descripcion_producto_empresa__icontains='laptop')
    )[:3]
    
    print(f"   Productos de usuario con 'laptop': {productos_laptop_usuario.count()}")
    for prod in productos_laptop_usuario:
        print(f"     - {prod.nombre_producto_usuario}")
        # Ver sus atributos EAV
        valores_eav = ValorAtributoProducto.objects.filter(producto_usuario=prod)
        for val in valores_eav:
            val_texto = val.valor_texto or val.valor_numero or val.valor_decimal
            print(f"       {val.atributo.nombre}: {val_texto}")
    
    print(f"   Productos de empresa con 'laptop': {productos_laptop_empresa.count()}")
    for prod in productos_laptop_empresa:
        print(f"     - {prod.nombre_producto_empresa}")
        # Ver sus atributos EAV
        valores_eav = ValorAtributoProducto.objects.filter(producto_empresa=prod)
        for val in valores_eav:
            val_texto = val.valor_texto or val.valor_numero or val.valor_decimal
            print(f"       {val.atributo.nombre}: {val_texto}")
    
    return True

def debug_search_process():
    """Diagnostica el proceso de búsqueda paso a paso"""
    print("\n=== DIAGNÓSTICO DEL PROCESO DE BÚSQUEDA ===")
    
    db_service = DatabaseService()
    consulta = "necesito una laptop de 8gb de ram"
    
    print(f"\n4. Procesando consulta: '{consulta}'")
    
    # Paso 1: Detectar atributos
    atributos_detectados = db_service._detectar_atributos_en_mensaje(consulta)
    print(f"   Atributos detectados: {atributos_detectados}")
    
    # Paso 2: Expandir términos
    terminos_expandidos = db_service.search_intelligence.expandir_terminos_busqueda(consulta)
    print(f"   Términos expandidos: {terminos_expandidos[:10]}...")
    
    # Paso 3: Búsqueda tradicional
    print("\n   Búsqueda tradicional por nombre/descripción:")
    productos_tradicional = []
    
    # Productos de usuario
    query_usuario = Q()
    for termino in ['laptop', 'laptops']:
        query_usuario |= Q(nombre_producto_usuario__icontains=termino) | Q(descripcion_producto_usuario__icontains=termino)
    
    productos_usuario = producto_usuario.objects.filter(
        query_usuario,
        estatus_producto_usuario='Activo'
    )
    print(f"     Productos de usuario encontrados: {productos_usuario.count()}")
    
    # Productos de empresa
    query_empresa = Q()
    for termino in ['laptop', 'laptops']:
        query_empresa |= Q(nombre_producto_empresa__icontains=termino) | Q(descripcion_producto_empresa__icontains=termino)
    
    productos_empresa = producto_empresa.objects.filter(query_empresa)
    print(f"     Productos de empresa encontrados: {productos_empresa.count()}")
    
    # Paso 4: Búsqueda EAV
    if atributos_detectados:
        print(f"\n   Búsqueda EAV con atributos: {atributos_detectados}")
        productos_eav = db_service.buscar_productos_por_atributos_eav(atributos_detectados, limite=10)
        print(f"     Productos encontrados por EAV: {len(productos_eav)}")
        for prod in productos_eav[:3]:
            print(f"       - {prod['nombre']} (coincidencia: {prod.get('coincidencia_eav', 'N/A')})")
    
    # Paso 5: Búsqueda completa
    print(f"\n   Búsqueda completa:")
    productos_completos = db_service.buscar_productos(consulta, limite=5)
    print(f"     Total productos encontrados: {len(productos_completos)}")
    
    for i, prod in enumerate(productos_completos, 1):
        print(f"     {i}. {prod['nombre']} - ${prod['precio']}")
        atributos = prod.get('atributos', {})
        if atributos:
            attrs_ram = {k: v for k, v in atributos.items() if 'ram' in k.lower() or 'memoria' in k.lower()}
            if attrs_ram:
                print(f"        RAM/Memoria: {attrs_ram}")
            else:
                print(f"        Atributos: {list(atributos.keys())[:5]}")
        else:
            print(f"        Sin atributos EAV")

def debug_manual_eav_search():
    """Búsqueda manual directa en tablas EAV"""
    print("\n=== BÚSQUEDA MANUAL DIRECTA EN EAV ===")
    
    # Buscar valores que contengan "8gb" o "8"
    print("\n5. Búsqueda directa de valores con '8gb' o '8':")
    
    valores_8gb = ValorAtributoProducto.objects.filter(
        Q(valor_texto__icontains='8gb') |
        Q(valor_texto__icontains='8 gb') |
        Q(valor_numero=8) |
        Q(valor_texto__icontains='8')
    ).select_related('atributo')
    
    print(f"   Valores encontrados con '8gb/8': {valores_8gb.count()}")
    
    for valor in valores_8gb:
        val_texto = valor.valor_texto or valor.valor_numero or valor.valor_decimal
        print(f"     - Atributo: {valor.atributo.nombre}, Valor: {val_texto}")
        
        if valor.producto_usuario_id:
            try:
                prod = producto_usuario.objects.get(id_producto_usuario=valor.producto_usuario_id)
                print(f"       Producto usuario: {prod.nombre_producto_usuario}")
            except:
                print(f"       Producto usuario ID: {valor.producto_usuario_id} (no encontrado)")
        
        if valor.producto_empresa_id:
            try:
                prod = producto_empresa.objects.get(id_producto_empresa=valor.producto_empresa_id)
                print(f"       Producto empresa: {prod.nombre_producto_empresa}")
            except:
                print(f"       Producto empresa ID: {valor.producto_empresa_id} (no encontrado)")

def main():
    """Función principal de diagnóstico"""
    print("DIAGNÓSTICO COMPLETO: ¿POR QUÉ NO SE ENCUENTRAN LAPTOPS CON 8GB RAM?")
    print("=" * 80)
    
    try:
        # Verificar estructura EAV
        eav_exists = debug_eav_structure()
        
        if eav_exists:
            # Diagnosticar proceso de búsqueda
            debug_search_process()
            
            # Búsqueda manual directa
            debug_manual_eav_search()
        
        print("\n" + "=" * 80)
        print("POSIBLES CAUSAS DEL PROBLEMA:")
        print("1. ❓ No hay atributos EAV configurados para RAM/memoria")
        print("2. ❓ Los valores de RAM están en formato diferente (ej: '8 GB' vs '8gb')")
        print("3. ❓ Los productos no tienen atributos EAV asignados")
        print("4. ❓ La búsqueda EAV no está funcionando correctamente")
        print("5. ❓ Los productos con RAM están inactivos o no existen")
        
        print("\nSOLUCIONES SUGERIDAS:")
        print("• Verificar que existan atributos EAV para 'RAM' o 'memoria'")
        print("• Revisar el formato de los valores de RAM en la base de datos")
        print("• Asegurar que los productos tengan valores EAV asignados")
        print("• Probar búsqueda directa en las tablas EAV")
        
    except Exception as e:
        print(f"\nERROR EN EL DIAGNÓSTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
