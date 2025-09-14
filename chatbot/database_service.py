from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth.models import User
from ecommerce_app.models import (
    usuario, empresa, producto_usuario, producto_empresa, producto_sucursal,
    servicio_usuario, servicio_empresa, servicio_sucursal,
    categoria_producto_usuario, categoria_producto_empresa,
    categoria_servicio_usuario, categoria_servicio_empresa,
    carrito_compra_producto_usuario, carrito_compra_producto_empresa,
    pedido_usuario, pedido_empresa, detalle_pedido_usuario, detalle_pedido_empresa,
    favorito_usuario, favorito_empresa_sucursal,
    sucursal, imagen_producto_empresa, imagen_producto_usuario
)
import logging
import math

logger = logging.getLogger(__name__)

class DatabaseService:
    """Servicio para consultar información de la base de datos del ecommerce"""
    
    def __init__(self):
        pass
    
    def calcular_distancia_haversine(self, lat1, lon1, lat2, lon2):
        """Calcula la distancia entre dos puntos usando la fórmula de Haversine"""
        if not all([lat1, lon1, lat2, lon2]):
            return float('inf')  # Retorna infinito si faltan coordenadas
        
        # Convertir grados a radianes
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radio de la Tierra en kilómetros
        r = 6371
        
        return c * r
    
    # ===== MÉTODOS DE BÚSQUEDA DE PRODUCTOS =====
    
    def buscar_productos(self, termino_busqueda, limite=10):
        """Busca productos por nombre o descripción"""
        try:
            # Dividir términos de búsqueda para búsqueda más flexible
            terminos = termino_busqueda.split()
            
            # Construir query para productos de usuario
            query_usuario = Q()
            for termino in terminos:
                query_usuario |= Q(nombre_producto_usuario__icontains=termino) | Q(descripcion_producto_usuario__icontains=termino)
            
            productos_usuario = producto_usuario.objects.filter(
                query_usuario,
                estatus_producto_usuario='Activo'
            )[:limite//2]
            
            # Construir query para productos de empresa
            query_empresa = Q()
            for termino in terminos:
                query_empresa |= Q(nombre_producto_empresa__icontains=termino) | Q(descripcion_producto_empresa__icontains=termino)
            
            productos_empresa = producto_empresa.objects.filter(
                query_empresa
            )[:limite//2]
            
            resultados = []
            
            for prod in productos_usuario:
                resultados.append({
                    'tipo': 'producto_usuario',
                    'id': prod.id_producto_usuario,
                    'nombre': prod.nombre_producto_usuario,
                    'descripcion': prod.descripcion_producto_usuario,
                    'precio': float(prod.precio_producto_usuario),
                    'stock': prod.stock_producto_usuario,
                    'vendedor': prod.id_usuario_fk.nombre_usuario,
                    'condicion': prod.condicion_producto_usuario,
                    'latitud': float(prod.latitud_entrega_producto) if prod.latitud_entrega_producto else None,
                    'longitud': float(prod.longitud_entrega_producto) if prod.longitud_entrega_producto else None
                })
            
            for prod in productos_empresa:
                # Obtener información de sucursales
                sucursales = producto_sucursal.objects.filter(
                    id_producto_fk=prod,
                    estatus_producto_sucursal='Activo'
                )
                for suc_prod in sucursales:
                    resultados.append({
                        'tipo': 'producto_empresa',
                        'id': suc_prod.id_producto_sucursal,
                        'nombre': prod.nombre_producto_empresa,
                        'descripcion': prod.descripcion_producto_empresa,
                        'precio': float(suc_prod.precio_producto_sucursal),
                        'stock': suc_prod.stock_producto_sucursal,
                        'vendedor': prod.id_empresa_fk.nombre_empresa,
                        'sucursal': suc_prod.id_sucursal_fk.nombre_sucursal,
                        'condicion': suc_prod.condicion_producto_sucursal,
                        'latitud': float(suc_prod.id_sucursal_fk.latitud_sucursal) if suc_prod.id_sucursal_fk.latitud_sucursal else None,
                        'longitud': float(suc_prod.id_sucursal_fk.longitud_sucursal) if suc_prod.id_sucursal_fk.longitud_sucursal else None
                    })
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar productos: {e}")
            return []
    
    def buscar_productos_cercanos(self, lat_usuario, lon_usuario, radio_km=10, limite=10):
        """Busca productos cercanos a la ubicación del usuario"""
        try:
            # Buscar productos de usuario
            productos_usuario = producto_usuario.objects.filter(
                estatus_producto_usuario='Activo',
                latitud_entrega_producto__isnull=False,
                longitud_entrega_producto__isnull=False
            )
            
            # Buscar productos de empresa (a través de sucursales)
            productos_empresa = producto_sucursal.objects.filter(
                estatus_producto_sucursal='Activo',
                id_sucursal_fk__latitud_sucursal__isnull=False,
                id_sucursal_fk__longitud_sucursal__isnull=False
            ).select_related('id_producto_fk', 'id_sucursal_fk')
            
            resultados = []
            
            # Procesar productos de usuario
            for prod in productos_usuario:
                distancia = self.calcular_distancia_haversine(
                    lat_usuario, lon_usuario,
                    float(prod.latitud_entrega_producto),
                    float(prod.longitud_entrega_producto)
                )
                
                if distancia <= radio_km:
                    resultados.append({
                        'tipo': 'producto_usuario',
                        'id': prod.id_producto_usuario,
                        'nombre': prod.nombre_producto_usuario,
                        'descripcion': prod.descripcion_producto_usuario,
                        'precio': float(prod.precio_producto_usuario),
                        'stock': prod.stock_producto_usuario,
                        'vendedor': prod.id_usuario_fk.nombre_usuario,
                        'condicion': prod.condicion_producto_usuario,
                        'latitud': float(prod.latitud_entrega_producto),
                        'longitud': float(prod.longitud_entrega_producto),
                        'distancia_km': round(distancia, 2)
                    })
            
            # Procesar productos de empresa
            for suc_prod in productos_empresa:
                distancia = self.calcular_distancia_haversine(
                    lat_usuario, lon_usuario,
                    float(suc_prod.id_sucursal_fk.latitud_sucursal),
                    float(suc_prod.id_sucursal_fk.longitud_sucursal)
                )
                
                if distancia <= radio_km:
                    resultados.append({
                        'tipo': 'producto_empresa',
                        'id': suc_prod.id_producto_sucursal,
                        'nombre': suc_prod.id_producto_fk.nombre_producto_empresa,
                        'descripcion': suc_prod.id_producto_fk.descripcion_producto_empresa,
                        'precio': float(suc_prod.precio_producto_sucursal),
                        'stock': suc_prod.stock_producto_sucursal,
                        'vendedor': suc_prod.id_producto_fk.id_empresa_fk.nombre_empresa,
                        'sucursal': suc_prod.id_sucursal_fk.nombre_sucursal,
                        'condicion': suc_prod.condicion_producto_sucursal,
                        'latitud': float(suc_prod.id_sucursal_fk.latitud_sucursal),
                        'longitud': float(suc_prod.id_sucursal_fk.longitud_sucursal),
                        'distancia_km': round(distancia, 2)
                    })
            
            # Ordenar por distancia
            resultados.sort(key=lambda x: x['distancia_km'])
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar productos cercanos: {e}")
            return []
    
    def obtener_productos_por_categoria(self, categoria_nombre, limite=10):
        """Obtiene productos de una categoría específica"""
        try:
            resultados = []
            
            # Buscar en categorías de usuario
            categorias_usuario = categoria_producto_usuario.objects.filter(
                nombre_categoria_prod_usuario__icontains=categoria_nombre,
                estatus_categoria_prod_usuario='Activo'
            )
            
            for categoria in categorias_usuario:
                productos = producto_usuario.objects.filter(
                    id_categoria_prod_fk=categoria,
                    estatus_producto_usuario='Activo'
                )[:limite//2]
                
                for prod in productos:
                    resultados.append({
                        'tipo': 'producto_usuario',
                        'id': prod.id_producto_usuario,
                        'nombre': prod.nombre_producto_usuario,
                        'precio': float(prod.precio_producto_usuario),
                        'vendedor': prod.id_usuario_fk.nombre_usuario,
                        'categoria': categoria.nombre_categoria_prod_usuario
                    })
            
            # Buscar en categorías de empresa
            categorias_empresa = categoria_producto_empresa.objects.filter(
                nombre_categoria_prod_empresa__icontains=categoria_nombre,
                estatus_categoria_prod_empresa='Activo'
            )
            
            for categoria in categorias_empresa:
                productos = producto_empresa.objects.filter(
                    id_categoria_prod_fk=categoria
                )[:limite//2]
                
                for prod in productos:
                    sucursales = producto_sucursal.objects.filter(
                        id_producto_fk=prod,
                        estatus_producto_sucursal='Activo'
                    )
                    for suc_prod in sucursales:
                        resultados.append({
                            'tipo': 'producto_empresa',
                            'id': suc_prod.id_producto_sucursal,
                            'nombre': prod.nombre_producto_empresa,
                            'precio': float(suc_prod.precio_producto_sucursal),
                            'vendedor': prod.id_empresa_fk.nombre_empresa,
                            'sucursal': suc_prod.id_sucursal_fk.nombre_sucursal,
                            'categoria': categoria.nombre_categoria_prod_empresa
                        })
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al obtener productos por categoría: {e}")
            return []
    
    # ===== MÉTODOS DE INFORMACIÓN DE PEDIDOS =====
    
    def obtener_pedidos_usuario(self, usuario_email, estado=None, limite=10):
        """Obtiene los pedidos de un usuario específico"""
        try:
            # Buscar usuario por email
            usuario_obj = usuario.objects.filter(correo_usuario=usuario_email).first()
            if not usuario_obj:
                return []
            
            # Obtener carritos del usuario
            carritos = carrito_compra_producto_usuario.objects.filter(
                id_usuario_fk=usuario_obj
            )
            
            # Filtrar pedidos
            pedidos_query = pedido_usuario.objects.filter(
                id_carrito_fk__in=carritos
            )
            
            if estado:
                pedidos_query = pedidos_query.filter(estado_pedido=estado)
            
            pedidos = pedidos_query.order_by('-fecha_pedido')[:limite]
            
            resultados = []
            for pedido in pedidos:
                detalles = detalle_pedido_usuario.objects.filter(id_pedido_fk=pedido)
                
                productos = []
                for detalle in detalles:
                    if detalle.idproducto_fk_usuario:
                        productos.append({
                            'nombre': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                            'cantidad': detalle.cantidad_detalle_pedido,
                            'precio_unitario': float(detalle.precio_unitario_pedido),
                            'subtotal': float(detalle.subtotal_detalle_pedido)
                        })
                    elif detalle.id_fk_producto_sucursal_empresa:
                        productos.append({
                            'nombre': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                            'cantidad': detalle.cantidad_detalle_pedido,
                            'precio_unitario': float(detalle.precio_unitario_pedido),
                            'subtotal': float(detalle.subtotal_detalle_pedido),
                            'empresa': detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa
                        })
                
                resultados.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha': pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M'),
                    'estado': pedido.estado_pedido,
                    'total': float(pedido.total_pedido),
                    'direccion_envio': pedido.direccion_envio,
                    'metodo_pago': pedido.metodo_pago,
                    'productos': productos,
                    'notas': pedido.notas_pedido
                })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error al obtener pedidos del usuario: {e}")
            return []
    
    def obtener_estadisticas_pedidos_usuario(self, usuario_email):
        """Obtiene estadísticas de pedidos de un usuario"""
        try:
            usuario_obj = usuario.objects.filter(correo_usuario=usuario_email).first()
            if not usuario_obj:
                return {}
            
            carritos = carrito_compra_producto_usuario.objects.filter(
                id_usuario_fk=usuario_obj
            )
            
            pedidos = pedido_usuario.objects.filter(id_carrito_fk__in=carritos)
            
            stats = {
                'total_pedidos': pedidos.count(),
                'pedidos_pendientes': pedidos.filter(estado_pedido='pendiente').count(),
                'pedidos_confirmados': pedidos.filter(estado_pedido='confirmado').count(),
                'pedidos_entregados': pedidos.filter(estado_pedido='entregado').count(),
                'pedidos_cancelados': pedidos.filter(estado_pedido='cancelado').count(),
                'total_gastado': float(pedidos.aggregate(Sum('total_pedido'))['total_pedido__sum'] or 0),
                'promedio_pedido': float(pedidos.aggregate(Avg('total_pedido'))['total_pedido__avg'] or 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de pedidos: {e}")
            return {}
    
    # ===== MÉTODOS DE INFORMACIÓN DE CARRITO =====
    
    def obtener_carrito_usuario(self, usuario_email):
        """Obtiene el carrito activo de un usuario"""
        try:
            usuario_obj = usuario.objects.filter(correo_usuario=usuario_email).first()
            if not usuario_obj:
                return None
            
            carrito = carrito_compra_producto_usuario.objects.filter(
                id_usuario_fk=usuario_obj,
                estatuscarrito_prod_usuario='activo'
            ).first()
            
            if not carrito:
                return None
            
            from ecommerce_app.models import detalle_compra_producto_usuario
            detalles = detalle_compra_producto_usuario.objects.filter(
                id_fk_carritocompra_usuario=carrito
            )
            
            productos = []
            for detalle in detalles:
                if detalle.idproducto_fk_usuario:
                    productos.append({
                        'nombre': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'precio_unitario': float(detalle.precio_unit_deta_carrito_prod_usuario),
                        'subtotal': float(detalle.subtotal_deta_carrito_prod_usuario),
                        'tipo': 'producto_usuario'
                    })
                elif detalle.id_fk_producto_sucursal_empresa:
                    productos.append({
                        'nombre': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'precio_unitario': float(detalle.precio_unit_deta_carrito_prod_usuario),
                        'subtotal': float(detalle.subtotal_deta_carrito_prod_usuario),
                        'empresa': detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa,
                        'tipo': 'producto_empresa'
                    })
            
            return {
                'id_carrito': carrito.id_carrito_prod_usuario,
                'total': float(carrito.total_carrito_prod_usuario),
                'fecha_creacion': carrito.fecha_creacion_carrito_prod_usuario.strftime('%d/%m/%Y %H:%M'),
                'productos': productos,
                'cantidad_productos': len(productos)
            }
            
        except Exception as e:
            logger.error(f"Error al obtener carrito del usuario: {e}")
            return None
    
    # ===== MÉTODOS DE INFORMACIÓN DE EMPRESAS =====
    
    def buscar_empresas(self, termino_busqueda, limite=10):
        """Busca empresas por nombre o descripción"""
        try:
            empresas = empresa.objects.filter(
                Q(nombre_empresa__icontains=termino_busqueda) |
                Q(descripcion_empresa__icontains=termino_busqueda)
            )[:limite]
            
            resultados = []
            for emp in empresas:
                # Contar productos y servicios
                productos_count = producto_empresa.objects.filter(id_empresa_fk=emp).count()
                servicios_count = servicio_empresa.objects.filter(id_empresa_fk=emp).count()
                sucursales_count = sucursal.objects.filter(id_empresa_fk=emp).count()
                
                resultados.append({
                    'id': emp.id_empresa,
                    'nombre': emp.nombre_empresa,
                    'descripcion': emp.descripcion_empresa,
                    'tipo_empresa': emp.tipo_empresa,
                    'pais': emp.pais_empresa,
                    'estado': emp.estado_empresa,
                    'direccion': emp.direccion_empresa,
                    'latitud': float(emp.latitud_empresa) if emp.latitud_empresa else None,
                    'longitud': float(emp.longitud_empresa) if emp.longitud_empresa else None,
                    'productos_count': productos_count,
                    'servicios_count': servicios_count,
                    'sucursales_count': sucursales_count,
                    'fecha_registro': emp.fecha_registro_empresa.strftime('%d/%m/%Y')
                })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error al buscar empresas: {e}")
            return []
    
    # ===== MÉTODOS DE SERVICIOS =====
    
    def buscar_servicios(self, termino_busqueda, limite=10):
        """Busca servicios por nombre o descripción"""
        try:
            servicios_usuario = servicio_usuario.objects.filter(
                Q(nombre_servicio_usuario__icontains=termino_busqueda) |
                Q(descripcion_servicio_usuario__icontains=termino_busqueda),
                estatus_servicio_usuario='Activo'
            )[:limite//2]
            
            servicios_empresa = servicio_empresa.objects.filter(
                Q(nombre_servicio_empresa__icontains=termino_busqueda) |
                Q(descripcion_servicio_empresa__icontains=termino_busqueda)
            )[:limite//2]
            
            resultados = []
            
            for serv in servicios_usuario:
                resultados.append({
                    'tipo': 'servicio_usuario',
                    'id': serv.id_servicio_usuario,
                    'nombre': serv.nombre_servicio_usuario,
                    'descripcion': serv.descripcion_servicio_usuario,
                    'precio': float(serv.precio_servicio_usuario or 0),
                    'proveedor': serv.id_usuario_fk.nombre_usuario,
                    'latitud': None,  # Los servicios de usuario no tienen ubicación específica
                    'longitud': None
                })
            
            for serv in servicios_empresa:
                sucursales = servicio_sucursal.objects.filter(
                    id_servicio_fk=serv,
                    estatus_servicio_sucursal='Activo'
                )
                for suc_serv in sucursales:
                    resultados.append({
                        'tipo': 'servicio_empresa',
                        'id': suc_serv.id_servicio_sucursal,
                        'nombre': serv.nombre_servicio_empresa,
                        'descripcion': serv.descripcion_servicio_empresa,
                        'precio': float(suc_serv.precio_servicio_sucursal or 0),
                        'proveedor': serv.id_empresa_fk.nombre_empresa,
                        'sucursal': suc_serv.id_sucursal_fk.nombre_sucursal,
                        'latitud': float(suc_serv.id_sucursal_fk.latitud_sucursal) if suc_serv.id_sucursal_fk.latitud_sucursal else None,
                        'longitud': float(suc_serv.id_sucursal_fk.longitud_sucursal) if suc_serv.id_sucursal_fk.longitud_sucursal else None
                    })
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar servicios: {e}")
            return []
    
    # ===== MÉTODOS DE CATEGORÍAS =====
    
    def obtener_categorias_productos(self):
        """Obtiene todas las categorías de productos disponibles"""
        try:
            categorias_usuario = categoria_producto_usuario.objects.filter(
                estatus_categoria_prod_usuario='Activo'
            ).values('nombre_categoria_prod_usuario').distinct()
            
            categorias_empresa = categoria_producto_empresa.objects.filter(
                estatus_categoria_prod_empresa='Activo'
            ).values('nombre_categoria_prod_empresa').distinct()
            
            categorias = []
            for cat in categorias_usuario:
                categorias.append(cat['nombre_categoria_prod_usuario'])
            
            for cat in categorias_empresa:
                categorias.append(cat['nombre_categoria_prod_empresa'])
            
            return list(set(categorias))  # Eliminar duplicados
            
        except Exception as e:
            logger.error(f"Error al obtener categorías: {e}")
            return []
    
    def obtener_categorias_servicios(self):
        """Obtiene todas las categorías de servicios disponibles"""
        try:
            categorias_usuario = categoria_servicio_usuario.objects.filter(
                estatus_categoria_serv_usuario='Activo'
            ).values('nombre_categoria_serv_usuario').distinct()
            
            categorias_empresa = categoria_servicio_empresa.objects.filter(
                estatus_categoria_serv_empresa='Activo'
            ).values('nombre_categoria_serv_empresa').distinct()
            
            categorias = []
            for cat in categorias_usuario:
                categorias.append(cat['nombre_categoria_serv_usuario'])
            
            for cat in categorias_empresa:
                categorias.append(cat['nombre_categoria_serv_empresa'])
            
            return list(set(categorias))  # Eliminar duplicados
            
        except Exception as e:
            logger.error(f"Error al obtener categorías de servicios: {e}")
            return []