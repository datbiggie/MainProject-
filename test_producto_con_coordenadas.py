import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import producto_usuario

# Buscar un producto CON coordenadas
producto_con_coords = producto_usuario.objects.filter(
    latitud_entrega_producto__isnull=False,
    longitud_entrega_producto__isnull=False
).exclude(
    latitud_entrega_producto='',
    longitud_entrega_producto=''
).first()

if producto_con_coords:
    print(f"Producto encontrado CON coordenadas:")
    print(f"ID: {producto_con_coords.id_producto_usuario}")
    print(f"Nombre: {producto_con_coords.nombre_producto_usuario}")
    print(f"Latitud: {producto_con_coords.latitud_entrega_producto}")
    print(f"Longitud: {producto_con_coords.longitud_entrega_producto}")
    print(f"\nURL para editar: http://127.0.0.1:8000/ecommerce/producto_config/?producto_id={producto_con_coords.id_producto_usuario}")
    print("\nInstrucciones:")
    print("1. Abre la URL en el navegador")
    print("2. Haz clic en 'Editar' en el producto mostrado")
    print("3. Abre las herramientas de desarrollador (F12)")
    print("4. Ve a la pestaña 'Console'")
    print("5. NO deberías ver el mensaje de advertencia, solo el mapa con la ubicación")
else:
    print("No se encontraron productos con coordenadas válidas")
    
    # Mostrar algunos productos para debug
    productos = producto_usuario.objects.all()[:5]
    print("\nPrimeros 5 productos en la base de datos:")
    for prod in productos:
        print(f"ID: {prod.id_producto_usuario}, Nombre: {prod.nombre_producto_usuario}")
        print(f"  Lat: {prod.latitud_entrega_producto}, Lng: {prod.longitud_entrega_producto}")