from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('enviar-mensaje/', views.enviar_mensaje, name='enviar_mensaje'),
    path('obtener-conversacion/', views.obtener_conversacion, name='obtener_conversacion'),
]