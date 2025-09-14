from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
import json
import uuid
import logging
import traceback

from .models import Conversacion, Mensaje
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def enviar_mensaje(request):
    try:
        logger.info("Iniciando enviar_mensaje")
        data = json.loads(request.body)
        mensaje_usuario = data.get('mensaje', '').strip()
        logger.info(f"Mensaje recibido: {mensaje_usuario}")
        
        if not mensaje_usuario:
            logger.warning("Mensaje vacío recibido")
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
        
        # Obtener o crear conversación
        logger.info("Obteniendo conversación")
        conversacion = obtener_o_crear_conversacion(request)
        logger.info(f"Conversación obtenida: {conversacion.id}")
        
        # Guardar mensaje del usuario
        logger.info("Guardando mensaje del usuario")
        mensaje_usuario_obj = Mensaje.objects.create(
            conversacion=conversacion,
            tipo='usuario',
            contenido=mensaje_usuario
        )
        logger.info(f"Mensaje del usuario guardado: {mensaje_usuario_obj.id}")
        
        # Obtener contexto de mensajes anteriores
        logger.info("Obteniendo contexto de mensajes anteriores")
        mensajes_anteriores = conversacion.mensajes.order_by('-timestamp')[:10]  # Últimos 10 mensajes
        
        # Generar respuesta con Gemini
        logger.info("Inicializando GeminiService")
        # Obtener usuario para consultas personalizadas
        usuario = request.user if request.user.is_authenticated else None
        
        gemini_service = GeminiService()
        logger.info("Obteniendo contexto de conversación")
        contexto = gemini_service.obtener_contexto_conversacion(mensajes_anteriores)
        logger.info("Generando respuesta con Gemini")
        respuesta_bot = gemini_service.generar_respuesta(mensaje_usuario, contexto, usuario)
        logger.info(f"Respuesta generada: {respuesta_bot[:100]}...")
        
        # Guardar respuesta del bot
        logger.info("Guardando respuesta del bot")
        mensaje_bot = Mensaje.objects.create(
            conversacion=conversacion,
            tipo='bot',
            contenido=respuesta_bot
        )
        logger.info(f"Respuesta del bot guardada: {mensaje_bot.id}")
        
        return JsonResponse({
            'respuesta': respuesta_bot,
            'timestamp': mensaje_bot.timestamp.isoformat(),
            'conversacion_id': conversacion.id
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Error de JSON: {str(e)}")
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en enviar_mensaje: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def obtener_conversacion(request):
    try:
        conversacion = obtener_o_crear_conversacion(request)
        
        mensajes = []
        for mensaje in conversacion.mensajes.all():
            mensajes.append({
                'tipo': mensaje.tipo,
                'contenido': mensaje.contenido,
                'timestamp': mensaje.timestamp.isoformat()
            })
        
        return JsonResponse({
            'mensajes': mensajes,
            'conversacion_id': conversacion.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def obtener_o_crear_conversacion(request):
    """Obtiene o crea una conversación basada en el usuario o sesión"""
    if request.user.is_authenticated:
        # Usuario autenticado: buscar conversación activa
        conversacion, created = Conversacion.objects.get_or_create(
            usuario=request.user,
            activa=True,
            defaults={'fecha_creacion': timezone.now()}
        )
    else:
        # Usuario anónimo: usar session_id
        session_id = request.session.get('chatbot_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['chatbot_session_id'] = session_id
        
        conversacion, created = Conversacion.objects.get_or_create(
            session_id=session_id,
            activa=True,
            defaults={'fecha_creacion': timezone.now()}
        )
    
    return conversacion
