from django.db import transaction
from django.core.exceptions import ValidationError
from .models import (
    AtributoProducto, CategoriaAtributo, ValorAtributoProducto,
    categoria_producto_usuario, categoria_producto_empresa,
    producto_usuario, producto_empresa
)


class EAVHelper:
    """Clase auxiliar para manejar operaciones EAV"""
    
    @staticmethod
    def crear_atributo(nombre, tipo_dato, descripcion='', obligatorio=False, opciones=None):
        """
        Crea un nuevo atributo
        
        Args:
            nombre (str): Nombre del atributo
            tipo_dato (str): Tipo de dato ('texto', 'numero', 'decimal', 'fecha', 'booleano', 'lista')
            descripcion (str): Descripción del atributo
            obligatorio (bool): Si el atributo es obligatorio
            opciones (list): Lista de opciones para tipo 'lista'
        
        Returns:
            AtributoProducto: El atributo creado
        """
        atributo = AtributoProducto.objects.create(
            nombre=nombre,
            tipo_dato=tipo_dato,
            descripcion=descripcion,
            obligatorio=obligatorio,
            opciones=opciones
        )
        return atributo
    
    @staticmethod
    def asociar_atributo_categoria_usuario(atributo, categoria_usuario, orden=0):
        """
        Asocia un atributo con una categoría de usuario
        
        Args:
            atributo (AtributoProducto): El atributo a asociar
            categoria_usuario (categoria_producto_usuario): La categoría de usuario
            orden (int): Orden de visualización
        
        Returns:
            CategoriaAtributo: La asociación creada
        """
        asociacion = CategoriaAtributo.objects.create(
            atributo=atributo,
            categoria_usuario=categoria_usuario,
            orden=orden
        )
        return asociacion
    
    @staticmethod
    def asociar_atributo_categoria_empresa(atributo, categoria_empresa, orden=0):
        """
        Asocia un atributo con una categoría de empresa
        
        Args:
            atributo (AtributoProducto): El atributo a asociar
            categoria_empresa (categoria_producto_empresa): La categoría de empresa
            orden (int): Orden de visualización
        
        Returns:
            CategoriaAtributo: La asociación creada
        """
        asociacion = CategoriaAtributo.objects.create(
            atributo=atributo,
            categoria_empresa=categoria_empresa,
            orden=orden
        )
        return asociacion
    
    @staticmethod
    def asignar_valor_producto_usuario(producto_usuario_obj, atributo, valor):
        """
        Asigna un valor de atributo a un producto de usuario
        
        Args:
            producto_usuario_obj (producto_usuario): El producto de usuario
            atributo (AtributoProducto): El atributo
            valor: El valor a asignar
        
        Returns:
            ValorAtributoProducto: El valor asignado
        """
        valor_atributo, created = ValorAtributoProducto.objects.get_or_create(
            producto_usuario=producto_usuario_obj,
            atributo=atributo
        )
        valor_atributo.set_valor(valor)
        valor_atributo.full_clean()
        valor_atributo.save()
        return valor_atributo
    
    @staticmethod
    def asignar_valor_producto_empresa(producto_empresa_obj, atributo, valor):
        """
        Asigna un valor de atributo a un producto de empresa
        
        Args:
            producto_empresa_obj (producto_empresa): El producto de empresa
            atributo (AtributoProducto): El atributo
            valor: El valor a asignar
        
        Returns:
            ValorAtributoProducto: El valor asignado
        """
        valor_atributo, created = ValorAtributoProducto.objects.get_or_create(
            producto_empresa=producto_empresa_obj,
            atributo=atributo
        )
        valor_atributo.set_valor(valor)
        valor_atributo.full_clean()
        valor_atributo.save()
        return valor_atributo
    
    @staticmethod
    def obtener_atributos_categoria_usuario(categoria_usuario_obj):
        """
        Obtiene todos los atributos asociados a una categoría de usuario
        
        Args:
            categoria_usuario_obj (categoria_producto_usuario): La categoría de usuario
        
        Returns:
            QuerySet: Atributos asociados ordenados
        """
        return AtributoProducto.objects.filter(
            categorias_asociadas__categoria_usuario=categoria_usuario_obj
        ).order_by('categorias_asociadas__orden', 'nombre')
    
    @staticmethod
    def obtener_atributos_categoria_empresa(categoria_empresa_obj):
        """
        Obtiene todos los atributos asociados a una categoría de empresa
        
        Args:
            categoria_empresa_obj (categoria_producto_empresa): La categoría de empresa
        
        Returns:
            QuerySet: Atributos asociados ordenados
        """
        return AtributoProducto.objects.filter(
            categorias_asociadas__categoria_empresa=categoria_empresa_obj
        ).order_by('categorias_asociadas__orden', 'nombre')
    
    @staticmethod
    def obtener_valores_producto_usuario(producto_usuario_obj):
        """
        Obtiene todos los valores de atributos de un producto de usuario
        
        Args:
            producto_usuario_obj (producto_usuario): El producto de usuario
        
        Returns:
            QuerySet: Valores de atributos del producto
        """
        return ValorAtributoProducto.objects.filter(
            producto_usuario=producto_usuario_obj
        ).select_related('atributo')
    
    @staticmethod
    def obtener_valores_producto_empresa(producto_empresa_obj):
        """
        Obtiene todos los valores de atributos de un producto de empresa
        
        Args:
            producto_empresa_obj (producto_empresa): El producto de empresa
        
        Returns:
            QuerySet: Valores de atributos del producto
        """
        return ValorAtributoProducto.objects.filter(
            producto_empresa=producto_empresa_obj
        ).select_related('atributo')
    
    @staticmethod
    @transaction.atomic
    def crear_categoria_con_atributos(nombre_categoria, descripcion_categoria, 
                                    atributos_data, usuario=None, empresa=None):
        """
        Crea una categoría con sus atributos asociados en una transacción
        
        Args:
            nombre_categoria (str): Nombre de la categoría
            descripcion_categoria (str): Descripción de la categoría
            atributos_data (list): Lista de diccionarios con datos de atributos
                Formato: [{
                    'nombre': 'Marca',
                    'tipo_dato': 'texto',
                    'descripcion': 'Marca del producto',
                    'obligatorio': True,
                    'opciones': None  # Solo para tipo 'lista'
                }]
            usuario (usuario): Usuario propietario (opcional)
            empresa (empresa): Empresa propietaria (opcional)
        
        Returns:
            tuple: (categoria, atributos_creados)
        """
        if not ((usuario and not empresa) or (empresa and not usuario)):
            raise ValidationError('Debe especificar exactamente un propietario (usuario o empresa).')
        
        # Crear la categoría
        if usuario:
            categoria = categoria_producto_usuario.objects.create(
                nombre_categoria_prod_usuario=nombre_categoria,
                descripcion_categoria_prod_usuario=descripcion_categoria,
                id_usuario_fk=usuario
            )
        else:
            categoria = categoria_producto_empresa.objects.create(
                nombre_categoria_prod_empresa=nombre_categoria,
                descripcion_categoria_prod_empresa=descripcion_categoria,
                id_empresa_fk=empresa
            )
        
        # Crear y asociar atributos
        atributos_creados = []
        for i, attr_data in enumerate(atributos_data):
            # Crear o obtener el atributo
            atributo, created = AtributoProducto.objects.get_or_create(
                nombre=attr_data['nombre'],
                defaults={
                    'tipo_dato': attr_data['tipo_dato'],
                    'descripcion': attr_data.get('descripcion', ''),
                    'obligatorio': attr_data.get('obligatorio', False),
                    'opciones': attr_data.get('opciones')
                }
            )
            
            # Asociar con la categoría
            if usuario:
                EAVHelper.asociar_atributo_categoria_usuario(atributo, categoria, orden=i)
            else:
                EAVHelper.asociar_atributo_categoria_empresa(atributo, categoria, orden=i)
            
            atributos_creados.append(atributo)
        
        return categoria, atributos_creados
    
    @staticmethod
    @transaction.atomic
    def crear_producto_con_valores(datos_producto, valores_atributos, usuario=None, empresa=None):
        """
        Crea un producto con sus valores de atributos en una transacción
        
        Args:
            datos_producto (dict): Datos básicos del producto
            valores_atributos (dict): Diccionario {atributo_id: valor}
            usuario (usuario): Usuario propietario (opcional)
            empresa (empresa): Empresa propietaria (opcional)
        
        Returns:
            tuple: (producto, valores_creados)
        """
        if not ((usuario and not empresa) or (empresa and not usuario)):
            raise ValidationError('Debe especificar exactamente un propietario (usuario o empresa).')
        
        # Crear el producto
        if usuario:
            producto = producto_usuario.objects.create(**datos_producto)
        else:
            producto = producto_empresa.objects.create(**datos_producto)
        
        # Asignar valores de atributos
        valores_creados = []
        for atributo_id, valor in valores_atributos.items():
            atributo = AtributoProducto.objects.get(id=atributo_id)
            
            if usuario:
                valor_atributo = EAVHelper.asignar_valor_producto_usuario(producto, atributo, valor)
            else:
                valor_atributo = EAVHelper.asignar_valor_producto_empresa(producto, atributo, valor)
            
            valores_creados.append(valor_atributo)
        
        return producto, valores_creados


