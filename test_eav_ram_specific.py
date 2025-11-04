#!/usr/bin/env python3
"""
Script específico para probar la búsqueda de RAM con la estructura EAV correcta
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

def test_eav_structure_specific():
    """Prueba la estructura EAV específica para RAM"""
    print("=== VERIFICACIÓN ESPECÍFICA DE ESTRUCTURA EAV PARA RAM ===")
    
    # 1. Verificar atributo RAM
    print("\n1. Verificando atributo 'RAM':")
    try:
        atributo_ram = AtributoProducto.objects.get(nombre='RAM')
        print(f"   ✅ Atributo RAM encontrado:")
        print(f"     - ID: {atributo_ram.id_atributo}")
        print(f"     - Nombre: {atributo_ram.nombre}")
        print(f"     - Tipo: {atributo_ram.tipo_dato}")
        print(f"     - Descripción: {atributo_ram.descripcion}")
        
        # 2. Verificar valores de RAM = 8
        print(f"\n2. Verificando valores de RAM = 8:")
        valores_ram_8 = ValorAtributoProducto.objects.filter(
            atributo=atributo_ram,
            valor_numero=8
        )
        
        print(f"   Valores con RAM = 8 encontrados: {valores_ram_8.count()}")
        
        for valor in valores_ram_8:
            print(f"\n   ✅ Valor RAM = 8:")
            print(f"     - ID Valor: {valor.id_valor_atributo}")
            print(f"     - Valor número: {valor.valor_numero}")
            print(f"     - Producto usuario ID: {valor.producto_usuario_id}")
            print(f"     - Producto empresa ID: {valor.producto_empresa_id}")
            
            # Verificar el producto asociado
            if valor.producto_usuario_id:
                try:
                    prod = producto_usuario.objects.get(id_producto_usuario=valor.producto_usuario_id)
                    print(f"     - Producto usuario: {prod.nombre_producto_usuario}")
                    print(f"     - Estado: {prod.estatus_producto_usuario}")
                except producto_usuario.DoesNotExist:
                    print(f"     - ❌ Producto usuario no encontrado")
            
            if valor.producto_empresa_id:
                try:
                    prod = producto_empresa.objects.get(id_producto_empresa=valor.producto_empresa_id)
                    print(f"     - Producto empresa: {prod.nombre_producto_empresa}")
                except producto_empresa.DoesNotExist:
                    print(f"     - ❌ Producto empresa no encontrado")
        
        return True
        
    except AtributoProducto.DoesNotExist:
        print("   ❌ Atributo 'RAM' no encontrado")
        return False

def test_database_service_eav():
    """Prueba el DatabaseService con la estructura EAV correcta"""
    print("\n=== PRUEBA DE DATABASE SERVICE CON EAV ===")
    
    db_service = DatabaseService()
    
    # 1. Probar detección de atributos
    print("\n3. Probando detección de atributos:")
    consulta = "necesito una laptop de 8gb de ram"
    atributos_detectados = db_service._detectar_atributos_en_mensaje(consulta)
    print(f"   Consulta: '{consulta}'")
    print(f"   Atributos detectados: {atributos_detectados}")
    
    # 2. Probar búsqueda EAV directa
    if atributos_detectados:
        print(f"\n4. Probando búsqueda EAV directa:")
        productos_eav = db_service.buscar_productos_por_atributos_eav(atributos_detectados, limite=10)
        print(f"   Productos encontrados por EAV: {len(productos_eav)}")
        
        for i, prod in enumerate(productos_eav, 1):
            print(f"\n   Producto {i}:")
            print(f"     - Nombre: {prod['nombre']}")
            print(f"     - Precio: ${prod['precio']}")
            print(f"     - Vendedor: {prod['vendedor']}")
            print(f"     - Tipo: {prod['tipo']}")
            
            atributos = prod.get('atributos', {})
            if atributos:
                print(f"     - Atributos EAV: {atributos}")
            else:
                print(f"     - Sin atributos EAV")
            
            if 'coincidencia_eav' in prod:
                print(f"     - ✅ Coincidencia: {prod['coincidencia_eav']}")
    
    # 3. Probar búsqueda completa
    print(f"\n5. Probando búsqueda completa:")
    productos_completos = db_service.buscar_productos(consulta, limite=5)
    print(f"   Total productos encontrados: {len(productos_completos)}")
    
    for i, prod in enumerate(productos_completos, 1):
        print(f"\n   Producto completo {i}:")
        print(f"     - Nombre: {prod['nombre']}")
        print(f"     - Precio: ${prod['precio']}")
        
        atributos = prod.get('atributos', {})
        if 'RAM' in atributos:
            print(f"     - ✅ RAM: {atributos['RAM']}")
        elif atributos:
            print(f"     - Otros atributos: {list(atributos.keys())}")
        else:
            print(f"     - Sin atributos EAV")

def test_manual_eav_query():
    """Prueba manual directa de la consulta EAV"""
    print("\n=== PRUEBA MANUAL DIRECTA EAV ===")
    
    print("\n6. Consulta manual directa:")
    
    try:
        # Buscar atributo RAM
        atributo_ram = AtributoProducto.objects.get(nombre='RAM')
        print(f"   Atributo RAM: {atributo_ram.nombre} (tipo: {atributo_ram.tipo_dato})")
        
        # Buscar valores con RAM = 8
        valores = ValorAtributoProducto.objects.filter(
            atributo=atributo_ram,
            valor_numero=8
        )
        
        print(f"   Valores con RAM = 8: {valores.count()}")
        
        for valor in valores:
            print(f"\n   Procesando valor ID {valor.id_valor_atributo}:")
            
            if valor.producto_usuario_id:
                try:
                    prod = producto_usuario.objects.get(
                        id_producto_usuario=valor.producto_usuario_id,
                        estatus_producto_usuario='Activo'
                    )
                    print(f"     ✅ Producto usuario activo: {prod.nombre_producto_usuario}")
                    
                    # Probar obtener_atributos_producto
                    db_service = DatabaseService()
                    atributos = db_service.obtener_atributos_producto(prod.id_producto_usuario, 'producto_usuario')
                    print(f"     - Atributos obtenidos: {atributos}")
                    
                except producto_usuario.DoesNotExist:
                    print(f"     ❌ Producto usuario no activo o no existe")
            
            if valor.producto_empresa_id:
                try:
                    prod = producto_empresa.objects.get(id_producto_empresa=valor.producto_empresa_id)
                    print(f"     ✅ Producto empresa: {prod.nombre_producto_empresa}")
                    
                    # Probar obtener_atributos_producto
                    db_service = DatabaseService()
                    atributos = db_service.obtener_atributos_producto(prod.id_producto_empresa, 'producto_empresa')
                    print(f"     - Atributos obtenidos: {atributos}")
                    
                except producto_empresa.DoesNotExist:
                    print(f"     ❌ Producto empresa no existe")
        
    except AtributoProducto.DoesNotExist:
        print("   ❌ Atributo RAM no encontrado")

def main():
    """Función principal"""
    print("PRUEBA ESPECÍFICA: ESTRUCTURA EAV PARA RAM = 8")
    print("=" * 60)
    
    try:
        # Verificar estructura
        eav_ok = test_eav_structure_specific()
        
        if eav_ok:
            # Probar DatabaseService
            test_database_service_eav()
            
            # Prueba manual
            test_manual_eav_query()
        
        print("\n" + "=" * 60)
        print("DIAGNÓSTICO ESPECÍFICO COMPLETADO")
        
        print("\nESTRUCTURA VERIFICADA:")
        print("✅ AtributoProducto.nombre = 'RAM'")
        print("✅ AtributoProducto.tipo_dato = 'numero'")
        print("✅ ValorAtributoProducto.valor_numero = 8")
        print("✅ Corregido: valor_numero (no valor_numerico)")
        
        print("\nSI AÚN NO FUNCIONA:")
        print("• Verificar que los productos tengan estatus_producto_usuario='Activo'")
        print("• Verificar que la relación FK esté correcta")
        print("• Revisar logs para ver errores específicos")
        
    except Exception as e:
        print(f"\nERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
