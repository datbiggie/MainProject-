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
    sucursal, imagen_producto_empresa, imagen_producto_usuario,
    AtributoProducto, ValorAtributoProducto
)
import logging
import math

logger = logging.getLogger(__name__)

class DatabaseService:
    """Servicio para consultar información de la base de datos del ecommerce"""
    
    def __init__(self):
        pass
    
    def obtener_atributos_producto(self, producto_id, tipo_producto):
        """Obtiene los atributos EAV de un producto específico"""
        try:
            atributos = {}
            
            if tipo_producto == 'producto_usuario':
                valores = ValorAtributoProducto.objects.filter(
                    producto_usuario_id=producto_id
                ).select_related('atributo')
            elif tipo_producto == 'producto_empresa':
                valores = ValorAtributoProducto.objects.filter(
                    producto_empresa_id=producto_id
                ).select_related('atributo')
            else:
                return atributos
            
            for valor in valores:
                atributo_nombre = valor.atributo.nombre
                if valor.atributo.tipo_dato == 'texto':
                    atributos[atributo_nombre] = valor.valor_texto
                elif valor.atributo.tipo_dato == 'numero':
                    atributos[atributo_nombre] = valor.valor_numerico
                elif valor.atributo.tipo_dato == 'decimal':
                    atributos[atributo_nombre] = float(valor.valor_decimal) if valor.valor_decimal else None
                elif valor.atributo.tipo_dato == 'fecha':
                    atributos[atributo_nombre] = valor.valor_fecha
                elif valor.atributo.tipo_dato == 'booleano':
                    atributos[atributo_nombre] = valor.valor_booleano
            
            return atributos
            
        except Exception as e:
            logger.error(f"Error al obtener atributos del producto: {e}")
            return {}
    
    def buscar_productos_por_atributos(self, filtros_atributos, limite=10):
        """Busca productos que coincidan con atributos específicos
        
        Args:
            filtros_atributos (dict): Diccionario con nombre_atributo: valor_buscado
            limite (int): Número máximo de resultados
        
        Returns:
            list: Lista de productos que coinciden con los atributos
        """
        try:
            resultados = []
            productos_encontrados = set()
            
            for nombre_atributo, valor_buscado in filtros_atributos.items():
                # Buscar el atributo por nombre
                try:
                    atributo = AtributoProducto.objects.get(nombre=nombre_atributo)
                except AtributoProducto.DoesNotExist:
                    continue
                
                # Buscar valores que coincidan según el tipo de dato
                valores_query = Q()
                
                if atributo.tipo_dato == 'texto':
                    valores_query = Q(valor_texto__icontains=valor_buscado)
                elif atributo.tipo_dato == 'numero':
                    try:
                        valores_query = Q(valor_numerico=int(valor_buscado))
                    except ValueError:
                        continue
                elif atributo.tipo_dato == 'decimal':
                    try:
                        valores_query = Q(valor_decimal=float(valor_buscado))
                    except ValueError:
                        continue
                elif atributo.tipo_dato == 'booleano':
                    bool_val = valor_buscado.lower() in ['true', '1', 'sí', 'si', 'verdadero']
                    valores_query = Q(valor_booleano=bool_val)
                
                # Obtener productos que tienen este atributo con el valor buscado
                valores = ValorAtributoProducto.objects.filter(
                    atributo=atributo
                ).filter(valores_query)
                
                for valor in valores:
                    # Agregar productos de usuario
                    if valor.producto_usuario_id and valor.producto_usuario_id not in productos_encontrados:
                        try:
                            prod = producto_usuario.objects.get(
                                id_producto_usuario=valor.producto_usuario_id,
                                estatus_producto_usuario='Activo'
                            )
                            atributos = self.obtener_atributos_producto(prod.id_producto_usuario, 'producto_usuario')
                            
                            resultados.append({
                                'tipo': 'producto_usuario',
                                'id': prod.id_producto_usuario,
                                'nombre': prod.nombre_producto_usuario,
                                'descripcion': prod.descripcion_producto_usuario,
                                'precio': float(prod.precio_producto_usuario),
                                'stock': prod.stock_producto_usuario,
                                'vendedor': prod.id_usuario_fk.nombre_usuario,
                                'condicion': prod.condicion_producto_usuario,
                                'atributos': atributos
                            })
                            productos_encontrados.add(valor.producto_usuario_id)
                        except producto_usuario.DoesNotExist:
                            continue
                    
                    # Agregar productos de empresa
                    if valor.producto_empresa_id and valor.producto_empresa_id not in productos_encontrados:
                        try:
                            prod = producto_empresa.objects.get(id_producto_empresa=valor.producto_empresa_id)
                            atributos = self.obtener_atributos_producto(prod.id_producto_empresa, 'producto_empresa')
                            
                            # Obtener sucursales activas
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
                                    'atributos': atributos
                                })
                            
                            productos_encontrados.add(valor.producto_empresa_id)
                        except producto_empresa.DoesNotExist:
                            continue
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar productos por atributos: {e}")
            return []
    
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
                # Obtener atributos EAV del producto
                atributos = self.obtener_atributos_producto(prod.id_producto_usuario, 'producto_usuario')
                
                resultado = {
                    'tipo': 'producto_usuario',
                    'id': prod.id_producto_usuario,
                    'nombre': prod.nombre_producto_usuario,
                    'descripcion': prod.descripcion_producto_usuario,
                    'precio': float(prod.precio_producto_usuario),
                    'stock': prod.stock_producto_usuario,
                    'vendedor': prod.id_usuario_fk.nombre_usuario,
                    'condicion': prod.condicion_producto_usuario,
                    'latitud': float(prod.latitud_entrega_producto) if prod.latitud_entrega_producto else None,
                    'longitud': float(prod.longitud_entrega_producto) if prod.longitud_entrega_producto else None,
                    'atributos': atributos
                }
                resultados.append(resultado)
            
            for prod in productos_empresa:
                # Obtener información de sucursales
                sucursales = producto_sucursal.objects.filter(
                    id_producto_fk=prod,
                    estatus_producto_sucursal='Activo'
                )
                for suc_prod in sucursales:
                    # Obtener atributos EAV del producto de empresa
                    atributos = self.obtener_atributos_producto(prod.id_producto_empresa, 'producto_empresa')
                    
                    resultado = {
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
                        'longitud': float(suc_prod.id_sucursal_fk.longitud_sucursal) if suc_prod.id_sucursal_fk.longitud_sucursal else None,
                        'atributos': atributos
                    }
                    resultados.append(resultado)
            
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
            
            # Normalizar término de búsqueda (quitar acentos y convertir a minúsculas)
            import unicodedata
            categoria_normalizada = unicodedata.normalize('NFD', categoria_nombre.lower()).encode('ascii', 'ignore').decode('ascii')
            
            # Buscar en categorías de usuario con múltiples variaciones
            categorias_usuario = categoria_producto_usuario.objects.filter(
                estatus_categoria_prod_usuario='Activo'
            )
            
            # Filtrar categorías que coincidan (con y sin acentos)
            categorias_coincidentes = []
            for cat in categorias_usuario:
                nombre_cat_normalizado = unicodedata.normalize('NFD', cat.nombre_categoria_prod_usuario.lower()).encode('ascii', 'ignore').decode('ascii')
                if categoria_normalizada in nombre_cat_normalizado or categoria_nombre.lower() in cat.nombre_categoria_prod_usuario.lower():
                    categorias_coincidentes.append(cat)
            
            for categoria in categorias_coincidentes:
                productos = producto_usuario.objects.filter(
                    id_categoria_prod_fk=categoria,
                    estatus_producto_usuario='Activo'
                )[:limite//2]
                
                for prod in productos:
                    # Obtener atributos EAV del producto
                    atributos = self.obtener_atributos_producto(prod.id_producto_usuario, 'producto_usuario')
                    
                    resultados.append({
                        'tipo': 'producto_usuario',
                        'id': prod.id_producto_usuario,
                        'nombre': prod.nombre_producto_usuario,
                        'precio': float(prod.precio_producto_usuario),
                        'vendedor': prod.id_usuario_fk.nombre_usuario,
                        'categoria': categoria.nombre_categoria_prod_usuario,
                        'atributos': atributos
                    })
            
            # Buscar en categorías de empresa con la misma lógica
            categorias_empresa = categoria_producto_empresa.objects.filter(
                estatus_categoria_prod_empresa='Activo'
            )
            
            # Filtrar categorías de empresa que coincidan
            categorias_empresa_coincidentes = []
            for cat in categorias_empresa:
                nombre_cat_normalizado = unicodedata.normalize('NFD', cat.nombre_categoria_prod_empresa.lower()).encode('ascii', 'ignore').decode('ascii')
                if categoria_normalizada in nombre_cat_normalizado or categoria_nombre.lower() in cat.nombre_categoria_prod_empresa.lower():
                    categorias_empresa_coincidentes.append(cat)
            
            for categoria in categorias_empresa_coincidentes:
                productos = producto_empresa.objects.filter(
                    id_categoria_prod_fk=categoria
                )[:limite//2]
                
                for prod in productos:
                    sucursales = producto_sucursal.objects.filter(
                        id_producto_fk=prod,
                        estatus_producto_sucursal='Activo'
                    )
                    for suc_prod in sucursales:
                        # Obtener atributos EAV del producto de empresa
                        atributos = self.obtener_atributos_producto(prod.id_producto_empresa, 'producto_empresa')
                        
                        resultados.append({
                            'tipo': 'producto_empresa',
                            'id': suc_prod.id_producto_sucursal,
                            'nombre': prod.nombre_producto_empresa,
                            'precio': float(suc_prod.precio_producto_sucursal),
                            'vendedor': prod.id_empresa_fk.nombre_empresa,
                            'sucursal': suc_prod.id_sucursal_fk.nombre_sucursal,
                            'categoria': categoria.nombre_categoria_prod_empresa,
                            'atributos': atributos
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
    
    def obtener_servicios_por_categoria(self, categoria_nombre, limite=10):
        """Obtiene servicios de una categoría específica"""
        try:
            resultados = []
            
            # Normalizar término de búsqueda (quitar acentos y convertir a minúsculas)
            import unicodedata
            categoria_normalizada = unicodedata.normalize('NFD', categoria_nombre.lower()).encode('ascii', 'ignore').decode('ascii')
            
            # Buscar en categorías de servicios de usuario con múltiples variaciones
            categorias_usuario = categoria_servicio_usuario.objects.filter(
                estatus_categoria_serv_usuario='Activo'
            )
            
            # Filtrar categorías que coincidan (con y sin acentos)
            categorias_coincidentes = []
            for cat in categorias_usuario:
                nombre_cat_normalizado = unicodedata.normalize('NFD', cat.nombre_categoria_serv_usuario.lower()).encode('ascii', 'ignore').decode('ascii')
                if categoria_normalizada in nombre_cat_normalizado or categoria_nombre.lower() in cat.nombre_categoria_serv_usuario.lower():
                    categorias_coincidentes.append(cat)
            
            for categoria in categorias_coincidentes:
                servicios = servicio_usuario.objects.filter(
                    id_categoria_serv_fk=categoria,
                    estatus_servicio_usuario='Activo'
                )[:limite//2]
                
                for serv in servicios:
                    resultados.append({
                        'tipo': 'servicio_usuario',
                        'id': serv.id_servicio_usuario,
                        'nombre': serv.nombre_servicio_usuario,
                        'precio': float(serv.precio_servicio_usuario or 0),
                        'proveedor': serv.id_usuario_fk.nombre_usuario,
                        'categoria': categoria.nombre_categoria_serv_usuario
                    })
            
            # Buscar en categorías de servicios de empresa con la misma lógica
            categorias_empresa = categoria_servicio_empresa.objects.filter(
                estatus_categoria_serv_empresa='Activo'
            )
            
            # Filtrar categorías de empresa que coincidan
            categorias_empresa_coincidentes = []
            for cat in categorias_empresa:
                nombre_cat_normalizado = unicodedata.normalize('NFD', cat.nombre_categoria_serv_empresa.lower()).encode('ascii', 'ignore').decode('ascii')
                if categoria_normalizada in nombre_cat_normalizado or categoria_nombre.lower() in cat.nombre_categoria_serv_empresa.lower():
                    categorias_empresa_coincidentes.append(cat)
            
            for categoria in categorias_empresa_coincidentes:
                servicios = servicio_empresa.objects.filter(
                    id_categoria_serv_fk=categoria
                )[:limite//2]
                
                for serv in servicios:
                    sucursales = servicio_sucursal.objects.filter(
                        id_servicio_fk=serv,
                        estatus_servicio_sucursal='Activo'
                    )
                    for suc_serv in sucursales:
                        resultados.append({
                            'tipo': 'servicio_empresa',
                            'id': suc_serv.id_servicio_sucursal,
                            'nombre': serv.nombre_servicio_empresa,
                            'precio': float(suc_serv.precio_servicio_sucursal or 0),
                            'proveedor': serv.id_empresa_fk.nombre_empresa,
                            'sucursal': suc_serv.id_sucursal_fk.nombre_sucursal,
                            'categoria': categoria.nombre_categoria_serv_empresa
                        })
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al obtener servicios por categoría: {e}")
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
    
    # ===== MÉTODOS DE INFORMACIÓN DE USUARIOS =====
    
    def buscar_usuario(self, criterio_busqueda):
        """Busca un usuario específico por nombre, email o ID"""
        try:
            # Intentar buscar por ID primero
            try:
                usuario_id = int(criterio_busqueda)
                usuario_obj = usuario.objects.filter(id_usuario=usuario_id).first()
                if usuario_obj:
                    return self._formatear_usuario(usuario_obj)
            except ValueError:
                pass
            
            # Buscar por email o nombre
            usuario_obj = usuario.objects.filter(
                Q(correo_usuario__icontains=criterio_busqueda) |
                Q(nombre_usuario__icontains=criterio_busqueda)
            ).first()
            
            if usuario_obj:
                return self._formatear_usuario(usuario_obj)
            
            return None
            
        except Exception as e:
            logger.error(f"Error al buscar usuario: {e}")
            return None
    
    def listar_usuarios_registrados(self, limite=10):
        """Lista los usuarios registrados más recientes"""
        try:
            usuarios = usuario.objects.all().order_by('-fecha_registro_usuario')[:limite]
            
            resultados = []
            for user in usuarios:
                resultados.append(self._formatear_usuario(user))
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error al listar usuarios registrados: {e}")
            return []
    
    def _formatear_usuario(self, usuario_obj):
        """Formatea la información de un usuario para el chatbot"""
        try:
            # Contar productos y servicios del usuario
            productos_count = producto_usuario.objects.filter(
                id_usuario_fk=usuario_obj,
                estatus_producto_usuario='Activo'
            ).count()
            
            servicios_count = servicio_usuario.objects.filter(
                id_usuario_fk=usuario_obj,
                estatus_servicio_usuario='Activo'
            ).count()
            
            # Contar pedidos realizados
            carritos = carrito_compra_producto_usuario.objects.filter(id_usuario_fk=usuario_obj)
            pedidos_count = pedido_usuario.objects.filter(id_carrito_fk__in=carritos).count()
            
            return {
                'id': usuario_obj.id_usuario,
                'nombre': usuario_obj.nombre_usuario,
                'email': usuario_obj.correo_usuario,
                'telefono': usuario_obj.telefono_usuario,
                'pais': usuario_obj.pais_usuario,
                'estado': usuario_obj.estado_usuario,
                'direccion': usuario_obj.direccion_usuario,
                'productos_count': productos_count,
                'servicios_count': servicios_count,
                'pedidos_count': pedidos_count,
                'fecha_registro': usuario_obj.fecha_registro_usuario.strftime('%d/%m/%Y') if usuario_obj.fecha_registro_usuario else 'No disponible'
            }
            
        except Exception as e:
            logger.error(f"Error al formatear usuario: {e}")
            return None
    
    def buscar_empresa(self, criterio_busqueda):
        """Busca una empresa específica por nombre, email o ID"""
        try:
            # Intentar buscar por ID primero
            try:
                empresa_id = int(criterio_busqueda)
                empresa_obj = empresa.objects.filter(id_empresa=empresa_id).first()
                if empresa_obj:
                    return self._formatear_empresa(empresa_obj)
            except ValueError:
                pass
            
            # Buscar por email o nombre
            empresa_obj = empresa.objects.filter(
                Q(correo_empresa__icontains=criterio_busqueda) |
                Q(nombre_empresa__icontains=criterio_busqueda)
            ).first()
            
            if empresa_obj:
                return self._formatear_empresa(empresa_obj)
            
            return None
            
        except Exception as e:
            logger.error(f"Error al buscar empresa: {e}")
            return None
    
    def listar_empresas_registradas(self, limite=10):
        """Lista las empresas registradas más recientes"""
        try:
            empresas = empresa.objects.all().order_by('-fecha_registro_empresa')[:limite]
            
            resultados = []
            for emp in empresas:
                resultados.append(self._formatear_empresa(emp))
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error al listar empresas registradas: {e}")
            return []
    
    def _formatear_empresa(self, empresa_obj):
        """Formatea la información de una empresa para el chatbot"""
        try:
            # Contar productos y servicios
            productos_count = producto_empresa.objects.filter(id_empresa_fk=empresa_obj).count()
            servicios_count = servicio_empresa.objects.filter(id_empresa_fk=empresa_obj).count()
            sucursales_count = sucursal.objects.filter(id_empresa_fk=empresa_obj).count()
            
            # Contar pedidos recibidos a través del carrito
            pedidos_count = pedido_empresa.objects.filter(
                id_carrito_fk__id_empresa_fk=empresa_obj
            ).count()
            
            return {
                'id': empresa_obj.id_empresa,
                'nombre': empresa_obj.nombre_empresa,
                'email': empresa_obj.correo_empresa,

                'tipo_empresa': empresa_obj.tipo_empresa,
                'descripcion': empresa_obj.descripcion_empresa,
                'pais': empresa_obj.pais_empresa,
                'estado': empresa_obj.estado_empresa,
                'direccion': empresa_obj.direccion_empresa,
                'productos_count': productos_count,
                'servicios_count': servicios_count,
                'sucursales_count': sucursales_count,
                'pedidos_count': pedidos_count,
                'fecha_registro': empresa_obj.fecha_registro_empresa.strftime('%d/%m/%Y') if empresa_obj.fecha_registro_empresa else 'No disponible'
            }
            
        except Exception as e:
            logger.error(f"Error al formatear empresa: {e}")
            return None