from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class JsonResponseMiddleware(MiddlewareMixin):
    """
    Middleware para asegurar que las respuestas JSON tengan el Content-Type correcto
    """
    
    def process_response(self, request, response):
        # Si la respuesta es un JsonResponse, asegurar que tenga el Content-Type correcto
        if isinstance(response, JsonResponse):
            if 'application/json' not in response.get('Content-Type', ''):
                response['Content-Type'] = 'application/json; charset=utf-8'
        
        # Agregar headers CORS para desarrollo solo si no es una respuesta JSON
        if not isinstance(response, JsonResponse):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With, X-CSRFToken'
        
        return response
    
    def process_exception(self, request, exception):
        """
        Manejar excepciones no capturadas y devolver una respuesta JSON
        """
        logger.error(f"Excepción no capturada: {str(exception)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor',
            'error': str(exception) if request.META.get('HTTP_ACCEPT', '').startswith('application/json') else None
        }, status=500, content_type='application/json') 