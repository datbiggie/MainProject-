from django.db import models
from django.utils import timezone

# Create your models here.
class usuario(models.Model):
    OPCIONES_AUTENTICACION = [
        ('local', 'Local'),
        ('google', 'Google'),
    ]

    OPCIONES_ROL = [
        ('persona', 'Persona'),
        ('empresa', 'Empresa'),
    ]

    id_usuario = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=150)
    correo_usuario = models.EmailField(unique=True)
    telefono_usuario = models.CharField(max_length=20, blank=True, null=True)
    password_usuario = models.CharField(max_length=255)
    autenticacion_usuario = models.CharField(max_length=10, choices=OPCIONES_AUTENTICACION, default='local')
    fecha_nacimiento = models.DateField()  
    pais = models.CharField(max_length=100)  
    estado = models.CharField(max_length=100)  
    rol_usuario = models.CharField(max_length=10, choices=OPCIONES_ROL, default='persona')
    foto_usuario = models.ImageField(upload_to='perfil_usuario/', blank=True, null=True)
    avatar_chatbot = models.CharField(max_length=255, default='avatars/Cartoon Style Robot.jpg', help_text='Avatar para el chatbot')
    fecha_registro_usuario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_usuario
    


class empresa(models.Model):
    OPCIONES_TIPO_EMPRESA = [
        ('pequeña', 'Pequeña'),
        ('mediana', 'Mediana'),
        ('grande', 'Grande'),
    ]

    OPCIONES_ROL = [
        ('persona', 'Persona'),
        ('empresa', 'Empresa'),
    ]

    OPCIONES_SECTOR = [
        ('tecnologia', 'Tecnología'),
        ('alimentos_bebidas', 'Alimentos y Bebidas'),
        ('moda_ropa', 'Moda y Ropa'),
        ('hogar', 'Hogar'),
        ('salud_belleza', 'Salud y Belleza'),
        ('deportes_ocio', 'Deportes y Ocio'),
        ('servicios', 'Servicios'),
    ]

    id_empresa = models.AutoField(primary_key=True)
    nombre_empresa = models.CharField(max_length=150)
    correo_empresa = models.EmailField(unique=True)
    password_empresa = models.CharField(max_length=255)
    descripcion_empresa = models.TextField(blank=True, null=True)
    logo_empresa = models.ImageField(upload_to='logos_empresas/', blank=True, null=True)
    pais_empresa = models.CharField(max_length=100)
    estado_empresa = models.CharField(max_length=100)
    tipo_empresa = models.CharField(max_length=10, choices=OPCIONES_TIPO_EMPRESA)
    sector_empresa = models.CharField(max_length=50, choices=OPCIONES_SECTOR, blank=True, null=True)
    direccion_empresa = models.CharField(max_length=255)
    avatar_chatbot_empresa = models.CharField(max_length=255, default='avatars/Cartoon Style Robot.jpg', help_text='Avatar para el chatbot de la empresa')
    rol_empresa = models.CharField(max_length=10, choices=OPCIONES_ROL, default='empresa')
    fecha_registro_empresa = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_empresa
    
class sucursal(models.Model):
    id_sucursal = models.AutoField(primary_key=True)
    nombre_sucursal = models.CharField(max_length=100)
    direccion_sucursal = models.TextField()
    telefono_sucursal = models.CharField(max_length=20)
    estado_sucursal = models.CharField(max_length=50)
    latitud_sucursal = models.FloatField()
    longitud_sucursal = models.FloatField()
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='sucursales')

    def __str__(self):
        return self.nombre_sucursal
    
class categoria_producto_empresa(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    id_categoria_prod_empresa = models.AutoField(primary_key=True)
    nombre_categoria_prod_empresa = models.CharField(max_length=100)
    descripcion_categoria_prod_empresa = models.TextField(blank=True, null=True)
    generico = models.CharField(max_length=1, choices=[('s', 'Sí'), ('n', 'No')], default='n')
    estatus_categoria_prod_empresa = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    fecha_creacion_prod_empresa = models.DateTimeField(auto_now_add=True)
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='categorias_producto', null=True, blank=True)

    def __str__(self):
        return self.nombre_categoria_prod_empresa
    

class categoria_servicio_empresa(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    id_categoria_serv_empresa = models.AutoField(primary_key=True)
    nombre_categoria_serv_empresa = models.CharField(max_length=100, unique=True)
    descripcion_categoria_serv_empresa = models.TextField(blank=True, null=True)
    generico = models.CharField(max_length=1, choices=[('s', 'Sí'), ('n', 'No')], default='n')
    estatus_categoria_serv_empresa = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    fecha_creacion_categ_serv_empresa = models.DateField(auto_now_add=True)
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='categorias_servicio', null=True, blank=True)

    def __str__(self):
        return self.nombre_categoria_serv_empresa
    


