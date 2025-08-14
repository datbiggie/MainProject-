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
        import traceback
        from django.conf import settings
        
        # Registrar el error completo con traceback
        logger.error(f"Excepción no capturada: {str(exception)}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        # En modo DEBUG, mostrar el error específico
        error_detail = str(exception) if settings.DEBUG else None
        
        return JsonResponse({
            'success': False,
            'message': f'Error interno del servidor: {str(exception)}' if settings.DEBUG else 'Error interno del servidor',
            'error': error_detail
        }, status=500, content_type='application/json')