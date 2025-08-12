from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
from .models import producto, servicio, producto_sucursal, servicio_sucursal, sucursal, imagen_producto, imagen_servicio

# API para obtener productos y servicios NO asociados a una sucursal
@require_GET
def api_productos_servicios_disponibles(request):
    try:
        id_sucursal = request.GET.get('id_sucursal') or request.GET.get('sucursal_id')
        tipo = request.GET.get('tipo', 'todos')  # Nuevo parámetro para filtrar por tipo (productos, servicios o todos)
        
        if not id_sucursal:
            return JsonResponse({'success': False, 'message': 'ID de sucursal requerido'})

        # Inicializar listas vacías
        productos_list = []
        servicios_list = []
        
        # Si se solicitan productos o todos
        if tipo == 'productos' or tipo == 'todos':
            productos_asociados_qs = producto_sucursal.objects.filter(id_sucursal_fk=id_sucursal).values_list('id_producto_fk', flat=True)
            productos_asociados_list = list(productos_asociados_qs)
            
            if productos_asociados_list:
                productos_disponibles = producto.objects.exclude(id_producto__in=productos_asociados_list)
            else:
                productos_disponibles = producto.objects.all()
                
            productos_list = [
                {'id': p.id_producto, 'nombre': p.nombre_producto}
                for p in productos_disponibles
            ]
        
        # Si se solicitan servicios o todos
        if tipo == 'servicios' or tipo == 'todos':
            servicios_asociados_qs = servicio_sucursal.objects.filter(id_sucursal_fk=id_sucursal).values_list('id_servicio_fk', flat=True)
            servicios_asociados_list = list(servicios_asociados_qs)
            
            if servicios_asociados_list:
                servicios_disponibles = servicio.objects.exclude(id_servicio__in=servicios_asociados_list)
            else:
                servicios_disponibles = servicio.objects.all()
                
            servicios_list = [
                {'id': s.id_servicio, 'nombre': s.nombre_servicio}
                for s in servicios_disponibles
            ]

        return JsonResponse({'success': True, 'productos': productos_list, 'servicios': servicios_list})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
from django.views.decorators.http import require_POST

