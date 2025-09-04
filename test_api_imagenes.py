import os
import django
import sys

# Configurar Django
sys.path.append('c:\\GitHub\\MainProject-')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from ecommerce_app.models import producto_empresa, producto_usuario, imagen_producto_empresa, imagen_producto_usuario
from django.test import RequestFactory
from ecommerce_app.views import api_obtener_imagenes_producto

def test_api_imagenes():
    print("=== TESTING API OBTENER IMAGENES PRODUCTO ===")
    
    # Crear factory para requests
    factory = RequestFactory()
    
    # Obtener algunos productos de prueba
    productos_empresa = producto_empresa.objects.all()[:3]
    productos_usuario = producto_usuario.objects.all()[:3]
    
    print(f"\nProductos empresa encontrados: {productos_empresa.count()}")
    print(f"Productos usuario encontrados: {productos_usuario.count()}")
    
    # Probar con productos de empresa
    for producto in productos_empresa:
        print(f"\n--- Probando producto empresa ID: {producto.id_producto_empresa} ---")
        print(f"Nombre: {producto.nombre_producto_empresa}")
        
        # Verificar imágenes en BD
        imagenes_bd = imagen_producto_empresa.objects.filter(id_producto_fk=producto.id_producto_empresa)
        print(f"Imágenes en BD: {imagenes_bd.count()}")
        
        for img in imagenes_bd:
            print(f"  - Imagen ID: {img.id_imagen_producto_empresa}")
            print(f"    Ruta: {img.ruta_imagen_producto_empresa}")
            print(f"    Existe archivo: {img.ruta_imagen_producto_empresa and os.path.exists(img.ruta_imagen_producto_empresa.path) if img.ruta_imagen_producto_empresa else False}")
        
        # Probar API
        request = factory.get(f'/ecommerce/api/obtener_imagenes_producto/?id_producto_empresa={producto.id_producto_empresa}')
        response = api_obtener_imagenes_producto(request)
        
        print(f"Status Code: {response.status_code}")
        if hasattr(response, 'content'):
            import json
            try:
                data = json.loads(response.content.decode('utf-8'))
                print(f"Response: {data}")
            except:
                print(f"Raw content: {response.content}")
    
    # Probar con productos de usuario
    for producto in productos_usuario:
        print(f"\n--- Probando producto usuario ID: {producto.id_producto_usuario} ---")
        print(f"Nombre: {producto.nombre_producto_usuario}")
        
        # Verificar imágenes en BD
        imagenes_bd = imagen_producto_usuario.objects.filter(id_producto_fk=producto.id_producto_usuario)
        print(f"Imágenes en BD: {imagenes_bd.count()}")
        
        for img in imagenes_bd:
            print(f"  - Imagen ID: {img.id_imagen_producto_usuario}")
            print(f"    Ruta: {img.ruta_imagen_producto_usuario}")
            print(f"    Existe archivo: {img.ruta_imagen_producto_usuario and os.path.exists(img.ruta_imagen_producto_usuario.path) if img.ruta_imagen_producto_usuario else False}")
        
        # Probar API
        request = factory.get(f'/ecommerce/api/obtener_imagenes_producto/?id_producto_usuario={producto.id_producto_usuario}')
        response = api_obtener_imagenes_producto(request)
        
        print(f"Status Code: {response.status_code}")
        if hasattr(response, 'content'):
            import json
            try:
                data = json.loads(response.content.decode('utf-8'))
                print(f"Response: {data}")
            except:
                print(f"Raw content: {response.content}")

if __name__ == '__main__':
    test_api_imagenes()