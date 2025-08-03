from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
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
    
    return render(request, 'ecommerce_app/iniciar_sesion.html')

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
    if request.method == 'POST':
        email = request.POST.get('login_email')
        password = request.POST.get('login_password')
        
        logger.info(f"Intento de login AJAX para el email: {email}")
        
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
                                return JsonResponse({
                                    'success': False, 
                                    'message': f'Ya tienes una empresa registrada: {empresa_existente.nombre_empresa}. No puedes registrar otra empresa.'
                                })
                        except Exception as e:
                            logger.error(f"Error al verificar empresa existente: {str(e)}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'user_name': user.nombre_usuario,
                            'user_type': user.tipo_usuario
                        })
                    else:
                        return JsonResponse({
                            'success': False, 
                            'message': 'Contraseña incorrecta'
                        })
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
                                return JsonResponse({
                                    'success': False, 
                                    'message': f'Ya tienes una empresa registrada: {empresa_existente.nombre_empresa}. No puedes registrar otra empresa.'
                                })
                        except Exception as e:
                            logger.error(f"Error al verificar empresa existente: {str(e)}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'user_name': user.nombre_usuario,
                            'user_type': user.tipo_usuario
                        })
                    else:
                        return JsonResponse({
                            'success': False, 
                            'message': 'Contraseña incorrecta'
                        })
            except usuario.DoesNotExist:
                logger.warning(f"Usuario no encontrado: {email}")
                return JsonResponse({
                    'success': False, 
                    'message': 'Usuario no encontrado'
                })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Por favor completa todos los campos'
            })
    
    return JsonResponse({
        'success': False, 
        'message': 'Método no permitido'
    })

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

    return render(request, 'ecommerce_app/registrar_persona.html')