class producto_empresa(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    id_producto_empresa = models.AutoField(primary_key=True)
    nombre_producto_empresa = models.CharField(max_length=150)
    descripcion_producto_empresa = models.TextField(blank=True, null=True)
    # El campo imagen_producto se ha movido a la tabla imagen_producto
    caracteristicas_generales_empresa = models.TextField(blank=True, null=True)
    # El campo estatus_producto se ha movido a producto_sucursal como estatus_producto_sucursal
    fecha_creacion_producto_empresa = models.DateTimeField(auto_now_add=True)
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='productos')
    id_categoria_prod_fk = models.ForeignKey('categoria_producto_empresa', on_delete=models.SET_NULL, null=True, related_name='productos')

    def __str__(self):
        return self.nombre_producto_empresa
    

    

class servicio_empresa(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    id_servicio_empresa = models.AutoField(primary_key=True)
    nombre_servicio_empresa = models.CharField(max_length=150)
    descripcion_servicio_empresa = models.TextField(blank=True, null=True)
    # El campo imagen_servicio se ha movido a la tabla imagen_servicio
    # El campo estatus_servicio se ha movido a servicio_sucursal como estatus_servicio_sucursal
    fecha_creacion_servicio_empresa = models.DateTimeField(auto_now_add=True)
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='servicios')
    id_categoria_servicios_fk = models.ForeignKey('categoria_servicio_empresa', on_delete=models.SET_NULL, null=True, related_name='servicios')

    def __str__(self):
        return self.nombre_servicio_empresa
    
    
class producto_sucursal(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    
    CONDICION_CHOICES = [
        ('Nuevo', 'Nuevo'),
        ('Usado', 'Usado'),
    ]
    
    id_producto_sucursal = models.AutoField(primary_key=True)
    stock_producto_sucursal = models.PositiveIntegerField(default=0)
    precio_producto_sucursal = models.DecimalField(max_digits=10, decimal_places=2)
    # Presentación del producto en la sucursal (unidad/paquete/bulto/...)
    UNIDAD_PRESENTACION_CHOICES = [
        ('unidad', 'Unidad'),
        ('paquete', 'Paquete'),
        ('bulto', 'Bulto'),
        ('caja', 'Caja'),
        ('kg', 'Kilogramo'),
        ('l', 'Litro'),
        ('otro', 'Otro'),
    ]

    unidad_presentacion_producto_sucursal = models.CharField(
        max_length=20,
        choices=UNIDAD_PRESENTACION_CHOICES,
        default='unidad',
        help_text='Formato de presentación del producto en la sucursal'
    )

    cantidad_por_presentacion_producto_sucursal = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Si aplica, cantidad de unidades por presentación (ej.: 6 por paquete)'
    )
    condicion_producto_sucursal = models.CharField(max_length=10, choices=CONDICION_CHOICES, default='Nuevo')
    estatus_producto_sucursal = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    id_sucursal_fk = models.ForeignKey('sucursal', on_delete=models.CASCADE, related_name='productos_sucursal')
    id_producto_fk = models.ForeignKey('producto_empresa', on_delete=models.CASCADE, related_name='sucursales_producto')

    def __str__(self):
        return f"{self.id_producto_fk.nombre_producto_empresa} en {self.id_sucursal_fk.nombre_sucursal}"


# Modelo para asociar servicios a sucursales
class servicio_sucursal(models.Model):
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    id_servicio_sucursal = models.AutoField(primary_key=True)
    precio_servicio_sucursal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    estatus_servicio_sucursal = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')
    id_sucursal_fk = models.ForeignKey('sucursal', on_delete=models.CASCADE, related_name='servicios_sucursal')
    id_servicio_fk = models.ForeignKey('servicio_empresa', on_delete=models.CASCADE, related_name='sucursales_servicio')

    def __str__(self):
        return f"{self.id_servicio_fk.nombre_servicio_empresa} en {self.id_sucursal_fk.nombre_sucursal}"


# Modelo para manejar múltiples imágenes de productos
class imagen_producto_empresa(models.Model):
    id_imagen_producto_empresa = models.AutoField(primary_key=True)
    ruta_imagen_producto_empresa = models.ImageField(upload_to='imagenes_productos/')
    id_producto_fk = models.ForeignKey('producto_empresa', on_delete=models.CASCADE, related_name='imagenes')
    fecha_creacion_producto_empresa = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen {self.id_imagen_producto_empresa} - {self.id_producto_fk.nombre_producto_empresa}"


# Modelo para manejar múltiples imágenes de servicios
class imagen_servicio_empresa(models.Model):
    id_imagen_servicio_empresa = models.AutoField(primary_key=True)
    ruta_imagen_servicio_empresa = models.ImageField(upload_to='imagenes_servicios/')
    id_servicio_fk = models.ForeignKey('servicio_empresa', on_delete=models.CASCADE, related_name='imagenes')
    fecha_creacion_servicio_empresa = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen {self.id_imagen_servicio_empresa} - {self.id_servicio_fk.nombre_servicio_empresa}"


class categoria_producto_usuario(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    id_categoria_prod_usuario = models.AutoField(primary_key=True)
    nombre_categoria_prod_usuario = models.CharField(max_length=100)
    descripcion_categoria_prod_usuario = models.TextField(blank=True, null=True)
    generico = models.CharField(max_length=1, choices=[('s', 'Sí'), ('n', 'No')], default='n')
    estatus_categoria_prod_usuario = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    fecha_creacion_prod_usuario = models.DateTimeField(auto_now_add=True)
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='categorias_producto', null=True, blank=True)

    def __str__(self):
        return self.nombre_categoria_prod_usuario
    

