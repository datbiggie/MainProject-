#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append('MainProject-')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import pedido_usuario, pedido_empresa, detalle_pedido_usuario, detalle_pedido_empresa

print("=== DEBUG PEDIDOS CONFIRMADOS ===")
print()

# Verificar pedidos de usuario
print("PEDIDOS DE USUARIO:")
pedidos_usuario_todos = pedido_usuario.objects.all()
print(f"Total pedidos de usuario: {pedidos_usuario_todos.count()}")

for pedido in pedidos_usuario_todos:
    print(f"  - Pedido #{pedido.numero_pedido} | Estado: {pedido.estado_pedido} | Usuario: {pedido.id_carrito_fk.id_usuario_fk.nombre_usuario if pedido.id_carrito_fk and pedido.id_carrito_fk.id_usuario_fk else 'N/A'}")

pedidos_usuario_confirmados = pedido_usuario.objects.filter(estado_pedido='confirmado')
print(f"Pedidos de usuario confirmados: {pedidos_usuario_confirmados.count()}")

print()

# Verificar pedidos de empresa
print("PEDIDOS DE EMPRESA:")
pedidos_empresa_todos = pedido_empresa.objects.all()
print(f"Total pedidos de empresa: {pedidos_empresa_todos.count()}")

for pedido in pedidos_empresa_todos:
    print(f"  - Pedido #{pedido.numero_pedido} | Estado: {pedido.estado_pedido} | Empresa: {pedido.id_carrito_fk.id_empresa_fk.nombre_empresa if pedido.id_carrito_fk and pedido.id_carrito_fk.id_empresa_fk else 'N/A'}")

pedidos_empresa_confirmados = pedido_empresa.objects.filter(estado_pedido='confirmado')
print(f"Pedidos de empresa confirmados: {pedidos_empresa_confirmados.count()}")

print()
print("=== ESTADOS DISPONIBLES ===")
print("Estados de pedido_usuario:", [choice[0] for choice in pedido_usuario.ESTADO_CHOICES])
print("Estados de pedido_empresa:", [choice[0] for choice in pedido_empresa.ESTADO_CHOICES])

print()
print("=== RESUMEN ===")
print(f"Total pedidos confirmados: {pedidos_usuario_confirmados.count() + pedidos_empresa_confirmados.count()}")