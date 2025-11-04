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
from .search_intelligence_service import SearchIntelligenceService
import logging
import math

logger = logging.getLogger(__name__)

class DatabaseService:
    """Servicio para consultar información de la base de datos del ecommerce"""
    
    def __init__(self):
        self.search_intelligence = SearchIntelligenceService()
    
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
                if valor.atributo.tipo_dato == 'texto' or valor.atributo.tipo_dato == 'lista':
                    atributos[atributo_nombre] = valor.valor_texto
                elif valor.atributo.tipo_dato == 'numero':
                    atributos[atributo_nombre] = valor.valor_numero  # Corregido: era valor_numerico
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
        """Busca productos por nombre, descripción y atributos EAV con búsqueda inteligente"""
        try:
            # Expandir términos de búsqueda con sinónimos y variaciones
            terminos_expandidos = self.search_intelligence.expandir_terminos_busqueda(termino_busqueda)
            logger.info(f"Términos expandidos para '{termino_busqueda}': {terminos_expandidos}")
            
            # Detectar atributos específicos en el mensaje (marca, RAM, etc.)
            deteccion_completa = self._detectar_atributos_en_mensaje(termino_busqueda)
            atributos_detectados = deteccion_completa.get('atributos', {}) if deteccion_completa else {}
            condiciones_precio = deteccion_completa.get('precio', {}) if deteccion_completa else {}
            logger.info(f"Atributos detectados: {atributos_detectados}")
            logger.info(f"Condiciones de precio: {condiciones_precio}")
            
            resultados = []
            productos_encontrados = set()
            
            # 1. Búsqueda por nombre y descripción (método tradicional + patrones específicos)
            query_usuario = Q()
            query_empresa = Q()
            
            # Búsqueda por términos expandidos
            for termino in terminos_expandidos:
                query_usuario |= Q(nombre_producto_usuario__icontains=termino) | Q(descripcion_producto_usuario__icontains=termino)
                query_empresa |= Q(nombre_producto_empresa__icontains=termino) | Q(descripcion_producto_empresa__icontains=termino)
            
            # Búsqueda adicional por patrones específicos detectados
            if atributos_detectados:
                for attr_name, attr_value in atributos_detectados.items():
                    # Buscar también en nombre/descripción por si no está en EAV
                    if attr_name == 'ram' or attr_name == 'memoria':
                        # Patrones de RAM en nombre/descripción
                        ram_patterns = [attr_value, attr_value.upper(), attr_value.replace('gb', ' GB'), 
                                      attr_value.replace('gb', 'GB'), f"{attr_value} RAM", f"{attr_value} memoria"]
                        for pattern in ram_patterns:
                            query_usuario |= Q(nombre_producto_usuario__icontains=pattern) | Q(descripcion_producto_usuario__icontains=pattern)
                            query_empresa |= Q(nombre_producto_empresa__icontains=pattern) | Q(descripcion_producto_empresa__icontains=pattern)
                    
                    elif attr_name == 'marca':
                        # Patrones de marca
                        marca_patterns = [attr_value, attr_value.upper(), attr_value.lower(), attr_value.title()]
                        for pattern in marca_patterns:
                            query_usuario |= Q(nombre_producto_usuario__icontains=pattern) | Q(descripcion_producto_usuario__icontains=pattern)
                            query_empresa |= Q(nombre_producto_empresa__icontains=pattern) | Q(descripcion_producto_empresa__icontains=pattern)
            
            productos_usuario = producto_usuario.objects.filter(
                query_usuario,
                estatus_producto_usuario='Activo'
            )
            
            productos_empresa = producto_empresa.objects.filter(
                query_empresa
            )
            
            # 2. Búsqueda por atributos EAV con operadores lógicos
            productos_por_atributos = []
            if atributos_detectados or condiciones_precio:
                productos_por_atributos = self.buscar_productos_con_operadores_logicos(
                    atributos_detectados, condiciones_precio, limite
                )
                logger.info(f"Productos encontrados por búsqueda lógica: {len(productos_por_atributos)}")
            
            # 3. Búsqueda por términos en valores de atributos EAV
            productos_por_valores_eav = self.buscar_productos_por_valores_eav(terminos_expandidos, limite)
            logger.info(f"Productos encontrados por valores EAV: {len(productos_por_valores_eav)}")
            
            # 4. Búsqueda de respaldo por patrones específicos en nombre/descripción
            productos_respaldo = []
            if atributos_detectados and len(resultados) < 3:  # Solo si no hemos encontrado suficientes
                productos_respaldo = self._buscar_por_patrones_especificos(atributos_detectados, limite)
                logger.info(f"Productos encontrados por búsqueda de respaldo: {len(productos_respaldo)}")
            
            # Procesar productos de usuario encontrados por nombre/descripción
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
                productos_encontrados.add(prod.id_producto_usuario)
            
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
                    productos_encontrados.add(suc_prod.id_producto_sucursal)
            
            # Combinar resultados de búsqueda EAV
            for prod_attr in productos_por_atributos:
                if prod_attr['id'] not in productos_encontrados:
                    resultados.append(prod_attr)
                    productos_encontrados.add(prod_attr['id'])
            
            for prod_eav in productos_por_valores_eav:
                if prod_eav['id'] not in productos_encontrados:
                    resultados.append(prod_eav)
                    productos_encontrados.add(prod_eav['id'])
            
            # Combinar resultados de búsqueda de respaldo
            for prod_resp in productos_respaldo:
                if prod_resp['id'] not in productos_encontrados:
                    resultados.append(prod_resp)
                    productos_encontrados.add(prod_resp['id'])
            
            # Filtrar resultados por relevancia usando búsqueda inteligente
            resultados_filtrados = self.search_intelligence.filtrar_resultados_por_relevancia(
                resultados, termino_busqueda, limite
            )
            
            return resultados_filtrados
            
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
        """Busca servicios por nombre o descripción con búsqueda inteligente"""
        try:
            # Expandir términos de búsqueda con sinónimos y variaciones
            terminos_expandidos = self.search_intelligence.expandir_terminos_busqueda(termino_busqueda)
            logger.info(f"Términos expandidos para servicios '{termino_busqueda}': {terminos_expandidos}")
            
            # Construir query para servicios de usuario con términos expandidos
            query_usuario = Q()
            for termino in terminos_expandidos:
                query_usuario |= Q(nombre_servicio_usuario__icontains=termino) | Q(descripcion_servicio_usuario__icontains=termino)
            
            servicios_usuario = servicio_usuario.objects.filter(
                query_usuario,
                estatus_servicio_usuario='Activo'
            )[:limite]
            
            # Construir query para servicios de empresa con términos expandidos
            query_empresa = Q()
            for termino in terminos_expandidos:
                query_empresa |= Q(nombre_servicio_empresa__icontains=termino) | Q(descripcion_servicio_empresa__icontains=termino)
            
            servicios_empresa = servicio_empresa.objects.filter(
                query_empresa
            )[:limite]
            
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
            
            # Filtrar resultados por relevancia usando búsqueda inteligente
            resultados_filtrados = self.search_intelligence.filtrar_resultados_por_relevancia(
                resultados, termino_busqueda, limite
            )
            
            return resultados_filtrados
            
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
    
    # ===== MÉTODOS DE ASESOR GENÉRICO =====
    
    def buscar_productos_por_marca_y_ubicacion(self, marca, lat_usuario=None, lon_usuario=None, radio_km=50, limite=10):
        """Busca productos de una marca específica, opcionalmente cerca de una ubicación"""
        try:
            # Expandir términos de búsqueda para la marca
            terminos_marca = self.search_intelligence.expandir_terminos_busqueda(marca)
            
            # Construir query para productos de usuario
            query_usuario = Q()
            for termino in terminos_marca:
                query_usuario |= Q(nombre_producto_usuario__icontains=termino) | Q(descripcion_producto_usuario__icontains=termino)
            
            productos_usuario = producto_usuario.objects.filter(
                query_usuario,
                estatus_producto_usuario='Activo'
            )
            
            # Construir query para productos de empresa
            query_empresa = Q()
            for termino in terminos_marca:
                query_empresa |= Q(nombre_producto_empresa__icontains=termino) | Q(descripcion_producto_empresa__icontains=termino)
            
            productos_empresa = producto_empresa.objects.filter(query_empresa)
            
            resultados = []
            
            # Procesar productos de usuario
            for prod in productos_usuario:
                distancia = None
                if lat_usuario and lon_usuario and prod.latitud_entrega_producto and prod.longitud_entrega_producto:
                    distancia = self.calcular_distancia_haversine(
                        lat_usuario, lon_usuario,
                        float(prod.latitud_entrega_producto),
                        float(prod.longitud_entrega_producto)
                    )
                    if distancia > radio_km:
                        continue
                
                resultados.append({
                    'tipo': 'producto_usuario',
                    'id': prod.id_producto_usuario,
                    'nombre': prod.nombre_producto_usuario,
                    'descripcion': prod.descripcion_producto_usuario,
                    'precio': float(prod.precio_producto_usuario),
                    'vendedor': prod.id_usuario_fk.nombre_usuario,
                    'distancia_km': round(distancia, 2) if distancia else None,
                    'tiene_envio': True  # Los usuarios pueden hacer envíos
                })
            
            # Procesar productos de empresa
            for prod in productos_empresa:
                sucursales = producto_sucursal.objects.filter(
                    id_producto_fk=prod,
                    estatus_producto_sucursal='Activo'
                )
                
                for suc_prod in sucursales:
                    distancia = None
                    if lat_usuario and lon_usuario and suc_prod.id_sucursal_fk.latitud_sucursal and suc_prod.id_sucursal_fk.longitud_sucursal:
                        distancia = self.calcular_distancia_haversine(
                            lat_usuario, lon_usuario,
                            float(suc_prod.id_sucursal_fk.latitud_sucursal),
                            float(suc_prod.id_sucursal_fk.longitud_sucursal)
                        )
                        if distancia > radio_km:
                            continue
                    
                    resultados.append({
                        'tipo': 'producto_empresa',
                        'id': suc_prod.id_producto_sucursal,
                        'nombre': prod.nombre_producto_empresa,
                        'descripcion': prod.descripcion_producto_empresa,
                        'precio': float(suc_prod.precio_producto_sucursal),
                        'vendedor': prod.id_empresa_fk.nombre_empresa,
                        'sucursal': suc_prod.id_sucursal_fk.nombre_sucursal,
                        'direccion_sucursal': suc_prod.id_sucursal_fk.direccion_sucursal,
                        'distancia_km': round(distancia, 2) if distancia else None,
                        'tiene_envio': True  # Las empresas suelen tener envío
                    })
            
            # Ordenar por distancia si hay ubicación
            if lat_usuario and lon_usuario:
                resultados.sort(key=lambda x: x['distancia_km'] if x['distancia_km'] is not None else float('inf'))
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar productos por marca y ubicación: {e}")
            return []
    
    def obtener_empresas_con_envio_rapido(self, ciudad_destino=None, limite=10):
        """Obtiene empresas que ofrecen envío rápido a una ciudad específica"""
        try:
            # Por ahora, asumimos que todas las empresas grandes ofrecen envío rápido
            # En una implementación real, esto vendría de una tabla de configuración de envíos
            
            query = Q(tipo_empresa__in=['mediana', 'grande'])
            
            if ciudad_destino:
                # Buscar empresas en la misma ciudad o estado
                ciudad_normalizada = self.search_intelligence.normalizar_texto(ciudad_destino)
                query &= (
                    Q(estado_empresa__icontains=ciudad_destino) |
                    Q(direccion_empresa__icontains=ciudad_destino)
                )
            
            empresas = empresa.objects.filter(query)[:limite]
            
            resultados = []
            for emp in empresas:
                # Contar sucursales
                sucursales_count = sucursal.objects.filter(id_empresa_fk=emp).count()
                
                resultados.append({
                    'id': emp.id_empresa,
                    'nombre': emp.nombre_empresa,
                    'tipo_empresa': emp.tipo_empresa,
                    'estado': emp.estado_empresa,
                    'direccion': emp.direccion_empresa,
                    'sucursales_count': sucursales_count,
                    'envio_rapido': True,  # Asumimos que empresas medianas/grandes tienen envío rápido
                    'tiempo_estimado': '24-48 horas' if emp.tipo_empresa == 'grande' else '2-3 días'
                })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error al obtener empresas con envío rápido: {e}")
            return []
    
    def calcular_distancia_a_sucursal(self, lat_usuario, lon_usuario, empresa_nombre, limite_sucursales=5):
        """Calcula la distancia desde la ubicación del usuario hasta las sucursales de una empresa"""
        try:
            # Buscar empresa por nombre
            empresas = empresa.objects.filter(
                nombre_empresa__icontains=empresa_nombre
            )
            
            if not empresas.exists():
                return []
            
            resultados = []
            
            for emp in empresas:
                sucursales_empresa = sucursal.objects.filter(
                    id_empresa_fk=emp,
                    latitud_sucursal__isnull=False,
                    longitud_sucursal__isnull=False
                )
                
                sucursales_con_distancia = []
                
                for suc in sucursales_empresa:
                    distancia = self.calcular_distancia_haversine(
                        lat_usuario, lon_usuario,
                        float(suc.latitud_sucursal),
                        float(suc.longitud_sucursal)
                    )
                    
                    sucursales_con_distancia.append({
                        'nombre_sucursal': suc.nombre_sucursal,
                        'direccion': suc.direccion_sucursal,
                        'telefono': suc.telefono_sucursal,
                        'estado': suc.estado_sucursal,
                        'distancia_km': round(distancia, 2)
                    })
                
                # Ordenar por distancia
                sucursales_con_distancia.sort(key=lambda x: x['distancia_km'])
                
                resultados.append({
                    'empresa': emp.nombre_empresa,
                    'sucursales': sucursales_con_distancia[:limite_sucursales]
                })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error al calcular distancia a sucursales: {e}")
            return []
    
    def buscar_servicios_por_ubicacion_y_tipo(self, tipo_servicio, lat_usuario=None, lon_usuario=None, radio_km=25, limite=10):
        """Busca servicios de un tipo específico cerca de una ubicación"""
        try:
            # Expandir términos de búsqueda para el tipo de servicio
            terminos_servicio = self.search_intelligence.expandir_terminos_busqueda(tipo_servicio)
            
            # Construir query para servicios de usuario
            query_usuario = Q()
            for termino in terminos_servicio:
                query_usuario |= Q(nombre_servicio_usuario__icontains=termino) | Q(descripcion_servicio_usuario__icontains=termino)
            
            servicios_usuario = servicio_usuario.objects.filter(
                query_usuario,
                estatus_servicio_usuario='Activo'
            )
            
            # Construir query para servicios de empresa
            query_empresa = Q()
            for termino in terminos_servicio:
                query_empresa |= Q(nombre_servicio_empresa__icontains=termino) | Q(descripcion_servicio_empresa__icontains=termino)
            
            servicios_empresa = servicio_empresa.objects.filter(query_empresa)
            
            resultados = []
            
            # Procesar servicios de usuario (sin ubicación específica, pero disponibles)
            for serv in servicios_usuario:
                resultados.append({
                    'tipo': 'servicio_usuario',
                    'id': serv.id_servicio_usuario,
                    'nombre': serv.nombre_servicio_usuario,
                    'descripcion': serv.descripcion_servicio_usuario,
                    'precio': float(serv.precio_servicio_usuario or 0),
                    'proveedor': serv.id_usuario_fk.nombre_usuario,
                    'contacto': serv.id_usuario_fk.correo_usuario,
                    'distancia_km': None,  # Servicios de usuario no tienen ubicación fija
                    'disponible_domicilio': True
                })
            
            # Procesar servicios de empresa
            for serv in servicios_empresa:
                sucursales = servicio_sucursal.objects.filter(
                    id_servicio_fk=serv,
                    estatus_servicio_sucursal='Activo'
                )
                
                for suc_serv in sucursales:
                    distancia = None
                    if lat_usuario and lon_usuario and suc_serv.id_sucursal_fk.latitud_sucursal and suc_serv.id_sucursal_fk.longitud_sucursal:
                        distancia = self.calcular_distancia_haversine(
                            lat_usuario, lon_usuario,
                            float(suc_serv.id_sucursal_fk.latitud_sucursal),
                            float(suc_serv.id_sucursal_fk.longitud_sucursal)
                        )
                        if distancia > radio_km:
                            continue
                    
                    resultados.append({
                        'tipo': 'servicio_empresa',
                        'id': suc_serv.id_servicio_sucursal,
                        'nombre': serv.nombre_servicio_empresa,
                        'descripcion': serv.descripcion_servicio_empresa,
                        'precio': float(suc_serv.precio_servicio_sucursal or 0),
                        'proveedor': serv.id_empresa_fk.nombre_empresa,
                        'sucursal': suc_serv.id_sucursal_fk.nombre_sucursal,
                        'direccion_sucursal': suc_serv.id_sucursal_fk.direccion_sucursal,
                        'telefono_sucursal': suc_serv.id_sucursal_fk.telefono_sucursal,
                        'distancia_km': round(distancia, 2) if distancia else None,
                        'disponible_domicilio': True
                    })
            
            # Ordenar por distancia si hay ubicación
            if lat_usuario and lon_usuario:
                resultados.sort(key=lambda x: x['distancia_km'] if x['distancia_km'] is not None else float('inf'))
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar servicios por ubicación y tipo: {e}")
            return []
    
    # ===== MÉTODOS DE BÚSQUEDA EAV =====
    
    def _detectar_atributos_en_mensaje(self, mensaje):
        """Detecta atributos específicos mencionados en el mensaje del usuario para búsqueda EAV con operadores lógicos"""
        mensaje_lower = mensaje.lower()
        atributos_detectados = {}
        condiciones_precio = {}
        
        # Mapeo de palabras clave a atributos EAV comunes (todo en minúsculas para comparación)
        mapeo_atributos_eav = {
            # Especificaciones técnicas
            'ram': ['4gb', '8gb', '16gb', '32gb', '64gb', 'memoria ram', 'memoria'],
            'almacenamiento': ['128gb', '256gb', '512gb', '1tb', '2tb', 'ssd', 'hdd', 'disco duro'],
            'procesador': ['intel', 'amd', 'core i3', 'core i5', 'core i7', 'ryzen', 'i3', 'i5', 'i7', 'celeron', 'pentium'],
            'pantalla': ['15 pulgadas', '17 pulgadas', '13 pulgadas', 'full hd', '4k', 'oled', 'hd', 'fhd'],
            
            # Marcas (agregar más variaciones)
            'marca': ['hp', 'dell', 'lenovo', 'asus', 'acer', 'apple', 'samsung', 'lg', 'sony', 'huawei', 
                     'hewlett packard', 'hewlett-packard', 'toshiba', 'msi', 'alienware', 'macbook'],
            
            # Colores
            'color': ['negro', 'blanco', 'gris', 'plata', 'azul', 'rojo', 'verde', 'dorado', 'plateado', 'gris oscuro'],
            
            # Tallas (para ropa)
            'talla': ['xs', 's', 'm', 'l', 'xl', 'xxl', 'pequeño', 'mediano', 'grande', 'extra grande'],
            
            # Materiales
            'material': ['algodón', 'poliéster', 'cuero', 'metal', 'plástico', 'madera', 'acero', 'aluminio'],
            
            # Condición
            'condicion': ['nuevo', 'usado', 'seminuevo', 'reacondicionado', 'refurbished', 'como nuevo'],
            
            # Características específicas
            'conectividad': ['wifi', 'bluetooth', 'usb', 'hdmi', 'ethernet', 'wi-fi', 'usb-c', 'thunderbolt'],
            'sistema_operativo': ['windows', 'macos', 'linux', 'android', 'ios', 'windows 10', 'windows 11', 'mac os'],
        }
        
        # Buscar patrones específicos en el mensaje
        for atributo, valores_posibles in mapeo_atributos_eav.items():
            for valor in valores_posibles:
                if valor in mensaje_lower:
                    atributos_detectados[atributo] = valor
                    break
        
        # Detectar patrones numéricos específicos y condiciones de precio
        import re
        
        # RAM: "8gb", "16 gb", "8 gb de ram", "8GB RAM", "con 8gb", etc.
        ram_patterns = [
            r'(\d+)\s*gb(?:\s+(?:de\s+)?ram)?',
            r'(\d+)\s*gb(?:\s+(?:de\s+)?memoria)',
            r'memoria\s+(?:ram\s+)?(?:de\s+)?(\d+)\s*gb',
            r'(?:con\s+)?(\d+)\s*gb(?:\s+de\s+)?(?:ram|memoria)',
            r'(?:ram|memoria)\s+(?:de\s+)?(\d+)\s*gb',
            r'(\d+)\s*gb\s+(?:ram|memoria)',
            r'(\d+)\s*gb(?:\s+de\s+)?(?:ram|memoria|memory)',
            r'(?:laptop|computadora|pc)\s+.*?(\d+)\s*gb'
        ]
        
        for pattern in ram_patterns:
            match = re.search(pattern, mensaje_lower)
            if match:
                ram_value = f"{match.group(1)}gb"
                atributos_detectados['ram'] = ram_value
                break
        
        # Almacenamiento: "256gb", "1tb"
        storage_patterns = [
            r'(\d+)\s*(gb|tb)(?:\s+(?:de\s+)?(?:almacenamiento|disco|ssd|hdd))?',
            r'(?:almacenamiento|disco|ssd|hdd)\s+(?:de\s+)?(\d+)\s*(gb|tb)'
        ]
        
        for pattern in storage_patterns:
            match = re.search(pattern, mensaje_lower)
            if match:
                storage_value = f"{match.group(1)}{match.group(2)}"
                atributos_detectados['almacenamiento'] = storage_value
                break
        
        # Pantalla: "15 pulgadas", "17""
        screen_patterns = [
            r'(\d+)\s*(?:pulgadas?|"|\'\')(?:\s+(?:de\s+)?pantalla)?',
            r'pantalla\s+(?:de\s+)?(\d+)\s*(?:pulgadas?|"|\'\')' 
        ]
        
        for pattern in screen_patterns:
            match = re.search(pattern, mensaje_lower)
            if match:
                screen_value = f"{match.group(1)} pulgadas"
                atributos_detectados['pantalla'] = screen_value
                break
        
        # Detectar condiciones de precio
        precio_patterns = [
            r'(?:precio\s+)?(?:menor|menos|bajo)\s+(?:de\s+|a\s+)?\$?(\d+(?:\.\d+)?)',  # menor a $1000
            r'(?:precio\s+)?(?:mayor|mas|más|alto)\s+(?:de\s+|a\s+)?\$?(\d+(?:\.\d+)?)',  # mayor a $500
            r'(?:precio\s+)?(?:entre|de)\s+\$?(\d+(?:\.\d+)?)\s+(?:y|a)\s+\$?(\d+(?:\.\d+)?)',  # entre $500 y $1000
            r'(?:precio\s+)?(?:hasta|máximo|maximo)\s+\$?(\d+(?:\.\d+)?)',  # hasta $800
            r'(?:precio\s+)?(?:desde|mínimo|minimo)\s+\$?(\d+(?:\.\d+)?)',  # desde $300
            r'(?:precio\s+)?\$?(\d+(?:\.\d+)?)\s+(?:o\s+)?(?:menos|menor)',  # $500 o menos
            r'(?:precio\s+)?\$?(\d+(?:\.\d+)?)\s+(?:o\s+)?(?:más|mas|mayor)',  # $800 o más
        ]
        
        for i, pattern in enumerate(precio_patterns):
            match = re.search(pattern, mensaje_lower)
            if match:
                if i == 0:  # menor a
                    condiciones_precio['max'] = float(match.group(1))
                elif i == 1:  # mayor a
                    condiciones_precio['min'] = float(match.group(1))
                elif i == 2:  # entre X y Y
                    condiciones_precio['min'] = float(match.group(1))
                    condiciones_precio['max'] = float(match.group(2))
                elif i == 3:  # hasta
                    condiciones_precio['max'] = float(match.group(1))
                elif i == 4:  # desde
                    condiciones_precio['min'] = float(match.group(1))
                elif i == 5:  # X o menos
                    condiciones_precio['max'] = float(match.group(1))
                elif i == 6:  # X o más
                    condiciones_precio['min'] = float(match.group(1))
                break
        
        # Combinar resultados
        resultado = {}
        if atributos_detectados:
            resultado['atributos'] = atributos_detectados
        if condiciones_precio:
            resultado['precio'] = condiciones_precio
        
        return resultado if resultado else None
    
    def buscar_productos_por_atributos_eav(self, atributos_detectados, limite=10):
        """Busca productos que coincidan con atributos EAV específicos"""
        try:
            resultados = []
            productos_encontrados = set()
            
            for nombre_atributo, valor_buscado in atributos_detectados.items():
                # Buscar atributos que coincidan con el nombre (flexible con mayúsculas/minúsculas)
                atributos_query = AtributoProducto.objects.filter(
                    Q(nombre__icontains=nombre_atributo) |
                    Q(descripcion__icontains=nombre_atributo) |
                    Q(nombre__iexact=nombre_atributo) |  # Coincidencia exacta sin importar mayúsculas
                    Q(nombre__icontains=nombre_atributo.replace('_', ' ')) |  # Reemplazar _ con espacios
                    Q(nombre__icontains=nombre_atributo.replace(' ', '_'))    # Reemplazar espacios con _
                )
                
                for atributo in atributos_query:
                    # Buscar valores que coincidan según el tipo de dato
                    valores_query = Q()
                    
                    if atributo.tipo_dato == 'texto':
                        # Búsqueda flexible de texto (mayúsculas/minúsculas, variaciones)
                        valores_query = (
                            Q(valor_texto__icontains=valor_buscado) |
                            Q(valor_texto__iexact=valor_buscado) |  # Coincidencia exacta sin mayúsculas
                            Q(valor_texto__icontains=valor_buscado.upper()) |  # Mayúsculas
                            Q(valor_texto__icontains=valor_buscado.lower()) |  # Minúsculas
                            Q(valor_texto__icontains=valor_buscado.title())    # Título
                        )
                    elif atributo.tipo_dato == 'numero':
                        try:
                            # Extraer número del valor buscado (ej: "8gb" -> 8)
                            import re
                            numero_match = re.search(r'(\d+)', str(valor_buscado))
                            if numero_match:
                                numero = int(numero_match.group(1))
                                valores_query = Q(valor_numero=numero)
                                logger.info(f"Buscando atributo '{atributo.nombre}' con valor numérico: {numero}")
                            else:
                                continue
                        except ValueError:
                            continue
                    elif atributo.tipo_dato == 'decimal':
                        try:
                            import re
                            numero_match = re.search(r'(\d+(?:\.\d+)?)', str(valor_buscado))
                            if numero_match:
                                decimal_val = float(numero_match.group(1))
                                valores_query = Q(valor_decimal=decimal_val)
                        except ValueError:
                            continue
                    elif atributo.tipo_dato == 'booleano':
                        bool_val = str(valor_buscado).lower() in ['true', '1', 'sí', 'si', 'verdadero', 'yes']
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
                                    'atributos': atributos,
                                    'coincidencia_eav': f"{atributo.nombre}: {valor_buscado}"
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
                                        'atributos': atributos,
                                        'coincidencia_eav': f"{atributo.nombre}: {valor_buscado}"
                                    })
                                
                                productos_encontrados.add(valor.producto_empresa_id)
                            except producto_empresa.DoesNotExist:
                                continue
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar productos por atributos EAV: {e}")
            return []
    
    def buscar_productos_por_valores_eav(self, terminos_expandidos, limite=10):
        """Busca productos cuyos valores de atributos EAV coincidan con los términos de búsqueda"""
        try:
            resultados = []
            productos_encontrados = set()
            
            for termino in terminos_expandidos:
                if len(termino) < 2:  # Ignorar términos muy cortos
                    continue
                
                # Buscar en valores de texto (flexible con mayúsculas/minúsculas)
                valores_texto = ValorAtributoProducto.objects.filter(
                    Q(valor_texto__icontains=termino) |
                    Q(valor_texto__iexact=termino) |
                    Q(valor_texto__icontains=termino.upper()) |
                    Q(valor_texto__icontains=termino.lower()) |
                    Q(valor_texto__icontains=termino.title())
                ).select_related('atributo')
                
                for valor in valores_texto:
                    # Procesar productos de usuario
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
                                'atributos': atributos,
                                'coincidencia_eav': f"{valor.atributo.nombre}: {valor.valor_texto}"
                            })
                            productos_encontrados.add(valor.producto_usuario_id)
                        except producto_usuario.DoesNotExist:
                            continue
                    
                    # Procesar productos de empresa
                    if valor.producto_empresa_id and valor.producto_empresa_id not in productos_encontrados:
                        try:
                            prod = producto_empresa.objects.get(id_producto_empresa=valor.producto_empresa_id)
                            atributos = self.obtener_atributos_producto(prod.id_producto_empresa, 'producto_empresa')
                            
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
                                    'atributos': atributos,
                                    'coincidencia_eav': f"{valor.atributo.nombre}: {valor.valor_texto}"
                                })
                            
                            productos_encontrados.add(valor.producto_empresa_id)
                        except producto_empresa.DoesNotExist:
                            continue
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error al buscar productos por valores EAV: {e}")
            return []
    
    def _buscar_por_patrones_especificos(self, atributos_detectados, limite=10):
        """Búsqueda de respaldo por patrones específicos en nombre y descripción"""
        try:
            resultados = []
            productos_encontrados = set()
            
            for attr_name, attr_value in atributos_detectados.items():
                if attr_name == 'ram':
                    # Patrones específicos para RAM
                    ram_patterns = [
                        attr_value,  # "8gb"
                        attr_value.upper(),  # "8GB"
                        attr_value.replace('gb', ' GB'),  # "8 GB"
                        f"{attr_value} RAM",  # "8gb RAM"
                        f"{attr_value} de RAM",  # "8gb de RAM"
                        f"RAM {attr_value}",  # "RAM 8gb"
                        f"memoria {attr_value}",  # "memoria 8gb"
                        f"{attr_value} memoria",  # "8gb memoria"
                        f"con {attr_value}",  # "con 8gb"
                        f"{attr_value.replace('gb', '')}GB",  # "8GB"
                        f"{attr_value.replace('gb', '')} GB"  # "8 GB"
                    ]
                    
                    # Buscar en productos de usuario
                    for pattern in ram_patterns:
                        productos_usuario = producto_usuario.objects.filter(
                            Q(nombre_producto_usuario__icontains=pattern) |
                            Q(descripcion_producto_usuario__icontains=pattern),
                            estatus_producto_usuario='Activo'
                        )
                        
                        for prod in productos_usuario:
                            if prod.id_producto_usuario not in productos_encontrados:
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
                                    'atributos': atributos,
                                    'coincidencia_patron': f"RAM: {pattern} encontrado en {prod.nombre_producto_usuario}"
                                })
                                productos_encontrados.add(prod.id_producto_usuario)
                    
                    # Buscar en productos de empresa
                    for pattern in ram_patterns:
                        productos_empresa = producto_empresa.objects.filter(
                            Q(nombre_producto_empresa__icontains=pattern) |
                            Q(descripcion_producto_empresa__icontains=pattern)
                        )
                        
                        for prod in productos_empresa:
                            if prod.id_producto_empresa not in productos_encontrados:
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
                                        'atributos': atributos,
                                        'coincidencia_patron': f"RAM: {pattern} encontrado en {prod.nombre_producto_empresa}"
                                    })
                                
                                productos_encontrados.add(prod.id_producto_empresa)
                
                elif attr_name == 'marca':
                    # Patrones específicos para marca
                    marca_patterns = [
                        attr_value,
                        attr_value.upper(),
                        attr_value.lower(),
                        attr_value.title(),
                        f"laptop {attr_value}",
                        f"{attr_value} laptop",
                        f"computadora {attr_value}",
                        f"{attr_value} computadora"
                    ]
                    
                    # Similar lógica para marcas...
                    # (Implementar si es necesario)
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error en búsqueda de respaldo por patrones: {e}")
            return []
    
    def buscar_productos_con_operadores_logicos(self, atributos_detectados, condiciones_precio, limite=10):
        """Busca productos usando operadores lógicos AND para múltiples atributos y condiciones de precio"""
        try:
            resultados = []
            productos_encontrados = set()
            
            logger.info(f"Búsqueda con operadores lógicos - Atributos: {atributos_detectados}, Precio: {condiciones_precio}")
            
            # Si no hay atributos EAV, solo aplicar filtros de precio
            if not atributos_detectados:
                return self._aplicar_filtros_precio_solamente(condiciones_precio, limite)
            
            # Obtener productos que cumplan TODOS los atributos (operador AND)
            productos_candidatos_usuario = set()
            productos_candidatos_empresa = set()
            
            # Para cada atributo, encontrar productos que lo cumplan
            for i, (nombre_atributo, valor_buscado) in enumerate(atributos_detectados.items()):
                logger.info(f"Procesando atributo {i+1}/{len(atributos_detectados)}: {nombre_atributo} = {valor_buscado}")
                
                # Buscar atributos que coincidan con el nombre
                atributos_query = AtributoProducto.objects.filter(
                    Q(nombre__icontains=nombre_atributo) |
                    Q(descripcion__icontains=nombre_atributo) |
                    Q(nombre__iexact=nombre_atributo) |
                    Q(nombre__icontains=nombre_atributo.replace('_', ' ')) |
                    Q(nombre__icontains=nombre_atributo.replace(' ', '_'))
                )
                
                productos_este_atributo_usuario = set()
                productos_este_atributo_empresa = set()
                
                for atributo in atributos_query:
                    # Construir query según el tipo de dato
                    valores_query = Q()
                    
                    if atributo.tipo_dato == 'texto' or atributo.tipo_dato == 'lista':
                        valores_query = (
                            Q(valor_texto__icontains=valor_buscado) |
                            Q(valor_texto__iexact=valor_buscado) |
                            Q(valor_texto__icontains=valor_buscado.upper()) |
                            Q(valor_texto__icontains=valor_buscado.lower()) |
                            Q(valor_texto__icontains=valor_buscado.title())
                        )
                    elif atributo.tipo_dato == 'numero':
                        import re
                        numero_match = re.search(r'(\d+)', str(valor_buscado))
                        if numero_match:
                            numero = int(numero_match.group(1))
                            valores_query = Q(valor_numero=numero)
                        else:
                            continue
                    elif atributo.tipo_dato == 'decimal':
                        import re
                        numero_match = re.search(r'(\d+(?:\.\d+)?)', str(valor_buscado))
                        if numero_match:
                            decimal_val = float(numero_match.group(1))
                            valores_query = Q(valor_decimal=decimal_val)
                        else:
                            continue
                    elif atributo.tipo_dato == 'booleano':
                        bool_val = str(valor_buscado).lower() in ['true', '1', 'sí', 'si', 'verdadero', 'yes']
                        valores_query = Q(valor_booleano=bool_val)
                    
                    # Obtener valores que coincidan
                    valores = ValorAtributoProducto.objects.filter(
                        atributo=atributo
                    ).filter(valores_query)
                    
                    for valor in valores:
                        if valor.producto_usuario_id:
                            productos_este_atributo_usuario.add(valor.producto_usuario_id)
                        if valor.producto_empresa_id:
                            productos_este_atributo_empresa.add(valor.producto_empresa_id)
                
                logger.info(f"Atributo '{nombre_atributo}': {len(productos_este_atributo_usuario)} productos usuario, {len(productos_este_atributo_empresa)} productos empresa")
                
                # En la primera iteración, inicializar los candidatos
                if i == 0:
                    productos_candidatos_usuario = productos_este_atributo_usuario
                    productos_candidatos_empresa = productos_este_atributo_empresa
                else:
                    # Intersección (AND lógico) - solo productos que cumplan TODOS los atributos
                    productos_candidatos_usuario &= productos_este_atributo_usuario
                    productos_candidatos_empresa &= productos_este_atributo_empresa
                
                logger.info(f"Después del AND: {len(productos_candidatos_usuario)} productos usuario, {len(productos_candidatos_empresa)} productos empresa")
            
            # Procesar productos de usuario que cumplen TODOS los atributos
            for producto_id in productos_candidatos_usuario:
                try:
                    prod = producto_usuario.objects.get(
                        id_producto_usuario=producto_id,
                        estatus_producto_usuario='Activo'
                    )
                    
                    # Aplicar filtros de precio si existen
                    if condiciones_precio:
                        precio = float(prod.precio_producto_usuario)
                        if not self._cumple_condiciones_precio(precio, condiciones_precio):
                            continue
                    
                    atributos = self.obtener_atributos_producto(prod.id_producto_usuario, 'producto_usuario')
                    
                    # Crear descripción de coincidencias
                    coincidencias = []
                    for attr_name, attr_value in atributos_detectados.items():
                        if attr_name in atributos:
                            coincidencias.append(f"{attr_name}: {atributos[attr_name]}")
                    
                    if condiciones_precio:
                        precio_desc = self._describir_condicion_precio(condiciones_precio)
                        coincidencias.append(f"Precio: ${prod.precio_producto_usuario} ({precio_desc})")
                    
                    resultados.append({
                        'tipo': 'producto_usuario',
                        'id': prod.id_producto_usuario,
                        'nombre': prod.nombre_producto_usuario,
                        'descripcion': prod.descripcion_producto_usuario,
                        'precio': float(prod.precio_producto_usuario),
                        'stock': prod.stock_producto_usuario,
                        'vendedor': prod.id_usuario_fk.nombre_usuario,
                        'condicion': prod.condicion_producto_usuario,
                        'atributos': atributos,
                        'coincidencia_logica': f"Cumple TODOS los criterios: {', '.join(coincidencias)}"
                    })
                    productos_encontrados.add(producto_id)
                    
                except producto_usuario.DoesNotExist:
                    continue
            
            # Procesar productos de empresa que cumplen TODOS los atributos
            for producto_id in productos_candidatos_empresa:
                try:
                    prod = producto_empresa.objects.get(id_producto_empresa=producto_id)
                    atributos = self.obtener_atributos_producto(prod.id_producto_empresa, 'producto_empresa')
                    
                    # Obtener sucursales activas
                    sucursales = producto_sucursal.objects.filter(
                        id_producto_fk=prod,
                        estatus_producto_sucursal='Activo'
                    )
                    
                    for suc_prod in sucursales:
                        # Aplicar filtros de precio si existen
                        if condiciones_precio:
                            precio = float(suc_prod.precio_producto_sucursal)
                            if not self._cumple_condiciones_precio(precio, condiciones_precio):
                                continue
                        
                        # Crear descripción de coincidencias
                        coincidencias = []
                        for attr_name, attr_value in atributos_detectados.items():
                            if attr_name in atributos:
                                coincidencias.append(f"{attr_name}: {atributos[attr_name]}")
                        
                        if condiciones_precio:
                            precio_desc = self._describir_condicion_precio(condiciones_precio)
                            coincidencias.append(f"Precio: ${suc_prod.precio_producto_sucursal} ({precio_desc})")
                        
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
                            'atributos': atributos,
                            'coincidencia_logica': f"Cumple TODOS los criterios: {', '.join(coincidencias)}"
                        })
                    
                    productos_encontrados.add(producto_id)
                    
                except producto_empresa.DoesNotExist:
                    continue
            
            logger.info(f"Búsqueda lógica completada: {len(resultados)} productos encontrados")
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error en búsqueda con operadores lógicos: {e}")
            return []
    
    def _cumple_condiciones_precio(self, precio, condiciones_precio):
        """Verifica si un precio cumple las condiciones especificadas"""
        if 'min' in condiciones_precio and precio < condiciones_precio['min']:
            return False
        if 'max' in condiciones_precio and precio > condiciones_precio['max']:
            return False
        return True
    
    def _describir_condicion_precio(self, condiciones_precio):
        """Crea una descripción textual de las condiciones de precio"""
        if 'min' in condiciones_precio and 'max' in condiciones_precio:
            return f"entre ${condiciones_precio['min']} y ${condiciones_precio['max']}"
        elif 'min' in condiciones_precio:
            return f"desde ${condiciones_precio['min']}"
        elif 'max' in condiciones_precio:
            return f"hasta ${condiciones_precio['max']}"
        return "precio válido"
    
    def _aplicar_filtros_precio_solamente(self, condiciones_precio, limite=10):
        """Aplica solo filtros de precio cuando no hay atributos EAV"""
        try:
            resultados = []
            
            # Construir query de precio para productos de usuario
            query_precio_usuario = Q(estatus_producto_usuario='Activo')
            if 'min' in condiciones_precio:
                query_precio_usuario &= Q(precio_producto_usuario__gte=condiciones_precio['min'])
            if 'max' in condiciones_precio:
                query_precio_usuario &= Q(precio_producto_usuario__lte=condiciones_precio['max'])
            
            productos_usuario = producto_usuario.objects.filter(query_precio_usuario)[:limite]
            
            for prod in productos_usuario:
                atributos = self.obtener_atributos_producto(prod.id_producto_usuario, 'producto_usuario')
                precio_desc = self._describir_condicion_precio(condiciones_precio)
                
                resultados.append({
                    'tipo': 'producto_usuario',
                    'id': prod.id_producto_usuario,
                    'nombre': prod.nombre_producto_usuario,
                    'descripcion': prod.descripcion_producto_usuario,
                    'precio': float(prod.precio_producto_usuario),
                    'stock': prod.stock_producto_usuario,
                    'vendedor': prod.id_usuario_fk.nombre_usuario,
                    'condicion': prod.condicion_producto_usuario,
                    'atributos': atributos,
                    'coincidencia_logica': f"Precio: ${prod.precio_producto_usuario} ({precio_desc})"
                })
            
            # Construir query de precio para productos de empresa
            query_precio_empresa = Q(estatus_producto_sucursal='Activo')
            if 'min' in condiciones_precio:
                query_precio_empresa &= Q(precio_producto_sucursal__gte=condiciones_precio['min'])
            if 'max' in condiciones_precio:
                query_precio_empresa &= Q(precio_producto_sucursal__lte=condiciones_precio['max'])
            
            productos_empresa = producto_sucursal.objects.filter(query_precio_empresa).select_related('id_producto_fk')[:limite]
            
            for suc_prod in productos_empresa:
                prod = suc_prod.id_producto_fk
                atributos = self.obtener_atributos_producto(prod.id_producto_empresa, 'producto_empresa')
                precio_desc = self._describir_condicion_precio(condiciones_precio)
                
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
                    'atributos': atributos,
                    'coincidencia_logica': f"Precio: ${suc_prod.precio_producto_sucursal} ({precio_desc})"
                })
            
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"Error en filtros de precio solamente: {e}")
            return []