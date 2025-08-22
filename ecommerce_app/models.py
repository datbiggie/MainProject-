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

    id_empresa = models.AutoField(primary_key=True)
    nombre_empresa = models.CharField(max_length=150)
    correo_empresa = models.EmailField(unique=True)
    password_empresa = models.CharField(max_length=255)
    descripcion_empresa = models.TextField(blank=True, null=True)
    logo_empresa = models.ImageField(upload_to='logos_empresas/', blank=True, null=True)
    pais_empresa = models.CharField(max_length=100)
    estado_empresa = models.CharField(max_length=100)
    tipo_empresa = models.CharField(max_length=10, choices=OPCIONES_TIPO_EMPRESA)
    direccion_empresa = models.CharField(max_length=255)
    latitud_empresa = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitud_empresa = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
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
    marca_producto_empresa = models.CharField(max_length=100, blank=True, null=True)
    modelo_producto_empresa = models.CharField(max_length=100, blank=True, null=True)
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
    marca_producto_usuario = models.CharField(max_length=100, blank=True, null=True)
    modelo_producto_usuario = models.CharField(max_length=100, blank=True, null=True)
    caracteristicas_generales_usuario = models.TextField(blank=True, null=True)
    stock_producto_usuario = models.PositiveIntegerField(default=0)
    precio_producto_usuario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    condicion_producto_usuario = models.CharField(max_length=10, choices=CONDICION_CHOICES, default='Nuevo')
    estatus_producto_usuario = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
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
        return f"Detalle {self.id_detalle_pedido_empresa} - Pedido {self.id_pedido_fk.numero_pedido}"