# API para guardar producto o servicio en una sucursal
@require_POST
def guardar_producto_servicio_sucursal(request):
    try:
        # Obtener datos del formulario
        sucursal_id = request.POST.get('sucursal_id')
        producto_id = request.POST.get('producto_id')
        servicio_id = request.POST.get('servicio_id')
        stock = request.POST.get('stock', 0)
        precio = request.POST.get('precio', 0)
        estatus_producto_sucursal = request.POST.get('estatus_producto_sucursal', 'Activo')
        estatus_servicio_sucursal = request.POST.get('estatus_servicio_sucursal', 'Activo')
        condicion_producto_sucursal = request.POST.get('condicion_producto_sucursal', 'Nuevo')
        
        # Validar datos básicos
        if not sucursal_id:
            return JsonResponse({'success': False, 'message': 'ID de sucursal requerido'})
        
        # Validar que se haya seleccionado un producto o un servicio, pero no ambos
        if (not producto_id and not servicio_id) or (producto_id and servicio_id):
            return JsonResponse({'success': False, 'message': 'Debe seleccionar un producto o un servicio, pero no ambos'})
            
        # Si es un producto, validar precio
        if producto_id and not precio:
            return JsonResponse({'success': False, 'message': 'Precio requerido para productos'})
        
        # Obtener la sucursal
        try:
            sucursal_obj = sucursal.objects.get(id_sucursal=sucursal_id)
        except sucursal.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'La sucursal no existe'})
        
        # Guardar producto en sucursal
        if producto_id:
            try:
                producto_obj = producto.objects.get(id_producto=producto_id)
                
                # Verificar si ya existe este producto en esta sucursal
                if producto_sucursal.objects.filter(id_sucursal_fk=sucursal_obj, id_producto_fk=producto_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Este producto ya está asociado a esta sucursal'})
                
                # Crear la relación producto-sucursal con el estatus y condición seleccionados
                producto_sucursal.objects.create(
                    stock_producto_sucursal=stock,
                    precio_producto_sucursal=precio,
                    estatus_producto_sucursal=estatus_producto_sucursal,
                    condicion_producto_sucursal=condicion_producto_sucursal,
                    id_sucursal_fk=sucursal_obj,
                    id_producto_fk=producto_obj
                )
                
                return JsonResponse({'success': True, 'message': 'Producto agregado a la sucursal correctamente'})
            except producto.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'El producto no existe'})
        
        # Guardar servicio en sucursal
        if servicio_id:
            try:
                servicio_obj = servicio.objects.get(id_servicio=servicio_id)
                
                # Verificar si ya existe este servicio en esta sucursal
                if servicio_sucursal.objects.filter(id_sucursal_fk=sucursal_obj, id_servicio_fk=servicio_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Este servicio ya está asociado a esta sucursal'})
                
                # Crear la relación servicio-sucursal con el estatus seleccionado
                servicio_sucursal.objects.create(
                    precio_servicio_sucursal=precio,
                    id_sucursal_fk=sucursal_obj,
                    id_servicio_fk=servicio_obj,
                    estatus_servicio_sucursal=estatus_servicio_sucursal
                )
                
                return JsonResponse({'success': True, 'message': 'Servicio agregado a la sucursal correctamente'})
            except servicio.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'El servicio no existe'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Vista para cambiar el logo de la empresa

@require_POST
def cambiar_logo_empresa(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    try:
        empresa_obj = empresa.objects.get(id_usuario_fk=current_user)
    except empresa.DoesNotExist:
        return redirect('/ecommerce/registrar_empresa/')
    logo = request.FILES.get('logo')
    if not logo:
        return redirect('/ecommerce/perfil_empresa/')
    empresa_obj.logo_empresa = logo
    empresa_obj.save()
    return redirect('/ecommerce/perfil_empresa/')

# Vista para eliminar servicio
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def eliminar_servicio(request):
    if request.method == 'POST':
        try:
            id_servicio = request.POST.get('id_servicio')
            if not id_servicio:
                return JsonResponse({'success': False, 'message': 'ID de servicio no proporcionado'})
            servicio_obj = servicio.objects.get(id_servicio=id_servicio)
            nombre_servicio = servicio_obj.nombre_servicio
            servicio_obj.delete()
            return JsonResponse({'success': True, 'message': f'Servicio "{nombre_servicio}" eliminado exitosamente'})
        except servicio.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al eliminar el servicio: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

# Vista para editar servicio
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def editar_servicio(request):
    if request.method == 'POST':
        try:
            id_servicio = request.POST.get('id_servicio')
            if not id_servicio:
                return JsonResponse({'success': False, 'message': 'ID de servicio no proporcionado'})
            servicio_obj = servicio.objects.get(id_servicio=id_servicio)
            servicio_obj.nombre_servicio = request.POST.get('nombre_servicio', servicio_obj.nombre_servicio)
            servicio_obj.descripcion_servicio = request.POST.get('descripcion_servicio', servicio_obj.descripcion_servicio)
            # El campo estatus_servicio ya no existe en el modelo servicio
            id_categoria = request.POST.get('categoria_servicio')
            if id_categoria:
                from .models import categoria_servicio
                try:
                    categoria_obj = categoria_servicio.objects.get(id_categoria_serv=id_categoria)
                    servicio_obj.id_categoria_servicios_fk = categoria_obj
                except categoria_servicio.DoesNotExist:
                    pass
            # Manejar múltiples imágenes si se proporcionan
            imagenes_servicio = request.FILES.getlist('imagenes_servicio')
            if imagenes_servicio:
                # Contar imágenes existentes
                imagenes_existentes = imagen_servicio.objects.filter(id_servicio_fk=servicio_obj).count()
                
                # Validar número máximo de imágenes (existentes + nuevas)
                if imagenes_existentes + len(imagenes_servicio) > 5:
                    return JsonResponse({
                        'success': False,
                        'message': f'Máximo 5 imágenes permitidas. Actualmente tienes {imagenes_existentes} imágenes. Puedes agregar máximo {5 - imagenes_existentes} más.'
                    })
                
                # Agregar nuevas imágenes sin eliminar las existentes
                for imagen in imagenes_servicio:
                    imagen_servicio.objects.create(
                        id_servicio_fk=servicio_obj,
                        ruta_imagen=imagen
                    )
            servicio_obj.save()
            return JsonResponse({'success': True, 'message': 'Servicio actualizado exitosamente'})
        except servicio.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al actualizar el servicio: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
from django.views.decorators.http import require_GET

# API para filtrar servicios por nombre (AJAX)
@require_GET
def api_filtrar_servicios(request):
    try:
        nombre = request.GET.get('nombre', '').strip().lower()
        estatus = request.GET.get('estatus', '').strip().lower()
        servicios_query = servicio.objects.all()
        if nombre:
            servicios_query = servicios_query.filter(nombre_servicio__icontains=nombre)
        
        # Ya no filtramos por estatus_servicio en el modelo servicio
        # El estatus ahora se maneja exclusivamente en servicio_sucursal
        
        servicios_list = []
        for idx, serv in enumerate(servicios_query, start=1):
            # Obtener la primera imagen del servicio desde la nueva tabla
            primera_imagen = imagen_servicio.objects.filter(id_servicio_fk=serv).first()
            imagen_url = primera_imagen.ruta_imagen.url if primera_imagen and primera_imagen.ruta_imagen else ''
                
            servicios_list.append({
                'id_servicio': serv.id_servicio,
                'nombre_servicio': serv.nombre_servicio,
                'descripcion_servicio': serv.descripcion_servicio or '',
                'imagen_servicio': imagen_url,
                'categoria_servicio': serv.id_categoria_servicios_fk.nombre_categoria_serv if serv.id_categoria_servicios_fk else '',
                'serial': idx
            })
        return JsonResponse({'success': True, 'servicios': servicios_list})
    except Exception as e:
        logger.error(f"Error al filtrar servicios: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error al filtrar servicios: {str(e)}'})

from django.views.decorators.http import require_GET

# API para filtrar productos por nombre (AJAX)
@require_GET
def api_filtrar_productos(request):
    try:
        nombre = request.GET.get('nombre', '').strip().lower()
        estatus = request.GET.get('estatus', '').strip().lower()
        productos_query = producto.objects.all()
        if nombre:
            productos_query = productos_query.filter(nombre_producto__icontains=nombre)
        # Ya no se filtra por estatus_producto porque el campo se ha movido a producto_sucursal
        productos_list = []
        for idx, prod in enumerate(productos_query, start=1):
            # Obtener la primera imagen del producto desde la nueva tabla
            primera_imagen = imagen_producto.objects.filter(id_producto_fk=prod).first()
            imagen_url = primera_imagen.ruta_imagen.url if primera_imagen and primera_imagen.ruta_imagen else ''
            
            productos_list.append({
                'id_producto': prod.id_producto,
                'nombre_producto': prod.nombre_producto,
                'descripcion_producto': prod.descripcion_producto or '',
                'marca_producto': prod.marca_producto or '',
                'modelo_producto': prod.modelo_producto or '',
                'imagen_producto': imagen_url,
                'caracteristicas_generales': prod.caracteristicas_generales or '',
                # Ya no se incluye estatus_producto porque el campo se ha movido a producto_sucursal
                'categoria_producto': prod.id_categoria_prod_fk.nombre_categoria_prod if prod.id_categoria_prod_fk else '',
                'serial': idx
            })
        return JsonResponse({'success': True, 'productos': productos_list})
    except Exception as e:
        logger.error(f"Error al filtrar productos: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error al filtrar productos: {str(e)}'})
from django.views.decorators.http import require_GET



# API para obtener nombres de categorías de producto
@require_GET
def api_categorias_producto(request):
    from .models import categoria_producto
    categorias = list(categoria_producto.objects.values_list('nombre_categoria_prod', flat=True))
    return JsonResponse({'categorias': categorias})

# API para obtener nombres de categorías de servicio
@require_GET
def api_categorias_servicio(request):
    from .models import categoria_servicio
    categorias = list(categoria_servicio.objects.values_list('nombre_categoria_serv', flat=True))
    return JsonResponse({'categorias': categorias})
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from .models import *
import logging

# Configurar el logger
logger = logging.getLogger(__name__)

# Funciones auxiliares para manejo de sesiones
def get_current_user(request):
    """
    Obtiene el usuario actual desde la sesión
    """
    if request.session.get('is_authenticated', False):
        try:
            user_id = request.session.get('user_id')
            return usuario.objects.get(id_usuario=user_id)
        except usuario.DoesNotExist:
            # Si el usuario no existe, limpiar la sesión
            logout_user(request)
            return None
    return None

def is_user_authenticated(request):
    """
    Verifica si el usuario está autenticado
    """
    return request.session.get('is_authenticated', False)

def logout_user(request):
    """
    Cierra la sesión del usuario
    """
    # Limpiar todas las variables de sesión
    request.session.flush()
    logger.info("Sesión cerrada exitosamente")

def require_login(view_func):
    """
    Decorador para proteger vistas que requieren autenticación
    """
    def wrapper(request, *args, **kwargs):
        if not is_user_authenticated(request):
            return redirect('/ecommerce/iniciar_sesion')
        return view_func(request, *args, **kwargs)
    return wrapper

# Create your views here.
def iniciar_sesion(request):
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.tipo_usuario,
                'is_authenticated': True
            }
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        logger.info(f"Intento de inicio de sesión para el email: {email}")
        
        if email and password:
            try:
                user = usuario.objects.get(correo_usuario=email)
                logger.info(f"Usuario encontrado: {user.correo_usuario}")
                logger.info(f"Contraseña almacenada: {user.password_usuario}")
                logger.info(f"Contraseña proporcionada: {password}")
                
                # Verificar si la contraseña está hasheada
                if not user.password_usuario.startswith('pbkdf2_sha256$'):
                    logger.warning("La contraseña no está hasheada correctamente")
                    # Si no está hasheada, comparar directamente
                    if user.password_usuario == password:
                        # Crear sesión personalizada
                        request.session['user_id'] = user.id_usuario
                        request.session['user_email'] = user.correo_usuario
                        request.session['user_name'] = user.nombre_usuario
                        request.session['user_type'] = user.tipo_usuario
                        request.session['is_authenticated'] = True
                        
                        logger.info(f"Sesión creada para usuario: {user.correo_usuario}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'redirect_url': '/ecommerce/index'
                        })
                    else:
                        return JsonResponse({'success': False, 'message': 'Contraseña incorrecta'})
                else:
                    # Si está hasheada, usar check_password
                    if check_password(password, user.password_usuario):
                        # Crear sesión personalizada
                        request.session['user_id'] = user.id_usuario
                        request.session['user_email'] = user.correo_usuario
                        request.session['user_name'] = user.nombre_usuario
                        request.session['user_type'] = user.tipo_usuario
                        request.session['is_authenticated'] = True
                        
                        logger.info(f"Sesión creada para usuario: {user.correo_usuario}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'redirect_url': '/ecommerce/index'
                        })
                    else:
                        return JsonResponse({'success': False, 'message': 'Contraseña incorrecta'})
            except usuario.DoesNotExist:
                logger.error(f"Usuario no encontrado: {email}")
                return JsonResponse({'success': False, 'message': 'Usuario no encontrado'})
            except Exception as e:
                logger.error(f"Error durante el inicio de sesión: {str(e)}")
                return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return render(request, 'ecommerce_app/iniciar_sesion.html', {'user_info': user_info})

@csrf_exempt
def validate_email(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        email = data.get('email')
        
        try:
            user = usuario.objects.get(correo_usuario=email)
            logger.info(f"Email validado exitosamente: {email}")
            return JsonResponse({'exists': True})
        except usuario.DoesNotExist:
            logger.warning(f"Email no encontrado: {email}")
            return JsonResponse({'exists': False})
        except Exception as e:
            logger.error(f"Error al validar email: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def login_ajax(request):
    """
    Vista para manejar el login AJAX desde el formulario de pasos
    """
    logger.info(f"login_ajax called with method: {request.method}")
    logger.info(f"Request headers: {request.headers}")
    logger.info(f"Request META: {request.META}")
    
    if request.method == 'POST':
        email = request.POST.get('login_email')
        password = request.POST.get('login_password')
        
        logger.info(f"Intento de login AJAX para el email: {email}")
        logger.info(f"POST data: {request.POST}")
        logger.info(f"Content-Type: {request.content_type}")
        
        if email and password:
            try:
                user = usuario.objects.get(correo_usuario=email)
                logger.info(f"Usuario encontrado: {user.correo_usuario}")
                
                # Verificar si la contraseña está hasheada
                if not user.password_usuario.startswith('pbkdf2_sha256$'):
                    logger.warning("La contraseña no está hasheada correctamente")
                    # Si no está hasheada, comparar directamente
                    if user.password_usuario == password:
                        # Crear sesión personalizada
                        request.session['user_id'] = user.id_usuario
                        request.session['user_email'] = user.correo_usuario
                        request.session['user_name'] = user.nombre_usuario
                        request.session['user_type'] = user.tipo_usuario
                        request.session['is_authenticated'] = True
                        
                        logger.info(f"Sesión creada para usuario: {user.correo_usuario}")
                        
                        # Verificar si el usuario ya tiene una empresa asociada
                        try:
                            empresa_existente = empresa.objects.filter(id_usuario_fk=user).first()
                            if empresa_existente:
                                logger.info(f"Usuario {user.correo_usuario} tiene empresa registrada")
                                return JsonResponse({
                                    'success': True, 
                                    'message': 'Inicio de sesión exitoso',
                                    'user_name': user.nombre_usuario,
                                    'user_type': user.tipo_usuario,
                                    'has_company': True,
                                    'redirect_url': '/ecommerce/sucursal/'
                                }, content_type='application/json')
                        except Exception as e:
                            logger.error(f"Error al verificar empresa existente: {str(e)}")
                        
                        logger.info(f"Usuario {user.correo_usuario} no tiene empresa registrada")
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'user_name': user.nombre_usuario,
                            'user_type': user.tipo_usuario,
                            'has_company': False
                        }, content_type='application/json')
                    else:
                        logger.warning(f"Contraseña incorrecta para usuario: {email}")
                        return JsonResponse({
                            'success': False, 
                            'message': 'Contraseña incorrecta'
                        }, content_type='application/json')
                else:
                    # Si está hasheada, usar check_password
                    if check_password(password, user.password_usuario):
                        # Crear sesión personalizada
                        request.session['user_id'] = user.id_usuario
                        request.session['user_email'] = user.correo_usuario
                        request.session['user_name'] = user.nombre_usuario
                        request.session['user_type'] = user.tipo_usuario
                        request.session['is_authenticated'] = True
                        
                        logger.info(f"Sesión creada para usuario: {user.correo_usuario}")
                        
                        # Verificar si el usuario ya tiene una empresa asociada
                        try:
                            empresa_existente = empresa.objects.filter(id_usuario_fk=user).first()
                            if empresa_existente:
                                logger.info(f"Usuario {user.correo_usuario} tiene empresa registrada")
                                return JsonResponse({
                                    'success': True, 
                                    'message': 'Inicio de sesión exitoso',
                                    'user_name': user.nombre_usuario,
                                    'user_type': user.tipo_usuario,
                                    'has_company': True,
                                    'redirect_url': '/ecommerce/sucursal/'
                                }, content_type='application/json')
                        except Exception as e:
                            logger.error(f"Error al verificar empresa existente: {str(e)}")
                        
                        logger.info(f"Usuario {user.correo_usuario} no tiene empresa registrada")
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'user_name': user.nombre_usuario,
                            'user_type': user.tipo_usuario,
                            'has_company': False
                        }, content_type='application/json')
                    else:
                        logger.warning(f"Contraseña incorrecta para usuario: {email}")
                        return JsonResponse({
                            'success': False, 
                            'message': 'Contraseña incorrecta'
                        }, content_type='application/json')
            except usuario.DoesNotExist:
                logger.warning(f"Usuario no encontrado: {email}")
                return JsonResponse({
                    'success': False, 
                    'message': 'Usuario no encontrado'
                }, content_type='application/json')
            except Exception as e:
                logger.error(f"Error in login_ajax: {str(e)}")
                return JsonResponse({
                    'success': False, 
                    'message': f'Error interno del servidor: {str(e)}'
                }, content_type='application/json')
        else:
            logger.warning("Campos faltantes en login AJAX")
            return JsonResponse({
                'success': False, 
                'message': 'Por favor completa todos los campos'
            }, content_type='application/json')
    
    logger.warning("Método no permitido en login_ajax")
    return JsonResponse({
        'success': False, 
        'message': 'Método no permitido'
    }, content_type='application/json')


