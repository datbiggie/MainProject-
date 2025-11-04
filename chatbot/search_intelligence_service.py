import re
import unicodedata
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class SearchIntelligenceService:
    """Servicio para búsqueda inteligente con sinónimos, variaciones y normalización"""
    
    def __init__(self):
        # Diccionario de sinónimos y variaciones
        self.sinonimos = {
            # Electrónicos y tecnología
            'celular': ['celulares', 'telefono', 'telefonos', 'movil', 'moviles', 'smartphone', 'smartphones', 'phone'],
            'telefono': ['telefonos', 'celular', 'celulares', 'movil', 'moviles', 'smartphone', 'smartphones'],
            'computadora': ['computadoras', 'pc', 'ordenador', 'ordenadores', 'laptop', 'laptops', 'portatil', 'portatiles'],
            'laptop': ['laptops', 'portatil', 'portatiles', 'computadora', 'computadoras', 'notebook', 'notebooks'],
            'tablet': ['tablets', 'tableta', 'tabletas', 'ipad', 'ipads'],
            'television': ['televisiones', 'tv', 'televisor', 'televisores', 'tele'],
            'televisor': ['televisores', 'television', 'televisiones', 'tv', 'tele'],
            'auricular': ['auriculares', 'audifonos', 'headphones', 'cascos'],
            'audifonos': ['auriculares', 'auricular', 'headphones', 'cascos'],
            'camara': ['camaras', 'fotografia', 'foto', 'fotos'],
            'mouse': ['raton', 'ratones', 'mouses'],
            'teclado': ['teclados', 'keyboard'],
            
            # Ropa y accesorios
            'camisa': ['camisas', 'blusa', 'blusas'],
            'pantalon': ['pantalones', 'jeans', 'vaqueros'],
            'zapato': ['zapatos', 'calzado', 'calzados', 'tenis', 'zapatillas'],
            'tenis': ['zapatos', 'calzado', 'zapatillas', 'deportivos'],
            'vestido': ['vestidos'],
            'falda': ['faldas'],
            'chaqueta': ['chaquetas', 'jacket', 'abrigo', 'abrigos'],
            'sombrero': ['sombreros', 'gorra', 'gorras', 'gorro', 'gorros'],
            'bolsa': ['bolsas', 'bolso', 'bolsos', 'cartera', 'carteras', 'mochila', 'mochilas'],
            
            # Hogar y decoración
            'sofa': ['sofas', 'sillon', 'sillones', 'mueble', 'muebles'],
            'mesa': ['mesas', 'escritorio', 'escritorios'],
            'silla': ['sillas', 'asiento', 'asientos'],
            'cama': ['camas', 'colchon', 'colchones'],
            'refrigerador': ['refrigeradores', 'nevera', 'neveras', 'heladera', 'heladeras'],
            'estufa': ['estufas', 'cocina', 'cocinas'],
            'microondas': ['horno', 'hornos'],
            'lavadora': ['lavadoras', 'lavarropas'],
            'television': ['televisiones', 'tv', 'televisor', 'televisores'],
            
            # Vehículos
            'carro': ['carros', 'auto', 'autos', 'automovil', 'automoviles', 'vehiculo', 'vehiculos', 'coche', 'coches'],
            'auto': ['autos', 'carro', 'carros', 'automovil', 'automoviles', 'vehiculo', 'vehiculos', 'coche', 'coches'],
            'moto': ['motos', 'motocicleta', 'motocicletas', 'scooter', 'scooters'],
            'bicicleta': ['bicicletas', 'bici', 'bicis', 'bike', 'bikes'],
            
            # Servicios
            'reparacion': ['reparaciones', 'arreglo', 'arreglos', 'mantenimiento', 'servicio tecnico'],
            'limpieza': ['limpiar', 'aseo', 'limpiador', 'limpiadores'],
            'plomeria': ['plomero', 'plomeros', 'fontaneria', 'fontanero', 'fontaneros'],
            'electricidad': ['electricista', 'electricistas', 'electrico', 'electricos'],
            'carpinteria': ['carpintero', 'carpinteros', 'madera', 'muebles'],
            'pintura': ['pintor', 'pintores', 'pintar'],
            'jardineria': ['jardinero', 'jardineros', 'jardin', 'jardines', 'plantas'],
            'transporte': ['mudanza', 'mudanzas', 'flete', 'fletes', 'envio', 'envios'],
            'delivery': ['entrega', 'entregas', 'envio', 'envios', 'domicilio'],
            
            # Servicios digitales y tecnológicos
            'diseño': ['diseno', 'design', 'diseñar', 'diseñador', 'diseñadores', 'grafico', 'gráfico'],
            'desarrollo': ['programacion', 'programación', 'programar', 'programador', 'programadores', 'software', 'codigo', 'código'],
            'web': ['website', 'sitio web', 'pagina web', 'página web', 'internet', 'online'],
            'sitios web': ['websites', 'sitio web', 'paginas web', 'páginas web', 'web development', 'desarrollo web'],
            'marketing': ['mercadeo', 'publicidad', 'promocion', 'promoción', 'advertising'],
            'consultoria': ['consultoría', 'asesoría', 'asesoria', 'consultancy', 'consulting'],
            'fotografia': ['fotografía', 'foto', 'fotos', 'photography', 'fotografo', 'fotógrafo'],
            'video': ['videos', 'audiovisual', 'grabacion', 'grabación', 'edicion', 'edición'],
            
            # Servicios profesionales
            'contabilidad': ['contador', 'contadores', 'accounting', 'finanzas', 'tributario'],
            'legal': ['abogado', 'abogados', 'juridico', 'jurídico', 'derecho', 'lawyer'],
            'medico': ['médico', 'doctor', 'doctores', 'medicina', 'salud', 'health'],
            'veterinario': ['veterinarios', 'vet', 'mascotas', 'animales'],
            
            # Servicios de belleza y bienestar
            'peluqueria': ['peluquería', 'salon', 'salón', 'cabello', 'hair'],
            'barberia': ['barbería', 'barber', 'barbero', 'barberos'],
            'masaje': ['masajes', 'terapia', 'relajacion', 'relajación', 'spa'],
            
            # Servicios de eventos
            'eventos': ['evento', 'organizacion', 'organización', 'planning', 'bodas', 'fiestas'],
            'catering': ['comida', 'banquetes', 'food service', 'alimentacion', 'alimentación'],
            
            # Servicios técnicos y especializados
            'cableado': ['cableado estructurado', 'networking', 'redes', 'instalacion de cables', 'instalación de cables'],
            'estructurado': ['cableado estructurado', 'infraestructura', 'redes estructuradas'],
            'redes': ['networking', 'red', 'conectividad', 'telecomunicaciones', 'internet'],
            'soporte': ['soporte tecnico', 'soporte técnico', 'asistencia', 'help desk', 'support'],
            'configuracion': ['configuración', 'setup', 'instalacion', 'instalación', 'puesta en marcha'],
            'mantenimiento': ['mantenimiento preventivo', 'mantenimiento correctivo', 'servicio tecnico', 'servicio técnico'],
            'migracion': ['migración', 'transferencia', 'mudanza de datos', 'backup', 'respaldo'],
            
            # Alimentación
            'comida': ['alimento', 'alimentos', 'food', 'meal'],
            'bebida': ['bebidas', 'drink', 'drinks', 'liquido', 'liquidos'],
            'fruta': ['frutas', 'fruit', 'fruits'],
            'verdura': ['verduras', 'vegetal', 'vegetales', 'hortaliza', 'hortalizas'],
            'carne': ['carnes', 'meat', 'pollo', 'res', 'cerdo', 'pescado'],
            'pan': ['panes', 'bread', 'panaderia'],
            'leche': ['lacteo', 'lacteos', 'dairy'],
            
            # Salud y belleza
            'medicina': ['medicinas', 'medicamento', 'medicamentos', 'farmaco', 'farmacos'],
            'shampoo': ['champu', 'jabon', 'jabones'],
            'crema': ['cremas', 'locion', 'lociones'],
            'perfume': ['perfumes', 'fragancia', 'fragancias', 'colonia', 'colonias'],
            'maquillaje': ['cosmetico', 'cosmeticos', 'makeup'],
            
            # Deportes
            'pelota': ['pelotas', 'balon', 'balones', 'ball'],
            'deporte': ['deportes', 'sport', 'sports', 'ejercicio', 'fitness'],
            'gimnasio': ['gym', 'fitness', 'ejercicio'],
            
            # Mascotas
            'mascota': ['mascotas', 'pet', 'pets', 'animal', 'animales'],
            'perro': ['perros', 'dog', 'dogs', 'can', 'canes'],
            'gato': ['gatos', 'cat', 'cats', 'felino', 'felinos'],
            
            # Libros y educación
            'libro': ['libros', 'book', 'books', 'texto', 'textos'],
            'cuaderno': ['cuadernos', 'libreta', 'libretas', 'notebook'],
            'lapiz': ['lapices', 'pencil', 'boligrafo', 'boligrafos', 'pluma', 'plumas'],
            
            # Juguetes
            'juguete': ['juguetes', 'toy', 'toys', 'juego', 'juegos'],
            'muneca': ['munecas', 'doll', 'dolls'],
            'carro': ['carritos', 'auto', 'autos'] # Para juguetes también
        }
        
        # Patrones de normalización
        self.patrones_normalizacion = [
            (r'ñ', 'n'),
            (r'[áàäâ]', 'a'),
            (r'[éèëê]', 'e'),
            (r'[íìïî]', 'i'),
            (r'[óòöô]', 'o'),
            (r'[úùüû]', 'u'),
            (r'[ç]', 'c'),
        ]
        
        # Palabras de ubicación y proximidad
        self.palabras_ubicacion = [
            'cerca', 'cercano', 'cercanos', 'cerca de mi', 'proximidad', 'distancia',
            'ubicacion', 'ubicación', 'alrededor', 'radio', 'km', 'kilometros',
            'metros', 'lejos', 'cerca de', 'mi ubicacion', 'mi ubicación',
            'donde', 'ubicado', 'ubicada', 'localizado', 'localizada'
        ]
        
        # Palabras de envío y delivery
        self.palabras_envio = [
            'envio', 'envios', 'envío', 'envíos', 'delivery', 'entrega', 'entregas',
            'domicilio', 'rapido', 'rápido', 'express', 'inmediato', 'urgente',
            'mismo dia', 'mismo día', 'gratis', 'gratuito', 'sin costo'
        ]
        
        # Marcas comunes
        self.marcas_conocidas = {
            'samsung': ['samsung', 'galaxy'],
            'apple': ['apple', 'iphone', 'ipad', 'mac', 'macbook'],
            'lg': ['lg'],
            'sony': ['sony', 'playstation', 'ps4', 'ps5'],
            'nike': ['nike'],
            'adidas': ['adidas'],
            'toyota': ['toyota'],
            'ford': ['ford'],
            'chevrolet': ['chevrolet', 'chevy'],
            'honda': ['honda'],
            'xiaomi': ['xiaomi', 'redmi'],
            'huawei': ['huawei'],
            'motorola': ['motorola', 'moto']
        }
    
    def normalizar_texto(self, texto):
        """Normaliza texto removiendo acentos y caracteres especiales"""
        if not texto:
            return ""
        
        # Convertir a minúsculas
        texto = texto.lower().strip()
        
        # Aplicar patrones de normalización
        for patron, reemplazo in self.patrones_normalizacion:
            texto = re.sub(patron, reemplazo, texto)
        
        # Remover caracteres especiales excepto espacios y números
        texto = re.sub(r'[^\w\s]', ' ', texto)
        
        # Normalizar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    def obtener_variaciones_termino(self, termino):
        """Obtiene todas las variaciones posibles de un término"""
        termino_normalizado = self.normalizar_texto(termino)
        variaciones = set([termino, termino_normalizado])
        
        # Agregar sinónimos
        if termino_normalizado in self.sinonimos:
            variaciones.update(self.sinonimos[termino_normalizado])
        
        # Buscar en sinónimos donde el término aparezca como variación
        for palabra_base, lista_sinonimos in self.sinonimos.items():
            if termino_normalizado in lista_sinonimos:
                variaciones.add(palabra_base)
                variaciones.update(lista_sinonimos)
        
        # Agregar variaciones de plural/singular
        if termino_normalizado.endswith('s') and len(termino_normalizado) > 3:
            # Posible plural, agregar singular
            singular = termino_normalizado[:-1]
            variaciones.add(singular)
            if singular in self.sinonimos:
                variaciones.update(self.sinonimos[singular])
        else:
            # Posible singular, agregar plural
            plural = termino_normalizado + 's'
            variaciones.add(plural)
            if plural in self.sinonimos:
                variaciones.update(self.sinonimos[plural])
        
        # Agregar variaciones de marcas
        for marca, variaciones_marca in self.marcas_conocidas.items():
            if termino_normalizado in variaciones_marca:
                variaciones.update(variaciones_marca)
        
        return list(variaciones)
    
    def expandir_terminos_busqueda(self, terminos_busqueda):
        """Expande los términos de búsqueda con sinónimos y variaciones"""
        if not terminos_busqueda:
            return []
        
        terminos = terminos_busqueda.split()
        terminos_expandidos = set()
        
        for termino in terminos:
            if len(termino) > 1:  # Ignorar términos muy cortos
                variaciones = self.obtener_variaciones_termino(termino)
                terminos_expandidos.update(variaciones)
        
        return list(terminos_expandidos)
    
    def calcular_similitud(self, texto1, texto2):
        """Calcula la similitud entre dos textos"""
        if not texto1 or not texto2:
            return 0.0
        
        texto1_norm = self.normalizar_texto(texto1)
        texto2_norm = self.normalizar_texto(texto2)
        
        return SequenceMatcher(None, texto1_norm, texto2_norm).ratio()
    
    def es_consulta_ubicacion(self, mensaje):
        """Detecta si el mensaje es una consulta sobre ubicación"""
        mensaje_norm = self.normalizar_texto(mensaje)
        return any(palabra in mensaje_norm for palabra in self.palabras_ubicacion)
    
    def es_consulta_envio(self, mensaje):
        """Detecta si el mensaje es una consulta sobre envíos"""
        mensaje_norm = self.normalizar_texto(mensaje)
        return any(palabra in mensaje_norm for palabra in self.palabras_envio)
    
    def extraer_marca_del_mensaje(self, mensaje):
        """Extrae marcas mencionadas en el mensaje"""
        mensaje_norm = self.normalizar_texto(mensaje)
        marcas_encontradas = []
        
        for marca, variaciones in self.marcas_conocidas.items():
            for variacion in variaciones:
                if variacion in mensaje_norm:
                    marcas_encontradas.append(marca)
                    break
        
        return marcas_encontradas
    
    def generar_consulta_flexible(self, terminos_expandidos):
        """Genera una consulta SQL flexible para búsqueda"""
        if not terminos_expandidos:
            return None
        
        # Crear condiciones OR para cada término expandido
        condiciones = []
        for termino in terminos_expandidos:
            if len(termino) > 1:
                condiciones.append(f"LOWER(nombre) LIKE '%{termino}%'")
                condiciones.append(f"LOWER(descripcion) LIKE '%{termino}%'")
        
        if condiciones:
            return " OR ".join(condiciones)
        
        return None
    
    def filtrar_resultados_por_relevancia(self, resultados, termino_original, limite=10):
        """Filtra y ordena resultados por relevancia"""
        if not resultados or not termino_original:
            return resultados[:limite]
        
        # Calcular puntuación de relevancia para cada resultado
        resultados_con_puntuacion = []
        
        for resultado in resultados:
            nombre = resultado.get('nombre', '')
            descripcion = resultado.get('descripcion', '')
            
            # Calcular similitud con el nombre (peso mayor)
            similitud_nombre = self.calcular_similitud(termino_original, nombre) * 2
            
            # Calcular similitud con la descripción (peso menor)
            similitud_descripcion = self.calcular_similitud(termino_original, descripcion)
            
            # Puntuación total
            puntuacion = similitud_nombre + similitud_descripcion
            
            # Bonus si el término aparece exactamente en el nombre
            if self.normalizar_texto(termino_original) in self.normalizar_texto(nombre):
                puntuacion += 1
            
            resultados_con_puntuacion.append((resultado, puntuacion))
        
        # Ordenar por puntuación descendente
        resultados_con_puntuacion.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar solo los resultados sin la puntuación
        return [resultado for resultado, _ in resultados_con_puntuacion[:limite]]
    
    def detectar_intencion_consulta(self, mensaje):
        """Detecta la intención de la consulta del usuario"""
        mensaje_norm = self.normalizar_texto(mensaje)
        
        intenciones = {
            'busqueda_producto': False,
            'busqueda_servicio': False,
            'consulta_ubicacion': False,
            'consulta_envio': False,
            'consulta_precio': False,
            'comparacion': False
        }
        
        # Detectar búsqueda de productos
        if any(palabra in mensaje_norm for palabra in ['producto', 'productos', 'comprar', 'vender']):
            intenciones['busqueda_producto'] = True
        
        # Detectar búsqueda de servicios
        if any(palabra in mensaje_norm for palabra in ['servicio', 'servicios', 'contratar', 'solicitar']):
            intenciones['busqueda_servicio'] = True
        
        # Detectar consulta de ubicación
        if self.es_consulta_ubicacion(mensaje):
            intenciones['consulta_ubicacion'] = True
        
        # Detectar consulta de envío
        if self.es_consulta_envio(mensaje):
            intenciones['consulta_envio'] = True
        
        # Detectar consulta de precio
        if any(palabra in mensaje_norm for palabra in ['precio', 'precios', 'costo', 'costos', 'cuanto', 'barato', 'caro']):
            intenciones['consulta_precio'] = True
        
        # Detectar comparación
        if any(palabra in mensaje_norm for palabra in ['comparar', 'diferencia', 'mejor', 'peor', 'vs', 'versus']):
            intenciones['comparacion'] = True
        
        return intenciones