def registrar_empresa(request):
    # Esta función debe ser accesible sin autenticación para el registro inicial
    # Solo se requiere autenticación para el POST (cuando se envía el formulario)
    current_user = get_current_user(request)
    
    if request.method == 'POST':
        # Verificar autenticación solo para el POST
        if not current_user:
            return JsonResponse({
                'success': False,
                'message': 'Debe iniciar sesión para registrar una empresa'
            })
            
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
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son obligatorios. Por favor complete todos los campos.'
                })
            
            # Validar que las coordenadas sean números válidos
            try:
                lat = float(latitud)
                lng = float(longitud)
            except ValueError:
                logger.warning("Coordenadas inválidas")
                return JsonResponse({
                    'success': False,
                    'message': 'Las coordenadas deben ser números válidos.'
                })
            
            # Validar longitud mínima de descripción
            if len(descripcion_empresa) < 10:
                logger.warning("Descripción demasiado corta")
                return JsonResponse({
                    'success': False,
                    'message': 'La descripción debe tener al menos 10 caracteres.'
                })
            
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
            
            return JsonResponse({
                'success': True,
                'message': 'Empresa registrada exitosamente',
                'redirect_url': '/ecommerce/sucursal'
            })
        except Exception as e:
            logger.error(f"Error al guardar la empresa: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    # Si es GET, mostrar el formulario
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
    
    return render(request, 'ecommerce_app/registrar_empresa.html', {'user_info': user_info})



@require_login
def sucursalfuncion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    # Obtener la empresa del usuario actual
    try:
        empresa_obj = empresa.objects.get(id_usuario_fk=current_user)
        # Obtener todas las sucursales de la empresa del usuario
        sqlsucursal = sucursal.objects.filter(id_empresa_fk=empresa_obj)
    except empresa.DoesNotExist:
        # Si el usuario no tiene empresa, redirigir a registrar empresa
        return redirect('/ecommerce/registrar_empresa')
   
    if request.method == 'POST':
        try:
            nombre_sucursal = request.POST.get('nombre_sucursal')
            telefono_sucursal = request.POST.get('telefono_sucursal')
            estado_sucursal = request.POST.get('estado_sucursal')
            direccion_sucursal = request.POST.get('direccion_sucursal')
            latitud_sucursal = request.POST.get('latitud_sucursal')
            longitud_sucursal = request.POST.get('longitud_sucursal')

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

    return render(request, 'ecommerce_app/sucursal.html', {
        'sqlsucursal': sqlsucursal
    })


def editar_sucursal(request):
    if request.method == 'POST':
        try:
            id_sucursal = request.POST.get('id_sucursal')
            sucursal_obj = sucursal.objects.get(id_sucursal=id_sucursal)
            
            # Actualizar los datos
            sucursal_obj.nombre_sucursal = request.POST.get('nombre_sucursal')
            sucursal_obj.telefono_sucursal = request.POST.get('telefono_sucursal')
            sucursal_obj.estado_sucursal = request.POST.get('estado_sucursal')
            sucursal_obj.direccion_sucursal = request.POST.get('direccion_sucursal')
            sucursal_obj.latitud_sucursal = float(request.POST.get('latitud_sucursal'))
            sucursal_obj.longitud_sucursal = float(request.POST.get('longitud_sucursal'))
            
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



def eliminar_sucursal(request):
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
        return redirect('/ecommerce/registrar_empresa')

    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            nombre_producto = request.POST.get('nombre_producto')
            descripcion_producto = request.POST.get('descripcion_producto')
            marca_producto = request.POST.get('marca_producto')
            modelo_producto = request.POST.get('modelo_producto')
            imagen_producto = request.FILES.get('imagen_producto')
            caracteristicas_generales = request.POST.get('caracteristicas_generales')
            estatus_producto = request.POST.get('estatus_producto')
            categoria_id = request.POST.get('categoria_producto')
            categoria_producto_consul = categoria_producto.objects.get(id_categoria_prod=categoria_id)

            nuevo_producto = producto(
                nombre_producto=nombre_producto,
                descripcion_producto=descripcion_producto,
                marca_producto=marca_producto,
                modelo_producto=modelo_producto,
                imagen_producto=imagen_producto,    
                caracteristicas_generales=caracteristicas_generales,
                estatus_producto=estatus_producto,
                id_empresa_fk=empresa_obj,
                id_categoria_prod_fk=categoria_producto_consul
            )
            nuevo_producto.save()
            logger.info(f"Producto guardado exitosamente: {nuevo_producto.nombre_producto}")
            
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
    
    return render(request, 'ecommerce_app/producto.html', {'categoria_producto_all': categoria_producto_all})

@require_login
def servicio_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    # Obtener la empresa del usuario actual
    try:
        empresa_obj = empresa.objects.get(id_usuario_fk=current_user)
        categoria_servicio_all = categoria_servicio.objects.all()
    except empresa.DoesNotExist:
        # Si el usuario no tiene empresa, redirigir a registrar empresa
        return redirect('/ecommerce/registrar_empresa')
    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            nombre_servicio = request.POST.get('nombre_servicio')
            descripcion_servicio = request.POST.get('descripcion_servicio')
            estatus_servicio = request.POST.get('estatus_servicio')
            categoria_id = request.POST.get('categoria_servicio')
            categoria_servicio_consul = categoria_servicio.objects.get(id_categoria_serv=categoria_id)
            imagen_servicio = request.FILES.get('imagen_servicio')

            nuevo_servicio = servicio(
                nombre_servicio=nombre_servicio,
                descripcion_servicio=descripcion_servicio,
                estatus_servicio=estatus_servicio,
                imagen_servicio=imagen_servicio,
                id_empresa_fk=empresa_obj,
                id_categoria_servicios_fk=categoria_servicio_consul
            )
            nuevo_servicio.save()   
            logger.info(f"Servicio guardado exitosamente: {nuevo_servicio.nombre_servicio}")
            
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

    return render(request, 'ecommerce_app/servicio.html', {'categoria_servicio_all': categoria_servicio_all})



def eliminar_todas_sucursales(request):
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






def categoria_producto_funcion(request):
    if request.method == 'POST':
        try:
            nombre_categoria = request.POST.get('nombre_categoria')
            descripcion_categoria = request.POST.get('descripcion_categoria')
            estatus_categoria = request.POST.get('estatus_categoria')
            fecha_creacion = request.POST.get('fecha_creacion')

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

    return render(request, 'ecommerce_app/categoria_producto.html')

def categoria_servicio_funcion(request):
    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            nombre_categoria = request.POST.get('nombre_categoria')
            descripcion_categoria = request.POST.get('descripcion_categoria')
            estatus_categoria = request.POST.get('estatus_categoria')
            fecha_creacion = request.POST.get('fecha_creacion')     
            
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

    return render(request, 'ecommerce_app/categoria_servicio.html')






def categ_producto_config_funcion(request):
    categ_producto_all= categoria_producto.objects.all().order_by('-fecha_creacion_prod')
    
    # Logging básico
    logger.info(f"Total de categorías encontradas: {categ_producto_all.count()}")

    return render(request, 'ecommerce_app/categ_producto_config.html', {'categoria_producto':categ_producto_all})





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
                return redirect('/ecommerce/categ_servicio_config/?error=true')
                
            categoria_obj = categoria_servicio.objects.get(id_categoria_serv=id_categoria_servicio)
            nombre_categoria_servicio = categoria_obj.nombre_categoria_serv
            
            # Verificar si hay productos asociados
            servicios_asociados = servicio.objects.filter(id_categoria_servicios_fk_id=categoria_obj).exists()
            if servicios_asociados:
                logger.error(f"No se puede eliminar la categoría {nombre_categoria_servicio} porque tiene productos asociados")
                return redirect('/ecommerce/categ_servicio_config/?error=true')
            
            categoria_obj.delete()
            logger.info(f"Categoría eliminada exitosamente: {nombre_categoria_servicio}")
            return redirect('/ecommerce/categ_servicio_config/?deleted=true')
            
        except categoria_servicio.DoesNotExist:
            logger.error(f"Error al eliminar la categoría: Categoría no encontrada con ID {id_categoria_servicio}")
            return redirect('/ecommerce/categ_servicio_config/?error=true')
        except Exception as e:
            logger.error(f"Error al eliminar la categoría: {str(e)}")
            return redirect('/ecommerce/categ_servicio_config/?error=true')
    
    return redirect('/ecommerce/categ_servicio_config/')

def producto_config_funcion(request):
    producto_sucursal_all= producto.objects.all()
    categoria_producto_all= categoria_producto.objects.all()

    
    return render(request, 'ecommerce_app/producto_config.html', {
        'producto_sucursal_all': producto_sucursal_all,
        'categoria_producto_all': categoria_producto_all
    })



def servicio_config_funcion(request):
    servicio_all= servicio.objects.all()

    
    return render(request, 'ecommerce_app/servicio_config.html', {'servicio_all':servicio_all})



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
            producto_obj.estatus_producto = request.POST.get('estatus_producto')
            
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
            
            # Actualizar imagen si se proporciona
            imagen_producto = request.FILES.get('imagen_producto')
            if imagen_producto:
                producto_obj.imagen_producto = imagen_producto
            
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
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.tipo_usuario,
                'is_authenticated': True
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