class categoria_servicio_usuario(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    
    id_categoria_serv_usuario = models.AutoField(primary_key=True)
    nombre_categoria_serv_usuario = models.CharField(max_length=100, unique=True)
    descripcion_categoria_serv_usuario = models.TextField(blank=True, null=True)
    generico = models.CharField(max_length=1, choices=[('s', 'Sí'), ('n', 'No')], default='n')
    estatus_categoria_serv_usuario = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    fecha_creacion_categ_serv_usuario = models.DateField(auto_now_add=True)
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='categorias_servicio', null=True, blank=True)

    def __str__(self):
        return self.nombre_categoria_serv_usuario


class producto_usuario(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    
    CONDICION_CHOICES = [
        ('Nuevo', 'Nuevo'),
        ('Usado', 'Usado'),
    ]

    id_producto_usuario = models.AutoField(primary_key=True)
    nombre_producto_usuario = models.CharField(max_length=150)
    descripcion_producto_usuario = models.TextField(blank=True, null=True)
    caracteristicas_generales_usuario = models.TextField(blank=True, null=True)
    stock_producto_usuario = models.PositiveIntegerField(default=0)
    precio_producto_usuario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Presentación del producto para usuarios (unidad/paquete/bulto/...)
    UNIDAD_PRESENTACION_CHOICES = [
        ('unidad', 'Unidad'),
        ('paquete', 'Paquete'),
        ('bulto', 'Bulto'),
        ('caja', 'Caja'),
        ('kg', 'Kilogramo'),
        ('l', 'Litro'),
        ('otro', 'Otro'),
    ]

    unidad_presentacion_producto_usuario = models.CharField(
        max_length=20,
        choices=UNIDAD_PRESENTACION_CHOICES,
        default='unidad',
        help_text='Formato de presentación del producto (unidades, paquetes, bultos, etc.)'
    )

    cantidad_por_presentacion_producto_usuario = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Si aplica, cantidad de unidades por cada presentación (ej.: 6 por paquete).'
    )
    condicion_producto_usuario = models.CharField(max_length=10, choices=CONDICION_CHOICES, default='Nuevo')
    estatus_producto_usuario = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    latitud_entrega_producto = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitud_entrega_producto = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    fecha_creacion_producto_usuario = models.DateTimeField(auto_now_add=True)
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='productos')
    id_categoria_prod_fk = models.ForeignKey('categoria_producto_usuario', on_delete=models.SET_NULL, null=True, related_name='productos')

    def __str__(self):
        return self.nombre_producto_usuario


class servicio_usuario(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    id_servicio_usuario = models.AutoField(primary_key=True)
    nombre_servicio_usuario = models.CharField(max_length=150)
    descripcion_servicio_usuario = models.TextField(blank=True, null=True)
    precio_servicio_usuario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    estatus_servicio_usuario = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    fecha_creacion_servicio_usuario = models.DateTimeField(auto_now_add=True)
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='servicios')
    id_categoria_servicios_fk = models.ForeignKey('categoria_servicio_usuario', on_delete=models.SET_NULL, null=True, related_name='servicios')

    def __str__(self):
        return self.nombre_servicio_usuario


class imagen_producto_usuario(models.Model):
    id_imagen_producto_usuario = models.AutoField(primary_key=True)
    ruta_imagen_producto_usuario = models.ImageField(upload_to='imagenes_productos/')
    id_producto_fk = models.ForeignKey('producto_usuario', on_delete=models.CASCADE, related_name='imagenes')
    fecha_creacion_producto_usuario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen {self.id_imagen_producto_usuario} - {self.id_producto_fk.nombre_producto_usuario}"


class imagen_servicio_usuario(models.Model):
    id_imagen_servicio_usuario = models.AutoField(primary_key=True)
    ruta_imagen_servicio_usuario = models.ImageField(upload_to='imagenes_servicios/')
    id_servicio_fk = models.ForeignKey('servicio_usuario', on_delete=models.CASCADE, related_name='imagenes')
    fecha_creacion_servicio_usuario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen de {self.id_servicio_fk.nombre_servicio_usuario}"


class carrito_compra_producto_usuario(models.Model):
    ESTATUS_CHOICES = [
        ('activo', 'Activo'),
        ('pendiente', 'Pendiente'),
    ]

    id_carrito_prod_usuario = models.AutoField(primary_key=True)
    estatuscarrito_prod_usuario = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='activo')
    fecha_creacion_carrito_prod_usuario = models.DateTimeField(auto_now_add=True)
    total_carrito_prod_usuario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='carritos_compra')

    def __str__(self):
        return f"Carrito {self.id_carrito_prod_usuario} - {self.id_usuario_fk.nombre_usuario}"


