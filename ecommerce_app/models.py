from django.db import models
from django.utils import timezone

# Create your models here.
class usuario(models.Model):
    OPCIONES_AUTENTICACION = [
        ('local', 'Local'),
        ('google', 'Google'),
    ]

    OPCIONES_TIPO = [
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
    tipo_usuario = models.CharField(max_length=10, choices=OPCIONES_TIPO, default='persona')
    fecha_registro_usuario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_usuario
    


class empresa(models.Model):
    OPCIONES_TIPO_EMPRESA = [
        ('pequeña', 'Pequeña'),
        ('mediana', 'Mediana'),
        ('grande', 'Grande'),
    ]

    id_empresa = models.AutoField(primary_key=True)
    nombre_empresa = models.CharField(max_length=150)
    descripcion_empresa = models.TextField(blank=True, null=True)
    logo_empresa = models.ImageField(upload_to='logos_empresas/', blank=True, null=True)
    pais_empresa = models.CharField(max_length=100)
    estado_empresa = models.CharField(max_length=100)
    tipo_empresa = models.CharField(max_length=10, choices=OPCIONES_TIPO_EMPRESA)
    direccion_empresa = models.CharField(max_length=255)
    latitud_empresa = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitud_empresa = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    id_usuario_fk = models.ForeignKey('usuario', on_delete=models.CASCADE, related_name='empresas')

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
    
class categoria_producto(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]

    id_categoria_prod = models.AutoField(primary_key=True)
    nombre_categoria_prod = models.CharField(max_length=100)
    descripcion_categoria_prod = models.TextField(blank=True, null=True)
    estatus_categoria_prod = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    fecha_creacion_prod = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_categoria_prod
    

class categoria_servicio(models.Model):
    ESTATUS_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    id_categoria_serv = models.AutoField(primary_key=True)
    nombre_categoria_serv = models.CharField(max_length=100, unique=True)
    descripcion_categoria_serv = models.TextField(blank=True, null=True)
    estatus_categoria_serv = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='Activo')
    fecha_creacion_categ_serv = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre_categoria_serv
    