# Funciones de consulta útiles
def buscar_productos_por_atributo(nombre_atributo, valor, tipo_producto='ambos'):
    """
    Busca productos que tengan un atributo específico con un valor determinado
    
    Args:
        nombre_atributo (str): Nombre del atributo
        valor: Valor a buscar
        tipo_producto (str): 'usuario', 'empresa' o 'ambos'
    
    Returns:
        dict: {'productos_usuario': QuerySet, 'productos_empresa': QuerySet}
    """
    atributo = AtributoProducto.objects.get(nombre=nombre_atributo)
    
    resultados = {'productos_usuario': None, 'productos_empresa': None}
    
    if tipo_producto in ['usuario', 'ambos']:
        if atributo.tipo_dato == 'texto' or atributo.tipo_dato == 'lista':
            valores = ValorAtributoProducto.objects.filter(
                atributo=atributo,
                valor_texto__icontains=valor,
                producto_usuario__isnull=False
            )
        elif atributo.tipo_dato == 'numero':
            valores = ValorAtributoProducto.objects.filter(
                atributo=atributo,
                valor_numero=valor,
                producto_usuario__isnull=False
            )
        # Agregar más tipos según necesidad
        
        resultados['productos_usuario'] = producto_usuario.objects.filter(
            id__in=valores.values_list('producto_usuario_id', flat=True)
        )
    
    if tipo_producto in ['empresa', 'ambos']:
        if atributo.tipo_dato == 'texto' or atributo.tipo_dato == 'lista':
            valores = ValorAtributoProducto.objects.filter(
                atributo=atributo,
                valor_texto__icontains=valor,
                producto_empresa__isnull=False
            )
        elif atributo.tipo_dato == 'numero':
            valores = ValorAtributoProducto.objects.filter(
                atributo=atributo,
                valor_numero=valor,
                producto_empresa__isnull=False
            )
        
        resultados['productos_empresa'] = producto_empresa.objects.filter(
            id__in=valores.values_list('producto_empresa_id', flat=True)
        )
    
    return resultados


def obtener_atributos_disponibles():
    """
    Obtiene todos los atributos disponibles en el sistema
    
    Returns:
        QuerySet: Todos los atributos ordenados por nombre
    """
    return AtributoProducto.objects.all().order_by('nombre')


def obtener_estadisticas_atributos():
    """
    Obtiene estadísticas de uso de atributos
    
    Returns:
        dict: Estadísticas de atributos
    """
    from django.db.models import Count
    
    stats = {
        'total_atributos': AtributoProducto.objects.count(),
        'atributos_por_tipo': AtributoProducto.objects.values('tipo_dato').annotate(
            count=Count('id')
        ),
        'atributos_mas_usados': AtributoProducto.objects.annotate(
            uso_count=Count('valores')
        ).order_by('-uso_count')[:10],
        'categorias_con_atributos': CategoriaAtributo.objects.values(
            'categoria_usuario__nombre_categoria_prod_usuario',
            'categoria_empresa__nombre_categoria_prod_empresa'
        ).annotate(count=Count('atributo')).order_by('-count')
    }
    
    return stats