class detalle_compra_producto_usuario(models.Model):
    id_deta_carrito_prod_usuario = models.AutoField(primary_key=True)
    cantidad_deta_carrito_prod_usuario = models.PositiveIntegerField(default=1)
    precio_unit_deta_carrito_prod_usuario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_original_deta_carrito_prod_usuario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal_deta_carrito_prod_usuario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_agregado_deta_carrito_prod_usuario = models.DateTimeField(auto_now_add=True)
    id_fk_carritocompra_usuario = models.ForeignKey('carrito_compra_producto_usuario', on_delete=models.CASCADE, related_name='detalles')
    idproducto_fk_usuario = models.ForeignKey('producto_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='detalles_carrito')
    id_fk_producto_sucursal_empresa = models.ForeignKey('producto_sucursal', on_delete=models.CASCADE, null=True, blank=True, related_name='detalles_carrito_usuario')

    def __str__(self):
        return f"Detalle {self.id_deta_carrito_prod_usuario} - Carrito {self.id_fk_carritocompra_usuario.id_carrito_prod_usuario}"


class carrito_compra_producto_empresa(models.Model):
    ESTATUS_CHOICES = [
        ('activo', 'Activo'),
        ('pendiente', 'Pendiente'),
    ]

    id_carrito_prod_empresa = models.AutoField(primary_key=True)
    estatuscarrito_prod_empresa = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='activo')
    fecha_creacion_carrito_prod_empresa = models.DateTimeField(auto_now_add=True)
    total_carrito_prod_empresa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='carritos_compra')

    def __str__(self):
        return f"Carrito {self.id_carrito_prod_empresa} - {self.id_empresa_fk.nombre_empresa}"