def prueba(request):
    return render(request, 'ecommerce_app/prueba.html')


def registrar_persona(request):
    if request.method=='POST':
        logger.info(f"Datos recibidos: {request.POST}")
        nombre_usuario=request.POST.get('nombre_usuario')
        apellido=request.POST.get('apellido')
        email=request.POST.get('email')
        telefono=request.POST.get('telefono')
        password=request.POST.get('password')
        fecha_nacimiento=request.POST.get('fecha_nacimiento')
        pais=request.POST.get('pais')
        estado=request.POST.get('estado')

        # Validaciones del backend
        import re
        
        # Validar nombre (solo letras y espacios)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre_usuario):
            logger.warning(f"Nombre inválido: {nombre_usuario}")
            return JsonResponse({
                'success': False,
                'message': 'El nombre solo puede contener letras y espacios.'
            })
        
        # Validar apellido (solo letras y espacios)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', apellido):
            logger.warning(f"Apellido inválido: {apellido}")
            return JsonResponse({
                'success': False,
                'message': 'El apellido solo puede contener letras y espacios.'
            })
        
        # Validar teléfono (solo números)
        if not re.match(r'^[0-9]+$', telefono):
            logger.warning(f"Teléfono inválido: {telefono}")
            return JsonResponse({
                'success': False,
                'message': 'El teléfono solo puede contener números.'
            })

        # Validar que todos los campos estén completos
        if not nombre_usuario or not apellido or not email or not password or not telefono or not fecha_nacimiento or not pais or not estado:
            logger.warning("Campos obligatorios faltantes en registro de persona")
            return JsonResponse({
                'success': False,
                'message': 'Todos los campos son obligatorios. Por favor complete todos los campos.'
            })

        # Validar formato de email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            logger.warning(f"Email inválido: {email}")
            return JsonResponse({
                'success': False,
                'message': 'Por favor ingrese un email válido.'
            })

        # Validar longitud mínima de contraseña
        if len(password) < 6:
            logger.warning("Contraseña demasiado corta")
            return JsonResponse({
                'success': False,
                'message': 'La contraseña debe tener al menos 6 caracteres.'
            })

        try:
            # Encriptar la contraseña antes de guardarla
            password_encriptada = make_password(password)
            logger.info(f"Contraseña encriptada correctamente para el usuario: {email}")
            
            nuevo_usuario = usuario(
                nombre_usuario=nombre_usuario + ' ' + apellido,
                correo_usuario=email,
                telefono_usuario=telefono,
                password_usuario=password_encriptada,  # Usar la contraseña encriptada
                autenticacion_usuario='local',  
                tipo_usuario='persona',          
                fecha_nacimiento=fecha_nacimiento,
                pais=pais,
                estado=estado
            )
            nuevo_usuario.save()
            logger.info(f"Usuario registrado exitosamente: {email}")
            
            # Crear sesión automáticamente después del registro exitoso
            request.session['user_id'] = nuevo_usuario.id_usuario
            request.session['user_email'] = nuevo_usuario.correo_usuario
            request.session['user_name'] = nuevo_usuario.nombre_usuario
            request.session['user_type'] = nuevo_usuario.tipo_usuario
            request.session['is_authenticated'] = True
            
            logger.info(f"Sesión creada automáticamente para usuario registrado: {email}")
            
            return JsonResponse({
                'success': True,
                'message': '¡Registro exitoso! Tu cuenta ha sido creada correctamente.',
                'redirect_url': '/ecommerce/index'
            })
        except Exception as e:
            logger.error(f"Error al registrar usuario: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Ha ocurrido un error al registrar el usuario.'
            })

    # Obtener información del usuario si está autenticado
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.tipo_usuario,
                'is_authenticated': True
            }
    
    return render(request, 'ecommerce_app/registrar_persona.html', {'user_info': user_info})

def registrar_empresa(request):
    # Esta función debe ser accesible sin autenticación para el registro inicial
    # Solo se requiere autenticación para el POST (cuando se envía el formulario)
    current_user = get_current_user(request)
    
    if request.method == 'POST':
        # Verificar autenticación solo para el POST
        if not current_user:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Debe iniciar sesión para registrar una empresa'
                })
            else:
                return redirect('/ecommerce/iniciar_sesion/')

        try:
            logger.info(f"Datos recibidos: {request.POST}")
            nombre_empresa = request.POST.get('nombre_empresa')
            descripcion_empresa = request.POST.get('descripcion_empresa')
            logo_empresa = request.FILES.get('logo_empresa')
            pais_empresa = request.POST.get('pais_empresa')
            estado_empresa = request.POST.get('estado_empresa')
            tipo_empresa = request.POST.get('tipo_empresa')
            direccion_empresa = request.POST.get('direccion_empresa')
            latitud = request.POST.get('latitud')
            longitud = request.POST.get('longitud')

            # Validar que todos los campos estén completos
            if not nombre_empresa or not descripcion_empresa or not pais_empresa or not estado_empresa or not tipo_empresa or not direccion_empresa or not latitud or not longitud:
                logger.warning("Campos obligatorios faltantes en registro de empresa")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Todos los campos son obligatorios. Por favor complete todos los campos.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'user_info': None,
                        'is_authenticated': False,
                        'has_company': False,
                        'error_message': 'Todos los campos son obligatorios. Por favor complete todos los campos.'
                    })

            # Validar que las coordenadas sean números válidos
            try:
                lat = float(latitud)
                lng = float(longitud)
            except ValueError:
                logger.warning("Coordenadas inválidas")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Las coordenadas deben ser números válidos.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'user_info': None,
                        'is_authenticated': False,
                        'has_company': False,
                        'error_message': 'Las coordenadas deben ser números válidos.'
                    })

            # Validar longitud mínima de descripción
            if len(descripcion_empresa) < 10:
                logger.warning("Descripción demasiado corta")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'La descripción debe tener al menos 10 caracteres.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'user_info': None,
                        'is_authenticated': False,
                        'has_company': False,
                        'error_message': 'La descripción debe tener al menos 10 caracteres.'
                    })

            # NO DUPLICAR EMPRESA: Verificar si ya existe una empresa para este usuario
            existing_empresa = empresa.objects.filter(id_usuario_fk=current_user).first()
            if existing_empresa:
                logger.warning(f"El usuario {current_user.correo_usuario} ya tiene una empresa registrada. No se creará otra.")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Empresa ya registrada previamente',
                        'redirect_url': '/ecommerce/sucursal/'
                    })
                else:
                    return redirect('/ecommerce/sucursal/')

            # Logging para verificar los datos
            logger.info(f"Dirección recibida: {direccion_empresa}")
            logger.info(f"Tipo de dirección: {type(direccion_empresa)}")

            nueva_empresa = empresa(
                nombre_empresa=nombre_empresa,
                descripcion_empresa=descripcion_empresa,
                logo_empresa=logo_empresa,
                pais_empresa=pais_empresa,
                estado_empresa=estado_empresa,
                tipo_empresa=tipo_empresa,  
                direccion_empresa=direccion_empresa,
                latitud_empresa=latitud,
                longitud_empresa=longitud,
                id_usuario_fk=current_user
            )
            nueva_empresa.save()
            logger.info(f"Empresa guardada exitosamente: {nueva_empresa.nombre_empresa}")
            logger.info(f"Dirección guardada: {nueva_empresa.direccion_empresa}")

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Empresa registrada exitosamente',
                    'redirect_url': '/ecommerce/sucursal/'
                })
            else:
                return redirect('/ecommerce/sucursal/')
        except Exception as e:
            logger.error(f"Error al guardar la empresa: {str(e)}")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
            else:
                return render(request, 'ecommerce_app/registrar_empresa.html', {
                    'user_info': None,
                    'is_authenticated': False,
                    'has_company': False,
                    'error_message': str(e)
                })
    
    # Si es GET, mostrar el formulario
    # Obtener información del usuario si está autenticado
    user_info = None
    is_authenticated = False
    has_company = False
    
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.tipo_usuario,
                'is_authenticated': True
            }
            is_authenticated = True
            
            # Verificar si el usuario ya tiene una empresa registrada
            existing_company = empresa.objects.filter(id_usuario_fk=current_user).first()
            if existing_company:
                has_company = True
                logger.info(f"Usuario {current_user.correo_usuario} ya tiene empresa registrada: {existing_company.nombre_empresa}")
            else:
                has_company = False
                logger.info(f"Usuario {current_user.correo_usuario} no tiene empresa registrada")
    
    return render(request, 'ecommerce_app/registrar_empresa.html', {
        'user_info': user_info,
        'is_authenticated': is_authenticated,
        'has_company': has_company
    })



