import google.generativeai as genai
import logging
import json
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        # TODO: Mover esto a variables de entorno en producción
        genai.configure(api_key="AIzaSyB0m9xT_Yt7MMSPFgHL4YgWxOgq2ujZTaA")
        
        # Configurar el modelo
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Inicializar servicio de base de datos
        self.db_service = DatabaseService()
    
    def generar_respuesta(self, mensaje_usuario, contexto_conversacion=None, usuario=None):
        try:
            # Extraer email del usuario si está disponible
            usuario_email = None
            if usuario and hasattr(usuario, 'email'):
                usuario_email = usuario.email
            elif usuario and hasattr(usuario, 'username'):
                # Si no tiene email, usar username como fallback
                usuario_email = usuario.username
            
            # Analizar el mensaje para determinar si necesita consultar la base de datos
            informacion_bd = self._consultar_base_datos(mensaje_usuario, usuario_email)
            
            if informacion_bd:
                contexto_bd = json.dumps(informacion_bd, ensure_ascii=False, indent=2)
            else:
                contexto_bd = "No se encontró información específica en la base de datos."
            
            # Agregar contexto de conversación si está disponible
            contexto_conversacion_texto = ""
            if contexto_conversacion:
                contexto_conversacion_texto = f"""
            Historial de conversación reciente:
            {contexto_conversacion}
            """
            
            # Crear el prompt con contexto de e-commerce y datos de la BD
            prompt = f"""
            Eres "EcommerceBot", un asistente de e-commerce. Responde de forma CONCISA y DIRECTA.
            {contexto_conversacion_texto}
            Información de la base de datos:
            {contexto_bd}
            
            Usuario: {mensaje_usuario}
            
            INSTRUCCIONES IMPORTANTES:
            - MANTÉN EL CONTEXTO de la conversación anterior
            - Si el usuario dice "otros", "más", "diferentes", etc., refiere a la categoría o tipo de productos mencionados anteriormente
            - Si encontraste productos en la base de datos, muestra SOLO esos productos específicos
            - Respuesta máxima: 3-4 líneas por producto
            - Incluye: nombre, precio, vendedor/empresa, disponibilidad
            - NUNCA muestres coordenadas (latitud/longitud) al usuario - siempre calcula y muestra distancia en km
            - Para productos de usuario, menciona "entrega disponible" o la distancia si tienes coordenadas del usuario
            - Para productos/servicios de empresa, menciona la sucursal y distancia si es relevante
            
            CONSULTAS DE PROXIMIDAD:
            - Si encontraste 'productos_cercanos', ordénalos por distancia y menciona la distancia en km (ej: "a 2.5 km")
            - NUNCA muestres coordenadas (latitud/longitud) al usuario, siempre calcula y muestra la distancia
            - Si hay 'solicitar_ubicacion', pide al usuario que proporcione su ubicación en formato: "latitud,longitud"
            - Ejemplo: "Para encontrar productos cerca de ti, comparte tu ubicación como: 19.4326,-99.1332"
            - Explica que puede obtener sus coordenadas desde Google Maps o su teléfono
            - Para productos con ubicación, di "a X km de distancia" en lugar de mostrar coordenadas
            
            - NO agregues sugerencias genéricas si ya encontraste productos
            - NO menciones "navegar por categorías" si ya hay resultados específicos
            - Si NO encontraste productos, entonces sí sugiere alternativas de búsqueda
            - Sé directo y específico, evita respuestas largas
            
            Respuesta:
            """
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error al generar respuesta con Gemini: {e}")
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo."
    
    def _consultar_base_datos(self, mensaje_usuario, usuario_email=None):
        """Analiza el mensaje del usuario y consulta la base de datos si es necesario"""
        mensaje_lower = mensaje_usuario.lower()
        informacion = {}
        
        try:
            logger.info(f"Analizando mensaje: {mensaje_usuario}")
            
            # Detectar consultas sobre productos - buscar automáticamente en todas las consultas
            # Palabras que NO son consultas de productos (para evitar falsos positivos)
            palabras_excluir = ['hola', 'gracias', 'adios', 'como', 'estas', 'bien', 'mal', 'si', 'no', 
                              'que', 'tal', 'ayuda', 'ayudar', 'puedes', 'favor', 'por', 'para']
            
            # Detectar palabras de continuación de conversación
            palabras_continuacion = ['otros', 'otras', 'más', 'mas', 'diferentes', 'distintos', 'distintas',
                                   'adicionales', 'también', 'tambien', 'que otros', 'que otras']
            
            es_continuacion = any(palabra in mensaje_lower for palabra in palabras_continuacion)
            
            # Si el mensaje no contiene solo palabras de saludo/conversación, buscar productos
            es_consulta_producto = not all(palabra in palabras_excluir for palabra in mensaje_lower.split()) or es_continuacion
            
            # Detectar consultas sobre proximidad/ubicación
            palabras_proximidad = ['cerca', 'cercano', 'cercanos', 'cerca de mi', 'proximidad', 'distancia', 
                                  'ubicacion', 'ubicación', 'alrededor', 'radio', 'km', 'kilometros', 
                                  'metros', 'lejos', 'cerca de', 'mi ubicacion', 'mi ubicación']
            
            es_consulta_proximidad = any(palabra in mensaje_lower for palabra in palabras_proximidad)
            
            if es_consulta_proximidad:
                logger.info(f"Consulta de proximidad detectada")
                # Extraer coordenadas del mensaje (formato: lat,lon o "mi ubicación es lat,lon")
                coordenadas = self._extraer_coordenadas(mensaje_usuario)
                if coordenadas:
                    lat_usuario, lon_usuario = coordenadas
                    # Extraer radio si se especifica
                    radio = self._extraer_radio(mensaje_usuario)
                    productos_cercanos = self.db_service.buscar_productos_cercanos(
                        lat_usuario, lon_usuario, radio_km=radio, limite=10
                    )
                    if productos_cercanos:
                        informacion['productos_cercanos'] = productos_cercanos
                        logger.info(f"Productos cercanos encontrados: {len(productos_cercanos)}")
                else:
                    informacion['solicitar_ubicacion'] = True
                    logger.info("Consulta de proximidad sin coordenadas - solicitando ubicación")
            elif es_consulta_producto:
                logger.info(f"Consulta de productos detectada")
                # Extraer términos de búsqueda (mejorado)
                if es_continuacion and contexto_conversacion:
                    # Si es una continuación, extraer términos del contexto anterior también
                    terminos_busqueda = self._extraer_terminos_busqueda(mensaje_usuario, contexto_conversacion)
                else:
                    terminos_busqueda = self._extraer_terminos_busqueda(mensaje_usuario)
                logger.info(f"Términos de búsqueda extraídos: '{terminos_busqueda}'")
                if terminos_busqueda:
                    productos = self.db_service.buscar_productos(terminos_busqueda, limite=5)
                    logger.info(f"Productos encontrados: {len(productos) if productos else 0}")
                    if productos:
                        informacion['productos_encontrados'] = productos
            
            # Detectar consultas sobre servicios
            if any(palabra in mensaje_lower for palabra in ['servicio', 'servicios']):
                terminos_busqueda = self._extraer_terminos_busqueda(mensaje_usuario)
                if terminos_busqueda:
                    servicios = self.db_service.buscar_servicios(terminos_busqueda, limite=5)
                    if servicios:
                        informacion['servicios_encontrados'] = servicios
            
            # Detectar consultas sobre empresas
            if any(palabra in mensaje_lower for palabra in ['empresa', 'tienda', 'vendedor']):
                terminos_busqueda = self._extraer_terminos_busqueda(mensaje_usuario)
                if terminos_busqueda:
                    empresas = self.db_service.buscar_empresas(terminos_busqueda, limite=5)
                    if empresas:
                        informacion['empresas_encontradas'] = empresas
            
            # Detectar consultas sobre categorías
            if any(palabra in mensaje_lower for palabra in ['categoria', 'categoría', 'tipo']):
                if 'producto' in mensaje_lower:
                    categorias = self.db_service.obtener_categorias_productos()
                    if categorias:
                        informacion['categorias_productos'] = categorias[:10]
                elif 'servicio' in mensaje_lower:
                    categorias = self.db_service.obtener_categorias_servicios()
                    if categorias:
                        informacion['categorias_servicios'] = categorias[:10]
            
            # Consultas específicas del usuario (requieren autenticación)
            if usuario_email:
                # Detectar consultas sobre pedidos
                if any(palabra in mensaje_lower for palabra in ['pedido', 'pedidos', 'orden', 'compra', 'historial']):
                    if 'pendiente' in mensaje_lower:
                        pedidos = self.db_service.obtener_pedidos_usuario(usuario_email, estado='pendiente')
                    elif 'confirmado' in mensaje_lower:
                        pedidos = self.db_service.obtener_pedidos_usuario(usuario_email, estado='confirmado')
                    elif 'entregado' in mensaje_lower:
                        pedidos = self.db_service.obtener_pedidos_usuario(usuario_email, estado='entregado')
                    else:
                        pedidos = self.db_service.obtener_pedidos_usuario(usuario_email, limite=5)
                    
                    if pedidos:
                        informacion['pedidos_usuario'] = pedidos
                    
                    # Obtener estadísticas si se solicita
                    if any(palabra in mensaje_lower for palabra in ['estadistica', 'resumen', 'total']):
                        stats = self.db_service.obtener_estadisticas_pedidos_usuario(usuario_email)
                        if stats:
                            informacion['estadisticas_pedidos'] = stats
                
                # Detectar consultas sobre carrito
                if any(palabra in mensaje_lower for palabra in ['carrito', 'carro', 'cesta']):
                    carrito = self.db_service.obtener_carrito_usuario(usuario_email)
                    if carrito:
                        informacion['carrito_usuario'] = carrito
            
            return informacion if informacion else None
            
        except Exception as e:
            logger.error(f"Error al consultar base de datos: {e}")
            return None
    
    def _extraer_terminos_busqueda(self, mensaje, contexto_conversacion=None):
        """Extrae términos de búsqueda del mensaje del usuario y opcionalmente del contexto"""
        # Palabras a ignorar
        palabras_ignorar = {
            'buscar', 'busco', 'quiero', 'necesito', 'me', 'puedes', 'ayudar', 
            'encontrar', 'ver', 'mostrar', 'hay', 'tiene', 'tienes', 'donde',
            'como', 'que', 'cual', 'cuando', 'producto', 'productos', 'servicio', 'servicios',
            'para', 'con', 'una', 'uno', 'del', 'las', 'los', 'por', 'mas', 'más',
            'otros', 'otras', 'diferentes', 'distintos', 'usuario', 'bot'
        }
        
        # Limpiar y dividir el mensaje
        palabras = mensaje.lower().replace('?', '').replace('¿', '').replace(',', '').replace('.', '').split()
        
        # Filtrar palabras relevantes
        terminos = [palabra for palabra in palabras if len(palabra) > 1 and palabra not in palabras_ignorar]
        
        # Si hay contexto de conversación y pocos términos en el mensaje actual, extraer del contexto
        if contexto_conversacion and len(terminos) <= 1:
            # Extraer términos relevantes del contexto (últimas consultas del usuario)
            lineas_contexto = contexto_conversacion.split('\n')
            for linea in lineas_contexto:
                if linea.startswith('Usuario:'):
                    mensaje_anterior = linea.replace('Usuario:', '').strip()
                    palabras_contexto = mensaje_anterior.lower().replace('?', '').replace('¿', '').replace(',', '').replace('.', '').split()
                    terminos_contexto = [palabra for palabra in palabras_contexto 
                                       if len(palabra) > 1 and palabra not in palabras_ignorar]
                    terminos.extend(terminos_contexto)
                    break  # Solo tomar la consulta más reciente del usuario
        
        # Normalizar plurales comunes (convertir plural a singular para mejor coincidencia)
        terminos_normalizados = []
        for termino in terminos:
            if termino.endswith('s') and len(termino) > 3:
                # Intentar versión singular
                terminos_normalizados.append(termino[:-1])  # laptop en lugar de laptops
            terminos_normalizados.append(termino)  # También mantener el original
        
        # Eliminar duplicados manteniendo el orden
        terminos_unicos = []
        for termino in terminos_normalizados:
            if termino not in terminos_unicos:
                terminos_unicos.append(termino)
        
        # Retornar todos los términos unidos con espacios para búsqueda más efectiva
        return ' '.join(terminos_unicos) if terminos_unicos else ''
    
    def _extraer_coordenadas(self, mensaje):
        """Extrae coordenadas del mensaje del usuario"""
        import re
        
        # Patrones para detectar coordenadas
        # Formato: lat,lon o lat, lon o "mi ubicación es lat,lon"
        patrones = [
            r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)',  # lat,lon con decimales
            r'(-?\d+)\s*,\s*(-?\d+)',  # lat,lon enteros
            r'ubicaci[oó]n\s+es\s+(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)',  # "mi ubicación es lat,lon"
            r'estoy\s+en\s+(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)'  # "estoy en lat,lon"
        ]
        
        for patron in patrones:
            match = re.search(patron, mensaje)
            if match:
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                    # Validar que las coordenadas estén en rangos válidos
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return (lat, lon)
                except ValueError:
                    continue
        
        return None
    
    def _extraer_radio(self, mensaje):
        """Extrae el radio de búsqueda del mensaje del usuario"""
        import re
        
        # Patrones para detectar radio en km
        patrones = [
            r'(\d+)\s*km',  # "5 km" o "5km"
            r'(\d+)\s*kil[oó]metros?',  # "5 kilómetros"
            r'radio\s+de\s+(\d+)',  # "radio de 5"
            r'en\s+(\d+)\s*km',  # "en 10 km"
            r'hasta\s+(\d+)\s*km'  # "hasta 15 km"
        ]
        
        for patron in patrones:
            match = re.search(patron, mensaje.lower())
            if match:
                try:
                    radio = int(match.group(1))
                    # Limitar radio máximo a 50 km
                    return min(radio, 50)
                except ValueError:
                    continue
        
        # Radio por defecto: 10 km
        return 10
    
    def obtener_contexto_conversacion(self, mensajes_anteriores, limite=5):
        """Obtiene el contexto de los mensajes anteriores"""
        if not mensajes_anteriores:
            return ""
        
        # Convertir QuerySet a lista (ya viene ordenado desde las vistas)
        mensajes_lista = list(mensajes_anteriores)[:limite]
        mensajes_lista.reverse()  # Revertir para orden cronológico
        
        contexto = []
        for mensaje in mensajes_lista:
            tipo = "Usuario" if mensaje.tipo == 'usuario' else "Bot"
            contexto.append(f"{tipo}: {mensaje.contenido}")
        
        return "\n".join(contexto)