class detalle_compra_producto_empresa(models.Model):
    id_deta_carrito_prod_empresa = models.AutoField(primary_key=True)
    cantidad_deta_carrito_prod_empresa = models.PositiveIntegerField(default=1)
    precio_unit_deta_carrito_prod_empresa = models.DecimalField(max_digits=10, decimal_places=2)
    precio_original_deta_carrito_prod_empresa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal_deta_carrito_prod_empresa = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_agregado_deta_carrito_prod_empresa = models.DateTimeField(auto_now_add=True)
    id_fk_carritocompra_empresa = models.ForeignKey('carrito_compra_producto_empresa', on_delete=models.CASCADE, related_name='detalles')
    idproducto_fk_usuario = models.ForeignKey('producto_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='detalles_carrito_empresa')
    id_fk_producto_sucursal_empresa = models.ForeignKey('producto_sucursal', on_delete=models.CASCADE, null=True, blank=True, related_name='detalles_carrito_empresa')

    def __str__(self):
        return f"Detalle {self.id_deta_carrito_prod_empresa} - Carrito {self.id_fk_carritocompra_empresa.id_carrito_prod_empresa}"


# MODELOS DE PEDIDOS
class pedido_usuario(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Efectivo'),
        ('paypal', 'PayPal'),
    ]
    
    id_pedido_usuario = models.AutoField(primary_key=True)
    id_carrito_fk = models.ForeignKey('carrito_compra_producto_usuario', on_delete=models.CASCADE, related_name='pedidos')
    numero_pedido = models.CharField(max_length=20, unique=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    direccion_envio = models.TextField()
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES)
    comprobante_pago = models.ImageField(upload_to='comprobantes_pago/', null=True, blank=True)
    notas_pedido = models.TextField(null=True, blank=True)
    comentario_rechazo = models.TextField(null=True, blank=True, help_text='Comentario explicando el motivo del rechazo del pedido')
    
    def __str__(self):
        return f"Pedido {self.numero_pedido} - Usuario {self.id_carrito_fk.id_usuario_fk.nombre_usuario}"


class detalle_pedido_usuario(models.Model):
    id_detalle_pedido_usuario = models.AutoField(primary_key=True)
    id_pedido_fk = models.ForeignKey('pedido_usuario', on_delete=models.CASCADE, related_name='detalles')
    idproducto_fk_usuario = models.ForeignKey('producto_usuario', null=True, blank=True, on_delete=models.SET_NULL, related_name='detalles_pedido_usuario')
    id_fk_producto_sucursal_empresa = models.ForeignKey('producto_sucursal', null=True, blank=True, on_delete=models.SET_NULL, related_name='detalles_pedido_usuario')
    cantidad_detalle_pedido = models.PositiveIntegerField()
    precio_unitario_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_detalle_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not (bool(self.idproducto_fk_usuario) ^ bool(self.id_fk_producto_sucursal_empresa)):
            raise ValidationError('Debe especificar exactamente un tipo de producto')
    
    def __str__(self):
        return f"Detalle {self.id_detalle_pedido_usuario} - Pedido {self.id_pedido_fk.numero_pedido}"


class pedido_empresa(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Efectivo'),
        ('paypal', 'PayPal'),
    ]
    
    id_pedido_empresa = models.AutoField(primary_key=True)
    id_carrito_fk = models.ForeignKey('carrito_compra_producto_empresa', on_delete=models.CASCADE, related_name='pedidos')
    numero_pedido = models.CharField(max_length=20, unique=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    direccion_envio = models.TextField()
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES)
    comprobante_pago = models.ImageField(upload_to='comprobantes_pago/', null=True, blank=True)
    notas_pedido = models.TextField(null=True, blank=True)
    comentario_rechazo = models.TextField(null=True, blank=True, help_text='Comentario explicando el motivo del rechazo del pedido')
    
    def __str__(self):
        return f"Pedido {self.numero_pedido} - Empresa {self.id_carrito_fk.id_empresa_fk.nombre_empresa}"


class detalle_pedido_empresa(models.Model):
    id_detalle_pedido_empresa = models.AutoField(primary_key=True)
    id_pedido_fk = models.ForeignKey('pedido_empresa', on_delete=models.CASCADE, related_name='detalles')
    idproducto_fk_usuario = models.ForeignKey('producto_usuario', null=True, blank=True, on_delete=models.SET_NULL, related_name='detalles_pedido_empresa')
    id_fk_producto_sucursal_empresa = models.ForeignKey('producto_sucursal', null=True, blank=True, on_delete=models.SET_NULL, related_name='detalles_pedido_empresa')
    cantidad_detalle_pedido = models.PositiveIntegerField()
    precio_unitario_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_detalle_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not (bool(self.idproducto_fk_usuario) ^ bool(self.id_fk_producto_sucursal_empresa)):
            raise ValidationError('Debe especificar exactamente un tipo de producto')
    
    def __str__(self):
        return f"Detalle Pedido {self.id_detalle_pedido_empresa} - Pedido {self.id_pedido_fk.numero_pedido}"


class solicitud_servicio_usuario(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('cotizada', 'Cotizada'),
        ('aceptada', 'Aceptada'),
        ('pagada', 'Pagada'),
        ('completada', 'Completada'),
        ('rechazada', 'Rechazada'),
    ]
    
    id_solicitud_servicio_usuario = models.AutoField(primary_key=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_requerida = models.DateTimeField()
    direccion = models.TextField()
    descripcion_detallada = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Campos de cotización
    presupuesto_cotizacion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Presupuesto de la cotización')
    descripcion_cotizacion = models.TextField(null=True, blank=True, help_text='Descripción de la cotización')
    archivo_cotizacion = models.FileField(upload_to='cotizaciones/', null=True, blank=True, help_text='Archivo de cotización (PDF, DOC, DOCX, JPG, PNG)')
    fecha_cotizacion = models.DateTimeField(null=True, blank=True, help_text='Fecha cuando se envió la cotización')
    
    # Campo de rechazo
    motivo_rechazo = models.TextField(null=True, blank=True, help_text='Motivo del rechazo de la solicitud')
    fecha_rechazo = models.DateTimeField(null=True, blank=True, help_text='Fecha cuando se rechazó la solicitud')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Foreign Keys
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='solicitudes_servicio')
    id_servicio_usuario_fk = models.ForeignKey('servicio_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='solicitudes')
    id_servicio_sucursal_fk = models.ForeignKey('servicio_sucursal', on_delete=models.CASCADE, null=True, blank=True, related_name='solicitudes_usuario')
    
    def __str__(self):
        return f"Solicitud {self.id_solicitud_servicio_usuario} - {self.estado}"


class solicitud_servicio_empresa(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('cotizada', 'Cotizada'),
        ('aceptada', 'Aceptada'),
        ('pagada', 'Pagada'),
        ('completada', 'Completada'),
        ('rechazada', 'Rechazada'),
    ]
    
    id_solicitud_servicio_empresa = models.AutoField(primary_key=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_requerida = models.DateTimeField()
    direccion = models.TextField()
    descripcion_detallada = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Campos de cotización
    presupuesto_cotizacion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Presupuesto de la cotización')
    descripcion_cotizacion = models.TextField(null=True, blank=True, help_text='Descripción de la cotización')
    archivo_cotizacion = models.FileField(upload_to='cotizaciones/', null=True, blank=True, help_text='Archivo de cotización (PDF, DOC, DOCX, JPG, PNG)')
    fecha_cotizacion = models.DateTimeField(null=True, blank=True, help_text='Fecha cuando se envió la cotización')
    
    # Campo de rechazo
    motivo_rechazo = models.TextField(null=True, blank=True, help_text='Motivo del rechazo de la solicitud')
    fecha_rechazo = models.DateTimeField(null=True, blank=True, help_text='Fecha cuando se rechazó la solicitud')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Foreign Keys
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='solicitudes_servicio')
    id_servicio_usuario_fk = models.ForeignKey('servicio_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='solicitudes_empresa')
    id_servicio_sucursal_fk = models.ForeignKey('servicio_sucursal', on_delete=models.CASCADE, null=True, blank=True, related_name='solicitudes_empresa')
    
    def __str__(self):
        return f"Solicitud {self.id_solicitud_servicio_empresa} - {self.estado}"


class notificacion_usuario(models.Model):
    TIPOS_NOTIFICACION = [
        ('pedido_confirmado', 'Pedido Confirmado'),
        ('pedido_rechazado', 'Pedido Rechazado'),
        ('pedido_enviado', 'Pedido Enviado'),
        ('pedido_entregado', 'Pedido Entregado'),
        ('servicio_cotizado', 'Servicio Cotizado'),
        ('servicio_aceptado', 'Servicio Aceptado'),
        ('servicio_completado', 'Servicio Completado'),
    ]
    
    ESTADOS_NOTIFICACION = [
        ('no_leida', 'No Leída'),
        ('leida', 'Leída'),
    ]
    
    id_notificacion_usuario = models.AutoField(primary_key=True)
    tipo_notificacion = models.CharField(max_length=20, choices=TIPOS_NOTIFICACION)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    estado = models.CharField(max_length=10, choices=ESTADOS_NOTIFICACION, default='no_leida')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_leida = models.DateTimeField(null=True, blank=True)
    
    # Relaciones
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='notificaciones')
    id_pedido_usuario_fk = models.ForeignKey('pedido_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    id_solicitud_servicio_usuario_fk = models.ForeignKey('solicitud_servicio_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    
    def __str__(self):
        return f"Notificación {self.id_notificacion_usuario} - {self.titulo} - Usuario {self.id_usuario_fk.nombre_usuario}"


class notificacion_empresa(models.Model):
    TIPOS_NOTIFICACION = [
        ('venta_pendiente', 'Venta Pendiente'),
        ('venta_confirmada', 'Venta Confirmada'),
        ('venta_rechazada', 'Venta Rechazada'),
        ('nuevo_pedido', 'Nuevo Pedido'),
        ('solicitud_servicio', 'Nueva Solicitud de Servicio'),
        ('servicio_pagado', 'Servicio Pagado'),
    ]
    
    ESTADOS_NOTIFICACION = [
        ('no_leida', 'No Leída'),
        ('leida', 'Leída'),
    ]
    
    id_notificacion_empresa = models.AutoField(primary_key=True)
    tipo_notificacion = models.CharField(max_length=20, choices=TIPOS_NOTIFICACION)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    estado = models.CharField(max_length=10, choices=ESTADOS_NOTIFICACION, default='no_leida')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_leida = models.DateTimeField(null=True, blank=True)
    
    # Relaciones
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='notificaciones')
    id_pedido_empresa_fk = models.ForeignKey('pedido_empresa', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    id_solicitud_servicio_empresa_fk = models.ForeignKey('solicitud_servicio_empresa', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    
    def __str__(self):
        return f"Notificación {self.id_notificacion_empresa} - {self.titulo} - Empresa {self.id_empresa_fk.nombre_empresa}"


class favorito_usuario(models.Model):
    id_favorito_usuario = models.AutoField(primary_key=True)
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='favoritos')
    
    # Items que puede guardar un usuario como favoritos
    id_producto_usuario_fk = models.ForeignKey('producto_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='favoritos_usuario')
    id_producto_sucursal_fk = models.ForeignKey('producto_sucursal', on_delete=models.CASCADE, null=True, blank=True, related_name='favoritos_usuario')
    id_servicio_usuario_fk = models.ForeignKey('servicio_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='favoritos_usuario')
    id_servicio_sucursal_fk = models.ForeignKey('servicio_sucursal', on_delete=models.CASCADE, null=True, blank=True, related_name='favoritos_usuario')
    
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('id_usuario_fk', 'id_producto_usuario_fk'),
            ('id_usuario_fk', 'id_producto_sucursal_fk'),
            ('id_usuario_fk', 'id_servicio_usuario_fk'),
            ('id_usuario_fk', 'id_servicio_sucursal_fk'),
        ]
        db_table = 'favoritos_usuarios'
        verbose_name = 'Favorito de Usuario'
        verbose_name_plural = 'Favoritos de Usuarios'
        ordering = ['-fecha_agregado']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validar que solo uno de los items esté definido
        items = [self.id_producto_usuario_fk, self.id_producto_sucursal_fk, 
                self.id_servicio_usuario_fk, self.id_servicio_sucursal_fk]
        if sum(x is not None for x in items) != 1:
            raise ValidationError('Debe especificar exactamente un item como favorito')
    
    def __str__(self):
        if self.id_producto_usuario_fk:
            item = self.id_producto_usuario_fk.nombre_producto_usuario
        elif self.id_producto_sucursal_fk:
            item = self.id_producto_sucursal_fk.id_producto_fk.nombre_producto_empresa
        elif self.id_servicio_usuario_fk:
            item = self.id_servicio_usuario_fk.nombre_servicio_usuario
        else:
            item = self.id_servicio_sucursal_fk.id_servicio_fk.nombre_servicio_empresa
        
        return f'{self.id_usuario_fk.nombre_usuario} - {item}'


class favorito_empresa_sucursal(models.Model):
    id_favorito_empresa = models.AutoField(primary_key=True)
    id_empresa_fk = models.ForeignKey('empresa', on_delete=models.CASCADE, related_name='favoritos')
    
    # Items que puede guardar una empresa como favoritos (solo de usuarios individuales)
    id_producto_usuario_fk = models.ForeignKey('producto_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='favoritos_empresa')
    id_servicio_usuario_fk = models.ForeignKey('servicio_usuario', on_delete=models.CASCADE, null=True, blank=True, related_name='favoritos_empresa')
    
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('id_empresa_fk', 'id_producto_usuario_fk'),
            ('id_empresa_fk', 'id_servicio_usuario_fk'),
        ]
        db_table = 'favoritos_empresas'
        verbose_name = 'Favorito de Empresa'
        verbose_name_plural = 'Favoritos de Empresas'
        ordering = ['-fecha_agregado']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validar que solo uno de los items esté definido
        items = [self.id_producto_usuario_fk, self.id_servicio_usuario_fk]
        if sum(x is not None for x in items) != 1:
            raise ValidationError('Debe especificar exactamente un item como favorito')
    
    def __str__(self):
        if self.id_producto_usuario_fk:
            item = self.id_producto_usuario_fk.nombre_producto_usuario
        else:
            item = self.id_servicio_usuario_fk.nombre_servicio_usuario
        
        return f'{self.id_empresa_fk.nombre_empresa} - {item}'


# ===== MODELOS EAV (Entity-Attribute-Value) =====

class AtributoProducto(models.Model):
    """Tabla de atributos dinámicos para productos"""
    TIPOS_DATO = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('decimal', 'Decimal'),
        ('fecha', 'Fecha'),
        ('booleano', 'Booleano'),
        ('lista', 'Lista de opciones')
    ]
    
    id_atributo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    tipo_dato = models.CharField(max_length=20, choices=TIPOS_DATO)
    opciones = models.JSONField(null=True, blank=True, help_text='Para tipo lista: ["opcion1", "opcion2"]')
    obligatorio = models.BooleanField(default=False)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Atributo de Producto'
        verbose_name_plural = 'Atributos de Productos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_dato_display()})"


class CategoriaAtributo(models.Model):
    """Tabla intermedia que asocia atributos con categorías"""
    id_categoria_atributo = models.AutoField(primary_key=True)
    
    # FK a AtributoProducto
    atributo = models.ForeignKey(AtributoProducto, on_delete=models.CASCADE, related_name='categorias_asociadas')
    
    # FK a categorías de usuario (opcional)
    categoria_usuario = models.ForeignKey(
        'categoria_producto_usuario', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='atributos_asociados'
    )
    
    # FK a categorías de empresa (opcional)
    categoria_empresa = models.ForeignKey(
        'categoria_producto_empresa', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='atributos_asociados'
    )
    
    orden = models.PositiveIntegerField(default=0, help_text='Orden de visualización del atributo')
    fecha_asociacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría-Atributo'
        verbose_name_plural = 'Categorías-Atributos'
        unique_together = [
            ('atributo', 'categoria_usuario'),
            ('atributo', 'categoria_empresa')
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(categoria_usuario__isnull=False, categoria_empresa__isnull=True) |
                    models.Q(categoria_usuario__isnull=True, categoria_empresa__isnull=False)
                ),
                name='categoria_atributo_exclusiva'
            )
        ]
        ordering = ['orden', 'fecha_asociacion']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validar que solo una categoría esté asignada
        if not ((self.categoria_usuario and not self.categoria_empresa) or 
                (self.categoria_empresa and not self.categoria_usuario)):
            raise ValidationError('Debe asignar exactamente una categoría (usuario o empresa).')
    
    def __str__(self):
        categoria = self.categoria_usuario or self.categoria_empresa
        categoria_tipo = 'Usuario' if self.categoria_usuario else 'Empresa'
        return f"{self.atributo.nombre} → {categoria} ({categoria_tipo})"


class ValorAtributoProducto(models.Model):
    """Tabla de valores de atributos para productos específicos"""
    id_valor_atributo = models.AutoField(primary_key=True)
    
    # FK a productos (puede ser de usuario o empresa)
    producto_usuario = models.ForeignKey(
        'producto_usuario', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='valores_atributos'
    )
    producto_empresa = models.ForeignKey(
        'producto_empresa', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='valores_atributos'
    )
    
    # FK a atributo
    atributo = models.ForeignKey(AtributoProducto, on_delete=models.CASCADE, related_name='valores')
    
    # Campos para diferentes tipos de datos
    valor_texto = models.TextField(null=True, blank=True)
    valor_numero = models.IntegerField(null=True, blank=True)
    valor_decimal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_fecha = models.DateField(null=True, blank=True)
    valor_booleano = models.BooleanField(null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Valor de Atributo'
        verbose_name_plural = 'Valores de Atributos'
        unique_together = [
            ('producto_usuario', 'atributo'),
            ('producto_empresa', 'atributo')
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(producto_usuario__isnull=False, producto_empresa__isnull=True) |
                    models.Q(producto_usuario__isnull=True, producto_empresa__isnull=False)
                ),
                name='valor_atributo_producto_exclusivo'
            )
        ]
        ordering = ['atributo__nombre']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validar que solo un producto esté asignado
        if not ((self.producto_usuario and not self.producto_empresa) or 
                (self.producto_empresa and not self.producto_usuario)):
            raise ValidationError('Debe asignar exactamente un producto (usuario o empresa).')
        
        # Validar que el valor corresponda al tipo de dato del atributo
        tipo_dato = self.atributo.tipo_dato
        valores_no_nulos = sum([
            self.valor_texto is not None,
            self.valor_numero is not None,
            self.valor_decimal is not None,
            self.valor_fecha is not None,
            self.valor_booleano is not None
        ])
        
        if valores_no_nulos != 1:
            raise ValidationError('Debe asignar exactamente un valor según el tipo de dato del atributo.')
        
        # Validar tipo específico
        if tipo_dato == 'texto' and self.valor_texto is None:
            raise ValidationError('El atributo requiere un valor de texto.')
        elif tipo_dato == 'numero' and self.valor_numero is None:
            raise ValidationError('El atributo requiere un valor numérico.')
        elif tipo_dato == 'decimal' and self.valor_decimal is None:
            raise ValidationError('El atributo requiere un valor decimal.')
        elif tipo_dato == 'fecha' and self.valor_fecha is None:
            raise ValidationError('El atributo requiere un valor de fecha.')
        elif tipo_dato == 'booleano' and self.valor_booleano is None:
            raise ValidationError('El atributo requiere un valor booleano.')
        elif tipo_dato == 'lista' and self.valor_texto is None:
            raise ValidationError('El atributo de lista requiere un valor de texto.')
    
    def get_valor(self):
        """Retorna el valor según el tipo de dato del atributo"""
        tipo_dato = self.atributo.tipo_dato
        if tipo_dato == 'texto' or tipo_dato == 'lista':
            return self.valor_texto
        elif tipo_dato == 'numero':
            return self.valor_numero
        elif tipo_dato == 'decimal':
            return self.valor_decimal
        elif tipo_dato == 'fecha':
            return self.valor_fecha
        elif tipo_dato == 'booleano':
            return self.valor_booleano
        return None
    
    def set_valor(self, valor):
        """Establece el valor según el tipo de dato del atributo"""
        # Limpiar todos los valores primero
        self.valor_texto = None
        self.valor_numero = None
        self.valor_decimal = None
        self.valor_fecha = None
        self.valor_booleano = None
        
        # Asignar según tipo
        tipo_dato = self.atributo.tipo_dato
        if tipo_dato == 'texto' or tipo_dato == 'lista':
            self.valor_texto = str(valor)
        elif tipo_dato == 'numero':
            self.valor_numero = int(valor)
        elif tipo_dato == 'decimal':
            self.valor_decimal = float(valor)
        elif tipo_dato == 'fecha':
            self.valor_fecha = valor
        elif tipo_dato == 'booleano':
            self.valor_booleano = bool(valor)
    
    def __str__(self):
        producto = self.producto_usuario or self.producto_empresa
        producto_tipo = 'Usuario' if self.producto_usuario else 'Empresa'
        return f"{producto} - {self.atributo.nombre}: {self.get_valor()} ({producto_tipo})"