@require_login
def sucursalfuncion(request):



    user_info = None
    
            
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.tipo_usuario,
                'is_authenticated': True
            }
    # Obtener la empresa del usuario actual
    empresa_obj = empresa.objects.filter(id_usuario_fk=current_user).first()
    if not empresa_obj:
        # Si el usuario no tiene empresa, redirigir a registrar empresa
        return redirect('/ecommerce/registrar_empresa/')
    # Obtener todas las sucursales de la empresa del usuario
    sqlsucursal = sucursal.objects.filter(id_empresa_fk=empresa_obj)
   
    if request.method == 'POST':
        try:
            nombre_sucursal = request.POST.get('nombre_sucursal', '').strip()
            telefono_sucursal = request.POST.get('telefono_sucursal', '').strip()
            estado_sucursal = request.POST.get('estado_sucursal', '').strip()
            direccion_sucursal = request.POST.get('direccion_sucursal', '').strip()
            latitud_sucursal = request.POST.get('latitud_sucursal', '').strip()
            longitud_sucursal = request.POST.get('longitud_sucursal', '').strip()

            # Validaciones de campos vacíos
            if not nombre_sucursal or not telefono_sucursal or not estado_sucursal or not direccion_sucursal:
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son obligatorios.'
                })

            # Validar que el teléfono sea numérico
            if not telefono_sucursal.isdigit():
                return JsonResponse({
                    'success': False,
                    'message': 'El número de teléfono solo debe contener dígitos.'
                })

            # Validar que el nombre de sucursal no se repita para la empresa
            if sucursal.objects.filter(id_empresa_fk=empresa_obj, nombre_sucursal__iexact=nombre_sucursal).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una sucursal con ese nombre para esta empresa.'
                })

            nueva_sucursal = sucursal(
                nombre_sucursal=nombre_sucursal,
                telefono_sucursal=telefono_sucursal,
                estado_sucursal=estado_sucursal,
                direccion_sucursal=direccion_sucursal,
                latitud_sucursal=float(latitud_sucursal) if latitud_sucursal else None,
                longitud_sucursal=float(longitud_sucursal) if longitud_sucursal else None,
                id_empresa_fk=empresa_obj
            )
            nueva_sucursal.save()
            return JsonResponse({
                'success': True,
                'message': 'Sucursal registrada exitosamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    # Implementar paginación
    page = request.GET.get('page', 1)
    paginator = Paginator(sqlsucursal, 5)  # 5 registros por página
    
    try:
        sucursales_paginadas = paginator.page(page)
    except:
        sucursales_paginadas = paginator.page(1)

    return render(request, 'ecommerce_app/sucursal.html', {
        'sqlsucursal': sucursales_paginadas,
        'total_sucursales': sqlsucursal.count(),
        'paginator': paginator,
        'user_info': user_info,
        'empresa_obj': empresa_obj
    })


@require_login
def editar_sucursal(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    if request.method == 'POST':
        try:
            id_sucursal = request.POST.get('id_sucursal')
            sucursal_obj = sucursal.objects.get(id_sucursal=id_sucursal)
            nombre_sucursal = request.POST.get('nombre_sucursal', '').strip()
            telefono_sucursal = request.POST.get('telefono_sucursal', '').strip()
            estado_sucursal = request.POST.get('estado_sucursal', '').strip()
            direccion_sucursal = request.POST.get('direccion_sucursal', '').strip()
            latitud_sucursal = request.POST.get('latitud_sucursal', '').strip()
            longitud_sucursal = request.POST.get('longitud_sucursal', '').strip()

            # Validaciones de campos vacíos
            if not nombre_sucursal or not telefono_sucursal or not estado_sucursal or not direccion_sucursal:
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son obligatorios.'
                }, content_type='application/json')

            # Validar que el teléfono sea numérico
            if not telefono_sucursal.isdigit():
                return JsonResponse({
                    'success': False,
                    'message': 'El número de teléfono solo debe contener dígitos.'
                }, content_type='application/json')

            # Validar que el nombre de sucursal no se repita para la empresa (excepto la actual)
            empresa_obj = sucursal_obj.id_empresa_fk
            if sucursal.objects.filter(id_empresa_fk=empresa_obj, nombre_sucursal__iexact=nombre_sucursal).exclude(id_sucursal=id_sucursal).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una sucursal con ese nombre para esta empresa.'
                }, content_type='application/json')

            # Actualizar los datos
            sucursal_obj.nombre_sucursal = nombre_sucursal
            sucursal_obj.telefono_sucursal = telefono_sucursal
            sucursal_obj.estado_sucursal = estado_sucursal
            sucursal_obj.direccion_sucursal = direccion_sucursal
            sucursal_obj.latitud_sucursal = float(latitud_sucursal) if latitud_sucursal else None
            sucursal_obj.longitud_sucursal = float(longitud_sucursal) if longitud_sucursal else None

            sucursal_obj.save()
            return JsonResponse({
                'success': True,
                'message': 'Sucursal actualizada exitosamente'
            }, content_type='application/json')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, content_type='application/json')
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, content_type='application/json')



@require_login
def eliminar_sucursal(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    if request.method == 'POST':
        try:
            id_sucursal = request.POST.get('id_sucursal')
            sucursal_obj = sucursal.objects.get(id_sucursal=id_sucursal)
            nombre_sucursal = sucursal_obj.nombre_sucursal
            sucursal_obj.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Sucursal {nombre_sucursal} eliminada exitosamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })





