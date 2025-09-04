import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import producto_usuario

# Buscar un producto sin coordenadas
producto_sin_coords = producto_usuario.objects.filter(
    latitud_entrega_producto__isnull=True,
    longitud_entrega_producto__isnull=True
).first()

if producto_sin_coords:
    print(f"Producto encontrado sin coordenadas:")
    print(f"ID: {producto_sin_coords.id_producto_usuario}")
    print(f"Nombre: {producto_sin_coords.nombre_producto_usuario}")
    print(f"Latitud: {producto_sin_coords.latitud_entrega_producto}")
    print(f"Longitud: {producto_sin_coords.longitud_entrega_producto}")
    print(f"\nURL para editar: http://127.0.0.1:8000/ecommerce/producto_config/?producto_id={producto_sin_coords.id_producto_usuario}")
    print("\nInstrucciones:")
    print("1. Abre la URL en el navegador")
    print("2. Haz clic en 'Editar' en el producto mostrado")
    print("3. Abre las herramientas de desarrollador (F12)")
    print("4. Ve a la pestaña 'Console'")
    print("5. Deberías ver los mensajes de debug y el mensaje de advertencia")
else:
    print("No se encontraron productos sin coordenadas")
    # Crear un producto de prueba sin coordenadas
    from ecommerce_app.models import categoria_producto_usuario, usuario
    
    categoria = categoria_producto_usuario.objects.first()
    usuario_obj = usuario.objects.first()
    if categoria and usuario_obj:
        nuevo_producto = producto_usuario.objects.create(
            nombre_producto_usuario="Producto Test Sin Coordenadas",
            descripcion_producto_usuario="Producto de prueba para verificar mensaje de advertencia",
            precio_producto_usuario=100.00,
            id_categoria_prod_fk=categoria,
            id_usuario_fk=usuario_obj,
            latitud_entrega_producto=None,
            longitud_entrega_producto=None
        )
        print(f"Producto de prueba creado:")
        print(f"ID: {nuevo_producto.id_producto_usuario}")
        print(f"Nombre: {nuevo_producto.nombre_producto_usuario}")
        print(f"URL para editar: http://127.0.0.1:8000/ecommerce/producto_config/?producto_id={nuevo_producto.id_producto_usuario}")
    else:
        print("No se pudo crear producto de prueba - no hay categorías o usuarios disponibles")