class pago_servicio(models.Model):
    METODO_PAGO_CHOICES = [
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Efectivo'),
        ('paypal', 'PayPal'),
        ('pago_movil', 'Pago Móvil'),
        ('criptomoneda', 'Criptomoneda'),
    ]
    
    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('confirmado', 'Confirmado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
    ]
    
    id_pago_servicio = models.AutoField(primary_key=True)
    
    # Foreign Keys opcionales - solo una debe estar llena
    solicitud_servicio_usuario = models.ForeignKey(
        'solicitud_servicio_usuario', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='pagos'
    )
    solicitud_servicio_empresa = models.ForeignKey(
        'solicitud_servicio_empresa', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='pagos'
    )
    
    # Campos de pago
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES)
    
    # Archivos y comprobantes
    comprobante_pago = models.ImageField(upload_to='comprobantes_pago/', null=True, blank=True)
    
    # Estados y fechas
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='pendiente')
    fecha_pago = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True, help_text='Fecha límite para confirmar el pago')
    
    # Campos adicionales
    notas_pago = models.TextField(null=True, blank=True)
    motivo_rechazo = models.TextField(null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pago de Servicio'
        verbose_name_plural = 'Pagos de Servicios'
        ordering = ['-fecha_pago']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(solicitud_servicio_usuario__isnull=False, solicitud_servicio_empresa__isnull=True) |
                    models.Q(solicitud_servicio_usuario__isnull=True, solicitud_servicio_empresa__isnull=False)
                ),
                name='pago_servicio_solicitud_exclusiva'
            )
        ]
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validar que solo una solicitud esté asignada
        if not ((self.solicitud_servicio_usuario and not self.solicitud_servicio_empresa) or 
                (self.solicitud_servicio_empresa and not self.solicitud_servicio_usuario)):
            raise ValidationError('Debe asignar exactamente una solicitud (usuario o empresa).')
    
    def get_solicitud(self):
        """Retorna la solicitud asociada (usuario o empresa)"""
        return self.solicitud_servicio_usuario or self.solicitud_servicio_empresa
    
    def get_tipo_solicitante(self):
        """Retorna el tipo de solicitante"""
        if self.solicitud_servicio_usuario:
            return 'usuario'
        elif self.solicitud_servicio_empresa:
            return 'empresa'
        return None
    
    def __str__(self):
        solicitud = self.get_solicitud()
        tipo = self.get_tipo_solicitante()
        return f"Pago {self.id_pago_servicio} - {solicitud} ({tipo}) - {self.estado_pago}"