@require_login
def producto_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    # Obtener la empresa del usuario actual
    try:
        empresa_obj = empresa.objects.get(id_usuario_fk=current_user)
        categoria_producto_all = categoria_producto.objects.all()
    except empresa.DoesNotExist:
        # Si el usuario no tiene empresa, redirigir a registrar empresa
        return redirect('/ecommerce/registrar_empresa/')

    # user_info para la sesión
    user_info = {
        'id': current_user.id_usuario,
        'nombre': current_user.nombre_usuario,
        'email': current_user.correo_usuario,
        'tipo': current_user.tipo_usuario,
        'is_authenticated': True
    }

    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            nombre_producto = request.POST.get('nombre_producto', '').strip()
            descripcion_producto = request.POST.get('descripcion_producto', '').strip()
            marca_producto = request.POST.get('marca_producto', '').strip()
            modelo_producto = request.POST.get('modelo_producto', '').strip()
            # Obtener múltiples imágenes (hasta 5)
            imagenes_producto = request.FILES.getlist('imagenes_producto')
            caracteristicas_generales = request.POST.get('caracteristicas_generales', '').strip()
            categoria_id = request.POST.get('categoria_producto', '').strip()

            # Validaciones backend
            if not nombre_producto:
                return JsonResponse({'success': False, 'message': 'El nombre del producto es obligatorio.', 'field': 'nombre'})
            if not descripcion_producto:
                return JsonResponse({'success': False, 'message': 'La descripción es obligatoria.', 'field': 'descripcion'})
            if not caracteristicas_generales:
                return JsonResponse({'success': False, 'message': 'Las características generales son obligatorias.', 'field': 'caracteristicas'})
            if not categoria_id:
                return JsonResponse({'success': False, 'message': 'Debe seleccionar una categoría.', 'field': 'categoria'})
            # Validar que se haya seleccionado al menos una imagen
            if not imagenes_producto:
                return JsonResponse({'success': False, 'message': 'Debe seleccionar al menos una imagen para el producto.', 'field': 'imagenes_producto'})
            
            # Validar que no se excedan las 5 imágenes
            if len(imagenes_producto) > 5:
                return JsonResponse({'success': False, 'message': 'No puede subir más de 5 imágenes por producto.', 'field': 'imagenes_producto'})

            categoria_producto_consul = categoria_producto.objects.get(id_categoria_prod=categoria_id)

            # Crear el producto sin imagen
            nuevo_producto = producto(
                nombre_producto=nombre_producto,
                descripcion_producto=descripcion_producto,
                marca_producto=marca_producto,
                modelo_producto=modelo_producto,
                caracteristicas_generales=caracteristicas_generales,
                id_empresa_fk=empresa_obj,
                id_categoria_prod_fk=categoria_producto_consul
            )
            nuevo_producto.save()
            logger.info(f"Producto guardado exitosamente: {nuevo_producto.nombre_producto}")
            
            # Guardar las imágenes en la tabla imagen_producto
            from .models import imagen_producto
            for imagen in imagenes_producto:
                imagen_producto.objects.create(
                    ruta_imagen=imagen,
                    id_producto_fk=nuevo_producto
                )
            logger.info(f"Se guardaron {len(imagenes_producto)} imágenes para el producto {nuevo_producto.nombre_producto}")
            
            # Ya no guardamos el estatus en la sesión porque el campo se ha eliminado del formulario
            
            return JsonResponse({
                'success': True,
                'message': 'Producto registrado exitosamente'
            })
        except Exception as e:
            logger.error(f"Error al guardar el producto: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return render(request, 'ecommerce_app/producto.html', {'categoria_producto_all': categoria_producto_all, 'user_info': user_info})

@require_login
def servicio_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    # user_info para la sesión
    user_info = {
        'id': current_user.id_usuario,
        'nombre': current_user.nombre_usuario,
        'email': current_user.correo_usuario,
        'tipo': current_user.tipo_usuario,
        'is_authenticated': True
    }

    # Obtener la empresa del usuario actual
    try:
        empresa_obj = empresa.objects.get(id_usuario_fk=current_user)
        categoria_servicio_all = categoria_servicio.objects.all()
    except empresa.DoesNotExist:
        # Si el usuario no tiene empresa, redirigir a registrar empresa
        return redirect('/ecommerce/registrar_empresa/')

    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            nombre_servicio = request.POST.get('nombre_servicio', '').strip()
            descripcion_servicio = request.POST.get('descripcion_servicio', '').strip()
            categoria_id = request.POST.get('categoria_servicio', '').strip()
            # Obtener múltiples imágenes (hasta 5)
            imagenes_servicio = request.FILES.getlist('imagenes_servicio')

            # Validaciones backend
            if not nombre_servicio:
                return JsonResponse({'success': False, 'message': 'El nombre del servicio es obligatorio.', 'field': 'nombre_servicio'})
            if servicio.objects.filter(nombre_servicio__iexact=nombre_servicio, id_empresa_fk=empresa_obj).exists():
                return JsonResponse({'success': False, 'message': 'Ya existe un servicio con ese nombre.', 'field': 'nombre_servicio'})
            if not descripcion_servicio:
                return JsonResponse({'success': False, 'message': 'La descripción del servicio es obligatoria.', 'field': 'descripcion_servicio'})
            if not categoria_id:
                return JsonResponse({'success': False, 'message': 'Debe seleccionar una categoría.', 'field': 'categoria_servicio'})
            # Validar que se haya seleccionado al menos una imagen
            if not imagenes_servicio:
                return JsonResponse({'success': False, 'message': 'Debe seleccionar al menos una imagen para el servicio.', 'field': 'imagenes_servicio'})
            
            # Validar que no se excedan las 5 imágenes
            if len(imagenes_servicio) > 5:
                return JsonResponse({'success': False, 'message': 'No puede subir más de 5 imágenes por servicio.', 'field': 'imagenes_servicio'})

            categoria_servicio_consul = categoria_servicio.objects.get(id_categoria_serv=categoria_id)

            # Crear el servicio sin imagen
            nuevo_servicio = servicio(
                nombre_servicio=nombre_servicio,
                descripcion_servicio=descripcion_servicio,
                id_empresa_fk=empresa_obj,
                id_categoria_servicios_fk=categoria_servicio_consul
            )
            nuevo_servicio.save()   
            logger.info(f"Servicio guardado exitosamente: {nuevo_servicio.nombre_servicio}")
            
            # Guardar las imágenes en la tabla imagen_servicio
            from .models import imagen_servicio
            for imagen in imagenes_servicio:
                imagen_servicio.objects.create(
                    ruta_imagen=imagen,
                    id_servicio_fk=nuevo_servicio
                )
            logger.info(f"Se guardaron {len(imagenes_servicio)} imágenes para el servicio {nuevo_servicio.nombre_servicio}")
            
            # Ya no guardamos el estatus en la sesión porque el campo se ha eliminado del formulario
            
            return JsonResponse({
                'success': True,
                'message': 'Servicio registrado exitosamente'
            })

        except Exception as e:
            logger.error(f"Error al registrar servicio: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error al registrar el servicio'
            })

    return render(request, 'ecommerce_app/servicio.html', {'categoria_servicio_all': categoria_servicio_all, 'user_info': user_info})



@require_login
def eliminar_todas_sucursales(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    if request.method == 'POST':
        try:
            # Obtener todas las sucursales
            sucursales = sucursal.objects.all()
            # Contar cuántas sucursales se eliminarán
            cantidad = sucursales.count()
            # Eliminar todas las sucursales
            sucursales.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Se han eliminado {cantidad} sucursales exitosamente'
            }, content_type='application/json')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, content_type='application/json')
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, content_type='application/json')





@require_login
def categoria_producto_funcion(request):
    # Obtener información de usuario en sesión
    user_info = None
    current_user = get_current_user(request)
    if current_user:
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.tipo_usuario,
            'is_authenticated': True
        }

    if request.method == 'POST':
        try:
            nombre_categoria = request.POST.get('nombre_categoria', '').strip()
            descripcion_categoria = request.POST.get('descripcion_categoria', '').strip()
            estatus_categoria = request.POST.get('estatus_categoria', '').strip()
            fecha_creacion = request.POST.get('fecha_creacion')

            # Validaciones
            if not nombre_categoria:
                return JsonResponse({'success': False, 'message': 'El nombre de la categoría es obligatorio.'}, content_type='application/json')
            if categoria_producto.objects.filter(nombre_categoria_prod__iexact=nombre_categoria).exists():
                return JsonResponse({'success': False, 'message': 'Ya existe una categoría con ese nombre.'}, content_type='application/json')
            if not estatus_categoria:
                return JsonResponse({'success': False, 'message': 'Debe seleccionar un estatus.'}, content_type='application/json')

            nueva_categoria = categoria_producto(
                nombre_categoria_prod=nombre_categoria,
                descripcion_categoria_prod=descripcion_categoria,
                estatus_categoria_prod=estatus_categoria,
                fecha_creacion_prod=fecha_creacion
            )
            nueva_categoria.save()
            return JsonResponse({
                'success': True,
                'message': 'Categoría registrada exitosamente'
            }, content_type='application/json')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, content_type='application/json')

    return render(request, 'ecommerce_app/categoria_producto.html', {'user_info': user_info})

def categoria_servicio_funcion(request):
    # Obtener información de usuario en sesión
    user_info = None
    current_user = get_current_user(request)
    if current_user:
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.tipo_usuario,
            'is_authenticated': True
        }

    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            nombre_categoria = request.POST.get('nombre_categoria', '').strip()
            descripcion_categoria = request.POST.get('descripcion_categoria', '').strip()
            estatus_categoria = request.POST.get('estatus_categoria', '').strip()
            fecha_creacion = request.POST.get('fecha_creacion')

            # Validaciones
            if not nombre_categoria:
                return JsonResponse({'success': False, 'message': 'El nombre de la categoría es obligatorio.'})
            if not descripcion_categoria:
                return JsonResponse({'success': False, 'message': 'La descripción de la categoría es obligatoria.'})
            if not estatus_categoria:
                return JsonResponse({'success': False, 'message': 'Debe seleccionar un estatus.'})
            if not fecha_creacion:
                return JsonResponse({'success': False, 'message': 'Debe ingresar la fecha de creación.'})
            if categoria_servicio.objects.filter(nombre_categoria_serv__iexact=nombre_categoria).exists():
                return JsonResponse({'success': False, 'message': 'Ya existe una categoría con ese nombre.'})

            nueva_categoria = categoria_servicio(
                nombre_categoria_serv=nombre_categoria,
                descripcion_categoria_serv=descripcion_categoria,
                estatus_categoria_serv=estatus_categoria,
                fecha_creacion_categ_serv=fecha_creacion
            )
            nueva_categoria.save()
            logger.info(f"Categoria guardada exitosamente: {nueva_categoria.nombre_categoria_serv}")
            return JsonResponse({
                'success': True,
                'message': 'Categoría registrada exitosamente'
            })
        except Exception as e:
            logger.error(f"Error al guardar la categoría: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al registrar la categoría: {str(e)}'
            })

    return render(request, 'ecommerce_app/categoria_servicio.html', {'user_info': user_info})





@require_login
def categ_producto_config_funcion(request):
    categ_producto_all = categoria_producto.objects.all().order_by('-fecha_creacion_prod')
    # Logging básico
    logger.info(f"Total de categorías encontradas: {categ_producto_all.count()}")

    # Obtener información de usuario autenticado
    user_info = None
    current_user = get_current_user(request)
    if current_user:
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.tipo_usuario,
            'is_authenticated': True
        }

    return render(request, 'ecommerce_app/categ_producto_config.html', {
        'categoria_producto': categ_producto_all,
        'user_info': user_info
    })

