from django.urls import path
from . import views
from .views import *
urlpatterns = [
   
    path('iniciar_sesion/', iniciar_sesion, name='iniciar_sesion'),
    path('validate-email/', validate_email, name='validate_email'),
    path('prueba/', prueba, name='prueba'),
    
    path('registrar_persona/',  registrar_persona, name='registrar_persona'),
    path('registrar_empresa/', registrar_empresa, name='registrar_empresa'),
    
    path('sucursal/', sucursalfuncion, name='sucursal'),
    path('editar_sucursal/', editar_sucursal, name='editar_sucursal'),
    path('eliminar_sucursal/', eliminar_sucursal, name='eliminar_sucursal'),
    path('eliminar_todas_sucursales/', eliminar_todas_sucursales, name='eliminar_todas_sucursales'),    


    path('categoria_producto/', views.categoria_producto_funcion, name='categoria_producto_funcion'),
    path('categ_producto_config/', categ_producto_config_funcion, name='categ_producto_config_funcion'),
   

    path('producto/', producto_funcion, name='producto_funcion'),
    path('producto_config/', producto_config_funcion, name='producto_config_funcion'),
    path('editar_producto/', editar_producto, name='editar_producto'),
    path('eliminar_producto/', eliminar_producto, name='eliminar_producto'),



    path('categoria_servicio/', categoria_servicio_funcion, name='categoria_servicio'),
    path('categ_servicio_config/', categ_servicio_config_funcion, name='categ_servicio_config_funcion'),



    path('servicio/', servicio_funcion, name='servicio_funcion'),
    path('servicio_config/', servicio_config_funcion, name='servicio_config_funcion'),




    path('eliminar_categoria_servicio/', eliminar_categoria_servicio_funcion, name='eliminar_categoria_servicio_funcion'),
    path('eliminar_categoria_producto/', eliminar_categoria_producto, name='eliminar_categoria_producto'),
    path('editar_categoria_producto/', editar_categoria_producto, name='editar_categoria_producto'),



] 