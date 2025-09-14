from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Conversacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        if self.usuario:
            return f"Conversación de {self.usuario.username} - {self.fecha_creacion}"
        return f"Conversación anónima {self.session_id} - {self.fecha_creacion}"

class Mensaje(models.Model):
    TIPOS_MENSAJE = [
        ('usuario', 'Usuario'),
        ('bot', 'Bot'),
    ]
    
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name='mensajes')
    tipo = models.CharField(max_length=10, choices=TIPOS_MENSAJE)
    contenido = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.tipo}: {self.contenido[:50]}..."