@require_GET
def api_filtrar_categorias_producto(request):
    try:
        # Obtener parámetros de la solicitud
        nombre = request.GET.get('nombre', '').strip().lower()
        estatus = request.GET.get('estatus', '').strip()
        
        # Iniciar con todas las categorías
        categorias_query = categoria_producto.objects.all()
        
        # Filtrar por nombre si se proporciona
        if nombre:
            categorias_query = categorias_query.filter(nombre_categoria_prod__icontains=nombre)
        
        # Filtrar por estatus si se proporciona y no es 'todos'
        if estatus and estatus.lower() != 'todos':
            categorias_query = categorias_query.filter(estatus_categoria_prod=estatus)
        
        # Convertir a lista de diccionarios para la respuesta JSON
        categorias_list = list(categorias_query.values(
            'id_categoria_prod', 
            'nombre_categoria_prod', 
            'descripcion_categoria_prod', 
            'estatus_categoria_prod'
        ))
        
        return JsonResponse({
            'success': True,
            'categorias': categorias_list
        })
    except Exception as e:
        logger.error(f"Error al filtrar categorías: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al filtrar categorías: {str(e)}'
        })





def eliminar_categoria_producto(request):
    if request.method == 'POST':
        try:
            # Logging de todos los datos recibidos
            logger.info(f"Datos POST recibidos: {request.POST}")
            logger.info(f"Headers recibidos: {request.headers}")
            
            id_categoria = request.POST.get('id_categoria')
            logger.info(f"ID de categoría extraído: '{id_categoria}' (tipo: {type(id_categoria)})")
            
            if not id_categoria:
                logger.error("No se proporcionó ID de categoría")
                return JsonResponse({
                    'success': False,
                    'message': 'ID de categoría no proporcionado'
                })
            
            # Validar que el ID sea un número válido
            try:
                id_categoria_int = int(id_categoria)
                logger.info(f"ID de categoría convertido a entero: {id_categoria_int}")
            except ValueError:
                logger.error(f"ID de categoría no es un número válido: '{id_categoria}'")
                return JsonResponse({
                    'success': False,
                    'message': f'ID de categoría inválido: {id_categoria}'
                })
                
            categoria_obj = categoria_producto.objects.get(id_categoria_prod=id_categoria_int)
            nombre_categoria = categoria_obj.nombre_categoria_prod
            logger.info(f"Categoría encontrada: {nombre_categoria}")
            
            # Verificar si hay productos asociados
            productos_asociados = producto.objects.filter(id_categoria_prod_fk=categoria_obj).exists()
            if productos_asociados:
                logger.error(f"No se puede eliminar la categoría {nombre_categoria} porque tiene productos asociados")
                return JsonResponse({
                    'success': False,
                    'message': f'No se puede eliminar la categoría "{nombre_categoria}" porque tiene productos asociados'
                })
            
            categoria_obj.delete()
            logger.info(f"Categoría eliminada exitosamente: {nombre_categoria}")
            
            return JsonResponse({
                'success': True,
                'message': f'Categoría "{nombre_categoria}" eliminada exitosamente'
            })
            
        except categoria_producto.DoesNotExist:
            logger.error(f"Error al eliminar la categoría: Categoría no encontrada con ID {id_categoria}")
            return JsonResponse({
                'success': False,
                'message': 'Categoría no encontrada'
            })
        except Exception as e:
            logger.error(f"Error al eliminar la categoría: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar la categoría: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })


def editar_categoria_producto(request):
    if request.method == 'POST':
        try:
            id_categoria = request.POST.get('id_categoria')
            logger.info(f"Intentando editar categoría con ID: {id_categoria}")
            
            if not id_categoria:
                logger.error("No se proporcionó ID de categoría")
                return JsonResponse({
                    'success': False,
                    'message': 'ID de categoría no proporcionado'
                })
            
            categoria_obj = categoria_producto.objects.get(id_categoria_prod=id_categoria)
            
            # Actualizar los datos
            categoria_obj.nombre_categoria_prod = request.POST.get('nombre_categoria')
            categoria_obj.descripcion_categoria_prod = request.POST.get('descripcion_categoria')
            categoria_obj.estatus_categoria_prod = request.POST.get('estatus_categoria')
            
            categoria_obj.save()
            logger.info(f"Categoría actualizada exitosamente: {categoria_obj.nombre_categoria_prod}")
            
            return JsonResponse({
                'success': True,
                'message': f'Categoría "{categoria_obj.nombre_categoria_prod}" actualizada exitosamente'
            })
            
        except categoria_producto.DoesNotExist:
            logger.error(f"Error al editar la categoría: Categoría no encontrada con ID {id_categoria}")
            return JsonResponse({
                'success': False,
                'message': 'Categoría no encontrada'
            })
        except Exception as e:
            logger.error(f"Error al editar la categoría: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al editar la categoría: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })



def editar_categoria_servicio(request):
    if request.method == 'POST':
        try:
            id_categoria = request.POST.get('id_categoria')
            logger.info(f"Intentando editar categoría de servicio con ID: {id_categoria}")
            if not id_categoria:
                logger.error("No se proporcionó ID de categoría de servicio")
                return JsonResponse({
                    'success': False,
                    'message': 'ID de categoría de servicio no proporcionado'
                })
            categoria_obj = categoria_servicio.objects.get(id_categoria_serv=id_categoria)
            # Actualizar los datos
            categoria_obj.nombre_categoria_serv = request.POST.get('nombre_categoria')
            categoria_obj.descripcion_categoria_serv = request.POST.get('descripcion_categoria')
            categoria_obj.estatus_categoria_serv = request.POST.get('estatus_categoria')
            categoria_obj.save()
            logger.info(f"Categoría de servicio actualizada exitosamente: {categoria_obj.nombre_categoria_serv}")
            return JsonResponse({
                'success': True,
                'message': f'Categoría de servicio "{categoria_obj.nombre_categoria_serv}" actualizada exitosamente'
            })
        except categoria_servicio.DoesNotExist:
            logger.error(f"Error al editar la categoría de servicio: Categoría no encontrada con ID {id_categoria}")
            return JsonResponse({
                'success': False,
                'message': 'Categoría de servicio no encontrada'
            })
        except Exception as e:
            logger.error(f"Error al editar la categoría de servicio: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al editar la categoría de servicio: {str(e)}'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })














def categ_servicio_config_funcion(request):
    categ_servicio_all= categoria_servicio.objects.all()


    return render(request, 'ecommerce_app/categ_servicio_config.html', {'categoria_servicio':categ_servicio_all})



def eliminar_categoria_servicio_funcion(request):
    if request.method == 'POST':
        try:
            id_categoria_servicio = request.POST.get('id_categoriaservicio')
            logger.info(f"Intentando eliminar categoría con ID: {id_categoria_servicio}")
            if not id_categoria_servicio:
                logger.error("No se proporcionó ID de categoría")
                return JsonResponse({'success': False, 'message': 'ID de categoría no proporcionado'})
            categoria_obj = categoria_servicio.objects.get(id_categoria_serv=id_categoria_servicio)
            nombre_categoria_servicio = categoria_obj.nombre_categoria_serv
            # Verificar si hay servicios asociados
            servicios_asociados = servicio.objects.filter(id_categoria_servicios_fk=categoria_obj).exists()
            if servicios_asociados:
                logger.error(f"No se puede eliminar la categoría {nombre_categoria_servicio} porque tiene servicios asociados")
                return JsonResponse({'success': False, 'message': f'No se puede eliminar la categoría "{nombre_categoria_servicio}" porque tiene servicios asociados'})
            categoria_obj.delete()
            logger.info(f"Categoría eliminada exitosamente: {nombre_categoria_servicio}")
            return JsonResponse({'success': True, 'message': f'Categoría "{nombre_categoria_servicio}" eliminada exitosamente'})
        except categoria_servicio.DoesNotExist:
            logger.error(f"Error al eliminar la categoría: Categoría no encontrada con ID {id_categoria_servicio}")
            return JsonResponse({'success': False, 'message': 'Categoría no encontrada'})
        except Exception as e:
            logger.error(f"Error al eliminar la categoría: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error al eliminar la categoría: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

def producto_config_funcion(request):
    # Obtenemos los productos con sus relaciones a sucursales
    productos_all = producto.objects.all()
    # También obtenemos las relaciones producto_sucursal para tener acceso al estatus
    producto_sucursal_all = producto_sucursal.objects.select_related('id_producto_fk').all()
    categoria_producto_all = categoria_producto.objects.all()
    
    # Agregar la primera imagen de cada producto
    productos_con_imagenes = []
    for prod in productos_all:
        primera_imagen = imagen_producto.objects.filter(id_producto_fk=prod).first()
        prod.primera_imagen = primera_imagen
        productos_con_imagenes.append(prod)
    
    return render(request, 'ecommerce_app/producto_config.html', {
        'producto_sucursal_all': productos_con_imagenes,  # Mantenemos el mismo nombre de variable para no cambiar la plantilla
        'producto_sucursal_relaciones': producto_sucursal_all,  # Añadimos las relaciones
        'categoria_producto_all': categoria_producto_all
    })



def servicio_config_funcion(request):
    servicios_all = servicio.objects.all()
    categoria_servicio_all = categoria_servicio.objects.all()
    
    # Agregar la primera imagen de cada servicio
    servicios_con_imagenes = []
    for serv in servicios_all:
        primera_imagen = imagen_servicio.objects.filter(id_servicio_fk=serv).first()
        serv.primera_imagen = primera_imagen
        servicios_con_imagenes.append(serv)
    
    return render(request, 'ecommerce_app/servicio_config.html', {
        'servicio_all': servicios_con_imagenes,
        'categoria_servicio_all': categoria_servicio_all
    })



def editar_producto(request):
    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos para editar producto: {request.POST}")
            
            id_producto = request.POST.get('id_producto')
            if not id_producto:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de producto no proporcionado'
                })
            
            producto_obj = producto.objects.get(id_producto=id_producto)
            
            # Actualizar los datos básicos
            producto_obj.nombre_producto = request.POST.get('nombre_producto')
            producto_obj.descripcion_producto = request.POST.get('descripcion_producto')
            producto_obj.marca_producto = request.POST.get('marca_producto')
            producto_obj.modelo_producto = request.POST.get('modelo_producto')
            producto_obj.caracteristicas_generales = request.POST.get('caracteristicas_generales')
            # El campo estatus_producto ya no existe en el modelo producto
            
            # Actualizar categoría si se proporciona
            categoria_id = request.POST.get('categoria_producto')
            if categoria_id:
                try:
                    categoria_obj = categoria_producto.objects.get(id_categoria_prod=categoria_id)
                    producto_obj.id_categoria_prod_fk = categoria_obj
                except categoria_producto.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Categoría no encontrada'
                    })
            
            # Manejar múltiples imágenes si se proporcionan
            imagenes_producto = request.FILES.getlist('imagenes_producto')
            if imagenes_producto:
                # Contar imágenes existentes
                imagenes_existentes = imagen_producto.objects.filter(id_producto_fk=producto_obj).count()
                
                # Validar número máximo de imágenes (existentes + nuevas)
                if imagenes_existentes + len(imagenes_producto) > 5:
                    return JsonResponse({
                        'success': False,
                        'message': f'Máximo 5 imágenes permitidas. Actualmente tienes {imagenes_existentes} imágenes. Puedes agregar máximo {5 - imagenes_existentes} más.'
                    })
                
                # Agregar nuevas imágenes sin eliminar las existentes
                for imagen in imagenes_producto:
                    imagen_producto.objects.create(
                        id_producto_fk=producto_obj,
                        ruta_imagen=imagen
                    )
            
            producto_obj.save()
            logger.info(f"Producto actualizado exitosamente: {producto_obj.nombre_producto}")
            
            return JsonResponse({
                'success': True,
                'message': 'Producto actualizado exitosamente'
            })
            
        except producto.DoesNotExist:
            logger.error(f"Producto no encontrado con ID: {id_producto}")
            return JsonResponse({
                'success': False,
                'message': 'Producto no encontrado'
            })
        except Exception as e:
            logger.error(f"Error al actualizar producto: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar el producto: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

def eliminar_producto(request):
    if request.method == 'POST':
        try:
            id_producto = request.POST.get('id_producto')
            logger.info(f"Intentando eliminar producto con ID: {id_producto}")
            
            if not id_producto:
                logger.error("No se proporcionó ID de producto")
                return JsonResponse({
                    'success': False,
                    'message': 'ID de producto no proporcionado'
                })
                
            producto_obj = producto.objects.get(id_producto=id_producto)
            nombre_producto = producto_obj.nombre_producto
            
            # Verificar si hay productos_sucursal asociados
            productos_sucursal_asociados = producto_sucursal.objects.filter(id_producto_fk=producto_obj).exists()
            if productos_sucursal_asociados:
                logger.error(f"No se puede eliminar el producto {nombre_producto} porque tiene registros en sucursales")
                return JsonResponse({
                    'success': False,
                    'message': f'No se puede eliminar el producto "{nombre_producto}" porque tiene registros en sucursales'
                })
            
            producto_obj.delete()
            logger.info(f"Producto eliminado exitosamente: {nombre_producto}")
            
            return JsonResponse({
                'success': True,
                'message': f'Producto "{nombre_producto}" eliminado exitosamente'
            })
            
        except producto.DoesNotExist:
            logger.error(f"Error al eliminar el producto: Producto no encontrado con ID {id_producto}")
            return JsonResponse({
                'success': False,
                'message': 'Producto no encontrado'
            })
        except Exception as e:
            logger.error(f"Error al eliminar el producto: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar el producto: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

def index(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            # Buscar empresa asociada
            empresa_nombre = None
            try:
                empresa_obj = empresa.objects.filter(id_usuario_fk=current_user).first()
                if empresa_obj:
                    empresa_nombre = empresa_obj.nombre_empresa
            except Exception as e:
                empresa_nombre = None
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.tipo_usuario,
                'is_authenticated': True,
                'empresa_nombre': empresa_nombre
            }
    
    return render(request, 'ecommerce_app/index.html', {'user_info': user_info})

# Vista para cerrar sesión
def cerrar_sesion(request):
    logout_user(request)
    return redirect('/ecommerce/iniciar_sesion')

@csrf_exempt
def logout_ajax(request):
    """
    Vista para manejar el logout AJAX
    """
    if request.method == 'POST':
        logout_user(request)
        return JsonResponse({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@csrf_exempt
def get_user_info(request):
    """
    Vista para obtener información del usuario en sesión
    """
    if request.method == 'GET':
        current_user = get_current_user(request)
        if current_user:
            return JsonResponse({
                'success': True,
                'user_name': current_user.nombre_usuario,
                'user_email': current_user.correo_usuario,
                'user_type': current_user.tipo_usuario
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no autenticado'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })


def perfil_empresa(request):
    # Validar usuario autenticado y obtener empresa asociada
    user_info = None
    empresa_obj = None
    
    if not is_user_authenticated(request):
        # Si no está autenticado, redirigir a iniciar sesión
        return redirect('/ecommerce/iniciar_sesion')
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    empresa_obj = None
    empresa_nombre = None
    try:
        empresa_obj = empresa.objects.filter(id_usuario_fk=current_user).first()
        if empresa_obj:
            empresa_nombre = empresa_obj.nombre_empresa
    except Exception as e:
        empresa_obj = None
        empresa_nombre = None
    user_info = {
        'id': current_user.id_usuario,
        'nombre': current_user.nombre_usuario,
        'email': current_user.correo_usuario,
        'tipo': current_user.tipo_usuario,
        'is_authenticated': True,
        'empresa_nombre': empresa_nombre
    }
    return render(request, 'ecommerce_app/perfil_empresa.html', {
        'user_info': user_info,
        'empresa': empresa_obj
    })


def busquedad(request):
    query = request.GET.get('query', '')
    resultados_productos = []
    resultados_servicios = []
    
    if query:
        # Buscar en productos_sucursal con estado activo
        productos_sucursal_list = producto_sucursal.objects.filter(
            id_producto_fk__nombre_producto__icontains=query,
            estatus_producto_sucursal='Activo'  # Ahora el estatus está en producto_sucursal
        ).select_related('id_producto_fk', 'id_sucursal_fk')
        
        # Buscar en servicios_sucursal con estado activo
        servicios_sucursal_list = servicio_sucursal.objects.filter(
            id_servicio_fk__nombre_servicio__icontains=query,
            estatus_servicio_sucursal='Activo'  # Ahora el estatus está en servicio_sucursal
        ).select_related('id_servicio_fk', 'id_sucursal_fk')
        
        # Formatear resultados de productos
        for ps in productos_sucursal_list:
            # Obtener la primera imagen del producto desde la nueva tabla
            primera_imagen = imagen_producto.objects.filter(id_producto_fk=ps.id_producto_fk).first()
            imagen_url = primera_imagen.ruta_imagen.url if primera_imagen and primera_imagen.ruta_imagen else None
            
            resultados_productos.append({
                'id': ps.id_producto_sucursal,
                'nombre': ps.id_producto_fk.nombre_producto,
                'descripcion': ps.id_producto_fk.descripcion_producto,
                'precio': ps.precio_producto_sucursal,
                'stock': ps.stock_producto_sucursal,
                'condicion': ps.condicion_producto_sucursal,
                'imagen': imagen_url,
                'sucursal': ps.id_sucursal_fk.nombre_sucursal,
                'tipo': 'producto'
            })
        
        # Formatear resultados de servicios
        for ss in servicios_sucursal_list:
            # Obtener la primera imagen del servicio desde la nueva tabla
            primera_imagen = imagen_servicio.objects.filter(id_servicio_fk=ss.id_servicio_fk).first()
            imagen_url = primera_imagen.ruta_imagen.url if primera_imagen and primera_imagen.ruta_imagen else None
            
            resultados_servicios.append({
                'id': ss.id_servicio_sucursal,
                'nombre': ss.id_servicio_fk.nombre_servicio,
                'descripcion': ss.id_servicio_fk.descripcion_servicio,
                'precio': ss.precio_servicio_sucursal if ss.precio_servicio_sucursal else 'Consultar',
                'imagen': imagen_url,
                'sucursal': ss.id_sucursal_fk.nombre_sucursal,
                'tipo': 'servicio'
            })
    
    # Combinar resultados
    resultados_combinados = resultados_productos + resultados_servicios
    
    return render(request, 'ecommerce_app/busquedad.html', {
        'query': query,
        'resultados': resultados_combinados,
        'total_resultados': len(resultados_combinados)
    })


# API para obtener todas las imágenes de un producto
@require_GET
def api_obtener_imagenes_producto(request):
    try:
        id_producto = request.GET.get('id_producto')
        if not id_producto:
            return JsonResponse({'success': False, 'message': 'ID de producto requerido'})
        
        imagenes = imagen_producto.objects.filter(id_producto_fk=id_producto)
        imagenes_list = []
        for img in imagenes:
            imagenes_list.append({
                'id_imagen': img.id_imagen,
                'url': img.ruta_imagen.url if img.ruta_imagen else '',
                'fecha_creacion': img.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True, 
            'imagenes': imagenes_list,
            'total': len(imagenes_list)
        })
    except Exception as e:
        logger.error(f"Error al obtener imágenes del producto: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


# API para obtener todas las imágenes de un servicio
@require_GET
def api_obtener_imagenes_servicio(request):
    try:
        id_servicio = request.GET.get('id_servicio')
        if not id_servicio:
            return JsonResponse({'success': False, 'message': 'ID de servicio requerido'})
        
        imagenes = imagen_servicio.objects.filter(id_servicio_fk=id_servicio)
        imagenes_list = []
        for img in imagenes:
            imagenes_list.append({
                'id_imagen': img.id_imagen,
                'url': img.ruta_imagen.url if img.ruta_imagen else '',
                'fecha_creacion': img.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True, 
            'imagenes': imagenes_list,
            'total': len(imagenes_list)
        })
    except Exception as e:
        logger.error(f"Error al obtener imágenes del servicio: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


# API para eliminar una imagen específica de producto
@require_POST
def api_eliminar_imagen_producto(request):
    try:
        id_imagen = request.POST.get('id_imagen')
        if not id_imagen:
            return JsonResponse({'success': False, 'message': 'ID de imagen requerido'})
        
        imagen_obj = imagen_producto.objects.get(id_imagen=id_imagen)
        
        # Verificar que el producto tenga al menos 2 imágenes antes de eliminar
        total_imagenes = imagen_producto.objects.filter(id_producto_fk=imagen_obj.id_producto_fk).count()
        if total_imagenes <= 1:
            return JsonResponse({
                'success': False, 
                'message': 'No se puede eliminar la imagen. El producto debe tener al menos una imagen.'
            })
        
        # Eliminar el archivo físico si existe
        if imagen_obj.ruta_imagen:
            try:
                imagen_obj.ruta_imagen.delete(save=False)
            except:
                pass  # Si no se puede eliminar el archivo, continuar
        
        imagen_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Imagen eliminada correctamente'
        })
        
    except imagen_producto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Imagen no encontrada'})
    except Exception as e:
        logger.error(f"Error al eliminar imagen del producto: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


# API para eliminar una imagen específica de servicio
@require_POST
def api_eliminar_imagen_servicio(request):
    try:
        id_imagen = request.POST.get('id_imagen')
        if not id_imagen:
            return JsonResponse({'success': False, 'message': 'ID de imagen requerido'})
        
        imagen_obj = imagen_servicio.objects.get(id_imagen=id_imagen)
        
        # Verificar que el servicio tenga al menos 2 imágenes antes de eliminar
        total_imagenes = imagen_servicio.objects.filter(id_servicio_fk=imagen_obj.id_servicio_fk).count()
        if total_imagenes <= 1:
            return JsonResponse({
                'success': False, 
                'message': 'No se puede eliminar la imagen. El servicio debe tener al menos una imagen.'
            })
        
        # Eliminar el archivo físico si existe
        if imagen_obj.ruta_imagen:
            try:
                imagen_obj.ruta_imagen.delete(save=False)
            except:
                pass  # Si no se puede eliminar el archivo, continuar
        
        imagen_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Imagen eliminada correctamente'
        })
        
    except imagen_servicio.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Imagen no encontrada'})
    except Exception as e:
        logger.error(f"Error al eliminar imagen del servicio: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})





def localizacion(request):
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calcular la distancia entre dos puntos en la Tierra usando la fórmula de Haversine
        """
        # Convertir grados decimales a radianes
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Fórmula de Haversine
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radio de la Tierra en kilómetros
        return c * r
    
    query = request.GET.get('query', '')
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    
    resultados_cercanos = []
    
    if query:
        # Buscar productos y servicios como en la vista de búsqueda
        productos_sucursal_list = producto_sucursal.objects.filter(
            id_producto_fk__nombre_producto__icontains=query,
            estatus_producto_sucursal='Activo'
        ).select_related('id_producto_fk', 'id_sucursal_fk')
        
        servicios_sucursal_list = servicio_sucursal.objects.filter(
            id_servicio_fk__nombre_servicio__icontains=query,
            estatus_servicio_sucursal='Activo'
        ).select_related('id_servicio_fk', 'id_sucursal_fk')
        
        # Combinar resultados con información de ubicación
        todos_resultados = []
        
        # Procesar productos
        for ps in productos_sucursal_list:
            if ps.id_sucursal_fk.latitud_sucursal and ps.id_sucursal_fk.longitud_sucursal:
                primera_imagen = imagen_producto.objects.filter(id_producto_fk=ps.id_producto_fk).first()
                imagen_url = primera_imagen.ruta_imagen.url if primera_imagen and primera_imagen.ruta_imagen else None
                
                resultado = {
                    'id': ps.id_producto_sucursal,
                    'nombre': ps.id_producto_fk.nombre_producto,
                    'descripcion': ps.id_producto_fk.descripcion_producto,
                    'precio': ps.precio_producto_sucursal,
                    'imagen': imagen_url,
                    'sucursal': ps.id_sucursal_fk.nombre_sucursal,
                    'direccion': ps.id_sucursal_fk.direccion_sucursal,
                    'lat': float(ps.id_sucursal_fk.latitud_sucursal),
                    'lng': float(ps.id_sucursal_fk.longitud_sucursal),
                    'tipo': 'producto',
                    'distancia': 0
                }
                
                # Calcular distancia si se proporcionan coordenadas del usuario
                if user_lat and user_lng:
                    try:
                        user_lat_float = float(user_lat)
                        user_lng_float = float(user_lng)
                        resultado['distancia'] = haversine(
                            user_lng_float, user_lat_float,
                            resultado['lng'], resultado['lat']
                        )
                    except (ValueError, TypeError):
                        resultado['distancia'] = float('inf')
                
                todos_resultados.append(resultado)
        
        # Procesar servicios
        for ss in servicios_sucursal_list:
            if ss.id_sucursal_fk.latitud_sucursal and ss.id_sucursal_fk.longitud_sucursal:
                primera_imagen = imagen_servicio.objects.filter(id_servicio_fk=ss.id_servicio_fk).first()
                imagen_url = primera_imagen.ruta_imagen.url if primera_imagen and primera_imagen.ruta_imagen else None
                
                resultado = {
                    'id': ss.id_servicio_sucursal,
                    'nombre': ss.id_servicio_fk.nombre_servicio,
                    'descripcion': ss.id_servicio_fk.descripcion_servicio,
                    'precio': ss.precio_servicio_sucursal if ss.precio_servicio_sucursal else 'Consultar',
                    'imagen': imagen_url,
                    'sucursal': ss.id_sucursal_fk.nombre_sucursal,
                    'direccion': ss.id_sucursal_fk.direccion_sucursal,
                    'lat': float(ss.id_sucursal_fk.latitud_sucursal),
                    'lng': float(ss.id_sucursal_fk.longitud_sucursal),
                    'tipo': 'servicio',
                    'distancia': 0
                }
                
                # Calcular distancia si se proporcionan coordenadas del usuario
                if user_lat and user_lng:
                    try:
                        user_lat_float = float(user_lat)
                        user_lng_float = float(user_lng)
                        resultado['distancia'] = haversine(
                            user_lng_float, user_lat_float,
                            resultado['lng'], resultado['lat']
                        )
                    except (ValueError, TypeError):
                        resultado['distancia'] = float('inf')
                
                todos_resultados.append(resultado)
        
        # Filtrar resultados dentro de 4km y ordenar por distancia
        if user_lat and user_lng:
            # Filtrar solo resultados dentro de 4km
            todos_resultados = [r for r in todos_resultados if r['distancia'] <= 4.0]
            todos_resultados.sort(key=lambda x: x['distancia'])
        
        resultados_cercanos = todos_resultados[:10]  # Aumentar a 10 resultados máximo
    
    # Preparar datos para JavaScript (formato JSON)
    import json
    resultados_json = []
    for resultado in resultados_cercanos:
        resultado_data = {
            'nombre': resultado['nombre'],
            'descripcion': resultado.get('descripcion', ''),
            'direccion': resultado.get('direccion', ''),
            'precio': str(resultado.get('precio', '')),
            'lat': resultado.get('lat'),
            'lng': resultado.get('lng'),
            'distancia': resultado['distancia']
        }
        resultados_json.append(resultado_data)
    
    return render(request, 'ecommerce_app/localizacion.html', {
        'query': query,
        'resultados': resultados_cercanos,
        'resultados_json': json.dumps(resultados_json),
        'user_lat': user_lat,
        'user_lng': user_lng
    })