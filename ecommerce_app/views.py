import json
import os
import logging
from django.db.models import Q, F
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import producto_empresa, servicio_empresa, producto_sucursal, servicio_sucursal, sucursal, imagen_producto_empresa, imagen_servicio_empresa, categoria_servicio_usuario, categoria_servicio_empresa, imagen_producto_usuario, producto_usuario, categoria_producto_usuario, categoria_producto_empresa

# Función auxiliar para generar user_info con avatar_chatbot
def get_user_info_with_avatar(current_user, account_type, empresa_nombre=None):
    """Genera el diccionario user_info con el campo avatar_chatbot incluido"""
    if account_type == 'empresa':
            # Las empresas almacenan el avatar en el campo `avatar_chatbot_empresa` y en `avatar_chatbot`.
        avatar = None
        try:
            avatar = getattr(current_user, 'avatar_chatbot_empresa', None) or getattr(current_user, 'avatar_chatbot', None)
        except Exception:
            avatar = None
        if not avatar:
            avatar = 'avatars/Cartoon Style Robot.jpg'
        return {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True,
            'avatar_chatbot': avatar
        }
    else:
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True,
            'avatar_chatbot': getattr(current_user, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
        }
        if empresa_nombre:
            user_info['empresa_nombre'] = empresa_nombre
        return user_info

# API para obtener productos y servicios NO asociados a una sucursal
@require_GET
def api_productos_servicios_disponibles(request):
    try:
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Solo las empresas pueden acceder a esta función
        if account_type != 'empresa':
            return JsonResponse({'success': False, 'message': 'Acceso no autorizado'})
        
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
            
            # Filtrar productos solo de la empresa actual
            if productos_asociados_list:
                productos_disponibles = producto_empresa.objects.filter(id_empresa_fk=current_user).exclude(id_producto_empresa__in=productos_asociados_list)
            else:
                productos_disponibles = producto_empresa.objects.filter(id_empresa_fk=current_user)
                
            productos_list = [
                {'id': p.id_producto_empresa, 'nombre': p.nombre_producto_empresa}
                for p in productos_disponibles
            ]
        
        # Si se solicitan servicios o todos
        if tipo == 'servicios' or tipo == 'todos':
            servicios_asociados_qs = servicio_sucursal.objects.filter(id_sucursal_fk=id_sucursal).values_list('id_servicio_fk', flat=True)
            servicios_asociados_list = list(servicios_asociados_qs)
            
            # Filtrar servicios solo de la empresa actual
            if servicios_asociados_list:
                servicios_disponibles = servicio_empresa.objects.filter(id_empresa_fk=current_user).exclude(id_servicio_empresa__in=servicios_asociados_list)
            else:
                servicios_disponibles = servicio_empresa.objects.filter(id_empresa_fk=current_user)
                
            servicios_list = [
                {'id': s.id_servicio_empresa, 'nombre': s.nombre_servicio_empresa}
                for s in servicios_disponibles
            ]

        return JsonResponse({'success': True, 'productos': productos_list, 'servicios': servicios_list})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_GET
def api_sucursales_disponibles(request):
    """Devuelve las sucursales de la empresa actual en formato JSON para poblar checkboxes/selects."""
    try:
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})

        account_type = request.session.get('account_type', 'usuario')
        if account_type != 'empresa':
            return JsonResponse({'success': False, 'message': 'Acceso no autorizado'})

        empresa_obj = current_user
        # Si se pasa producto_id o servicio_id, excluir sucursales donde ya existe la asociación
        producto_id = request.GET.get('producto_id')
        servicio_id = request.GET.get('servicio_id')

        sucursales_qs = sucursal.objects.filter(id_empresa_fk=empresa_obj)
        if producto_id:
            try:
                # obtener IDs de sucursales que ya tienen este producto
                assigned_ids = producto_sucursal.objects.filter(id_producto_fk__id_producto_empresa=producto_id).values_list('id_sucursal_fk__id_sucursal', flat=True)
                sucursales_qs = sucursales_qs.exclude(id_sucursal__in=list(assigned_ids))
            except Exception:
                # si ocurre algún error al filtrar por producto, devolvemos todas las sucursales
                pass
        elif servicio_id:
            try:
                assigned_ids = servicio_sucursal.objects.filter(id_servicio_fk__id_servicio_empresa=servicio_id).values_list('id_sucursal_fk__id_sucursal', flat=True)
                sucursales_qs = sucursales_qs.exclude(id_sucursal__in=list(assigned_ids))
            except Exception:
                pass

        sucursales = [{'id': s.id_sucursal, 'nombre': s.nombre_sucursal} for s in sucursales_qs]
        return JsonResponse({'success': True, 'sucursales': sucursales})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# API para guardar producto o servicio en una sucursal
@require_POST
def guardar_producto_servicio_sucursal(request):
    try:
        # Obtener datos del formulario
        sucursal_id = request.POST.get('sucursal_id')
        producto_id = request.POST.get('producto_id')
        servicio_id = request.POST.get('servicio_id')
        stock = request.POST.get('stock', 0)
        precio_raw = request.POST.get('precio', '')
        # Convertir precio a decimal, usar 0 si está vacío o no es válido
        try:
            precio = float(precio_raw) if precio_raw and precio_raw.strip() else 0
        except (ValueError, TypeError):
            precio = 0
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
                producto_obj = producto_empresa.objects.get(id_producto_empresa=producto_id)
                
                # Verificar si ya existe este producto en esta sucursal
                if producto_sucursal.objects.filter(id_sucursal_fk=sucursal_obj, id_producto_fk=producto_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Este producto ya está asociado a esta sucursal'})
                
                # Leer nuevos campos de presentación
                unidad_presentacion = request.POST.get('unidad_presentacion_producto_sucursal', 'unidad')
                cantidad_por_presentacion = request.POST.get('cantidad_por_presentacion_producto_sucursal', None)
                try:
                    cantidad_por_presentacion = int(cantidad_por_presentacion) if cantidad_por_presentacion else None
                    if cantidad_por_presentacion is not None and cantidad_por_presentacion <= 0:
                        cantidad_por_presentacion = None
                except (ValueError, TypeError):
                    cantidad_por_presentacion = None

                # Crear la relación producto-sucursal con el estatus, condición y presentación seleccionados
                producto_sucursal.objects.create(
                    stock_producto_sucursal=stock,
                    precio_producto_sucursal=precio,
                    estatus_producto_sucursal=estatus_producto_sucursal,
                    condicion_producto_sucursal=condicion_producto_sucursal,
                    unidad_presentacion_producto_sucursal=unidad_presentacion,
                    cantidad_por_presentacion_producto_sucursal=cantidad_por_presentacion,
                    id_sucursal_fk=sucursal_obj,
                    id_producto_fk=producto_obj
                )
                
                return JsonResponse({'success': True, 'message': 'Producto agregado a la sucursal correctamente'})
            except producto_empresa.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'El producto no existe'})
        
        # Guardar servicio en sucursal
        if servicio_id:
            try:
                servicio_obj = servicio_empresa.objects.get(id_servicio_empresa=servicio_id)
                
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
            except servicio_empresa.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'El servicio no existe'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Vista para cambiar el logo de la empresa

@require_POST
def cambiar_logo_empresa(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, current_user ya es la empresa
        empresa_obj = current_user
    else:
        # Para usuarios, buscar empresa asociada
        try:
            empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
            if not empresa_obj:
                return redirect('/ecommerce/registrar_empresa/')
        except Exception:
            return redirect('/ecommerce/registrar_empresa/')
    
    logo = request.FILES.get('logo')
    if not logo:
        return redirect('/ecommerce/perfil_empresa/')
    empresa_obj.logo_empresa = logo
    empresa_obj.save()
    return redirect('/ecommerce/perfil_empresa/')

# Vista para cambiar la foto del usuario
@require_POST
def cambiar_foto_usuario(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'usuario':
        # Para usuarios, current_user ya es el usuario
        usuario_obj = current_user
    else:
        # Si es empresa, redirigir al perfil de empresa
        return redirect('/ecommerce/perfil_empresa/')
    
    foto = request.FILES.get('foto')
    if not foto:
        return redirect('/ecommerce/perfil_usuario/')
    usuario_obj.foto_usuario = foto
    usuario_obj.save()
    return redirect('/ecommerce/perfil_usuario/')


def recuperar_clave(request):
    """Renderiza la página para solicitar recuperación (ingresar email)."""
    return render(request, 'ecommerce_app/recuperar_clave.html')


# ----- Password reset (request and confirm) -----
@require_POST
def request_password_reset(request):
    """Recibe JSON {email} y, si existe usuario o empresa con ese email, envía un correo con token firmado.
    Responde siempre {success: True} para no filtrar existencia de cuentas.
    """
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        data = {}
        
    email = data.get('email') or request.POST.get('email')
    if not email:
        return JsonResponse({'success': False, 'message': 'Email requerido'})

    # Buscar usuario o empresa
    user_obj = None
    user_type = None
    try:
        from .models import usuario, empresa
        user_obj = usuario.objects.filter(correo_usuario__iexact=email).first()
        if user_obj:
            user_type = 'usuario'
        else:
            user_obj = empresa.objects.filter(correo_empresa__iexact=email).first()
            if user_obj:
                user_type = 'empresa'
    except Exception:
        user_obj = None

    # Generar token firmado con payload minimal: {type, id}
    token = None
    if user_obj and user_type:
        payload = {'type': user_type, 'id': getattr(user_obj, 'id_usuario', None) or getattr(user_obj, 'id_empresa', None)}
        token = signing.dumps(payload, salt='password-reset')

        # Preparar link
        base_url = getattr(settings, 'SITE_BASE_URL', '') or request.build_absolute_uri('/')[:-1]
        reset_link = f"{base_url}/ecommerce/confirmar_recuperacion/?token={token}"

        # Render email
        subject = 'Recuperación de contraseña'
        html_message = render_to_string('ecommerce_app/emails/password_reset.html', {'reset_link': reset_link, 'user': user_obj})
        plain_message = strip_tags(html_message)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')
        recipient_list = [email]

        try:
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message, fail_silently=False)
        except Exception as e:
            # Log error but do not expose to client
            try:
                import logging
                logging.exception('Error sending password reset email: %s', e)
            except Exception:
                pass

    # Responder siempre genérico
    return JsonResponse({'success': True, 'message': 'Si existe una cuenta asociada se ha enviado un correo con instrucciones.'})


logger = logging.getLogger(__name__)

@require_http_methods(['GET', 'POST'])
@csrf_exempt  # Añadir exemption para manejar CSRF manualmente
def confirmar_recuperacion(request):
    """Página que muestra el formulario para introducir nueva contraseña.
    Si GET y token presente -> mostrar formulario. Si POST -> validar token y cambiar contraseña.
    """
    if request.method == 'GET':
        token = request.GET.get('token')
        return render(request, 'ecommerce_app/confirmar_recuperacion.html', {'token': token})

    # POST
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        data = {}
    
    token = data.get('token') or request.POST.get('token')
    new_password = data.get('password') or request.POST.get('password')
    
    # Validación de entrada
    if not token:
        logger.warning("Intento de recuperación sin token")
        return JsonResponse({'success': False, 'message': 'Token requerido'})
    
    if not new_password:
        logger.warning("Intento de recuperación sin contraseña")
        return JsonResponse({'success': False, 'message': 'Nueva contraseña requerida'})
    
    if len(new_password) < 6:
        return JsonResponse({'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'})

    # Validar token
    try:
        payload = signing.loads(token, salt='password-reset', max_age=60 * 60 * 2)  # 2 horas
        logger.info(f"Token válido para payload: {payload}")
    except signing.BadSignature as e:
        logger.warning(f"Token inválido o expirado: {e}")
        return JsonResponse({'success': False, 'message': 'Token inválido o expirado'})

    user_type = payload.get('type')
    user_id = payload.get('id')
    
    if not user_type or not user_id:
        logger.error(f"Payload incompleto: type={user_type}, id={user_id}")
        return JsonResponse({'success': False, 'message': 'Token corrupto'})

    try:
        from .models import usuario, empresa
        from django.contrib.auth.hashers import make_password
        
        hashed = make_password(new_password)
        logger.info(f"Contraseña hasheada generada para {user_type} ID {user_id}")
        
        if user_type == 'usuario':
            try:
                user_obj = usuario.objects.get(id_usuario=user_id)
                logger.info(f"Usuario encontrado: {user_obj.nombre_usuario} ({user_obj.correo_usuario})")
                user_obj.password_usuario = hashed
                user_obj.save()
                logger.info(f"Contraseña actualizada para usuario {user_obj.nombre_usuario}")
            except usuario.DoesNotExist:
                logger.error(f"Usuario con ID {user_id} no encontrado")
                return JsonResponse({'success': False, 'message': 'Usuario no encontrado'})
                
        elif user_type == 'empresa':
            try:
                user_obj = empresa.objects.get(id_empresa=user_id)
                logger.info(f"Empresa encontrada: {user_obj.nombre_empresa} ({user_obj.correo_empresa})")
                user_obj.password_empresa = hashed
                user_obj.save()
                logger.info(f"Contraseña actualizada para empresa {user_obj.nombre_empresa}")
            except empresa.DoesNotExist:
                logger.error(f"Empresa con ID {user_id} no encontrada")
                return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
        else:
            logger.error(f"Tipo de usuario inválido: {user_type}")
            return JsonResponse({'success': False, 'message': 'Tipo de usuario inválido'})
            
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar contraseña: {e}")
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'})

    logger.info(f"Contraseña actualizada exitosamente para {user_type} ID {user_id}")
    return JsonResponse({'success': True, 'message': 'Contraseña actualizada correctamente'})

# Vista para eliminar servicio
@csrf_exempt
def eliminar_servicio(request):
    if request.method == 'POST':
        try:
            # Buscar ID de servicio según el tipo de usuario
            id_servicio_empresa = request.POST.get('id_servicio_empresa')
            id_servicio_usuario = request.POST.get('id_servicio_usuario')
            id_servicio = request.POST.get('id_servicio')
            
            logger.info(f"Intentando eliminar servicio - Empresa: {id_servicio_empresa}, Usuario: {id_servicio_usuario}, Genérico: {id_servicio}")
            
            # Determinar qué tipo de servicio eliminar
            if id_servicio_empresa or (id_servicio and not id_servicio_usuario):
                # Es un servicio de empresa
                servicio_id = id_servicio_empresa or id_servicio
                try:
                    servicio_obj = servicio_empresa.objects.get(id_servicio_empresa=servicio_id)
                    nombre_servicio = servicio_obj.nombre_servicio_empresa
                    servicio_obj.delete()
                    logger.info(f"Servicio de empresa eliminado exitosamente: {nombre_servicio}")
                    return JsonResponse({'success': True, 'message': f'Servicio "{nombre_servicio}" eliminado exitosamente'})
                except servicio_empresa.DoesNotExist:
                    logger.error(f"Servicio de empresa no encontrado con ID {servicio_id}")
                    return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})
            
            elif id_servicio_usuario:
                # Es un servicio de usuario
                try:
                    servicio_obj = servicio_usuario.objects.get(id_servicio_usuario=id_servicio_usuario)
                    nombre_servicio = servicio_obj.nombre_servicio_usuario
                    servicio_obj.delete()
                    logger.info(f"Servicio de usuario eliminado exitosamente: {nombre_servicio}")
                    return JsonResponse({'success': True, 'message': f'Servicio "{nombre_servicio}" eliminado exitosamente'})
                except servicio_usuario.DoesNotExist:
                    logger.error(f"Servicio de usuario no encontrado con ID {id_servicio_usuario}")
                    return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})
            
            else:
                logger.error("No se proporcionó ID de servicio válido")
                return JsonResponse({'success': False, 'message': 'ID de servicio no proporcionado'})
                
        except Exception as e:
            logger.error(f"Error al eliminar el servicio: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error al eliminar el servicio: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

# Vista para editar servicio
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def editar_servicio(request):
    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos para editar servicio: {request.POST}")
            
            # Buscar ID de servicio según el tipo de usuario
            id_servicio_empresa = request.POST.get('id_servicio_empresa')
            id_servicio_usuario = request.POST.get('id_servicio_usuario')
            id_servicio = request.POST.get('id_servicio')
            
            logger.info(f"IDs recibidos - empresa: {id_servicio_empresa}, usuario: {id_servicio_usuario}, genérico: {id_servicio}")
            
            # Determinar si es servicio de empresa o usuario
            if id_servicio_empresa or (id_servicio and not id_servicio_usuario):
                # Es un servicio de empresa
                servicio_id = id_servicio_empresa or id_servicio
                try:
                    servicio_obj = servicio_empresa.objects.get(id_servicio_empresa=servicio_id)
                    
                    # Actualizar los datos básicos
                    servicio_obj.nombre_servicio_empresa = request.POST.get('nombre_servicio_empresa') or request.POST.get('nombre_servicio', servicio_obj.nombre_servicio_empresa)
                    servicio_obj.descripcion_servicio_empresa = request.POST.get('descripcion_servicio_empresa') or request.POST.get('descripcion_servicio', servicio_obj.descripcion_servicio_empresa)
                    
                    # Actualizar categoría si se proporciona
                    id_categoria = request.POST.get('categoria_servicio')
                    if id_categoria:
                        try:
                            categoria_obj = categoria_servicio_empresa.objects.get(id_categoria_serv_empresa=id_categoria)
                            servicio_obj.id_categoria_servicios_fk = categoria_obj
                        except categoria_servicio_empresa.DoesNotExist:
                            pass
                    
                    # Manejar múltiples imágenes si se proporcionan
                    imagenes_servicio = request.FILES.getlist('imagenes_servicio')
                    if imagenes_servicio:
                        # Contar imágenes existentes
                        imagenes_existentes = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio_obj).count()
                        
                        # Validar número máximo de imágenes (existentes + nuevas)
                        if imagenes_existentes + len(imagenes_servicio) > 5:
                            return JsonResponse({
                                'success': False,
                                'message': f'Máximo 5 imágenes permitidas. Actualmente tienes {imagenes_existentes} imágenes. Puedes agregar máximo {5 - imagenes_existentes} más.'
                            })
                        
                        # Agregar nuevas imágenes sin eliminar las existentes
                        for imagen in imagenes_servicio:
                            imagen_servicio_empresa.objects.create(
                                id_servicio_fk=servicio_obj,
                                ruta_imagen_servicio_empresa=imagen
                            )
                    
                    servicio_obj.save()
                    logger.info(f"Servicio de empresa actualizado exitosamente: {servicio_obj.nombre_servicio_empresa}")
                    return JsonResponse({'success': True, 'message': 'Servicio actualizado exitosamente'})
                    
                except servicio_empresa.DoesNotExist:
                    logger.error(f"Servicio de empresa no encontrado con ID: {servicio_id}")
                    return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})
                    
            elif id_servicio_usuario:
                # Es un servicio de usuario
                try:
                    servicio_obj = servicio_usuario.objects.get(id_servicio_usuario=id_servicio_usuario)
                    
                    # Actualizar los datos básicos
                    servicio_obj.nombre_servicio_usuario = request.POST.get('nombre_servicio_usuario') or request.POST.get('nombre_servicio', servicio_obj.nombre_servicio_usuario)
                    servicio_obj.descripcion_servicio_usuario = request.POST.get('descripcion_servicio_usuario') or request.POST.get('descripcion_servicio', servicio_obj.descripcion_servicio_usuario)
                    
                    # Actualizar campos adicionales para usuarios
                    precio_servicio = request.POST.get('precio_servicio_usuario')
                    if precio_servicio is not None:
                        try:
                            servicio_obj.precio_servicio_usuario = float(precio_servicio)
                        except (ValueError, TypeError):
                            servicio_obj.precio_servicio_usuario = 0.0
                    
                    estatus_servicio = request.POST.get('estatus_servicio_usuario')
                    if estatus_servicio:
                        servicio_obj.estatus_servicio_usuario = estatus_servicio
                    
                    # Actualizar categoría si se proporciona
                    id_categoria = request.POST.get('categoria_servicio')
                    if id_categoria:
                        try:
                            categoria_obj = categoria_servicio_usuario.objects.get(id_categoria_serv_usuario=id_categoria)
                            servicio_obj.id_categoria_servicios_fk = categoria_obj
                        except categoria_servicio_usuario.DoesNotExist:
                            pass
                    
                    # Manejar múltiples imágenes si se proporcionan
                    imagenes_servicio = request.FILES.getlist('imagenes_servicio')
                    if imagenes_servicio:
                        # Contar imágenes existentes
                        imagenes_existentes = imagen_servicio_usuario.objects.filter(id_servicio_fk=servicio_obj).count()
                        
                        # Validar número máximo de imágenes (existentes + nuevas)
                        if imagenes_existentes + len(imagenes_servicio) > 5:
                            return JsonResponse({
                                'success': False,
                                'message': f'Máximo 5 imágenes permitidas. Actualmente tienes {imagenes_existentes} imágenes. Puedes agregar máximo {5 - imagenes_existentes} más.'
                            })
                        
                        # Agregar nuevas imágenes sin eliminar las existentes
                        for imagen in imagenes_servicio:
                            imagen_servicio_usuario.objects.create(
                                id_servicio_fk=servicio_obj,
                                ruta_imagen_servicio_usuario=imagen
                            )
                    
                    servicio_obj.save()
                    logger.info(f"Servicio de usuario actualizado exitosamente: {servicio_obj.nombre_servicio_usuario}")
                    return JsonResponse({'success': True, 'message': 'Servicio actualizado exitosamente'})
                    
                except servicio_usuario.DoesNotExist:
                    logger.error(f"Servicio de usuario no encontrado con ID: {id_servicio_usuario}")
                    return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})
            else:
                return JsonResponse({'success': False, 'message': 'ID de servicio no proporcionado'})
                
        except Exception as e:
            logger.error(f"Error al actualizar el servicio: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error al actualizar el servicio: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
from django.views.decorators.http import require_GET

# API para filtrar servicios por nombre (AJAX)
@require_GET
def api_filtrar_servicios(request):
    try:
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
        
        account_type = request.session.get('account_type', 'usuario')
        nombre = request.GET.get('nombre', '').strip().lower()
        estatus = request.GET.get('estatus', '').strip().lower()
        
        servicios_list = []
        
        if account_type == 'empresa':
            # Filtrar servicios de empresa
            servicios_query = servicio_empresa.objects.filter(id_empresa_fk=current_user)
            if nombre:
                servicios_query = servicios_query.filter(nombre_servicio_empresa__icontains=nombre)
            
            for idx, serv in enumerate(servicios_query, start=1):
                # Obtener la primera imagen del servicio desde la nueva tabla
                primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=serv).first()
                imagen_url = primera_imagen.ruta_imagen_servicio_empresa.url if primera_imagen and primera_imagen.ruta_imagen_servicio_empresa else ''
                
                # Obtener sucursales asignadas al servicio
                sucursales_asignadas = []
                servicios_sucursal = servicio_sucursal.objects.filter(id_servicio_fk=serv).select_related('id_sucursal_fk')
                for ss in servicios_sucursal:
                    sucursales_asignadas.append({
                        'id': ss.id_sucursal_fk.id_sucursal,
                        'nombre': ss.id_sucursal_fk.nombre_sucursal
                    })
                    
                servicios_list.append({
                    'id_servicio_empresa': serv.id_servicio_empresa,
                    'nombre_servicio_empresa': serv.nombre_servicio_empresa,
                    'descripcion_servicio_empresa': serv.descripcion_servicio_empresa or '',
                    'imagen_url': imagen_url,
                    'categoria_servicio': serv.id_categoria_servicios_fk.nombre_categoria_serv_empresa if serv.id_categoria_servicios_fk else '',
                    'categoria_servicio_id': serv.id_categoria_servicios_fk.id_categoria_serv_empresa if serv.id_categoria_servicios_fk else '',
                    'caracteristicas_generales_empresa': '',
                    'sucursales_asignadas': sucursales_asignadas,
                    'serial': idx
                })
        else:
            # Filtrar servicios de usuario
            servicios_query = servicio_usuario.objects.filter(id_usuario_fk=current_user)
            if nombre:
                servicios_query = servicios_query.filter(nombre_servicio_usuario__icontains=nombre)
            
            for idx, serv in enumerate(servicios_query, start=1):
                # Obtener la primera imagen del servicio desde la nueva tabla
                primera_imagen = imagen_servicio_usuario.objects.filter(id_servicio_fk=serv).first()
                imagen_url = primera_imagen.ruta_imagen_servicio_usuario.url if primera_imagen and primera_imagen.ruta_imagen_servicio_usuario else ''
                    
                servicios_list.append({
                    'id_servicio_usuario': serv.id_servicio_usuario,
                    'nombre_servicio_usuario': serv.nombre_servicio_usuario,
                    'descripcion_servicio_usuario': serv.descripcion_servicio_usuario or '',
                    'imagen_url': imagen_url,
                    'categoria_servicio': serv.id_categoria_servicios_fk.nombre_categoria_serv_usuario if serv.id_categoria_servicios_fk else '',
                    'categoria_servicio_id': serv.id_categoria_servicios_fk.id_categoria_serv_usuario if serv.id_categoria_servicios_fk else '',
                    'caracteristicas_generales_usuario': '',
                    'precio_servicio_usuario': serv.precio_servicio_usuario or 0,
                    'estatus_servicio_usuario': serv.estatus_servicio_usuario or 'Activo',
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
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
        
        account_type = request.session.get('account_type', 'usuario')
        nombre = request.GET.get('nombre', '').strip().lower()
        
        productos_list = []
        
        if account_type == 'empresa':
            # Filtrar productos de empresa
            productos_query = producto_empresa.objects.filter(id_empresa_fk=current_user)
            if nombre:
                productos_query = productos_query.filter(nombre_producto_empresa__icontains=nombre)
            
            for idx, prod in enumerate(productos_query, start=1):
                # Obtener la primera imagen del producto desde la nueva tabla
                primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
                imagen_url = primera_imagen.ruta_imagen_producto_empresa.url if primera_imagen and primera_imagen.ruta_imagen_producto_empresa else ''
                
                # Obtener sucursales donde está asignado este producto
                sucursales_asignadas = producto_sucursal.objects.filter(id_producto_fk=prod).select_related('id_sucursal_fk')
                sucursales_list = [{'nombre': ps.id_sucursal_fk.nombre_sucursal} for ps in sucursales_asignadas]
                
                productos_list.append({
                    'id_producto_empresa': prod.id_producto_empresa,
                    'nombre_producto_empresa': prod.nombre_producto_empresa,
                    'descripcion_producto_empresa': prod.descripcion_producto_empresa or '',
                    'caracteristicas_generales_empresa': prod.caracteristicas_generales_empresa or '',
                    'categoria_producto': prod.id_categoria_prod_fk.nombre_categoria_prod_empresa if prod.id_categoria_prod_fk else '',
                    'serial': idx,
                    'imagen_url': imagen_url,
                    'sucursales_asignadas': sucursales_list
                })
        else:
            # Filtrar productos de usuario
            productos_query = producto_usuario.objects.filter(id_usuario_fk=current_user)
            if nombre:
                productos_query = productos_query.filter(nombre_producto_usuario__icontains=nombre)
            
            for idx, prod in enumerate(productos_query, start=1):
                # Obtener la primera imagen del producto desde la nueva tabla
                primera_imagen = imagen_producto_usuario.objects.filter(id_producto_fk=prod).first()
                imagen_url = primera_imagen.ruta_imagen_producto_usuario.url if primera_imagen and primera_imagen.ruta_imagen_producto_usuario else ''
                
                productos_list.append({
                    'id_producto_usuario': prod.id_producto_usuario,
                    'nombre_producto_usuario': prod.nombre_producto_usuario,
                    'descripcion_producto_usuario': prod.descripcion_producto_usuario or '',
                    'caracteristicas_generales_usuario': prod.caracteristicas_generales_usuario or '',
                    'categoria_producto': prod.id_categoria_prod_fk.nombre_categoria_prod_usuario if prod.id_categoria_prod_fk else '',
                    'precio_producto_usuario': str(prod.precio_producto_usuario) if prod.precio_producto_usuario else '0',
                    'stock_producto_usuario': prod.stock_producto_usuario or 0,
                    'condicion_producto_usuario': prod.condicion_producto_usuario or '',
                    'estatus_producto_usuario': prod.estatus_producto_usuario or '',
                    'latitud_producto_usuario': str(prod.latitud_entrega_producto) if prod.latitud_entrega_producto else '',
                    'longitud_producto_usuario': str(prod.longitud_entrega_producto) if prod.longitud_entrega_producto else '',
                    'serial': idx,
                    'imagen_url': imagen_url
                })
        
        return JsonResponse({'success': True, 'productos': productos_list})
    except Exception as e:
        logger.error(f"Error al filtrar productos: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error al filtrar productos: {str(e)}'})
from django.views.decorators.http import require_GET



# API para obtener nombres de categorías de producto
@require_GET
def api_categorias_producto(request):
    from .models import categoria_producto_empresa, categoria_producto_usuario
    
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'categorias': []})
    
    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        categorias = list(categoria_producto_empresa.objects.filter(Q(id_empresa_fk=current_user) | Q(generico='s')).values_list('nombre_categoria_prod_empresa', flat=True))
    else:
        categorias = list(categoria_producto_usuario.objects.filter(id_usuario_fk=current_user).values_list('nombre_categoria_prod_usuario', flat=True))
    
    return JsonResponse({'categorias': categorias})

# API para obtener nombres de categorías de servicio
@require_GET
def api_categorias_servicio(request):
    from .models import categoria_servicio_empresa, categoria_servicio_usuario
    
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'categorias': []})
    
    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        categorias = list(categoria_servicio_empresa.objects.filter(Q(id_empresa_fk=current_user) | Q(generico='s')).values_list('nombre_categoria_serv_empresa', flat=True))
    else:
        categorias = list(categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user).values_list('nombre_categoria_serv_usuario', flat=True))
    
    return JsonResponse({'categorias': categorias})
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import os
from django.conf import settings
from django.views.decorators.http import require_GET
from django.db import transaction, IntegrityError
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
            account_type = request.session.get('account_type', 'usuario')
            
            if account_type == 'empresa':
                return empresa.objects.get(id_empresa=user_id)
            else:
                return usuario.objects.get(id_usuario=user_id)
        except (usuario.DoesNotExist, empresa.DoesNotExist):
            # Si el usuario/empresa no existe, limpiar la sesión
            logout_user(request)
            return None
    return None


@csrf_exempt
def publicar_comentario(request):
    """Vista AJAX para publicar un comentario desde la vista de item.
    Espera JSON con: item_id, tipo (producto/servicio), origen (empresa/usuario), comentario
    Retorna JSON {success: bool, message: str, autor: str, fecha: str, avatar: str}
    """
    import json
    from django.utils import timezone
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        logger.info(f"publicar_comentario called with data: {data}")

        # Validar sesión
        if not is_user_authenticated(request):
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado. Debes iniciar sesión para comentar.'}, status=403)

        comentario_text = data.get('comentario') or data.get('texto') or ''
        if not comentario_text.strip():
            return JsonResponse({'success': False, 'message': 'Comentario vacío'}, status=400)

        item_id = data.get('item_id')
        tipo = data.get('tipo')  # 'producto' o 'servicio'
        origen = data.get('origen', 'empresa')  # 'empresa' o 'usuario'

        # Obtener autor actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Sesión inválida'}, status=403)

        # Crear instancia de comentario según tipo/origen
        c = comentario()
        c.texto = comentario_text.strip()
        # Autor
        if isinstance(current_user, usuario):
            c.id_usuario_autor = current_user
        else:
            c.id_empresa_autor = current_user

        # Asociar al objeto comentado
        if tipo == 'producto':
            if origen == 'empresa':
                # item_id se refiere a producto_sucursal id
                try:
                    prod_s = producto_sucursal.objects.get(id_producto_sucursal=item_id)
                    c.producto_sucursal = prod_s
                except producto_sucursal.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Producto (sucursal) no encontrado'}, status=404)
            else:
                try:
                    prod_u = producto_usuario.objects.get(id_producto_usuario=item_id)
                    c.producto_usuario = prod_u
                except producto_usuario.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Producto (usuario) no encontrado'}, status=404)
        elif tipo == 'servicio':
            if origen == 'empresa':
                try:
                    svc_s = servicio_sucursal.objects.get(id_servicio_sucursal=item_id)
                    c.servicio_sucursal = svc_s
                except servicio_sucursal.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Servicio (sucursal) no encontrado'}, status=404)
            else:
                try:
                    svc_u = servicio_usuario.objects.get(id_servicio_usuario=item_id)
                    c.servicio_usuario = svc_u
                except servicio_usuario.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Servicio (usuario) no encontrado'}, status=404)
        else:
            return JsonResponse({'success': False, 'message': 'Tipo inválido'}, status=400)

        # Validar y guardar
        try:
            c.full_clean()
        except Exception as e:
            logger.error(f"Validación comentario falló: {e}")
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

        c.save()

        autor_nombre = current_user.nombre_usuario if isinstance(current_user, usuario) else current_user.nombre_empresa

        # Obtener url de avatar si existe (ImageFieldFile) y convertir a string
        avatar_field = getattr(current_user, 'foto_usuario', None) or getattr(current_user, 'logo_empresa', None)
        avatar_url = None
        try:
            if avatar_field:
                # Si es ImageFieldFile, usar .url; si es string, usar tal cual
                avatar_url = avatar_field.url if hasattr(avatar_field, 'url') else str(avatar_field)
        except Exception:
            avatar_url = None
        return JsonResponse({'success': True, 'message': 'Comentario publicado', 'id': c.id_comentario, 'is_author': True, 'autor': autor_nombre, 'fecha': timezone.localtime(c.fecha_creacion).strftime('%Y-%m-%d %H:%M:%S'), 'avatar': avatar_url})

    except Exception as e:
        logger.exception(f"Error en publicar_comentario: {e}")
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'}, status=500)


@require_GET
def obtener_comentarios(request):
    """API GET que devuelve comentarios paginados para un item.
    Parámetros: item_id, tipo (producto|servicio), origen (empresa|usuario), offset, limit
    Retorna JSON: {success: True, comments: [...], has_more: bool, next_offset: int}
    """
    try:
        item_id = request.GET.get('item_id') or request.GET.get('id')
        tipo = request.GET.get('tipo')
        origen = request.GET.get('origen', 'empresa')
        try:
            offset = int(request.GET.get('offset', 0))
        except (ValueError, TypeError):
            offset = 0
        try:
            limit = int(request.GET.get('limit', 5))
        except (ValueError, TypeError):
            limit = 5

        if not item_id or not tipo:
            return JsonResponse({'success': False, 'message': 'Parámetros inválidos', 'comments': []})

        # Current user (if any) to mark ownership
        current_user = get_current_user(request)

        qs = comentario.objects.none()

        if tipo == 'producto':
            if origen == 'empresa':
                qs = comentario.objects.filter(producto_sucursal__id_producto_sucursal=item_id)
            else:
                qs = comentario.objects.filter(producto_usuario__id_producto_usuario=item_id)
        elif tipo == 'servicio':
            if origen == 'empresa':
                qs = comentario.objects.filter(servicio_sucursal__id_servicio_sucursal=item_id)
            else:
                qs = comentario.objects.filter(servicio_usuario__id_servicio_usuario=item_id)
        else:
            return JsonResponse({'success': False, 'message': 'Tipo inválido', 'comments': []})

        total = qs.count()
        # qs already ordered by -fecha_creacion from Meta
        comentarios = list(qs[offset:offset+limit])

        comments_data = []
        for c in comentarios:
            if c.id_usuario_autor:
                autor = getattr(c.id_usuario_autor, 'nombre_usuario', 'Usuario')
                avatar_field = getattr(c.id_usuario_autor, 'foto_usuario', None)
            else:
                autor = getattr(c.id_empresa_autor, 'nombre_empresa', 'Empresa')
                avatar_field = getattr(c.id_empresa_autor, 'logo_empresa', None)

            avatar_url = None
            try:
                if avatar_field:
                    avatar_url = avatar_field.url if hasattr(avatar_field, 'url') else str(avatar_field)
            except Exception:
                avatar_url = None

            if not avatar_url:
                avatar_url = '/static/avatars/Cartoon Style Robot.jpg'

            # Determine if current_user is the author
            is_author = False
            try:
                if current_user:
                    # usuario instance
                    if hasattr(current_user, 'id_usuario') and c.id_usuario_autor and c.id_usuario_autor.id_usuario == getattr(current_user, 'id_usuario'):
                        is_author = True
                    # empresa instance
                    if hasattr(current_user, 'id_empresa') and c.id_empresa_autor and c.id_empresa_autor.id_empresa == getattr(current_user, 'id_empresa'):
                        is_author = True
            except Exception:
                is_author = False

            comments_data.append({
                'id': c.id_comentario,
                'autor': autor,
                'avatar': avatar_url,
                'texto': c.texto,
                'fecha': timezone.localtime(c.fecha_creacion).strftime('%Y-%m-%d %H:%M:%S'),
                'is_author': is_author
            })

        next_offset = offset + len(comments_data)
        has_more = next_offset < total

        return JsonResponse({'success': True, 'comments': comments_data, 'has_more': has_more, 'next_offset': next_offset})
    except Exception as e:
        logger.exception(f"Error en obtener_comentarios: {e}")
        return JsonResponse({'success': False, 'message': str(e), 'comments': []}, status=500)


def safe_get(obj, path, default=None):
    """Accede de forma segura a atributos anidados. path es 'a.b.c'."""
    try:
        cur = obj
        for part in path.split('.'):
            if cur is None:
                return default
            cur = getattr(cur, part, None)
        return cur if cur is not None else default
    except Exception:
        return default


def collect_service_images(svc_obj):
    """Devuelve lista de dicts con la forma que espera la plantilla: [{'imagen': {'url': '...'}}]
       Acepta objetos de servicio tanto de usuario como de empresa.
    """
    images = []
    try:
        if not svc_obj:
            return images
        imgs_manager = getattr(svc_obj, 'imagenes', None)
        if imgs_manager is None:
            return images
        # imgs_manager puede ser un RelatedManager
        for img in imgs_manager.all():
            # Intentar obtener el campo de ruta conocido
            url = None
            for attr in ('ruta_imagen_servicio_empresa', 'ruta_imagen_servicio_usuario'):
                if hasattr(img, attr):
                    filefield = getattr(img, attr)
                    try:
                        url = filefield.url
                        break
                    except Exception:
                        url = None
            if url:
                images.append({'imagen': {'url': url}})
    except Exception:
        return images
    return images


def resolve_service_name_from_solicitud(solicitud):
    """Intentar resolver un nombre de servicio desde una solicitud inspeccionando múltiples relaciones."""
    # Posibles caminos donde buscar el nombre
    candidates = [
        'id_servicio_usuario_fk.nombre_servicio_usuario',
        'id_servicio_usuario_fk.nombre_servicio_empresa',
        'id_servicio_sucursal_fk.nombre_servicio_sucursal',
        'id_servicio_sucursal_fk.id_servicio_fk.nombre_servicio_empresa',
        'id_servicio_sucursal_fk.id_servicio_fk.nombre_servicio_usuario',
    ]
    for path in candidates:
        val = safe_get(solicitud, path, None)
        if val:
            return val
    # Fallback a descripción o dirección
    desc = safe_get(solicitud, 'descripcion_detallada', None)
    if desc:
        # Use first 30 chars
        return (desc[:30] + '...') if len(desc) > 30 else desc
    direccion = safe_get(solicitud, 'direccion', None)
    if direccion:
        return direccion
    # Fallback final: usar el id de la solicitud si está disponible
    try:
        sid = getattr(solicitud, 'id_solicitud_servicio_usuario', None) or getattr(solicitud, 'id_solicitud_servicio_empresa', None)
        if sid:
            return f"Solicitud #{sid}"
    except Exception:
        pass
    return None


def resolve_service_name_strict(solicitud):
    """Resolver el nombre del servicio inspeccionando atributos ORM directamente y logueando el hallazgo."""
    try:
        # servicio_usuario direct
        svc_user = getattr(solicitud, 'id_servicio_usuario_fk', None)
        if svc_user:
            if getattr(svc_user, 'nombre_servicio_usuario', None):
                logger.info(f"resolve_service_name_strict: found nombre_servicio_usuario='{svc_user.nombre_servicio_usuario}' on solicitud {getattr(solicitud,'id_solicitud_servicio_usuario', getattr(solicitud,'id_solicitud_servicio_empresa', '?'))}")
                return svc_user.nombre_servicio_usuario
            if getattr(svc_user, 'nombre_servicio_empresa', None):
                logger.info(f"resolve_service_name_strict: found nombre_servicio_empresa on servicio_usuario: '{svc_user.nombre_servicio_empresa}'")
                return svc_user.nombre_servicio_empresa

        # servicio_sucursal
        svc_sucursal = getattr(solicitud, 'id_servicio_sucursal_fk', None)
        if svc_sucursal:
            if getattr(svc_sucursal, 'nombre_servicio_sucursal', None):
                logger.info(f"resolve_service_name_strict: found nombre_servicio_sucursal='{svc_sucursal.nombre_servicio_sucursal}' on solicitud")
                return svc_sucursal.nombre_servicio_sucursal
            svc_empresa = getattr(svc_sucursal, 'id_servicio_fk', None)
            if svc_empresa:
                if getattr(svc_empresa, 'nombre_servicio_empresa', None):
                    logger.info(f"resolve_service_name_strict: found nombre_servicio_empresa='{svc_empresa.nombre_servicio_empresa}' via servicio_sucursal")
                    return svc_empresa.nombre_servicio_empresa
                if getattr(svc_empresa, 'nombre_servicio_usuario', None):
                    logger.info(f"resolve_service_name_strict: found nombre_servicio_usuario='{svc_empresa.nombre_servicio_usuario}' via servicio_sucursal")
                    return svc_empresa.nombre_servicio_usuario

        # Try description or fallback
        desc = getattr(solicitud, 'descripcion_detallada', None)
        if desc:
            return desc[:30] + '...' if len(desc) > 30 else desc
        direccion = getattr(solicitud, 'direccion', None)
        if direccion:
            return direccion
        sid = getattr(solicitud, 'id_solicitud_servicio_usuario', None) or getattr(solicitud, 'id_solicitud_servicio_empresa', None)
        if sid:
            return f"Solicitud #{sid}"
    except Exception as e:
        logger.debug(f"resolve_service_name_strict error: {e}")
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
            account_type = request.session.get('account_type', 'usuario')
            
            if account_type == 'empresa':
                user_info = {
                    'id': current_user.id_empresa,
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'tipo': current_user.rol_empresa,
                    'is_authenticated': True
                }
            else:
                user_info = {
                    'id': current_user.id_usuario,
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'tipo': current_user.rol_usuario,
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
                        request.session['user_type'] = user.rol_usuario
                        request.session['is_authenticated'] = True
                        request.session['account_type'] = 'usuario'
                        
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
                        request.session['user_type'] = user.rol_usuario
                        request.session['is_authenticated'] = True
                        request.session['account_type'] = 'usuario'
                        
                        logger.info(f"Sesión creada para usuario: {user.correo_usuario}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'redirect_url': '/ecommerce/index'
                        })
                    else:
                        return JsonResponse({'success': False, 'message': 'Contraseña incorrecta'})
            except usuario.DoesNotExist:
                # Si no se encuentra en usuario, buscar en empresa
                try:
                    empresa_obj = empresa.objects.get(correo_empresa=email)
                    logger.info(f"Empresa encontrada: {empresa_obj.correo_empresa}")
                    
                    # Verificar contraseña de empresa
                    if check_password(password, empresa_obj.password_empresa):
                        # Crear sesión personalizada para empresa
                        request.session['user_id'] = empresa_obj.id_empresa
                        request.session['user_email'] = empresa_obj.correo_empresa
                        request.session['user_name'] = empresa_obj.nombre_empresa
                        request.session['user_type'] = empresa_obj.rol_empresa
                        request.session['is_authenticated'] = True
                        request.session['account_type'] = 'empresa'
                        request.session['empresa_id'] = empresa_obj.id_empresa
                        
                        logger.info(f"Sesión creada para empresa: {empresa_obj.correo_empresa}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'redirect_url': '/ecommerce/sucursal/'
                        })
                    else:
                        logger.warning(f"Contraseña incorrecta para empresa: {email}")
                        return JsonResponse({'success': False, 'message': 'Contraseña incorrecta'})
                except empresa.DoesNotExist:
                    logger.error(f"Email no encontrado en ninguna tabla: {email}")
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
            # Buscar primero en tabla usuario
            user = usuario.objects.get(correo_usuario=email)
            logger.info(f"Email validado exitosamente en tabla usuario: {email}")
            return JsonResponse({'exists': True})
        except usuario.DoesNotExist:
            # Si no se encuentra en usuario, buscar en empresa
            try:
                empresa_obj = empresa.objects.get(correo_empresa=email)
                logger.info(f"Email validado exitosamente en tabla empresa: {email}")
                return JsonResponse({'exists': True})
            except empresa.DoesNotExist:
                logger.warning(f"Email no encontrado en ninguna tabla: {email}")
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
            # Primero intentar buscar en la tabla usuario
            try:
                user = usuario.objects.get(correo_usuario=email)
                logger.info(f"Usuario encontrado: {user.correo_usuario}")
                
                # Verificar si la contraseña está hasheada
                if not user.password_usuario.startswith('pbkdf2_sha256$'):
                    logger.warning("La contraseña no está hasheada correctamente")
                    # Si no está hasheada, comparar directamente
                    if user.password_usuario == password:
                        # Crear sesión personalizada para usuario
                        request.session['user_id'] = user.id_usuario
                        request.session['user_email'] = user.correo_usuario
                        request.session['user_name'] = user.nombre_usuario
                        request.session['user_type'] = user.rol_usuario
                        request.session['is_authenticated'] = True
                        request.session['account_type'] = 'usuario'
                        
                        logger.info(f"Sesión creada para usuario: {user.correo_usuario}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'user_name': user.nombre_usuario,
                            'user_type': user.rol_usuario,
                            'account_type': 'usuario',
                            'redirect_url': '/ecommerce/index/'
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
                        # Crear sesión personalizada para usuario
                        request.session['user_id'] = user.id_usuario
                        request.session['user_email'] = user.correo_usuario
                        request.session['user_name'] = user.nombre_usuario
                        request.session['user_type'] = user.rol_usuario
                        request.session['is_authenticated'] = True
                        request.session['account_type'] = 'usuario'
                        
                        logger.info(f"Sesión creada para usuario: {user.correo_usuario}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'user_name': user.nombre_usuario,
                            'user_type': user.rol_usuario,
                            'account_type': 'usuario',
                            'redirect_url': '/ecommerce/index/'
                        }, content_type='application/json')
                    else:
                        logger.warning(f"Contraseña incorrecta para usuario: {email}")
                        return JsonResponse({
                            'success': False, 
                            'message': 'Contraseña incorrecta'
                        }, content_type='application/json')
            except usuario.DoesNotExist:
                # Si no se encuentra en usuario, buscar en empresa
                try:
                    empresa_obj = empresa.objects.get(correo_empresa=email)
                    logger.info(f"Empresa encontrada: {empresa_obj.correo_empresa}")
                    
                    # Verificar contraseña de empresa
                    if check_password(password, empresa_obj.password_empresa):
                        # Crear sesión personalizada para empresa
                        request.session['user_id'] = empresa_obj.id_empresa
                        request.session['user_email'] = empresa_obj.correo_empresa
                        request.session['user_name'] = empresa_obj.nombre_empresa
                        request.session['user_type'] = empresa_obj.rol_empresa
                        request.session['is_authenticated'] = True
                        request.session['account_type'] = 'empresa'
                        
                        logger.info(f"Sesión creada para empresa: {empresa_obj.correo_empresa}")
                        
                        return JsonResponse({
                            'success': True, 
                            'message': 'Inicio de sesión exitoso',
                            'user_name': empresa_obj.nombre_empresa,
                            'user_type': empresa_obj.rol_empresa,
                            'account_type': 'empresa',
                            'redirect_url': '/ecommerce/sucursal/'
                        }, content_type='application/json')
                    else:
                        logger.warning(f"Contraseña incorrecta para empresa: {email}")
                        return JsonResponse({
                            'success': False, 
                            'message': 'Contraseña incorrecta'
                        }, content_type='application/json')
                except empresa.DoesNotExist:
                    logger.warning(f"Email no encontrado en ninguna tabla: {email}")
                    return JsonResponse({
                        'success': False, 
                        'message': 'Email no encontrado'
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
        avatar_chatbot_file=request.FILES.get('avatar_chatbot')

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

        # Verificar si el email ya está registrado (en usuarios o empresas)
        try:
            if usuario.objects.filter(correo_usuario__iexact=email).exists() or empresa.objects.filter(correo_empresa__iexact=email).exists():
                logger.info(f"Intento de registro con email ya existente: {email}")
                return JsonResponse({
                    'success': False,
                    'message': 'Este correo ya tiene una cuenta asociada.'
                })
        except Exception as e:
            # No bloquear el flujo si hay un error inesperado al comprobar duplicados
            logger.debug(f"No se pudo verificar existencia de email: {e}")

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
            
            # Manejar el avatar del chatbot
            avatar_option = request.POST.get('avatar_option', 'avatars/Cartoon Style Robot.jpg')
            
            if avatar_option == 'custom' and avatar_chatbot_file:
                # Guardar la imagen personalizada del avatar del chatbot
                import os
                from django.core.files.storage import default_storage
                from django.conf import settings
                
                # Crear directorio si no existe
                avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars_chatbot')
                os.makedirs(avatar_dir, exist_ok=True)
                
                # Generar nombre único para el archivo
                import uuid
                file_extension = os.path.splitext(avatar_chatbot_file.name)[1]
                unique_filename = f"avatar_{uuid.uuid4().hex}{file_extension}"
                avatar_path = f"avatars_chatbot/{unique_filename}"
                
                # Guardar el archivo
                saved_path = default_storage.save(avatar_path, avatar_chatbot_file)
                avatar_chatbot_path = saved_path
                logger.info(f"Avatar personalizado del chatbot guardado en: {avatar_chatbot_path}")
            else:
                # Usar avatar predefinido seleccionado
                avatar_chatbot_path = avatar_option if avatar_option != 'custom' else 'avatars/Cartoon Style Robot.jpg'
                logger.info(f"Avatar predefinido seleccionado: {avatar_chatbot_path}")
            
            nuevo_usuario = usuario(
                nombre_usuario=nombre_usuario + ' ' + apellido,
                correo_usuario=email,
                telefono_usuario=telefono,
                password_usuario=password_encriptada,  # Usar la contraseña encriptada
                autenticacion_usuario='local',  
                rol_usuario='persona',          
                fecha_nacimiento=fecha_nacimiento,
                pais=pais,
                estado=estado,
                avatar_chatbot=avatar_chatbot_path
            )
            nuevo_usuario.save()
            logger.info(f"Usuario registrado exitosamente: {email}")
            
            # Crear sesión automáticamente después del registro exitoso
            request.session['user_id'] = nuevo_usuario.id_usuario
            request.session['user_email'] = nuevo_usuario.correo_usuario
            request.session['user_name'] = nuevo_usuario.nombre_usuario
            request.session['user_type'] = nuevo_usuario.rol_usuario
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
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
    
    return render(request, 'ecommerce_app/registrar_persona.html', {'user_info': user_info})

@transaction.atomic
def registrar_empresa(request):
    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            # Normalizar y sanear entradas para evitar issues con espacios/case
            nombre_empresa = (request.POST.get('nombre_empresa') or '').strip()
            correo_empresa = (request.POST.get('correo_empresa') or '').strip().lower()
            password_empresa = request.POST.get('password_empresa') or ''
            confirm_password = request.POST.get('confirm_password') or ''
            descripcion_empresa = (request.POST.get('descripcion_empresa') or '').strip()
            logo_empresa = request.FILES.get('logo_empresa')
            pais_empresa = request.POST.get('pais_empresa')
            estado_empresa = request.POST.get('estado_empresa')
            tipo_empresa = request.POST.get('tipo_empresa')
            sector_empresa = request.POST.get('sector_empresa')
            direccion_empresa = (request.POST.get('direccion_empresa') or '').strip()
            
            # Avatar del chatbot
            avatar_option = request.POST.get('avatar_option', 'avatars/Cartoon Style Robot.jpg')
            avatar_chatbot_file = request.FILES.get('avatar_chatbot')
            
            # Si se sube un archivo personalizado, usarlo
            if avatar_chatbot_file and avatar_option == 'custom':
                avatar_chatbot_empresa = avatar_chatbot_file
            else:
                # Usar la opción seleccionada (ruta del avatar predefinido)
                avatar_chatbot_empresa = avatar_option

            # Validar que se haya subido el logo de la empresa
            if not logo_empresa:
                logger.warning("Logo de empresa no proporcionado en registro de empresa")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'El logo de la empresa es obligatorio.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'error_message': 'El logo de la empresa es obligatorio.'
                    })

            # Validar que todos los campos estén completos
            if not nombre_empresa or not correo_empresa or not password_empresa or not confirm_password or not descripcion_empresa or not pais_empresa or not estado_empresa or not tipo_empresa or not direccion_empresa:
                logger.warning("Campos obligatorios faltantes en registro de empresa")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Todos los campos son obligatorios. Por favor complete todos los campos.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'error_message': 'Todos los campos son obligatorios. Por favor complete todos los campos.'
                    })

            # Validar que las contraseñas coincidan
            if password_empresa != confirm_password:
                logger.warning("Las contraseñas no coinciden")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Las contraseñas no coinciden.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'error_message': 'Las contraseñas no coinciden.'
                    })

            # Validar que el correo no exista en la tabla usuario (case-insensitive)
            if usuario.objects.filter(correo_usuario__iexact=correo_empresa).exists():
                logger.warning(f"El correo {correo_empresa} ya existe en la tabla usuario")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Este correo ya está registrado como usuario.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'error_message': 'Este correo ya está registrado como usuario.'
                    })

            # Validar que el correo no exista en la tabla empresa
            if empresa.objects.filter(correo_empresa__iexact=correo_empresa).exists():
                logger.warning(f"El correo {correo_empresa} ya existe en la tabla empresa")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Este correo ya está registrado como empresa.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'error_message': 'Este correo ya está registrado como empresa.'
                    })

            # Validar que el nombre de la empresa no exista (case-insensitive)
            if nombre_empresa and empresa.objects.filter(nombre_empresa__iexact=nombre_empresa).exists():
                logger.warning(f"El nombre de empresa {nombre_empresa} ya existe en la tabla empresa")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'El nombre de la empresa ya está registrado.'
                    })
                else:
                    return render(request, 'ecommerce_app/registrar_empresa.html', {
                        'error_message': 'El nombre de la empresa ya está registrado.'
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
                        'error_message': 'La descripción debe tener al menos 10 caracteres.'
                    })

            # Hashear la contraseña antes de guardar
            password_hasheada = make_password(password_empresa)
            
            # Logging para verificar los datos
            logger.info(f"Dirección recibida: {direccion_empresa}")
            logger.info(f"Tipo de dirección: {type(direccion_empresa)}")

            nueva_empresa = empresa(
                nombre_empresa=nombre_empresa,
                correo_empresa=correo_empresa,
                password_empresa=password_hasheada,
                descripcion_empresa=descripcion_empresa,
                logo_empresa=logo_empresa,
                pais_empresa=pais_empresa,
                estado_empresa=estado_empresa,
                tipo_empresa=tipo_empresa,
                sector_empresa=sector_empresa,
                direccion_empresa=direccion_empresa,
                avatar_chatbot_empresa=avatar_chatbot_empresa
            )
            nueva_empresa.save()
            logger.info(f"Empresa guardada exitosamente: {nueva_empresa.nombre_empresa}")
            logger.info(f"Dirección guardada: {nueva_empresa.direccion_empresa}")

            # Crear sesión automáticamente después del registro exitoso
            request.session['user_id'] = nueva_empresa.id_empresa
            request.session['user_email'] = nueva_empresa.correo_empresa
            request.session['user_name'] = nueva_empresa.nombre_empresa
            request.session['user_type'] = nueva_empresa.rol_empresa
            request.session['is_authenticated'] = True
            request.session['account_type'] = 'empresa'
            
            logger.info(f"Sesión creada automáticamente para empresa: {nueva_empresa.correo_empresa}")

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Empresa registrada exitosamente',
                    'redirect_url': '/ecommerce/sucursal/'
                })
            else:
                return redirect('/ecommerce/sucursal/')
        except IntegrityError as e:
            logger.error(f"Error de integridad al guardar la empresa: {str(e)}")
            error_message = 'El correo electrónico ya está registrado. Por favor, use otro correo.'
            if 'correo_empresa' in str(e):
                error_message = 'El correo electrónico ya está registrado. Por favor, use otro correo.'
            elif 'nombre_empresa' in str(e):
                error_message = 'El nombre de empresa ya está registrado. Por favor, use otro nombre.'
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
            else:
                return render(request, 'ecommerce_app/registrar_empresa.html', {
                    'error_message': error_message
                })
        except Exception as e:
            logger.error(f"Error inesperado al guardar la empresa: {str(e)}")
            error_message = 'Ocurrió un error inesperado. Por favor, inténtelo de nuevo.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
            else:
                return render(request, 'ecommerce_app/registrar_empresa.html', {
                    'error_message': error_message
                })
    
    # Si es GET, mostrar el formulario
    return render(request, 'ecommerce_app/registrar_empresa.html')



@require_login
def sucursalfuncion(request):
    user_info = None
    
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    if is_user_authenticated(request):
        account_type = request.session.get('account_type', 'usuario')
        
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
            # Para empresas, current_user ya es la empresa
            empresa_obj = current_user
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
            # Para usuarios, buscar la empresa asociada (aunque esto ya no debería pasar)
            empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
            if not empresa_obj:
                return redirect('/ecommerce/registrar_empresa/')
    
    # Obtener todas las sucursales de la empresa
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





def procesar_atributos_producto(request, producto_empresa=None, producto_usuario=None, account_type='usuario'):
    """
    Procesa y guarda los valores de atributos dinámicos para un producto
    """
    try:
        logger.info(f"Campos recibidos en request.POST: {dict(request.POST)}")
        # Obtener todos los campos del formulario que empiecen con 'atributo_'
        for key, value in request.POST.items():
            if key.startswith('atributo_'):
                atributo_id = key.replace('atributo_', '')
                try:
                    atributo = AtributoProducto.objects.get(id_atributo=atributo_id)
                    if atributo.obligatorio and (not value or value.strip() == ''):
                        continue
                    # Preparar kwargs para el valor según tipo de dato
                    valor_kwargs = {}
                    if atributo.tipo_dato == 'texto':
                        valor_kwargs['valor_texto'] = value
                    elif atributo.tipo_dato == 'numero':
                        try:
                            valor_kwargs['valor_numero'] = int(value) if value else None
                        except ValueError:
                            valor_kwargs['valor_numero'] = None
                    elif atributo.tipo_dato == 'decimal':
                        try:
                            valor_kwargs['valor_decimal'] = float(value) if value else None
                        except ValueError:
                            valor_kwargs['valor_decimal'] = None
                    elif atributo.tipo_dato == 'fecha':
                        valor_kwargs['valor_fecha'] = value if value else None
                    elif atributo.tipo_dato == 'booleano':
                        valor_kwargs['valor_booleano'] = value.lower() in ['true', '1', 'on', 'yes']
                    elif atributo.tipo_dato == 'lista':
                        valor_kwargs['valor_texto'] = value
                    else:
                        valor_kwargs['valor_texto'] = value
                    # Crear el registro en ValorAtributoProducto
                    if producto_empresa:
                        ValorAtributoProducto.objects.create(
                            producto_empresa=producto_empresa,
                            atributo=atributo,
                            **valor_kwargs
                        )
                    elif producto_usuario:
                        ValorAtributoProducto.objects.create(
                            producto_usuario=producto_usuario,
                            atributo=atributo,
                            **valor_kwargs
                        )
                    logger.info(f"Atributo {atributo.nombre} guardado con valor: {value}")
                except AtributoProducto.DoesNotExist:
                    logger.warning(f"Atributo con ID {atributo_id} no encontrado")
                    continue
                except Exception as e:
                    logger.error(f"Error al procesar atributo {atributo_id}: {str(e)}")
                    continue
    except Exception as e:
        logger.error(f"Error general al procesar atributos: {str(e)}")

@require_login
def producto_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, usar categorías de empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        categoria_producto_all = categoria_producto_empresa.objects.filter(Q(id_empresa_fk=empresa_obj) | Q(generico='s'))
    else:
        # Para usuarios, usar categorías de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        # Mostrar SOLO categorías definidas en la tabla de usuario: aquellas propias
        # del usuario y las marcadas como genéricas (generico='s'). No incluir categorias de empresa.
        categoria_producto_all = categoria_producto_usuario.objects.filter(
            Q(id_usuario_fk=current_user) | Q(generico='s')
        ).order_by('nombre_categoria_prod_usuario')

    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            if account_type == 'empresa':
                nombre_producto = request.POST.get('nombre_producto_empresa', '').strip()
                descripcion_producto = request.POST.get('descripcion_producto_empresa', '').strip()
            else:
                nombre_producto = request.POST.get('nombre_producto_usuario', '').strip()
                descripcion_producto = request.POST.get('descripcion_producto_usuario', '').strip()
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

            if account_type == 'empresa':
                categoria_producto_consul = categoria_producto_empresa.objects.get(id_categoria_prod_empresa=categoria_id)
                
                # Crear el producto para empresa
                nuevo_producto = producto_empresa(
                    nombre_producto_empresa=nombre_producto,
                    descripcion_producto_empresa=descripcion_producto,
                    caracteristicas_generales_empresa=caracteristicas_generales,
                    id_empresa_fk=empresa_obj,
                    id_categoria_prod_fk=categoria_producto_consul
                )
                nuevo_producto.save()
                logger.info(f"Producto guardado exitosamente: {nuevo_producto.nombre_producto_empresa}")
                
                # Guardar las imágenes en la tabla imagen_producto_empresa
                for imagen in imagenes_producto:
                    imagen_producto_empresa.objects.create(
                        ruta_imagen_producto_empresa=imagen,
                        id_producto_fk=nuevo_producto
                    )
                logger.info(f"Se guardaron {len(imagenes_producto)} imágenes para el producto {nuevo_producto.nombre_producto_empresa}")
                
                # Procesar y guardar atributos dinámicos para empresa
                procesar_atributos_producto(request, nuevo_producto, None, account_type)
                
            else:
                # Intentar buscar la categoría en las categorías de usuario;
                # si no existe, podría tratarse de una categoría genérica de empresa, probar ahí.
                try:
                    categoria_producto_consul = categoria_producto_usuario.objects.get(id_categoria_prod_usuario=categoria_id)
                except categoria_producto_usuario.DoesNotExist:
                    # Si no existe como categoría de usuario, intentar buscar en categorías de empresa (genéricas)
                    try:
                        categoria_empresa_obj = categoria_producto_empresa.objects.get(id_categoria_prod_empresa=categoria_id)
                        # Buscar si el usuario ya tiene una categoría con el mismo nombre
                        categoria_usuario_obj = categoria_producto_usuario.objects.filter(
                            nombre_categoria_prod_usuario__iexact=categoria_empresa_obj.nombre_categoria_prod_empresa,
                            id_usuario_fk=current_user
                        ).first()
                        if not categoria_usuario_obj:
                            # Crear una categoría de usuario basada en la genérica de empresa
                            categoria_usuario_obj = categoria_producto_usuario.objects.create(
                                nombre_categoria_prod_usuario=categoria_empresa_obj.nombre_categoria_prod_empresa,
                                descripcion_categoria_prod_usuario=categoria_empresa_obj.descripcion_categoria_prod_empresa,
                                generico='n',
                                estatus_categoria_prod_usuario=categoria_empresa_obj.estatus_categoria_prod_empresa,
                                id_usuario_fk=current_user
                            )
                        categoria_producto_consul = categoria_usuario_obj
                    except categoria_producto_empresa.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'La categoría seleccionada no existe.', 'field': 'categoria'})
                
                # Obtener los campos adicionales para usuario
                stock_producto = request.POST.get('stock_producto_usuario', 0)
                precio_producto = request.POST.get('precio_producto_usuario', 0)
                condicion_producto = request.POST.get('condicion_producto_usuario', 'Nuevo')
                estatus_producto = request.POST.get('estatus_producto_usuario', 'Activo')
                
                # Obtener los campos de ubicación (latitud y longitud)
                latitud_entrega = request.POST.get('latitud_entrega_producto', None)
                longitud_entrega = request.POST.get('longitud_entrega_producto', None)
                # Nuevos campos: presentacin
                unidad_presentacion = request.POST.get('unidad_presentacion_producto_usuario', 'unidad')
                cantidad_por_presentacion = request.POST.get('cantidad_por_presentacion_producto_usuario', None)

                # Validar/convetir cantidad si viene
                if cantidad_por_presentacion:
                    try:
                        cantidad_por_presentacion = int(cantidad_por_presentacion)
                        if cantidad_por_presentacion <= 0:
                            cantidad_por_presentacion = None
                    except (ValueError, TypeError):
                        cantidad_por_presentacion = None

                # Si la unidad es 'unidad', entonces no usamos cantidad_por_presentacion
                if unidad_presentacion == 'unidad':
                    cantidad_por_presentacion = None
                else:
                    # si no es 'unidad', podemos requerir la cantidad (opcional según policy)
                    if cantidad_por_presentacion is None:
                        # Si no se proporcionó cantidad válida, devolver error
                        return JsonResponse({'success': False, 'message': 'Si la presentación no es "Unidad", debe indicar la cantidad por presentación (ej.: 6 por paquete).'} )
                
                # Validar y convertir latitud y longitud si están presentes
                if latitud_entrega:
                    try:
                        latitud_entrega = float(latitud_entrega)
                    except (ValueError, TypeError):
                        latitud_entrega = None
                        
                if longitud_entrega:
                    try:
                        longitud_entrega = float(longitud_entrega)
                    except (ValueError, TypeError):
                        longitud_entrega = None
                
                # Crear el producto para usuario
                nuevo_producto = producto_usuario(
                    nombre_producto_usuario=nombre_producto,
                    descripcion_producto_usuario=descripcion_producto,
                    caracteristicas_generales_usuario=caracteristicas_generales,
                    stock_producto_usuario=stock_producto,
                    precio_producto_usuario=precio_producto,
                    condicion_producto_usuario=condicion_producto,
                    estatus_producto_usuario=estatus_producto,
                    latitud_entrega_producto=latitud_entrega,
                    longitud_entrega_producto=longitud_entrega,
                    unidad_presentacion_producto_usuario=unidad_presentacion,
                    cantidad_por_presentacion_producto_usuario=cantidad_por_presentacion,
                    id_usuario_fk=current_user,
                    id_categoria_prod_fk=categoria_producto_consul
                )
                nuevo_producto.save()
                logger.info(f"Producto guardado exitosamente: {nuevo_producto.nombre_producto_usuario}")
                
                # Guardar las imágenes en la tabla imagen_producto_usuario
                for imagen in imagenes_producto:
                    imagen_producto_usuario.objects.create(
                        ruta_imagen_producto_usuario=imagen,
                        id_producto_fk=nuevo_producto
                    )
                logger.info(f"Se guardaron {len(imagenes_producto)} imágenes para el producto {nuevo_producto.nombre_producto_usuario}")
                
                # Procesar y guardar atributos dinámicos para usuario
                procesar_atributos_producto(request, None, nuevo_producto, account_type)
            
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

    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, current_user ya es la empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        categoria_servicio_all = categoria_servicio_empresa.objects.filter(Q(id_empresa_fk=empresa_obj) | Q(generico='s'))
    else:
        # Para usuarios, usar categorías de usuario directamente
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        # Para usuarios incluir tanto las categorías propias del usuario como
        # las categorías genéricas que residan en la tabla de categorías de usuario
        # (campo generico='s'). Usamos un único queryset para que la plantilla
        # reciba objetos del mismo modelo `categoria_servicio_usuario`.
        from django.db.models import Q as _Q
        categoria_servicio_all = categoria_servicio_usuario.objects.filter(_Q(id_usuario_fk=current_user) | _Q(generico='s'))

    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            if account_type == 'empresa':
                nombre_servicio = request.POST.get('nombre_servicio_empresa', '').strip()
                descripcion_servicio = request.POST.get('descripcion_servicio_empresa', '').strip()
            else:
                nombre_servicio = request.POST.get('nombre_servicio_usuario', '').strip()
                descripcion_servicio = request.POST.get('descripcion_servicio_usuario', '').strip()
            categoria_id = request.POST.get('categoria_servicio', '').strip()
            # Obtener múltiples imágenes (hasta 5)
            imagenes_servicio = request.FILES.getlist('imagenes_servicio')

            # Validaciones backend
            if not nombre_servicio:
                return JsonResponse({'success': False, 'message': 'El nombre del servicio es obligatorio.', 'field': 'nombre_servicio'})
            
            # Validar duplicados según el tipo de cuenta
            if account_type == 'empresa':
                if servicio_empresa.objects.filter(nombre_servicio_empresa__iexact=nombre_servicio, id_empresa_fk=empresa_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Ya existe un servicio con ese nombre.', 'field': 'nombre_servicio'})
            else:
                if servicio_usuario.objects.filter(nombre_servicio_usuario__iexact=nombre_servicio, id_usuario_fk=current_user).exists():
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

            # Crear el servicio según el tipo de cuenta
            if account_type == 'empresa':
                categoria_servicio_consul = categoria_servicio_empresa.objects.get(id_categoria_serv_empresa=categoria_id)
                nuevo_servicio = servicio_empresa(
                    nombre_servicio_empresa=nombre_servicio,
                    descripcion_servicio_empresa=descripcion_servicio,
                    id_empresa_fk=empresa_obj,
                    id_categoria_servicios_fk=categoria_servicio_consul
                )
                nuevo_servicio.save()   
                logger.info(f"Servicio de empresa guardado exitosamente: {nuevo_servicio.nombre_servicio_empresa}")
                
                # Guardar las imágenes en la tabla imagen_servicio_empresa
                for imagen in imagenes_servicio:
                    imagen_servicio_empresa.objects.create(
                        ruta_imagen_servicio_empresa=imagen,
                        id_servicio_fk=nuevo_servicio
                    )
                logger.info(f"Se guardaron {len(imagenes_servicio)} imágenes para el servicio de empresa {nuevo_servicio.nombre_servicio_empresa}")
            else:
                categoria_servicio_consul = categoria_servicio_usuario.objects.get(id_categoria_serv_usuario=categoria_id)
                
                # Obtener campos adicionales para usuarios con rol 'persona'
                precio_servicio = request.POST.get('precio_servicio_usuario', '0')
                estatus_servicio = request.POST.get('estatus_servicio_usuario', 'Activo')
                
                # Convertir precio a float con manejo de errores
                try:
                    precio_float = float(precio_servicio) if precio_servicio else 0.0
                except (ValueError, TypeError):
                    precio_float = 0.0
                
                nuevo_servicio = servicio_usuario(
                    nombre_servicio_usuario=nombre_servicio,
                    descripcion_servicio_usuario=descripcion_servicio,
                    precio_servicio_usuario=precio_float,
                    estatus_servicio_usuario=estatus_servicio,
                    id_usuario_fk=current_user,
                    id_categoria_servicios_fk=categoria_servicio_consul
                )
                nuevo_servicio.save()   
                logger.info(f"Servicio de usuario guardado exitosamente: {nuevo_servicio.nombre_servicio_usuario} con precio: {precio_float} y estatus: {estatus_servicio}")
                
                # Guardar las imágenes en la tabla imagen_servicio_usuario
                for imagen in imagenes_servicio:
                    imagen_servicio_usuario.objects.create(
                        ruta_imagen_servicio_usuario=imagen,
                        id_servicio_fk=nuevo_servicio
                    )
                logger.info(f"Se guardaron {len(imagenes_servicio)} imágenes para el servicio de usuario {nuevo_servicio.nombre_servicio_usuario}")
            
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
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    
    # Obtener todos los atributos disponibles
    atributos_disponibles = AtributoProducto.objects.all().order_by('nombre')
    
    if account_type == 'empresa':
        # Para empresas, usar categorías de empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
    else:
        # Para usuarios, usar categorías de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
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
            
            if account_type == 'empresa':
                # Validar duplicados para empresa
                if categoria_producto_empresa.objects.filter(nombre_categoria_prod_empresa__iexact=nombre_categoria, id_empresa_fk=empresa_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Ya existe una categoría con ese nombre.'}, content_type='application/json')
            else:
                # Validar duplicados para usuario
                if categoria_producto_usuario.objects.filter(nombre_categoria_prod_usuario__iexact=nombre_categoria, id_usuario_fk=current_user).exists():
                    return JsonResponse({'success': False, 'message': 'Ya existe una categoría con ese nombre.'}, content_type='application/json')
            
            if not estatus_categoria:
                return JsonResponse({'success': False, 'message': 'Debe seleccionar un estatus.'}, content_type='application/json')

            # Primero validar todos los nuevos atributos antes de crear la categoría
            contador = 1
            nuevos_atributos_data = []
            while f'nuevo_atributo_nombre_{contador}' in request.POST:
                nombre_attr = request.POST.get(f'nuevo_atributo_nombre_{contador}', '').strip()
                tipo_attr = request.POST.get(f'nuevo_atributo_tipo_{contador}', '').strip()
                descripcion_attr = request.POST.get(f'nuevo_atributo_descripcion_{contador}', '').strip()
                obligatorio_attr = request.POST.get(f'nuevo_atributo_obligatorio_{contador}') == '1'
                opciones_attr = request.POST.get(f'nuevo_atributo_opciones_{contador}', '').strip()
                
                if nombre_attr and tipo_attr:
                    # Verificar si ya existe un atributo con ese nombre
                    atributo_existente = AtributoProducto.objects.filter(nombre__iexact=nombre_attr).first()
                    if atributo_existente:
                        return JsonResponse({
                            'success': False, 
                            'message': f'Ya existe un atributo con el nombre "{nombre_attr}". Por favor, use un nombre diferente o seleccione el atributo existente de la lista.'
                        }, content_type='application/json')
                    
                    # Procesar opciones para tipo lista
                    opciones_json = None
                    if tipo_attr == 'lista' and opciones_attr:
                        opciones_json = [opcion.strip() for opcion in opciones_attr.split(',') if opcion.strip()]
                    
                    # Guardar datos del atributo para crear después
                    nuevos_atributos_data.append({
                        'nombre': nombre_attr,
                        'tipo_dato': tipo_attr,
                        'descripcion': descripcion_attr,
                        'obligatorio': obligatorio_attr,
                        'opciones': opciones_json
                    })
                
                contador += 1
            
            # Si llegamos aquí, todas las validaciones pasaron, ahora crear la categoría
            if account_type == 'empresa':
                nueva_categoria = categoria_producto_empresa(
                    nombre_categoria_prod_empresa=nombre_categoria,
                    descripcion_categoria_prod_empresa=descripcion_categoria,
                    estatus_categoria_prod_empresa=estatus_categoria,
                    fecha_creacion_prod_empresa=fecha_creacion,
                    id_empresa_fk=empresa_obj
                )
            else:
                nueva_categoria = categoria_producto_usuario(
                    nombre_categoria_prod_usuario=nombre_categoria,
                    descripcion_categoria_prod_usuario=descripcion_categoria,
                    estatus_categoria_prod_usuario=estatus_categoria,
                    fecha_creacion_prod_usuario=fecha_creacion,
                    id_usuario_fk=current_user
                )
            
            nueva_categoria.save()
            
            # Procesar atributos seleccionados existentes
            atributos_existentes = request.POST.getlist('atributos_existentes')
            for atributo_id in atributos_existentes:
                try:
                    atributo = AtributoProducto.objects.get(id_atributo=atributo_id)
                    if account_type == 'empresa':
                        CategoriaAtributo.objects.create(
                            atributo=atributo,
                            categoria_empresa=nueva_categoria
                        )
                    else:
                        CategoriaAtributo.objects.create(
                            atributo=atributo,
                            categoria_usuario=nueva_categoria
                        )
                except AtributoProducto.DoesNotExist:
                    continue
            
            # Crear los nuevos atributos validados
            for atributo_data in nuevos_atributos_data:
                nuevo_atributo = AtributoProducto.objects.create(
                    nombre=atributo_data['nombre'],
                    tipo_dato=atributo_data['tipo_dato'],
                    descripcion=atributo_data['descripcion'],
                    obligatorio=atributo_data['obligatorio'],
                    opciones=atributo_data['opciones']
                )
                
                # Asociar el nuevo atributo con la categoría
                if account_type == 'empresa':
                    CategoriaAtributo.objects.create(
                        atributo=nuevo_atributo,
                        categoria_empresa=nueva_categoria
                    )
                else:
                    CategoriaAtributo.objects.create(
                        atributo=nuevo_atributo,
                        categoria_usuario=nueva_categoria
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Categoría y atributos registrados exitosamente'
            }, content_type='application/json')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, content_type='application/json')

    return render(request, 'ecommerce_app/categoria_producto.html', {
        'user_info': user_info,
        'atributos_disponibles': atributos_disponibles
    })

@require_login
def categoria_servicio_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, current_user ya es la empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
    else:
        # Para usuarios, usar categorías de usuario directamente
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
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
            if account_type == 'empresa':
                # Validar duplicados para empresa
                if categoria_servicio_empresa.objects.filter(nombre_categoria_serv_empresa__iexact=nombre_categoria, id_empresa_fk=empresa_obj).exists():
                    return JsonResponse({'success': False, 'message': 'Ya existe una categoría con ese nombre.'})
            else:
                # Validar duplicados para usuario
                if categoria_servicio_usuario.objects.filter(nombre_categoria_serv_usuario__iexact=nombre_categoria, id_usuario_fk=current_user).exists():
                    return JsonResponse({'success': False, 'message': 'Ya existe una categoría con ese nombre.'})

            if account_type == 'empresa':
                nueva_categoria = categoria_servicio_empresa(
                    nombre_categoria_serv_empresa=nombre_categoria,
                    descripcion_categoria_serv_empresa=descripcion_categoria,
                    estatus_categoria_serv_empresa=estatus_categoria,
                    fecha_creacion_categ_serv_empresa=fecha_creacion,
                    id_empresa_fk=empresa_obj
                )
            else:
                nueva_categoria = categoria_servicio_usuario(
                    nombre_categoria_serv_usuario=nombre_categoria,
                    descripcion_categoria_serv_usuario=descripcion_categoria,
                    estatus_categoria_serv_usuario=estatus_categoria,
                    fecha_creacion_categ_serv_usuario=fecha_creacion,
                    id_usuario_fk=current_user
                )
            nueva_categoria.save()
            if account_type == 'empresa':
                logger.info(f"Categoria guardada exitosamente: {nueva_categoria.nombre_categoria_serv_empresa}")
            else:
                logger.info(f"Categoria guardada exitosamente: {nueva_categoria.nombre_categoria_serv_usuario}")
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
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, usar categorías de empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        categ_producto_all = categoria_producto_empresa.objects.filter(Q(id_empresa_fk=empresa_obj) | Q(generico='s')).order_by('-fecha_creacion_prod_empresa')
    else:
        # Para usuarios, incluir tanto categorías de usuario como categorías genéricas de empresa
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        # Categorías genéricas creadas a nivel empresa
        empresa_genericas_qs = categoria_producto_empresa.objects.filter(generico='s')
        usuario_qs = categoria_producto_usuario.objects.filter(id_usuario_fk=current_user)
        # Combinar resultados para pasarlos a la plantilla (lista de objetos)
        categ_producto_all = list(empresa_genericas_qs) + list(usuario_qs)
    
    # Calcular estadísticas
    if account_type == 'empresa':
        total_categorias = categ_producto_all.count()
        categorias_activas = categ_producto_all.filter(estatus_categoria_prod_empresa='Activo').count()
        categorias_inactivas = categ_producto_all.filter(estatus_categoria_prod_empresa='Inactivo').count()
    else:
        # En el caso de usuario combinamos querysets en una lista: calcular contadores desde los querysets originales
        total_categorias = empresa_genericas_qs.count() + usuario_qs.count()
        categorias_activas = empresa_genericas_qs.filter(estatus_categoria_prod_empresa='Activo').count() + usuario_qs.filter(estatus_categoria_prod_usuario='Activo').count()
        categorias_inactivas = empresa_genericas_qs.filter(estatus_categoria_prod_empresa='Inactivo').count() + usuario_qs.filter(estatus_categoria_prod_usuario='Inactivo').count()
    
    # Logging básico
    logger.info(f"Total de categorías encontradas: {total_categorias}")
    logger.info(f"Categorías activas: {categorias_activas}, inactivas: {categorias_inactivas}")

    return render(request, 'ecommerce_app/categ_producto_config.html', {
        'categoria_producto': categ_producto_all,
        'user_info': user_info,
        'total_categorias': total_categorias,
        'categorias_activas': categorias_activas,
        'categorias_inactivas': categorias_inactivas
    })

@require_GET
def api_filtrar_categorias_producto(request):
    try:
        # Obtener parámetros de la solicitud
        nombre = request.GET.get('nombre', '').strip().lower()
        estatus = request.GET.get('estatus', '').strip()
        
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"api_filtrar_categorias_producto called - nombre='{nombre}' estatus='{estatus}' account_type='{account_type}' user='{getattr(current_user, 'id_empresa', getattr(current_user, 'id_usuario', None))}'")
        
        if account_type == 'empresa':
            categorias_query = categoria_producto_empresa.objects.filter(Q(id_empresa_fk=current_user) | Q(generico='s'))

            # Filtrar por nombre si se proporciona
            if nombre:
                categorias_query = categorias_query.filter(nombre_categoria_prod_empresa__icontains=nombre)

            # Filtrar por estatus si se proporciona y no es 'todos'
            if estatus and estatus.lower() != 'todos':
                categorias_query = categorias_query.filter(estatus_categoria_prod_empresa=estatus)

            # Convertir a lista de diccionarios para la respuesta JSON incluyendo campos auxiliares
            raw_list = list(categorias_query.values(
                'id_categoria_prod_empresa', 
                'nombre_categoria_prod_empresa', 
                'descripcion_categoria_prod_empresa', 
                'estatus_categoria_prod_empresa',
                'generico',
                'id_empresa_fk'
            ))

            categorias_list = []
            for c in raw_list:
                # editable sólo si la categoría pertenece a la empresa (id_empresa_fk igual) y no es genérica
                editable = False
                try:
                    editable = (c.get('generico') != 's') and (c.get('id_empresa_fk') == getattr(current_user, 'id_empresa', None))
                except Exception:
                    editable = False

                item = {
                    'id_categoria_prod_empresa': c.get('id_categoria_prod_empresa'),
                    'nombre_categoria_prod_empresa': c.get('nombre_categoria_prod_empresa'),
                    'descripcion_categoria_prod_empresa': c.get('descripcion_categoria_prod_empresa'),
                    'estatus_categoria_prod_empresa': c.get('estatus_categoria_prod_empresa'),
                    'editable': editable
                }
                categorias_list.append(item)

            logger.info(f"api_filtrar_categorias_producto -> empresa found {len(categorias_list)} categorias. sample: {[c.get('nombre_categoria_prod_empresa') for c in categorias_list[:5]]}")
        else:
            # Para usuarios: incluir categorías genéricas de empresa (generico='s') y las propias del usuario
            empresa_qs = categoria_producto_empresa.objects.filter(generico='s')
            usuario_qs = categoria_producto_usuario.objects.filter(id_usuario_fk=current_user)

            # Loguear conteos iniciales
            logger.info(f"api_filtrar_categorias_producto -> usuario initial counts - empresa:{empresa_qs.count()} usuario:{usuario_qs.count()}")

            # Aplicar filtro por nombre a ambas consultas si se proporciona
            if nombre:
                empresa_qs = empresa_qs.filter(nombre_categoria_prod_empresa__icontains=nombre)
                usuario_qs = usuario_qs.filter(nombre_categoria_prod_usuario__icontains=nombre)

            # Filtrar por estatus si se proporciona y no es 'todos'
            if estatus and estatus.lower() != 'todos':
                empresa_qs = empresa_qs.filter(estatus_categoria_prod_empresa=estatus)
                usuario_qs = usuario_qs.filter(estatus_categoria_prod_usuario=estatus)

            # Loguear conteos después de aplicar filtros
            logger.info(f"api_filtrar_categorias_producto -> usuario after-filter counts - empresa:{empresa_qs.count()} usuario:{usuario_qs.count()}")

            # Convertir a lista de diccionarios para la respuesta JSON combinada
            raw_empresa = list(empresa_qs.values(
                'id_categoria_prod_empresa', 
                'nombre_categoria_prod_empresa', 
                'descripcion_categoria_prod_empresa', 
                'estatus_categoria_prod_empresa'
            ))
            raw_usuario = list(usuario_qs.values(
                'id_categoria_prod_usuario', 
                'nombre_categoria_prod_usuario', 
                'descripcion_categoria_prod_usuario', 
                'estatus_categoria_prod_usuario'
            ))

            categorias_list = []
            # Las categorías de empresa (genéricas) no son editables por usuarios
            for c in raw_empresa:
                item = {
                    'id_categoria_prod_empresa': c.get('id_categoria_prod_empresa'),
                    'nombre_categoria_prod_empresa': c.get('nombre_categoria_prod_empresa'),
                    'descripcion_categoria_prod_empresa': c.get('descripcion_categoria_prod_empresa'),
                    'estatus_categoria_prod_empresa': c.get('estatus_categoria_prod_empresa'),
                    'editable': False
                }
                categorias_list.append(item)

            # Las categorías de usuario sí son editables por el usuario
            for c in raw_usuario:
                item = {
                    'id_categoria_prod_usuario': c.get('id_categoria_prod_usuario'),
                    'nombre_categoria_prod_usuario': c.get('nombre_categoria_prod_usuario'),
                    'descripcion_categoria_prod_usuario': c.get('descripcion_categoria_prod_usuario'),
                    'estatus_categoria_prod_usuario': c.get('estatus_categoria_prod_usuario'),
                    'editable': True
                }
                categorias_list.append(item)

            logger.info(f"api_filtrar_categorias_producto -> usuario found {len(categorias_list)} categorias. sample: {[c.get('nombre_categoria_prod_empresa') or c.get('nombre_categoria_prod_usuario') for c in categorias_list[:5]]}")
        
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




@require_POST
def api_agregar_atributo_categoria(request):
    """API para agregar un nuevo atributo a una categoría"""
    try:
        data = json.loads(request.body)
        categoria_id = data.get('categoria_id')
        nombre_atributo = data.get('nombre')
        tipo_dato = data.get('tipo_dato')
        opciones = data.get('opciones')
        obligatorio = data.get('obligatorio', False)
        descripcion = data.get('descripcion', '')
        
        if not all([categoria_id, nombre_atributo, tipo_dato]):
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Crear o obtener el atributo
        atributo, created = AtributoProducto.objects.get_or_create(
            nombre=nombre_atributo,
            defaults={
                'tipo_dato': tipo_dato,
                'opciones': opciones,
                'obligatorio': obligatorio,
                'descripcion': descripcion
            }
        )
        
        # Crear la asociación categoría-atributo
        if account_type == 'empresa':
            categoria_atributo, created = CategoriaAtributo.objects.get_or_create(
                atributo=atributo,
                categoria_empresa_id=categoria_id,
                defaults={'orden': 0}
            )
        else:
            categoria_atributo, created = CategoriaAtributo.objects.get_or_create(
                atributo=atributo,
                categoria_usuario_id=categoria_id,
                defaults={'orden': 0}
            )
        
        if not created:
            return JsonResponse({
                'success': False,
                'message': 'El atributo ya está asociado a esta categoría'
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Atributo agregado exitosamente',
            'atributo': {
                'id_categoria_atributo': categoria_atributo.id_categoria_atributo,
                'id_atributo': atributo.id_atributo,
                'nombre': atributo.nombre,
                'tipo_dato': atributo.tipo_dato,
                'opciones': atributo.opciones,
                'obligatorio': atributo.obligatorio,
                'descripcion': atributo.descripcion,
                'orden': categoria_atributo.orden
            }
        })
    except Exception as e:
        logger.error(f"Error al agregar atributo: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al agregar atributo: {str(e)}'
        })

@require_POST
def api_modificar_atributo_categoria(request):
    """API para modificar un atributo de una categoría"""
    try:
        data = json.loads(request.body)
        id_categoria_atributo = data.get('id_categoria_atributo')
        nombre_atributo = data.get('nombre')
        tipo_dato = data.get('tipo_dato')
        opciones = data.get('opciones')
        obligatorio = data.get('obligatorio', False)
        descripcion = data.get('descripcion', '')
        orden = data.get('orden', 0)
        
        if not all([id_categoria_atributo, nombre_atributo, tipo_dato]):
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        # Obtener la asociación categoría-atributo
        categoria_atributo = CategoriaAtributo.objects.get(
            id_categoria_atributo=id_categoria_atributo
        )
        
        # Actualizar el atributo
        atributo = categoria_atributo.atributo
        atributo.nombre = nombre_atributo
        atributo.tipo_dato = tipo_dato
        atributo.opciones = opciones
        atributo.obligatorio = obligatorio
        atributo.descripcion = descripcion
        atributo.save()
        
        # Actualizar el orden
        categoria_atributo.orden = orden
        categoria_atributo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Atributo modificado exitosamente'
        })
    except CategoriaAtributo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Atributo no encontrado'
        })
    except Exception as e:
        logger.error(f"Error al modificar atributo: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al modificar atributo: {str(e)}'
        })

@require_POST
def api_eliminar_atributo_categoria(request):
    """API para eliminar un atributo de una categoría"""
    try:
        data = json.loads(request.body)
        id_categoria_atributo = data.get('id_categoria_atributo')
        
        if not id_categoria_atributo:
            return JsonResponse({'error': 'ID de categoría-atributo requerido'}, status=400)
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        # Eliminar la asociación categoría-atributo
        categoria_atributo = CategoriaAtributo.objects.get(
            id_categoria_atributo=id_categoria_atributo
        )
        categoria_atributo.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Atributo eliminado exitosamente'
        })
    except CategoriaAtributo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Atributo no encontrado'
        })
    except Exception as e:
        logger.error(f"Error al eliminar atributo: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar atributo: {str(e)}'
        })

@require_GET
def api_filtrar_categorias_servicio(request):
    try:
        # Obtener parámetros de la solicitud
        nombre = request.GET.get('nombre', '').strip().lower()
        estatus = request.GET.get('estatus', '').strip()
        
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        account_type = request.session.get('account_type', 'usuario')
        
        if account_type == 'empresa':
            # Para empresas, incluir las categorías propias y las genéricas (generico='s')
            categorias_query = categoria_servicio_empresa.objects.filter(
                Q(id_empresa_fk=current_user) | Q(generico='s')
            )

            # Filtrar por nombre si se proporciona
            if nombre:
                categorias_query = categorias_query.filter(nombre_categoria_serv_empresa__icontains=nombre)

            # Filtrar por estatus si se proporciona y no es 'todos'
            if estatus and estatus.lower() != 'todos':
                categorias_query = categorias_query.filter(estatus_categoria_serv_empresa=estatus)

            # Convertir a lista de diccionarios para la respuesta JSON
            categorias_list = list(categorias_query.values(
                'id_categoria_serv_empresa',
                'nombre_categoria_serv_empresa',
                'descripcion_categoria_serv_empresa',
                'estatus_categoria_serv_empresa',
                'generico'
            ))
        else:
            # Para usuarios, incluir tanto categorías de servicio de usuario como categorías genéricas de empresa
            empresa_qs = categoria_servicio_empresa.objects.filter(generico='s')
            usuario_qs = categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user)

            # Aplicar filtro por nombre a ambas consultas si se proporciona
            if nombre:
                empresa_qs = empresa_qs.filter(nombre_categoria_serv_empresa__icontains=nombre)
                usuario_qs = usuario_qs.filter(nombre_categoria_serv_usuario__icontains=nombre)

            # Filtrar por estatus si se proporciona y no es 'todos'
            if estatus and estatus.lower() != 'todos':
                empresa_qs = empresa_qs.filter(estatus_categoria_serv_empresa=estatus)
                usuario_qs = usuario_qs.filter(estatus_categoria_serv_usuario=estatus)

            # Convertir a lista de diccionarios para la respuesta JSON combinada
            categorias_empresa = list(empresa_qs.values(
                'id_categoria_serv_empresa',
                'nombre_categoria_serv_empresa',
                'descripcion_categoria_serv_empresa',
                'estatus_categoria_serv_empresa',
                'generico'
            ))
            categorias_usuario = list(usuario_qs.values(
                'id_categoria_serv_usuario',
                'nombre_categoria_serv_usuario',
                'descripcion_categoria_serv_usuario',
                'estatus_categoria_serv_usuario'
            ))

            categorias_list = categorias_empresa + categorias_usuario
            logger.info(f"api_filtrar_categorias_servicio -> usuario found {len(categorias_list)} categorias.")
        return JsonResponse({
            'success': True,
            'categorias': categorias_list
        })
    except Exception as e:
        logger.error(f"Error al filtrar categorías de servicio: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al filtrar categorías de servicio: {str(e)}'
        })


@require_login
def eliminar_categoria_producto(request):
    if request.method == 'POST':
        try:
            # Obtener usuario actual y tipo de cuenta
            current_user = get_current_user(request)
            if not current_user:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no autenticado'
                })
            
            account_type = request.session.get('account_type', 'usuario')
            
            # Logging de todos los datos recibidos
            logger.info(f"Datos POST recibidos: {request.POST}")
            logger.info(f"Tipo de cuenta: {account_type}")
            
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
            
            # Determinar el modelo y campos según el tipo de cuenta
            if account_type == 'empresa':
                try:
                    categoria_obj = categoria_producto_empresa.objects.get(id_categoria_prod_empresa=id_categoria_int)
                    nombre_categoria = categoria_obj.nombre_categoria_prod_empresa
                    logger.info(f"Categoría de empresa encontrada: {nombre_categoria}")
                    
                    # Verificar si hay productos asociados
                    productos_asociados = producto_empresa.objects.filter(id_categoria_prod_fk=categoria_obj).exists()
                    if productos_asociados:
                        logger.error(f"No se puede eliminar la categoría {nombre_categoria} porque tiene productos asociados")
                        return JsonResponse({
                            'success': False,
                            'message': f'No se puede eliminar la categoría "{nombre_categoria}" porque tiene productos asociados'
                        })
                    
                    categoria_obj.delete()
                    logger.info(f"Categoría de empresa eliminada exitosamente: {nombre_categoria}")
                    
                except categoria_producto_empresa.DoesNotExist:
                    logger.error(f"Categoría de empresa no encontrada con ID {id_categoria}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Categoría no encontrada'
                    })
            else:
                try:
                    categoria_obj = categoria_producto_usuario.objects.get(id_categoria_prod_usuario=id_categoria_int)
                    nombre_categoria = categoria_obj.nombre_categoria_prod_usuario
                    logger.info(f"Categoría de usuario encontrada: {nombre_categoria}")
                    
                    # Verificar si hay productos asociados (si existe modelo producto_usuario)
                    # Por ahora asumimos que no hay productos de usuario, pero se puede agregar después
                    
                    categoria_obj.delete()
                    logger.info(f"Categoría de usuario eliminada exitosamente: {nombre_categoria}")
                    
                except categoria_producto_usuario.DoesNotExist:
                    logger.error(f"Categoría de usuario no encontrada con ID {id_categoria}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Categoría no encontrada'
                    })
            
            return JsonResponse({
                'success': True,
                'message': f'Categoría "{nombre_categoria}" eliminada exitosamente'
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


@require_login
def editar_categoria_producto(request):
    if request.method == 'POST':
        try:
            # Obtener usuario actual y tipo de cuenta
            current_user = get_current_user(request)
            if not current_user:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no autenticado'
                })
            
            account_type = request.session.get('account_type', 'usuario')
            
            id_categoria = request.POST.get('id_categoria')
            logger.info(f"Intentando editar categoría con ID: {id_categoria}, Tipo de cuenta: {account_type}")
            
            if not id_categoria:
                logger.error("No se proporcionó ID de categoría")
                return JsonResponse({
                    'success': False,
                    'message': 'ID de categoría no proporcionado'
                })
            
            # Determinar el modelo y campos según el tipo de cuenta
            if account_type == 'empresa':
                try:
                    categoria_obj = categoria_producto_empresa.objects.get(id_categoria_prod_empresa=id_categoria)
                    
                    # Actualizar los datos
                    categoria_obj.nombre_categoria_prod_empresa = request.POST.get('nombre_categoria')
                    categoria_obj.descripcion_categoria_prod_empresa = request.POST.get('descripcion_categoria')
                    categoria_obj.estatus_categoria_prod_empresa = request.POST.get('estatus_categoria')
                    
                    categoria_obj.save()
                    logger.info(f"Categoría de empresa actualizada exitosamente: {categoria_obj.nombre_categoria_prod_empresa}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Categoría "{categoria_obj.nombre_categoria_prod_empresa}" actualizada exitosamente'
                    })
                    
                except categoria_producto_empresa.DoesNotExist:
                    logger.error(f"Categoría de empresa no encontrada con ID {id_categoria}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Categoría no encontrada'
                    })
            else:
                try:
                    categoria_obj = categoria_producto_usuario.objects.get(id_categoria_prod_usuario=id_categoria)
                    
                    # Actualizar los datos
                    categoria_obj.nombre_categoria_prod_usuario = request.POST.get('nombre_categoria')
                    categoria_obj.descripcion_categoria_prod_usuario = request.POST.get('descripcion_categoria')
                    categoria_obj.estatus_categoria_prod_usuario = request.POST.get('estatus_categoria')
                    
                    categoria_obj.save()
                    logger.info(f"Categoría de usuario actualizada exitosamente: {categoria_obj.nombre_categoria_prod_usuario}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Categoría "{categoria_obj.nombre_categoria_prod_usuario}" actualizada exitosamente'
                    })
                    
                except categoria_producto_usuario.DoesNotExist:
                    logger.error(f"Categoría de usuario no encontrada con ID {id_categoria}")
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


@require_login
def obtener_atributos_categoria(request):
    """Vista AJAX para obtener los atributos asociados a una categoría específica"""
    if request.method == 'GET':
        try:
            # Obtener usuario actual y tipo de cuenta
            current_user = get_current_user(request)
            if not current_user:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no autenticado'
                })
            
            # We no longer rely on session account_type to locate attributes because
            # the product category select can contain mixed categories (empresa + usuario).
            # Try to detect the category object first in empresa table, then in usuario.
            id_categoria = request.GET.get('id_categoria')

            if not id_categoria:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de categoría requerido'
                })

            logger.info(f"obtener_atributos_categoria called with id_categoria={id_categoria} by user={getattr(current_user, 'id_usuario', getattr(current_user, 'id_empresa', None))}")

            atributos = []

            # If frontend provides explicit tipo (empresa|usuario), prefer it to avoid ambiguity
            tipo_param = request.GET.get('tipo')
            if tipo_param:
                logger.info(f"Tipo param recibido: {tipo_param}")

            # Try empresa category first (or only if tipo indicates empresa)
            categoria_empresa_obj = None
            try:
                if not tipo_param or tipo_param == 'empresa':
                    categoria_empresa_obj = categoria_producto_empresa.objects.filter(id_categoria_prod_empresa=id_categoria).first()
            except Exception:
                categoria_empresa_obj = None

            if categoria_empresa_obj:
                logger.info(f"Categoria encontrada en empresa: id={categoria_empresa_obj.id_categoria_prod_empresa}")
                categoria_atributos = CategoriaAtributo.objects.filter(
                    categoria_empresa=categoria_empresa_obj
                ).select_related('atributo')

                for cat_attr in categoria_atributos:
                    atributos.append({
                        'id_categoria_atributo': cat_attr.id_categoria_atributo,
                        'id_atributo': cat_attr.atributo.id_atributo,
                        'nombre': cat_attr.atributo.nombre,
                        'tipo_dato': cat_attr.atributo.tipo_dato,
                        'obligatorio': cat_attr.atributo.obligatorio,
                        'descripcion': cat_attr.atributo.descripcion,
                        'opciones': cat_attr.atributo.opciones,
                        'orden': cat_attr.orden
                    })
            else:
                logger.info(f"Categoria no encontrada en empresa, buscando en usuario con id {id_categoria}")
                # Fallback to usuario category (or only if tipo indicates usuario)
                categoria_usuario_obj = None
                try:
                    if not tipo_param or tipo_param == 'usuario':
                        categoria_usuario_obj = categoria_producto_usuario.objects.filter(id_categoria_prod_usuario=id_categoria).first()
                except Exception:
                    categoria_usuario_obj = None

                if categoria_usuario_obj:
                    logger.info(f"Categoria encontrada en usuario: id={categoria_usuario_obj.id_categoria_prod_usuario}")
                    categoria_atributos = CategoriaAtributo.objects.filter(
                        categoria_usuario=categoria_usuario_obj
                    ).select_related('atributo')

                    for cat_attr in categoria_atributos:
                        atributos.append({
                            'id_categoria_atributo': cat_attr.id_categoria_atributo,
                            'id_atributo': cat_attr.atributo.id_atributo,
                            'nombre': cat_attr.atributo.nombre,
                            'tipo_dato': cat_attr.atributo.tipo_dato,
                            'obligatorio': cat_attr.atributo.obligatorio,
                            'descripcion': cat_attr.atributo.descripcion,
                            'opciones': cat_attr.atributo.opciones,
                            'orden': cat_attr.orden
                        })
                else:
                    # No category object found — log and return empty list (compatible with callers)
                    logger.info(f"No se encontró categoría con id={id_categoria} en ninguna tabla")
                    return JsonResponse({
                        'success': True,
                        'atributos': []
                    })

            logger.info(f"Retornando {len(atributos)} atributos para categoria id={id_categoria}")
            
            # Ordenar atributos por orden
            atributos.sort(key=lambda x: x['orden'] if x['orden'] else 999)
            
            return JsonResponse({
                'success': True,
                'atributos': atributos
            })
            
        except Exception as e:
            logger.error(f"Error al obtener atributos de categoría: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al obtener atributos: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })


@require_login
def editar_categoria_servicio(request):
    if request.method == 'POST':
        try:
            # Obtener usuario actual y tipo de cuenta
            current_user = get_current_user(request)
            if not current_user:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no autenticado'
                })
            
            account_type = request.session.get('account_type', 'usuario')
            
            id_categoria = request.POST.get('id_categoria')
            logger.info(f"Intentando editar categoría de servicio con ID: {id_categoria}, Tipo de cuenta: {account_type}")
            
            if not id_categoria:
                logger.error("No se proporcionó ID de categoría de servicio")
                return JsonResponse({
                    'success': False,
                    'message': 'ID de categoría de servicio no proporcionado'
                })
            
            # Determinar el modelo y campos según el tipo de cuenta
            if account_type == 'empresa':
                try:
                    categoria_obj = categoria_servicio_empresa.objects.get(id_categoria_serv_empresa=id_categoria)
                    
                    # Actualizar los datos
                    categoria_obj.nombre_categoria_serv_empresa = request.POST.get('nombre_categoria')
                    categoria_obj.descripcion_categoria_serv_empresa = request.POST.get('descripcion_categoria')
                    categoria_obj.estatus_categoria_serv_empresa = request.POST.get('estatus_categoria')
                    
                    categoria_obj.save()
                    logger.info(f"Categoría de servicio de empresa actualizada exitosamente: {categoria_obj.nombre_categoria_serv_empresa}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Categoría de servicio "{categoria_obj.nombre_categoria_serv_empresa}" actualizada exitosamente'
                    })
                    
                except categoria_servicio_empresa.DoesNotExist:
                    logger.error(f"Categoría de servicio de empresa no encontrada con ID {id_categoria}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Categoría de servicio no encontrada'
                    })
            else:
                try:
                    categoria_obj = categoria_servicio_usuario.objects.get(id_categoria_serv_usuario=id_categoria)
                    
                    # Actualizar los datos
                    categoria_obj.nombre_categoria_serv_usuario = request.POST.get('nombre_categoria')
                    categoria_obj.descripcion_categoria_serv_usuario = request.POST.get('descripcion_categoria')
                    categoria_obj.estatus_categoria_serv_usuario = request.POST.get('estatus_categoria')
                    
                    categoria_obj.save()
                    logger.info(f"Categoría de servicio de usuario actualizada exitosamente: {categoria_obj.nombre_categoria_serv_usuario}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Categoría de servicio "{categoria_obj.nombre_categoria_serv_usuario}" actualizada exitosamente'
                    })
                    
                except categoria_servicio_usuario.DoesNotExist:
                    logger.error(f"Categoría de servicio de usuario no encontrada con ID {id_categoria}")
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














@require_login
def categ_servicio_config_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, usar categorías de empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        categ_servicio_all = categoria_servicio_empresa.objects.filter(Q(id_empresa_fk=empresa_obj) | Q(generico='s')).order_by('-fecha_creacion_categ_serv_empresa')
    else:
        # Para usuarios, usar categorías de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        categ_servicio_all = categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user).order_by('-fecha_creacion_categ_serv_usuario')
    
    # Calcular estadísticas
    total_categorias = categ_servicio_all.count()
    
    if account_type == 'empresa':
        categorias_activas = categ_servicio_all.filter(estatus_categoria_serv_empresa='Activo').count()
        categorias_inactivas = categ_servicio_all.filter(estatus_categoria_serv_empresa='Inactivo').count()
    else:
        categorias_activas = categ_servicio_all.filter(estatus_categoria_serv_usuario='Activo').count()
        categorias_inactivas = categ_servicio_all.filter(estatus_categoria_serv_usuario='Inactivo').count()
    
    # Logging básico
    logger.info(f"Total de categorías de servicio encontradas: {total_categorias}")
    logger.info(f"Categorías de servicio activas: {categorias_activas}, inactivas: {categorias_inactivas}")

    return render(request, 'ecommerce_app/categ_servicio_config.html', {
        'categoria_servicio': categ_servicio_all,
        'user_info': user_info,
        'total_categorias': total_categorias,
        'categorias_activas': categorias_activas,
        'categorias_inactivas': categorias_inactivas
    })



@require_login
def eliminar_categoria_servicio_funcion(request):
    if request.method == 'POST':
        try:
            # Obtener usuario actual y tipo de cuenta
            current_user = get_current_user(request)
            if not current_user:
                return JsonResponse({
                    'success': False,
                    'message': 'Usuario no autenticado'
                })
            
            account_type = request.session.get('account_type', 'usuario')
            
            id_categoria_servicio = request.POST.get('id_categoriaservicio')
            logger.info(f"Intentando eliminar categoría con ID: {id_categoria_servicio}, Tipo de cuenta: {account_type}")
            
            if not id_categoria_servicio:
                logger.error("No se proporcionó ID de categoría")
                return JsonResponse({'success': False, 'message': 'ID de categoría no proporcionado'})
            
            # Determinar el modelo y campos según el tipo de cuenta
            if account_type == 'empresa':
                try:
                    categoria_obj = categoria_servicio_empresa.objects.get(id_categoria_serv_empresa=id_categoria_servicio)
                    nombre_categoria_servicio = categoria_obj.nombre_categoria_serv_empresa
                    
                    # Verificar si hay servicios asociados
                    servicios_asociados = servicio_empresa.objects.filter(id_categoria_servicios_fk=categoria_obj).exists()
                    if servicios_asociados:
                        logger.error(f"No se puede eliminar la categoría {nombre_categoria_servicio} porque tiene servicios asociados")
                        return JsonResponse({'success': False, 'message': f'No se puede eliminar la categoría "{nombre_categoria_servicio}" porque tiene servicios asociados'})
                    
                    categoria_obj.delete()
                    logger.info(f"Categoría de empresa eliminada exitosamente: {nombre_categoria_servicio}")
                    return JsonResponse({'success': True, 'message': f'Categoría "{nombre_categoria_servicio}" eliminada exitosamente'})
                    
                except categoria_servicio_empresa.DoesNotExist:
                    logger.error(f"Categoría de servicio de empresa no encontrada con ID {id_categoria_servicio}")
                    return JsonResponse({'success': False, 'message': 'Categoría no encontrada'})
            else:
                try:
                    categoria_obj = categoria_servicio_usuario.objects.get(id_categoria_serv_usuario=id_categoria_servicio)
                    nombre_categoria_servicio = categoria_obj.nombre_categoria_serv_usuario
                    
                    # Para usuarios individuales, no hay modelo de servicios asociados, se puede eliminar directamente
                    categoria_obj.delete()
                    logger.info(f"Categoría de usuario eliminada exitosamente: {nombre_categoria_servicio}")
                    return JsonResponse({'success': True, 'message': f'Categoría "{nombre_categoria_servicio}" eliminada exitosamente'})
                    
                except categoria_servicio_usuario.DoesNotExist:
                    logger.error(f"Categoría de servicio de usuario no encontrada con ID {id_categoria_servicio}")
                    return JsonResponse({'success': False, 'message': 'Categoría no encontrada'})
            
        except Exception as e:
            logger.error(f"Error al eliminar la categoría: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error al eliminar la categoría: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@require_login
def producto_config_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, current_user ya es la empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        # Obtenemos los productos de la empresa actual
        productos_all = producto_empresa.objects.filter(id_empresa_fk=empresa_obj)
        # También obtenemos las relaciones producto_sucursal para tener acceso al estatus
        producto_sucursal_all = producto_sucursal.objects.select_related('id_producto_fk').filter(id_producto_fk__id_empresa_fk=empresa_obj)
        # Incluir categorías propias de la empresa y categorías genéricas (generico='s')
        categoria_producto_all = categoria_producto_empresa.objects.filter(
            Q(id_empresa_fk=empresa_obj) | Q(generico='s')
        )
        
        # Calcular estadísticas de productos para empresa
        # Para empresas, contamos productos únicos que tienen al menos una sucursal con ese estatus
        total_productos = productos_all.count()
        # Productos que tienen al menos una sucursal activa
        productos_activos = productos_all.filter(sucursales_producto__estatus_producto_sucursal='Activo').distinct().count()
        # Productos que solo tienen sucursales inactivas o no tienen sucursales
        productos_con_sucursal = productos_all.filter(sucursales_producto__isnull=False).distinct()
        productos_inactivos = productos_all.exclude(sucursales_producto__estatus_producto_sucursal='Activo').distinct().count()
        
        # Agregar la primera imagen de cada producto y las sucursales asignadas
        productos_con_imagenes = []
        for prod in productos_all:
            primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
            prod.primera_imagen_empresa = primera_imagen
            
            # Obtener sucursales donde está asignado este producto
            sucursales_asignadas = producto_sucursal.objects.filter(id_producto_fk=prod).select_related('id_sucursal_fk')
            prod.sucursales_asignadas = [ps.id_sucursal_fk for ps in sucursales_asignadas]
            
            productos_con_imagenes.append(prod)
        # Obtener sucursales de la empresa para facilitar selección en la vista de productos
        sucursales_empresa_qs = sucursal.objects.filter(id_empresa_fk=empresa_obj).values('id_sucursal', 'nombre_sucursal')
        sucursales_empresa_list = list(sucursales_empresa_qs)
    else:
        # Para usuarios, usar productos de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        # Obtenemos los productos del usuario actual
        productos_all = producto_usuario.objects.filter(id_usuario_fk=current_user)
        producto_sucursal_all = []  # Los usuarios no tienen sucursales
        # Incluir categorías propias del usuario y categorías genéricas (generico='s')
        categoria_producto_all = categoria_producto_usuario.objects.filter(
            Q(id_usuario_fk=current_user) | Q(generico='s')
        )
        
        # Calcular estadísticas de productos
        total_productos = productos_all.count()
        productos_activos = productos_all.filter(estatus_producto_usuario='Activo').count()
        productos_inactivos = productos_all.filter(estatus_producto_usuario='Inactivo').count()
        
        # Agregar la primera imagen de cada producto
        productos_con_imagenes = []
        for prod in productos_all:
            primera_imagen = imagen_producto_usuario.objects.filter(id_producto_fk=prod).first()
            prod.primera_imagen = primera_imagen
            productos_con_imagenes.append(prod)
    
    return render(request, 'ecommerce_app/producto_config.html', {
        'producto_sucursal_all': productos_con_imagenes,  # Mantenemos el mismo nombre de variable para no cambiar la plantilla
        'producto_sucursal_relaciones': producto_sucursal_all,  # Añadimos las relaciones
        'categoria_producto_all': categoria_producto_all,
        'user_info': user_info,
        'total_productos': total_productos,
        'productos_activos': productos_activos,
        'productos_inactivos': productos_inactivos
        , 'sucursales_empresa': sucursales_empresa_list if account_type == 'empresa' else []
    })



@require_login
def servicio_config_funcion(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    if account_type == 'empresa':
        # Para empresas, current_user ya es la empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        # Filtrar servicios por empresa actual
        servicios_all = servicio_empresa.objects.filter(id_empresa_fk=empresa_obj)
        # Incluir tanto las categorías propias de la empresa como las genéricas (generico='s')
        categoria_servicio_all = categoria_servicio_empresa.objects.filter(Q(id_empresa_fk=empresa_obj) | Q(generico='s'))

        # Agregar la primera imagen de cada servicio y las sucursales asignadas
        servicios_con_imagenes = []
        for serv in servicios_all:
            primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=serv).first()
            serv.primera_imagen = primera_imagen

            # Obtener sucursales donde está asignado este servicio
            sucursales_asignadas = servicio_sucursal.objects.filter(id_servicio_fk=serv).select_related('id_sucursal_fk')
            serv.sucursales_asignadas = [ss.id_sucursal_fk for ss in sucursales_asignadas]

            servicios_con_imagenes.append(serv)
    else:
        # Para usuarios, usar servicios de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        # Filtrar servicios por usuario actual
        servicios_all = servicio_usuario.objects.filter(id_usuario_fk=current_user)
        # Incluir tanto las categorías propias del usuario como las categorías genéricas (si existen)
        categoria_servicio_all = categoria_servicio_usuario.objects.filter(Q(id_usuario_fk=current_user) | Q(generico='s'))

        # Agregar la primera imagen de cada servicio
        servicios_con_imagenes = []
        for serv in servicios_all:
            primera_imagen = imagen_servicio_usuario.objects.filter(id_servicio_fk=serv).first()
            serv.primera_imagen = primera_imagen
            servicios_con_imagenes.append(serv)
    
    # Calcular estadísticas de servicios en el servidor para evitar discrepancias
    try:
        total_servicios = len(servicios_con_imagenes)
        servicios_activos = 0
        servicios_inactivos = 0

        # Para cada servicio, intentar inferir su estado a partir de asignaciones en sucursales
        for serv in servicios_con_imagenes:
            try:
                # Buscar asignaciones en sucursales relacionadas a este servicio
                asignaciones = servicio_sucursal.objects.filter(id_servicio_fk=serv)
                if asignaciones.exists():
                    # Si alguna asignación está activa, consideramos el servicio como activo
                    if asignaciones.filter(estatus_servicio_sucursal__iexact='Activo').exists():
                        servicios_activos += 1
                    else:
                        # Ninguna asignación activa => marcamos como inactivo
                        servicios_inactivos += 1
                else:
                    # Si no hay asignaciones en sucursales, asumimos que el servicio está activo por defecto
                    servicios_activos += 1
            except Exception:
                # En caso de error al inspeccionar asignaciones, no bloqueamos la vista: contar como inactivo
                servicios_inactivos += 1
    except Exception:
        total_servicios = len(servicios_con_imagenes)
        servicios_activos = total_servicios
        servicios_inactivos = 0

    return render(request, 'ecommerce_app/servicio_config.html', {
        'servicio_all': servicios_con_imagenes,
        'categoria_servicio_all': categoria_servicio_all,
        'user_info': user_info,
        'total_servicios': total_servicios,
        'servicios_activos': servicios_activos,
        'servicios_inactivos': servicios_inactivos
    })



def editar_producto(request):
    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos para editar producto: {request.POST}")
            
            # Buscar ID de producto según el tipo de usuario
            id_producto_empresa = request.POST.get('id_producto_empresa')
            id_producto_usuario = request.POST.get('id_producto_usuario')
            id_producto = request.POST.get('id_producto')
            
            logger.info(f"IDs recibidos - empresa: {id_producto_empresa}, usuario: {id_producto_usuario}, genérico: {id_producto}")
            
            # Determinar si es producto de empresa o usuario
            if id_producto_empresa or (id_producto and not id_producto_usuario):
                # Es un producto de empresa
                producto_id = id_producto_empresa or id_producto
                try:
                    producto_obj = producto_empresa.objects.get(id_producto_empresa=producto_id)
                    
                    # Actualizar los datos básicos
                    producto_obj.nombre_producto_empresa = request.POST.get('nombre_producto_empresa')
                    producto_obj.descripcion_producto_empresa = request.POST.get('descripcion_producto_empresa')
                    producto_obj.caracteristicas_generales_empresa = request.POST.get('caracteristicas_generales')
                    
                    # Actualizar categoría si se proporciona
                    categoria_id = request.POST.get('categoria_producto')
                    if categoria_id:
                        try:
                            categoria_obj = categoria_producto_empresa.objects.get(id_categoria_prod_empresa=categoria_id)
                            
                            # Detectar si cambió la categoría
                            categoria_cambio = producto_obj.id_categoria_prod_fk != categoria_obj
                            
                            if categoria_cambio:
                                # Eliminar todos los valores de atributos antiguos asociados a la categoría anterior
                                from .models import ValorAtributoProducto
                                valores_eliminados = ValorAtributoProducto.objects.filter(
                                    producto_empresa=producto_obj
                                ).delete()
                                logger.info(f"Categoría cambiada. Eliminados {valores_eliminados[0]} valores de atributos antiguos")
                            
                            producto_obj.id_categoria_prod_fk = categoria_obj
                        except categoria_producto_empresa.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'message': 'Categoría no encontrada'
                            })
                    
                    # Manejar múltiples imágenes si se proporcionan
                    imagenes_producto = request.FILES.getlist('imagenes_producto')
                    if imagenes_producto:
                        # Contar imágenes existentes
                        imagenes_existentes = imagen_producto_empresa.objects.filter(id_producto_fk=producto_obj).count()
                        
                        # Validar número máximo de imágenes (existentes + nuevas)
                        if imagenes_existentes + len(imagenes_producto) > 5:
                            return JsonResponse({
                                'success': False,
                                'message': f'Máximo 5 imágenes permitidas. Actualmente tienes {imagenes_existentes} imágenes. Puedes agregar máximo {5 - imagenes_existentes} más.'
                            })
                        
                        # Agregar nuevas imágenes sin eliminar las existentes
                        for imagen in imagenes_producto:
                            imagen_producto_empresa.objects.create(
                                id_producto_fk=producto_obj,
                                ruta_imagen_producto_empresa=imagen
                            )
                    
                    producto_obj.save()
                    logger.info(f"Producto de empresa actualizado exitosamente: {producto_obj.nombre_producto_empresa}")
                    
                    # Procesar atributos EAV dinámicos
                    from .models import AtributoProducto, ValorAtributoProducto
                    from .eav_helpers import EAVHelper
                    
                    for key, value in request.POST.items():
                        if key.startswith('atributo_'):
                            try:
                                atributo_id = key.replace('atributo_', '')
                                atributo = AtributoProducto.objects.get(id_atributo=atributo_id)
                                
                                # Si el valor está vacío, eliminar el valor existente si existe
                                if not value or not value.strip():
                                    ValorAtributoProducto.objects.filter(
                                        producto_empresa=producto_obj,
                                        atributo=atributo
                                    ).delete()
                                    logger.info(f"Atributo {atributo.nombre} eliminado (valor vacío)")
                                else:
                                    # Guardar o actualizar el valor
                                    EAVHelper.asignar_valor_producto_empresa(producto_obj, atributo, value)
                                    logger.info(f"Atributo {atributo.nombre} actualizado con valor: {value}")
                            except AtributoProducto.DoesNotExist:
                                logger.warning(f"Atributo con ID {atributo_id} no encontrado")
                            except Exception as e:
                                logger.error(f"Error al guardar atributo {key}: {str(e)}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Producto actualizado exitosamente'
                    })
                    
                except producto_empresa.DoesNotExist:
                    logger.error(f"Producto de empresa no encontrado con ID: {producto_id}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado'
                    })
            
            elif id_producto_usuario:
                # Es un producto de usuario
                try:
                    producto_obj = producto_usuario.objects.get(id_producto_usuario=id_producto_usuario)
                    
                    # Actualizar los datos básicos
                    producto_obj.nombre_producto_usuario = request.POST.get('nombre_producto_usuario')
                    producto_obj.descripcion_producto_usuario = request.POST.get('descripcion_producto_usuario')
                    producto_obj.caracteristicas_generales_usuario = request.POST.get('caracteristicas_generales')
                    
                    # Actualizar campos adicionales para usuarios
                    producto_obj.stock_producto_usuario = request.POST.get('stock_producto_usuario', 0)
                    producto_obj.precio_producto_usuario = request.POST.get('precio_producto_usuario', 0)
                    producto_obj.condicion_producto_usuario = request.POST.get('condicion_producto_usuario', 'Nuevo')
                    producto_obj.estatus_producto_usuario = request.POST.get('estatus_producto_usuario', 'Activo')
                    
                    # Actualizar coordenadas de entrega
                    latitud = request.POST.get('latitud_entrega_producto')
                    longitud = request.POST.get('longitud_entrega_producto')
                    
                    if latitud and latitud != 'None' and latitud.strip():
                        try:
                            producto_obj.latitud_entrega_producto = float(latitud)
                        except (ValueError, TypeError):
                            producto_obj.latitud_entrega_producto = None
                    else:
                        producto_obj.latitud_entrega_producto = None
                        
                    if longitud and longitud != 'None' and longitud.strip():
                        try:
                            producto_obj.longitud_entrega_producto = float(longitud)
                        except (ValueError, TypeError):
                            producto_obj.longitud_entrega_producto = None
                    else:
                        producto_obj.longitud_entrega_producto = None
                    
                    # Actualizar categoría si se proporciona
                    categoria_id = request.POST.get('categoria_producto')
                    if categoria_id:
                        try:
                            categoria_obj = categoria_producto_usuario.objects.get(id_categoria_prod_usuario=categoria_id)
                            
                            # Detectar si cambió la categoría
                            categoria_cambio = producto_obj.id_categoria_prod_fk != categoria_obj
                            
                            if categoria_cambio:
                                # Eliminar todos los valores de atributos antiguos asociados a la categoría anterior
                                from .models import ValorAtributoProducto
                                valores_eliminados = ValorAtributoProducto.objects.filter(
                                    producto_usuario=producto_obj
                                ).delete()
                                logger.info(f"Categoría cambiada. Eliminados {valores_eliminados[0]} valores de atributos antiguos")
                            
                            producto_obj.id_categoria_prod_fk = categoria_obj
                        except categoria_producto_usuario.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'message': 'Categoría no encontrada'
                            })
                    
                    # Manejar múltiples imágenes si se proporcionan
                    imagenes_producto = request.FILES.getlist('imagenes_producto')
                    if imagenes_producto:
                        # Contar imágenes existentes
                        imagenes_existentes = imagen_producto_usuario.objects.filter(id_producto_fk=producto_obj).count()
                        
                        # Validar número máximo de imágenes (existentes + nuevas)
                        if imagenes_existentes + len(imagenes_producto) > 5:
                            return JsonResponse({
                                'success': False,
                                'message': f'Máximo 5 imágenes permitidas. Actualmente tienes {imagenes_existentes} imágenes. Puedes agregar máximo {5 - imagenes_existentes} más.'
                            })
                        
                        # Agregar nuevas imágenes sin eliminar las existentes
                        for imagen in imagenes_producto:
                            imagen_producto_usuario.objects.create(
                                id_producto_fk=producto_obj,
                                ruta_imagen_producto_usuario=imagen
                            )
                    
                    producto_obj.save()
                    logger.info(f"Producto de usuario actualizado exitosamente: {producto_obj.nombre_producto_usuario}")
                    
                    # Procesar atributos EAV dinámicos
                    from .models import AtributoProducto, ValorAtributoProducto
                    from .eav_helpers import EAVHelper
                    
                    for key, value in request.POST.items():
                        if key.startswith('atributo_'):
                            try:
                                atributo_id = key.replace('atributo_', '')
                                atributo = AtributoProducto.objects.get(id_atributo=atributo_id)
                                
                                # Si el valor está vacío, eliminar el valor existente si existe
                                if not value or not value.strip():
                                    ValorAtributoProducto.objects.filter(
                                        producto_usuario=producto_obj,
                                        atributo=atributo
                                    ).delete()
                                    logger.info(f"Atributo {atributo.nombre} eliminado (valor vacío)")
                                else:
                                    # Guardar o actualizar el valor
                                    EAVHelper.asignar_valor_producto_usuario(producto_obj, atributo, value)
                                    logger.info(f"Atributo {atributo.nombre} actualizado con valor: {value}")
                            except AtributoProducto.DoesNotExist:
                                logger.warning(f"Atributo con ID {atributo_id} no encontrado")
                            except Exception as e:
                                logger.error(f"Error al guardar atributo {key}: {str(e)}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Producto actualizado exitosamente'
                    })
                    
                except producto_usuario.DoesNotExist:
                    logger.error(f"Producto de usuario no encontrado con ID: {id_producto_usuario}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado'
                    })
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de producto no proporcionado'
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

@require_login
def eliminar_producto(request):
    if request.method == 'POST':
        try:
            # Buscar ID de producto según el tipo de usuario
            id_producto_empresa = request.POST.get('id_producto_empresa')
            id_producto_usuario = request.POST.get('id_producto_usuario')
            id_producto = request.POST.get('id_producto')
            
            logger.info(f"Intentando eliminar producto - Empresa: {id_producto_empresa}, Usuario: {id_producto_usuario}, Genérico: {id_producto}")
            
            # Determinar qué tipo de producto eliminar
            if id_producto_empresa:
                try:
                    producto_obj = producto_empresa.objects.get(id_producto_empresa=id_producto_empresa)
                    nombre_producto = producto_obj.nombre_producto_empresa
                    
                    # Verificar si hay productos_sucursal asociados
                    productos_sucursal_asociados = producto_sucursal.objects.filter(id_producto_fk=producto_obj).exists()
                    if productos_sucursal_asociados:
                        logger.error(f"No se puede eliminar el producto {nombre_producto} porque tiene registros en sucursales")
                        return JsonResponse({
                            'success': False,
                            'message': f'No se puede eliminar el producto "{nombre_producto}" porque tiene registros en sucursales'
                        })
                    
                    producto_obj.delete()
                    logger.info(f"Producto de empresa eliminado exitosamente: {nombre_producto}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Producto "{nombre_producto}" eliminado exitosamente'
                    })
                    
                except producto_empresa.DoesNotExist:
                    logger.error(f"Producto de empresa no encontrado con ID {id_producto_empresa}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado'
                    })
                    
            elif id_producto_usuario:
                try:
                    producto_obj = producto_usuario.objects.get(id_producto_usuario=id_producto_usuario)
                    nombre_producto = producto_obj.nombre_producto_usuario
                    
                    producto_obj.delete()
                    logger.info(f"Producto de usuario eliminado exitosamente: {nombre_producto}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Producto "{nombre_producto}" eliminado exitosamente'
                    })
                    
                except producto_usuario.DoesNotExist:
                    logger.error(f"Producto de usuario no encontrado con ID {id_producto_usuario}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado'
                    })
                    
            elif id_producto:
                # Fallback para compatibilidad - intentar primero empresa, luego usuario
                try:
                    producto_obj = producto_empresa.objects.get(id_producto_empresa=id_producto)
                    nombre_producto = producto_obj.nombre_producto_empresa
                    
                    # Verificar si hay productos_sucursal asociados
                    productos_sucursal_asociados = producto_sucursal.objects.filter(id_producto_fk=producto_obj).exists()
                    if productos_sucursal_asociados:
                        logger.error(f"No se puede eliminar el producto {nombre_producto} porque tiene registros en sucursales")
                        return JsonResponse({
                            'success': False,
                            'message': f'No se puede eliminar el producto "{nombre_producto}" porque tiene registros en sucursales'
                        })
                    
                    producto_obj.delete()
                    logger.info(f"Producto de empresa eliminado exitosamente: {nombre_producto}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Producto "{nombre_producto}" eliminado exitosamente'
                    })
                    
                except producto_empresa.DoesNotExist:
                    # Si no es de empresa, intentar con usuario
                    try:
                        producto_obj = producto_usuario.objects.get(id_producto_usuario=id_producto)
                        nombre_producto = producto_obj.nombre_producto_usuario
                        
                        producto_obj.delete()
                        logger.info(f"Producto de usuario eliminado exitosamente: {nombre_producto}")
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'Producto "{nombre_producto}" eliminado exitosamente'
                        })
                        
                    except producto_usuario.DoesNotExist:
                        logger.error(f"Producto no encontrado con ID {id_producto}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Producto no encontrado'
                        })
            else:
                logger.error("No se proporcionó ID de producto")
                return JsonResponse({
                    'success': False,
                    'message': 'ID de producto no proporcionado'
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
            account_type = request.session.get('account_type', 'usuario')
            
            # Buscar empresa asociada para usuarios
            empresa_nombre = None
            if account_type == 'usuario':
                try:
                    empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                    if empresa_obj:
                        empresa_nombre = empresa_obj.nombre_empresa
                except Exception as e:
                    empresa_nombre = None
            elif account_type == 'empresa':
                empresa_nombre = current_user.nombre_empresa
            
            user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
            # Para el index, usar siempre el avatar por defecto del chatbot (chatbot general del ecommerce)
            user_info['avatar_chatbot'] = 'avatars/Cartoon Style Robot.jpg'
    
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
            account_type = request.session.get('account_type', 'usuario')
            
            if account_type == 'empresa':
                return JsonResponse({
                    'success': True,
                    'user_name': current_user.nombre_empresa,
                    'user_email': current_user.correo_empresa,
                    'user_type': current_user.rol_empresa
                })
            else:
                return JsonResponse({
                    'success': True,
                    'user_name': current_user.nombre_usuario,
                    'user_email': current_user.correo_usuario,
                    'user_type': current_user.rol_usuario
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
    # Obtener información del usuario si está autenticado
    user_info = None
    empresa_obj = None
    
    # Verificar si se está solicitando un perfil específico por ID
    empresa_id = request.GET.get('id')
    if empresa_id:
        try:
            empresa_obj = empresa.objects.get(id_empresa=empresa_id)

            # Verificar si hay usuario autenticado para mantener la información de sesión
            current_user = None
            if is_user_authenticated(request):
                current_user = get_current_user(request)

            account_type = request.session.get('account_type', 'usuario')

            # Determinar si el visitante es el propietario de este perfil
            is_owner = False
            if current_user and account_type == 'empresa' and getattr(current_user, 'id_empresa', None) == empresa_obj.id_empresa:
                is_owner = True

            if is_owner:
                # Propietario viendo su propio perfil
                user_info = get_user_info_with_avatar(current_user, account_type, current_user.nombre_empresa)
                user_info['is_public_profile'] = False
            elif current_user:
                # Un usuario/empresa autenticada viendo el perfil de otra empresa -> perfil público
                user_info = get_user_info_with_avatar(current_user, account_type)
                user_info['is_public_profile'] = True
                # Guardar el avatar del perfil que se está viendo (campo correcto para empresa)
                user_info['avatar_chatbot'] = getattr(empresa_obj, 'avatar_chatbot_empresa', None) or getattr(empresa_obj, 'avatar_chatbot', None)
            else:
                # Para perfiles públicos sin autenticación
                user_info = {
                'is_authenticated': False,
                'is_public_profile': True,
                'avatar_chatbot': getattr(empresa_obj, 'avatar_chatbot_empresa', None) or getattr(empresa_obj, 'avatar_chatbot', None)
                }
        except empresa.DoesNotExist:
            # Si no existe la empresa, redirigir o mostrar error
            return render(request, 'ecommerce_app/perfil_empresa.html', {
                'error': 'Empresa no encontrada',
                'user_info': {'is_authenticated': False}
            })
    else:
        # Verificar si hay usuario autenticado
        current_user = None
        if is_user_authenticated(request):
            current_user = get_current_user(request)
        
        account_type = request.session.get('account_type', 'usuario')
        
        if current_user and account_type == 'empresa':
            # Para empresas autenticadas, current_user ya es la empresa
            empresa_obj = current_user
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True,
                'empresa_nombre': current_user.nombre_empresa,
                'avatar_chatbot': getattr(current_user, 'avatar_chatbot_empresa', None) or getattr(current_user, 'avatar_chatbot', None) or 'avatars/Cartoon Style Robot.jpg'
            }
        elif current_user:
            # Para usuarios autenticados, buscar empresa asociada
            empresa_nombre = None
            try:
                # Si el usuario tiene una empresa asociada, redirigir al perfil de empresa
                if empresa.objects.filter(correo_empresa=current_user.correo_usuario).exists():
                    empresa_obj = empresa.objects.get(correo_empresa=current_user.correo_usuario)
                    return redirect(f"/ecommerce/perfil_empresa/?id={empresa_obj.id_empresa}")

                empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                if empresa_obj:
                    empresa_nombre = empresa_obj.nombre_empresa
            except Exception as e:
                empresa_obj = None
                empresa_nombre = None
            
            usuario_obj = current_user # Asegurarse de que usuario_obj esté definido
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True,
                'empresa_nombre': empresa_nombre
            }
        else:
            # Usuario no autenticado - mostrar información por defecto
            user_info = {
                'is_authenticated': False
            }
            # Obtener la primera empresa disponible para mostrar como ejemplo
            empresa_obj = empresa.objects.first()
    
    # Obtener productos y servicios recientes si hay una empresa
    productos_recientes = []
    servicios_recientes = []
    
    if empresa_obj:
        # Obtener los 4 productos más recientes de la empresa con sus imágenes
        productos_query = producto_empresa.objects.filter(
            id_empresa_fk=empresa_obj
        ).order_by('-fecha_creacion_producto_empresa')[:4]
        
        for prod in productos_query:
            primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
            prod.primera_imagen = primera_imagen
            productos_recientes.append(prod)
        
        # Obtener los 4 servicios más recientes de la empresa con sus imágenes
        servicios_query = servicio_empresa.objects.filter(
            id_empresa_fk=empresa_obj
        ).order_by('-fecha_creacion_servicio_empresa')[:4]
        
        for serv in servicios_query:
            primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=serv).first()
            serv.primera_imagen = primera_imagen
            servicios_recientes.append(serv)
    
    # Agregar métodos de pago de la empresa en sesión (si hay una empresa autenticada en sesión)
    session_metodos_pago = []
    try:
        if is_user_authenticated(request) and request.session.get('account_type') == 'empresa':
            sess_empresa = get_current_user(request)
            if sess_empresa:
                from django.db.models import Case, When, Value, IntegerField
                from .models import MetodoPago
                # Orden deseado: transferencia, pago_movil, paypal
                ordering = Case(
                    When(tipo='transferencia', then=Value(0)),
                    When(tipo='pago_movil', then=Value(1)),
                    When(tipo='paypal', then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField()
                )
                session_metodos_pago = list(MetodoPago.objects.filter(empresa=sess_empresa, activo=True).order_by(ordering, 'fecha_creacion'))
    except Exception:
        session_metodos_pago = []

    return render(request, 'ecommerce_app/perfil_empresa.html', {
        'user_info': user_info,
        'empresa': empresa_obj,
        'productos_recientes': productos_recientes,
        'servicios_recientes': servicios_recientes,
        'session_metodos_pago': session_metodos_pago
    })


def busquedad(request):
    query = request.GET.get('query', '')
    tipo = request.GET.get('tipo', '')  # Nuevo parámetro para filtrar por tipo
    
    # Obtener parámetros de filtrado
    condicion = request.GET.get('condicion', '')
    marca = request.GET.get('marca', '')
    modelo = request.GET.get('modelo', '')
    categoria_producto = request.GET.get('categoria_producto', '')
    categoria_servicio = request.GET.get('categoria_servicio', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    latitud = request.GET.get('latitud', '')
    longitud = request.GET.get('longitud', '')
    rango_km = request.GET.get('rango_km', '')
    
    resultados_productos = []
    resultados_servicios = []
    resultados_empresas = []
    resultados_usuarios = []
    
    # Si no hay query ni filtros, mostrar productos y servicios generales
    if query or tipo or any([condicion, marca, modelo, categoria_producto, categoria_servicio, precio_min, precio_max]) or not any([query, tipo, condicion, marca, modelo, categoria_producto, categoria_servicio, precio_min, precio_max]):
        # Determinar el tipo de búsqueda
        query_lower = query.lower().strip() if query else ''
        
        # Palabras clave que indican búsqueda de productos/servicios
        palabras_producto = ['laptop', 'computadora', 'celular', 'telefono', 'ropa', 'zapatos', 'libro', 'mueble', 'casa', 'carro', 'auto']
        palabras_servicio = ['reparacion', 'mantenimiento', 'limpieza', 'consultoria', 'asesoria', 'diseño', 'programacion', 'corte', 'pintura']
        
        # Buscar empresas por nombre (prioridad alta) - solo si hay query y no hay filtros específicos
        empresas_list = empresa.objects.none()
        usuarios_list = usuario.objects.none()
        
        if query and not any([condicion, marca, modelo, categoria_producto, categoria_servicio, precio_min, precio_max]):
            empresas_list = empresa.objects.filter(
                nombre_empresa__icontains=query
            )
            
            # Buscar usuarios por nombre (prioridad alta)
            usuarios_list = usuario.objects.filter(
                nombre_usuario__icontains=query
            )
        
        # Determinar si la búsqueda es para productos/servicios o personas/empresas
        es_busqueda_producto_servicio = any(palabra in query_lower for palabra in palabras_producto + palabras_servicio) or any([condicion, marca, modelo, categoria_producto, categoria_servicio, precio_min, precio_max]) or tipo in ['productos', 'servicios']
        es_busqueda_persona_empresa = query and len(query) <= 3 or query_lower in ['juan', 'maria', 'carlos', 'ana', 'empresa', 'tienda', 'negocio']
        
        # Buscar productos y servicios si hay filtros, es búsqueda específica, o no hay parámetros (búsqueda general)
        if es_busqueda_producto_servicio or (query and len(query) > 3 and not empresas_list.exists() and not usuarios_list.exists()) or not query:
            # Construir filtros para productos de empresa (solo si no es búsqueda exclusiva de servicios)
            if tipo != 'servicios':
                filtros_productos_sucursal = {'estatus_producto_sucursal': 'Activo'}
                if query:
                    filtros_productos_sucursal['id_producto_fk__nombre_producto_empresa__icontains'] = query
                if condicion:
                    filtros_productos_sucursal['condicion_producto_sucursal'] = condicion

                if categoria_producto:
                    filtros_productos_sucursal['id_producto_fk__id_categoria_producto_fk__nombre_categoria_producto'] = categoria_producto
                
                productos_sucursal_list = producto_sucursal.objects.filter(
                    **filtros_productos_sucursal
                ).select_related('id_producto_fk', 'id_sucursal_fk')
                
                # Si es búsqueda de solo productos, ordenar por más recientes
                if tipo == 'productos':
                    productos_sucursal_list = productos_sucursal_list.order_by('-id_producto_fk__fecha_creacion_producto_empresa')
                # Si no hay query (búsqueda general), limitar resultados y ordenar por más recientes
                elif not query:
                    productos_sucursal_list = productos_sucursal_list.order_by('-id_producto_fk__fecha_creacion_producto_empresa')[:10]
            else:
                productos_sucursal_list = producto_sucursal.objects.none()
            
            # Aplicar filtro de precio para productos de empresa
            if precio_min:
                try:
                    productos_sucursal_list = productos_sucursal_list.filter(precio_producto_sucursal__gte=float(precio_min))
                except ValueError:
                    pass
            if precio_max:
                try:
                    productos_sucursal_list = productos_sucursal_list.filter(precio_producto_sucursal__lte=float(precio_max))
                except ValueError:
                    pass
            
            # Construir filtros para productos de usuario (solo si no es búsqueda exclusiva de servicios)
            if tipo != 'servicios':
                filtros_productos_usuario = {'estatus_producto_usuario': 'Activo'}
                if query:
                    filtros_productos_usuario['nombre_producto_usuario__icontains'] = query
                if condicion:
                    filtros_productos_usuario['condicion_producto_usuario'] = condicion

                if categoria_producto:
                    filtros_productos_usuario['id_categoria_producto_fk__nombre_categoria_producto'] = categoria_producto
                
                productos_usuario_list = producto_usuario.objects.filter(
                    **filtros_productos_usuario
                )
                
                # Si es búsqueda de solo productos, ordenar por más recientes
                if tipo == 'productos':
                    productos_usuario_list = productos_usuario_list.order_by('-fecha_creacion_producto_usuario')
                # Si no hay query (búsqueda general), limitar resultados y ordenar por más recientes
                elif not query:
                    productos_usuario_list = productos_usuario_list.order_by('-fecha_creacion_producto_usuario')[:10]
            else:
                productos_usuario_list = producto_usuario.objects.none()
            
            # Aplicar filtro de precio para productos de usuario
            if precio_min:
                try:
                    productos_usuario_list = productos_usuario_list.filter(precio_producto_usuario__gte=float(precio_min))
                except ValueError:
                    pass
            if precio_max:
                try:
                    productos_usuario_list = productos_usuario_list.filter(precio_producto_usuario__lte=float(precio_max))
                except ValueError:
                    pass
            
            # Construir filtros para servicios de empresa (solo si no es búsqueda exclusiva de productos)
            if tipo != 'productos':
                filtros_servicios_sucursal = {'estatus_servicio_sucursal': 'Activo'}
                if query:
                    filtros_servicios_sucursal['id_servicio_fk__nombre_servicio_empresa__icontains'] = query
                if categoria_servicio:
                    filtros_servicios_sucursal['id_servicio_fk__id_categoria_servicio_fk__nombre_categoria_servicio'] = categoria_servicio
                
                servicios_sucursal_list = servicio_sucursal.objects.filter(
                    **filtros_servicios_sucursal
                ).select_related('id_servicio_fk', 'id_sucursal_fk')
                
                # Si es búsqueda de solo servicios, ordenar por más recientes
                if tipo == 'servicios':
                    servicios_sucursal_list = servicios_sucursal_list.order_by('-id_servicio_fk__fecha_creacion_servicio_empresa')
                # Si no hay query (búsqueda general), limitar resultados y ordenar por más recientes
                elif not query:
                    servicios_sucursal_list = servicios_sucursal_list.order_by('-id_servicio_fk__fecha_creacion_servicio_empresa')[:10]
            else:
                servicios_sucursal_list = servicio_sucursal.objects.none()
            
            # Aplicar filtro de precio para servicios de empresa
            if precio_min:
                try:
                    servicios_sucursal_list = servicios_sucursal_list.filter(precio_servicio_sucursal__gte=float(precio_min))
                except ValueError:
                    pass
            if precio_max:
                try:
                    servicios_sucursal_list = servicios_sucursal_list.filter(precio_servicio_sucursal__lte=float(precio_max))
                except ValueError:
                    pass
            
            # Construir filtros para servicios de usuario (solo si no es búsqueda exclusiva de productos)
            if tipo != 'productos':
                filtros_servicios_usuario = {'estatus_servicio_usuario': 'Activo'}
                if query:
                    filtros_servicios_usuario['nombre_servicio_usuario__icontains'] = query
                if categoria_servicio:
                    filtros_servicios_usuario['id_categoria_servicio_fk__nombre_categoria_servicio'] = categoria_servicio
                
                servicios_usuario_list = servicio_usuario.objects.filter(
                    **filtros_servicios_usuario
                )
                
                # Si es búsqueda de solo servicios, ordenar por más recientes
                if tipo == 'servicios':
                    servicios_usuario_list = servicios_usuario_list.order_by('-fecha_creacion_servicio_usuario')
                # Si no hay query (búsqueda general), limitar resultados y ordenar por más recientes
                elif not query:
                    servicios_usuario_list = servicios_usuario_list.order_by('-fecha_creacion_servicio_usuario')[:10]
            else:
                servicios_usuario_list = servicio_usuario.objects.none()
            
            # Aplicar filtro de precio para servicios de usuario
            if precio_min:
                try:
                    servicios_usuario_list = servicios_usuario_list.filter(precio_servicio_usuario__gte=float(precio_min))
                except ValueError:
                    pass
            if precio_max:
                try:
                    servicios_usuario_list = servicios_usuario_list.filter(precio_servicio_usuario__lte=float(precio_max))
                except ValueError:
                    pass
        else:
            # Si se encontraron empresas o usuarios, no mostrar productos/servicios
            productos_sucursal_list = producto_sucursal.objects.none()
            productos_usuario_list = producto_usuario.objects.none()
            servicios_sucursal_list = servicio_sucursal.objects.none()
            servicios_usuario_list = servicio_usuario.objects.none()
        
        # Función para calcular distancia entre dos puntos geográficos (fórmula de Haversine)
        def calcular_distancia(lat1, lon1, lat2, lon2):
            from math import radians, cos, sin, asin, sqrt
            
            # Convertir grados a radianes
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Fórmula de Haversine
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radio de la Tierra en kilómetros
            return c * r
        
        # Obtener coordenadas del usuario para filtro de localización
        user_lat = None
        user_lng = None
        rango_km_float = None
        
        if latitud and longitud and rango_km:
            try:
                user_lat = float(latitud)
                user_lng = float(longitud)
                rango_km_float = float(rango_km)
            except ValueError:
                pass
        
        # Formatear resultados de productos de empresa
        for ps in productos_sucursal_list:
            # Verificar filtro de localización
            incluir_producto = True
            distancia = None
            
            if user_lat is not None and user_lng is not None and rango_km_float is not None:
                # Verificar si la sucursal tiene coordenadas
                if (hasattr(ps.id_sucursal_fk, 'latitud_sucursal') and 
                    hasattr(ps.id_sucursal_fk, 'longitud_sucursal') and 
                    ps.id_sucursal_fk.latitud_sucursal and 
                    ps.id_sucursal_fk.longitud_sucursal):
                    
                    try:
                        sucursal_lat = float(ps.id_sucursal_fk.latitud_sucursal)
                        sucursal_lng = float(ps.id_sucursal_fk.longitud_sucursal)
                        distancia = calcular_distancia(user_lat, user_lng, sucursal_lat, sucursal_lng)
                        
                        if distancia > rango_km_float:
                            incluir_producto = False
                    except (ValueError, TypeError):
                        incluir_producto = False
                else:
                    incluir_producto = False
            
            if incluir_producto:
                # Obtener la primera imagen del producto desde la nueva tabla
                primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=ps.id_producto_fk).first()
                imagen_url = primera_imagen.ruta_imagen_producto_empresa.url if primera_imagen and primera_imagen.ruta_imagen_producto_empresa else None
                
                producto_data = {
                    'id': ps.id_producto_sucursal,
                    'nombre': ps.id_producto_fk.nombre_producto_empresa,
                    'descripcion': ps.id_producto_fk.descripcion_producto_empresa,
                    'precio': ps.precio_producto_sucursal,
                    'stock': ps.stock_producto_sucursal,
                    'condicion': ps.condicion_producto_sucursal,
                    'imagen': imagen_url,
                    'sucursal': ps.id_sucursal_fk.nombre_sucursal,
                    'empresa_nombre': ps.id_sucursal_fk.id_empresa_fk.nombre_empresa,
                    'tipo': 'producto',
                    'origen': 'empresa',
                    'latitud': ps.id_sucursal_fk.latitud_sucursal if hasattr(ps.id_sucursal_fk, 'latitud_sucursal') else None,
                    'longitud': ps.id_sucursal_fk.longitud_sucursal if hasattr(ps.id_sucursal_fk, 'longitud_sucursal') else None
                }
                
                if distancia is not None:
                    producto_data['distancia'] = round(distancia, 2)
                
                resultados_productos.append(producto_data)
        
        # Formatear resultados de productos de usuario
        for pu in productos_usuario_list:
            # Verificar filtro de localización
            incluir_producto = True
            distancia = None
            
            if user_lat is not None and user_lng is not None and rango_km_float is not None:
                # Verificar si el producto tiene coordenadas de entrega
                if (hasattr(pu, 'latitud_entrega_producto') and 
                    hasattr(pu, 'longitud_entrega_producto') and 
                    pu.latitud_entrega_producto and 
                    pu.longitud_entrega_producto):
                    
                    try:
                        producto_lat = float(pu.latitud_entrega_producto)
                        producto_lng = float(pu.longitud_entrega_producto)
                        distancia = calcular_distancia(user_lat, user_lng, producto_lat, producto_lng)
                        
                        if distancia > rango_km_float:
                            incluir_producto = False
                    except (ValueError, TypeError):
                        incluir_producto = False
                else:
                    incluir_producto = False
            
            if incluir_producto:
                # Obtener la primera imagen del producto de usuario
                primera_imagen = imagen_producto_usuario.objects.filter(id_producto_fk=pu).first()
                imagen_url = primera_imagen.ruta_imagen_producto_usuario.url if primera_imagen and primera_imagen.ruta_imagen_producto_usuario else None
                
                producto_data = {
                    'id': pu.id_producto_usuario,
                    'nombre': pu.nombre_producto_usuario,
                    'descripcion': pu.descripcion_producto_usuario,
                    'precio': pu.precio_producto_usuario,
                    'stock': pu.stock_producto_usuario,
                    'condicion': pu.condicion_producto_usuario,
                    'imagen': imagen_url,
                    'sucursal': f"Usuario: {pu.id_usuario_fk.nombre_usuario}",
                    'empresa_nombre': None,
                    'tipo': 'producto',
                    'origen': 'usuario',
                    'latitud': pu.latitud_entrega_producto if hasattr(pu, 'latitud_entrega_producto') else None,
                    'longitud': pu.longitud_entrega_producto if hasattr(pu, 'longitud_entrega_producto') else None
                }
                
                if distancia is not None:
                    producto_data['distancia'] = round(distancia, 2)
                
                resultados_productos.append(producto_data)
        
        # Formatear resultados de servicios de empresa
        for ss in servicios_sucursal_list:
            # Verificar filtro de localización
            incluir_servicio = True
            distancia = None
            
            if user_lat is not None and user_lng is not None and rango_km_float is not None:
                # Verificar si la sucursal tiene coordenadas
                if (hasattr(ss.id_sucursal_fk, 'latitud_sucursal') and 
                    hasattr(ss.id_sucursal_fk, 'longitud_sucursal') and 
                    ss.id_sucursal_fk.latitud_sucursal and 
                    ss.id_sucursal_fk.longitud_sucursal):
                    
                    try:
                        sucursal_lat = float(ss.id_sucursal_fk.latitud_sucursal)
                        sucursal_lng = float(ss.id_sucursal_fk.longitud_sucursal)
                        distancia = calcular_distancia(user_lat, user_lng, sucursal_lat, sucursal_lng)
                        
                        if distancia > rango_km_float:
                            incluir_servicio = False
                    except (ValueError, TypeError):
                        incluir_servicio = False
                else:
                    incluir_servicio = False
            
            if incluir_servicio:
                # Obtener la primera imagen del servicio desde la nueva tabla
                primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=ss.id_servicio_fk).first()
                imagen_url = primera_imagen.ruta_imagen_servicio_empresa.url if primera_imagen and primera_imagen.ruta_imagen_servicio_empresa else None
                
                servicio_data = {
                    'id': ss.id_servicio_sucursal,
                    'nombre': ss.id_servicio_fk.nombre_servicio_empresa,
                    'descripcion': ss.id_servicio_fk.descripcion_servicio_empresa,
                    'precio': ss.precio_servicio_sucursal if ss.precio_servicio_sucursal else 'Consultar',
                    'imagen': imagen_url,
                    'sucursal': ss.id_sucursal_fk.nombre_sucursal,
                    'empresa_nombre': ss.id_sucursal_fk.id_empresa_fk.nombre_empresa,
                    'tipo': 'servicio',
                    'origen': 'empresa',
                    'latitud': ss.id_sucursal_fk.latitud_sucursal if hasattr(ss.id_sucursal_fk, 'latitud_sucursal') else None,
                    'longitud': ss.id_sucursal_fk.longitud_sucursal if hasattr(ss.id_sucursal_fk, 'longitud_sucursal') else None
                }
                
                if distancia is not None:
                    servicio_data['distancia'] = round(distancia, 2)
                
                resultados_servicios.append(servicio_data)
        
        # Formatear resultados de servicios de usuario
        for su in servicios_usuario_list:
            # Verificar filtro de localización
            incluir_servicio = True
            distancia = None
            
            if user_lat is not None and user_lng is not None and rango_km_float is not None:
                # Verificar si el usuario tiene coordenadas
                if (hasattr(su.id_usuario_fk, 'latitud_usuario') and 
                    hasattr(su.id_usuario_fk, 'longitud_usuario') and 
                    su.id_usuario_fk.latitud_usuario and 
                    su.id_usuario_fk.longitud_usuario):
                    
                    try:
                        usuario_lat = float(su.id_usuario_fk.latitud_usuario)
                        usuario_lng = float(su.id_usuario_fk.longitud_usuario)
                        distancia = calcular_distancia(user_lat, user_lng, usuario_lat, usuario_lng)
                        
                        if distancia > rango_km_float:
                            incluir_servicio = False
                    except (ValueError, TypeError):
                        incluir_servicio = False
                else:
                    incluir_servicio = False
            
            if incluir_servicio:
                # Obtener la primera imagen del servicio de usuario
                primera_imagen = imagen_servicio_usuario.objects.filter(id_servicio_fk=su).first()
                imagen_url = primera_imagen.ruta_imagen_servicio_usuario.url if primera_imagen and primera_imagen.ruta_imagen_servicio_usuario else None
                
                servicio_data = {
                    'id': su.id_servicio_usuario,
                    'nombre': su.nombre_servicio_usuario,
                    'descripcion': su.descripcion_servicio_usuario,
                    'precio': su.precio_servicio_usuario if su.precio_servicio_usuario else 'Consultar',
                    'imagen': imagen_url,
                    'sucursal': f"Usuario: {su.id_usuario_fk.nombre_usuario}",
                    'empresa_nombre': None,
                    'tipo': 'servicio',
                    'origen': 'usuario',
                    'latitud': su.id_usuario_fk.latitud_usuario if hasattr(su.id_usuario_fk, 'latitud_usuario') else None,
                    'longitud': su.id_usuario_fk.longitud_usuario if hasattr(su.id_usuario_fk, 'longitud_usuario') else None
                }
                
                if distancia is not None:
                    servicio_data['distancia'] = round(distancia, 2)
                
                resultados_servicios.append(servicio_data)
        
        # Formatear resultados de empresas
        for emp in empresas_list:
            resultados_empresas.append({
                'id': emp.id_empresa,
                'nombre': emp.nombre_empresa,
                'descripcion': emp.descripcion_empresa or 'Sin descripción disponible',
                'tipo': 'empresa',
                'logo': emp.logo_empresa.url if emp.logo_empresa else None,
                'pais': emp.pais_empresa,
                'estado': emp.estado_empresa,
                'tipo_empresa': emp.tipo_empresa
            })
        
        # Formatear resultados de usuarios
        for usr in usuarios_list:
            resultados_usuarios.append({
                'id': usr.id_usuario,
                'nombre': usr.nombre_usuario,
                'descripcion': f'Usuario registrado en {usr.fecha_registro_usuario.strftime("%Y")}',
                'tipo': 'usuario',
                'foto': usr.foto_usuario.url if usr.foto_usuario else None,
                'pais': usr.pais,
                'estado': usr.estado
            })
    
    # Combinar resultados de productos y servicios
    resultados_productos_servicios = resultados_productos + resultados_servicios
    
    # Ordenar por distancia si se proporcionaron coordenadas del usuario
    if user_lat is not None and user_lng is not None:
        # Separar elementos con y sin distancia
        con_distancia = [item for item in resultados_productos_servicios if 'distancia' in item]
        sin_distancia = [item for item in resultados_productos_servicios if 'distancia' not in item]
        
        # Ordenar los elementos con distancia de menor a mayor
        con_distancia.sort(key=lambda x: x['distancia'])
        
        # Combinar: primero los ordenados por distancia, luego los sin distancia
        resultados_productos_servicios = con_distancia + sin_distancia
    
    # Combinar con empresas y usuarios (estos no se ordenan por distancia)
    resultados_combinados = resultados_productos_servicios + resultados_empresas + resultados_usuarios
    
    # Implementar paginación
    page = request.GET.get('page', 1)
    paginator = Paginator(resultados_combinados, 3)  # 3 elementos por página
    
    try:
        resultados_paginados = paginator.page(page)
    except PageNotAnInteger:
        resultados_paginados = paginator.page(1)
    except EmptyPage:
        resultados_paginados = paginator.page(paginator.num_pages)
    
    # Obtener información del usuario para el modal de sesión
    current_user = get_current_user(request)
    account_type = request.session.get('account_type')
    
    if current_user and account_type:
        empresa_nombre = None
        if account_type == 'empresa':
            # Obtener el nombre de la empresa
            empresa_nombre = current_user.nombre_empresa if hasattr(current_user, 'nombre_empresa') else None
        
        user_info = {
            'id': current_user.id_usuario if account_type == 'usuario' else current_user.id_empresa,
            'nombre': current_user.nombre_usuario if account_type == 'usuario' else current_user.nombre_empresa,
            'email': current_user.correo_usuario if account_type == 'usuario' else current_user.correo_empresa,
            'tipo': account_type,
            'is_authenticated': True,
            'empresa_nombre': empresa_nombre
        }
    else:
        user_info = {
            'is_authenticated': False
        }
    
    return render(request, 'ecommerce_app/busquedad.html', {
        'query': query,
        'resultados': resultados_paginados,
        'total_resultados': len(resultados_combinados),
        'resultados_productos': resultados_productos,
        'resultados_servicios': resultados_servicios,
        'resultados_empresas': resultados_empresas,
        'resultados_usuarios': resultados_usuarios,
        'user_info': user_info,
        'paginator': paginator,
        'page_obj': resultados_paginados
    })


# API para obtener todas las imágenes de un producto
@require_GET
def api_obtener_imagenes_producto(request):
    try:
        # Buscar ID de producto según el tipo de usuario
        id_producto_empresa = request.GET.get('id_producto_empresa')
        id_producto_usuario = request.GET.get('id_producto_usuario')
        id_producto = request.GET.get('id_producto')
        
        if not (id_producto_empresa or id_producto_usuario or id_producto):
            return JsonResponse({'success': False, 'message': 'ID de producto requerido'})
        
        imagenes_list = []
        
        # Si es un producto de empresa
        if id_producto_empresa or (id_producto and not id_producto_usuario):
            producto_id = id_producto_empresa or id_producto
            imagenes = imagen_producto_empresa.objects.filter(id_producto_fk=producto_id)
            for img in imagenes:
                imagenes_list.append({
                    'id_imagen_producto_empresa': img.id_imagen_producto_empresa,
                    'url': img.ruta_imagen_producto_empresa.url if img.ruta_imagen_producto_empresa else '',
                    'fecha_creacion': img.fecha_creacion_producto_empresa.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Si es un producto de usuario
        elif id_producto_usuario:
            imagenes = imagen_producto_usuario.objects.filter(id_producto_fk=id_producto_usuario)
            for img in imagenes:
                imagenes_list.append({
                    'id_imagen_producto_usuario': img.id_imagen_producto_usuario,
                    'url': img.ruta_imagen_producto_usuario.url if img.ruta_imagen_producto_usuario else '',
                    'fecha_creacion': img.fecha_creacion_producto_usuario.strftime('%Y-%m-%d %H:%M:%S')
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
        # Buscar ID de servicio según el tipo de usuario
        id_servicio_empresa = request.GET.get('id_servicio_empresa')
        id_servicio_usuario = request.GET.get('id_servicio_usuario')
        id_servicio = request.GET.get('id_servicio')
        
        if not (id_servicio_empresa or id_servicio_usuario or id_servicio):
            return JsonResponse({'success': False, 'message': 'ID de servicio requerido'})
        
        imagenes_list = []
        
        # Si es un servicio de empresa
        if id_servicio_empresa or (id_servicio and not id_servicio_usuario):
            servicio_id = id_servicio_empresa or id_servicio
            imagenes = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio_id)
            for img in imagenes:
                imagenes_list.append({
                    'id_imagen_servicio_empresa': img.id_imagen_servicio_empresa,
                    'url': img.ruta_imagen_servicio_empresa.url if img.ruta_imagen_servicio_empresa else '',
                    'fecha_creacion': img.fecha_creacion_servicio_empresa.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Si es un servicio de usuario
        elif id_servicio_usuario:
            imagenes = imagen_servicio_usuario.objects.filter(id_servicio_fk=id_servicio_usuario)
            for img in imagenes:
                imagenes_list.append({
                    'id_imagen_servicio_usuario': img.id_imagen_servicio_usuario,
                    'url': img.ruta_imagen_servicio_usuario.url if img.ruta_imagen_servicio_usuario else '',
                    'fecha_creacion': img.fecha_creacion_servicio_usuario.strftime('%Y-%m-%d %H:%M:%S')
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
        # Intentar obtener ID de imagen de empresa o usuario
        id_imagen_empresa = request.POST.get('id_imagen_producto_empresa')
        id_imagen_usuario = request.POST.get('id_imagen_producto_usuario')
        
        if not id_imagen_empresa and not id_imagen_usuario:
            return JsonResponse({'success': False, 'message': 'ID de imagen requerido'})
        
        imagen_obj = None
        total_imagenes = 0
        
        if id_imagen_empresa:
            # Buscar en imágenes de empresa
            imagen_obj = imagen_producto_empresa.objects.get(id_imagen_producto_empresa=id_imagen_empresa)
            total_imagenes = imagen_producto_empresa.objects.filter(id_producto_fk=imagen_obj.id_producto_fk).count()
            ruta_imagen = imagen_obj.ruta_imagen_producto_empresa
        elif id_imagen_usuario:
            # Buscar en imágenes de usuario
            imagen_obj = imagen_producto_usuario.objects.get(id_imagen_producto_usuario=id_imagen_usuario)
            total_imagenes = imagen_producto_usuario.objects.filter(id_producto_fk=imagen_obj.id_producto_fk).count()
            ruta_imagen = imagen_obj.ruta_imagen_producto_usuario
        
        # Verificar que el producto tenga al menos 2 imágenes antes de eliminar
        if total_imagenes <= 1:
            return JsonResponse({
                'success': False, 
                'message': 'No se puede eliminar la imagen. El producto debe tener al menos una imagen.'
            })
        
        # Eliminar el archivo físico si existe
        if ruta_imagen:
            try:
                ruta_imagen.delete(save=False)
            except:
                pass  # Si no se puede eliminar el archivo, continuar
        
        imagen_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Imagen eliminada correctamente'
        })
        
    except (imagen_producto_empresa.DoesNotExist, imagen_producto_usuario.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Imagen no encontrada'})
    except Exception as e:
        logger.error(f"Error al eliminar imagen del producto: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


# API para eliminar una imagen específica de servicio
@require_POST
def api_eliminar_imagen_servicio(request):
    try:
        # Intentar obtener ID de imagen de empresa o usuario
        id_imagen_empresa = request.POST.get('id_imagen_servicio_empresa')
        id_imagen_usuario = request.POST.get('id_imagen_servicio_usuario')
        
        if not id_imagen_empresa and not id_imagen_usuario:
            return JsonResponse({'success': False, 'message': 'ID de imagen requerido'})
        
        imagen_obj = None
        total_imagenes = 0
        
        if id_imagen_empresa:
            # Buscar en imágenes de empresa
            imagen_obj = imagen_servicio_empresa.objects.get(id_imagen_servicio_empresa=id_imagen_empresa)
            total_imagenes = imagen_servicio_empresa.objects.filter(id_servicio_fk=imagen_obj.id_servicio_fk).count()
            ruta_imagen = imagen_obj.ruta_imagen_servicio_empresa
        elif id_imagen_usuario:
            # Buscar en imágenes de usuario
            imagen_obj = imagen_servicio_usuario.objects.get(id_imagen_servicio_usuario=id_imagen_usuario)
            total_imagenes = imagen_servicio_usuario.objects.filter(id_servicio_fk=imagen_obj.id_servicio_fk).count()
            ruta_imagen = imagen_obj.ruta_imagen_servicio_usuario
        
        # Verificar que el servicio tenga al menos 2 imágenes antes de eliminar
        if total_imagenes <= 1:
            return JsonResponse({
                'success': False, 
                'message': 'No se puede eliminar la imagen. El servicio debe tener al menos una imagen.'
            })
        
        # Eliminar el archivo físico si existe
        if ruta_imagen:
            try:
                ruta_imagen.delete(save=False)
            except:
                pass  # Si no se puede eliminar el archivo, continuar
        
        imagen_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Imagen eliminada correctamente'
        })
        
    except (imagen_servicio_empresa.DoesNotExist, imagen_servicio_usuario.DoesNotExist):
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
            id_producto_fk__nombre_producto_empresa__icontains=query,
            estatus_producto_sucursal='Activo'
        ).select_related('id_producto_fk', 'id_sucursal_fk')
        
        # Buscar productos de usuarios con coordenadas de entrega
        productos_usuario_list = producto_usuario.objects.filter(
            nombre_producto_usuario__icontains=query,
            estatus_producto_usuario='Activo',
            latitud_entrega_producto__isnull=False,
            longitud_entrega_producto__isnull=False
        ).select_related('id_usuario_fk')
        
        servicios_sucursal_list = servicio_sucursal.objects.filter(
            id_servicio_fk__nombre_servicio_empresa__icontains=query,
            estatus_servicio_sucursal='Activo'
        ).select_related('id_servicio_fk', 'id_sucursal_fk')
        
        # Combinar resultados con información de ubicación
        todos_resultados = []
        
        # Procesar productos
        for ps in productos_sucursal_list:
            if ps.id_sucursal_fk.latitud_sucursal and ps.id_sucursal_fk.longitud_sucursal:
                primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=ps.id_producto_fk).first()
                imagen_url = primera_imagen.ruta_imagen_producto_empresa.url if primera_imagen and primera_imagen.ruta_imagen_producto_empresa else None
                
                # Para productos de empresa, el propietario siempre es empresa
                empresa_nombre = ps.id_producto_fk.id_empresa_fk.nombre_empresa if hasattr(ps.id_producto_fk, 'id_empresa_fk') else ps.id_sucursal_fk.nombre_sucursal
                
                resultado = {
                    'id': ps.id_producto_sucursal,
                    'nombre': ps.id_producto_fk.nombre_producto_empresa,
                    'descripcion': ps.id_producto_fk.descripcion_producto_empresa,
                    'precio': ps.precio_producto_sucursal,
                    'imagen': imagen_url,
                    'sucursal': f"Empresa: {empresa_nombre}",
                    'direccion': ps.id_sucursal_fk.direccion_sucursal,
                    'lat': float(ps.id_sucursal_fk.latitud_sucursal),
                    'lng': float(ps.id_sucursal_fk.longitud_sucursal),
                    'tipo': 'producto',
                    'origen': 'empresa',
                    'tipo_propietario': 'empresa',
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
        
        # Procesar productos de usuarios
        for pu in productos_usuario_list:
            if pu.latitud_entrega_producto and pu.longitud_entrega_producto:
                primera_imagen = imagen_producto_usuario.objects.filter(id_producto_fk=pu).first()
                imagen_url = primera_imagen.ruta_imagen_producto_usuario.url if primera_imagen and primera_imagen.ruta_imagen_producto_usuario else None
                
                # Determinar el tipo de usuario (persona o empresa)
                tipo_usuario = pu.id_usuario_fk.rol_usuario if hasattr(pu.id_usuario_fk, 'rol_usuario') else 'persona'
                tipo_usuario_texto = 'Empresa' if tipo_usuario == 'empresa' else 'Persona'
                
                resultado = {
                    'id': pu.id_producto_usuario,
                    'nombre': pu.nombre_producto_usuario,
                    'descripcion': pu.descripcion_producto_usuario,
                    'precio': pu.precio_producto_usuario,
                    'imagen': imagen_url,
                    'sucursal': f"{tipo_usuario_texto}: {pu.id_usuario_fk.nombre_usuario}",
                    'direccion': f"Entrega desde ubicación del usuario",
                    'lat': float(pu.latitud_entrega_producto),
                    'lng': float(pu.longitud_entrega_producto),
                    'tipo': 'producto',
                    'origen': 'usuario',
                    'tipo_propietario': tipo_usuario,
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
                primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=ss.id_servicio_fk).first()
                imagen_url = primera_imagen.ruta_imagen_servicio_empresa.url if primera_imagen and primera_imagen.ruta_imagen_servicio_empresa else None
                
                # Para servicios de empresa, el propietario siempre es empresa
                empresa_nombre = ss.id_servicio_fk.id_empresa_fk.nombre_empresa if hasattr(ss.id_servicio_fk, 'id_empresa_fk') else ss.id_sucursal_fk.nombre_sucursal
                
                resultado = {
                    'id': ss.id_servicio_sucursal,
                    'nombre': ss.id_servicio_fk.nombre_servicio_empresa,
                    'descripcion': ss.id_servicio_fk.descripcion_servicio_empresa,
                    'precio': ss.precio_servicio_sucursal if ss.precio_servicio_sucursal else 'Consultar',
                    'imagen': imagen_url,
                    'sucursal': f"Empresa: {empresa_nombre}",
                    'direccion': ss.id_sucursal_fk.direccion_sucursal,
                    'lat': float(ss.id_sucursal_fk.latitud_sucursal),
                    'lng': float(ss.id_sucursal_fk.longitud_sucursal),
                    'tipo': 'servicio',
                    'origen': 'empresa',
                    'tipo_propietario': 'empresa',
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
        
        # Obtener rango de búsqueda del parámetro GET (por defecto 20km para cargar más resultados)
        rango_busqueda = request.GET.get('rango', '20')
        try:
            rango_busqueda_float = float(rango_busqueda)
        except (ValueError, TypeError):
            rango_busqueda_float = 20.0  # Valor por defecto amplio
        
        # Filtrar resultados dentro del rango especificado y ordenar por distancia
        if user_lat and user_lng:
            # Filtrar solo resultados dentro del rango especificado
            todos_resultados = [r for r in todos_resultados if r['distancia'] <= rango_busqueda_float]
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


@require_login
def carrito(request):
    # Obtener información del usuario autenticado
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    # Determinar el tipo de cuenta
    account_type = request.session.get('account_type', 'usuario')
    
    # Inicializar variables para el carrito
    productos_carrito = []
    servicios_carrito = []
    total_productos = 0
    total_servicios = 0
    cantidad_productos = 0
    
    if account_type == 'empresa':
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        
        # Obtener carrito activo o pendiente de la empresa
        carrito_empresa = carrito_compra_producto_empresa.objects.filter(
            id_empresa_fk=current_user,
            estatuscarrito_prod_empresa__in=['activo', 'pendiente']
        ).first()
        
        if carrito_empresa:
            # Validar precios antes de mostrar el carrito
            cambios_precio = validar_precios_carrito_empresa(carrito_empresa)
            
            # Obtener detalles del carrito
            detalles_carrito = detalle_compra_producto_empresa.objects.filter(
                id_fk_carritocompra_empresa=carrito_empresa
            ).select_related('id_fk_producto_sucursal_empresa__id_producto_fk')
            
            for detalle in detalles_carrito:
                # Manejar productos de empresa (a través de producto_sucursal)
                if detalle.id_fk_producto_sucursal_empresa:
                    producto_sucursal = detalle.id_fk_producto_sucursal_empresa
                    producto = producto_sucursal.id_producto_fk
                    
                    # Obtener la primera imagen del producto
                    imagen = imagen_producto_empresa.objects.filter(
                        id_producto_fk=producto
                    ).first()
                    
                    # Obtener información de la sucursal
                    sucursal_info = producto_sucursal.id_sucursal_fk
                    
                    productos_carrito.append({
                        'id': producto_sucursal.id_producto_sucursal,
                        'nombre': producto.nombre_producto_empresa,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_empresa,
                        'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                        'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                        'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                        'sucursal': sucursal_info.nombre_sucursal if sucursal_info else 'N/A',
                        'estatus_carrito': carrito_empresa.estatuscarrito_prod_empresa,
                        'fecha_creacion_carrito': carrito_empresa.fecha_creacion_carrito_prod_empresa
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_empresa
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_empresa
                
                elif detalle.idproducto_fk_usuario:
                    producto_usuario = detalle.idproducto_fk_usuario
                    
                    # Obtener la primera imagen del producto de usuario
                    imagen = imagen_producto_usuario.objects.filter(
                        id_producto_fk=producto_usuario
                    ).first()
                    
                    productos_carrito.append({
                        'id': producto_usuario.id_producto_usuario,
                        'nombre': producto_usuario.nombre_producto_usuario,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_empresa,
                        'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                        'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                        'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None,
                        'sucursal': 'Producto de Usuario',
                        'estatus_carrito': carrito_empresa.estatuscarrito_prod_empresa,
                        'fecha_creacion_carrito': carrito_empresa.fecha_creacion_carrito_prod_empresa
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_empresa
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_empresa



            
    else:
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        
        # Obtener carrito activo o pendiente del usuario
        carrito_usuario = carrito_compra_producto_usuario.objects.filter(
            id_usuario_fk=current_user,
            estatuscarrito_prod_usuario__in=['activo', 'pendiente']
        ).first()
        
        if carrito_usuario:
            # Validar precios antes de mostrar el carrito
            cambios_precio = validar_precios_carrito_usuario(carrito_usuario)
            
            # Obtener detalles del carrito
            detalles_carrito = detalle_compra_producto_usuario.objects.filter(
                id_fk_carritocompra_usuario=carrito_usuario
            ).select_related('idproducto_fk_usuario', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            for detalle in detalles_carrito:
                # Manejar productos de empresa (a través de producto_sucursal)
                if detalle.id_fk_producto_sucursal_empresa:
                    producto_sucursal = detalle.id_fk_producto_sucursal_empresa
                    producto = producto_sucursal.id_producto_fk
                    
                    # Obtener la primera imagen del producto
                    imagen = imagen_producto_empresa.objects.filter(
                        id_producto_fk=producto
                    ).first()
                    
                    # Obtener información de la sucursal
                    sucursal_info = producto_sucursal.id_sucursal_fk
                    
                    productos_carrito.append({
                        'id': producto_sucursal.id_producto_sucursal,
                        'nombre': producto.nombre_producto_empresa,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_usuario,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                        'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                        'sucursal': sucursal_info.nombre_sucursal if sucursal_info else 'N/A',
                        'estatus_carrito': carrito_usuario.estatuscarrito_prod_usuario,
                        'fecha_creacion_carrito': carrito_usuario.fecha_creacion_carrito_prod_usuario
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_usuario
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_usuario
                
                elif detalle.idproducto_fk_usuario:
                    producto = detalle.idproducto_fk_usuario
                    
                    # Obtener la primera imagen del producto
                    imagen = imagen_producto_usuario.objects.filter(
                        id_producto_fk=producto
                    ).first()
                    
                    productos_carrito.append({
                        'id': producto.id_producto_usuario,
                        'detalle_id': detalle.id_deta_carrito_prod_usuario,
                        'nombre': producto.nombre_producto_usuario,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_usuario,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                        'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None,
                        'sucursal': 'Producto de Usuario',
                        'estatus_carrito': carrito_usuario.estatuscarrito_prod_usuario,
                        'fecha_creacion_carrito': carrito_usuario.fecha_creacion_carrito_prod_usuario
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_usuario
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_usuario
    
    # Calcular total general
    total_general = total_productos + total_servicios
    
    # Información adicional del carrito
    carrito_info = None
    if account_type == 'empresa' and 'carrito_empresa' in locals() and carrito_empresa is not None:
        carrito_info = {
            'id': carrito_empresa.id_carrito_prod_empresa,
            'estatus': carrito_empresa.estatuscarrito_prod_empresa,
            'fecha_creacion': carrito_empresa.fecha_creacion_carrito_prod_empresa,
            'total': carrito_empresa.total_carrito_prod_empresa,
            'propietario': {
                'tipo': 'empresa',
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'id': current_user.id_empresa
            }
        }
    elif account_type == 'usuario' and 'carrito_usuario' in locals() and carrito_usuario is not None:
        carrito_info = {
            'id': carrito_usuario.id_carrito_prod_usuario,
            'estatus': carrito_usuario.estatuscarrito_prod_usuario,
            'fecha_creacion': carrito_usuario.fecha_creacion_carrito_prod_usuario,
            'total': carrito_usuario.total_carrito_prod_usuario,
            'propietario': {
                'tipo': 'usuario',
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'id': current_user.id_usuario
            }
        }
    
    # Verificar si existen pedidos pendientes
    pedidos_pendientes = False
    if account_type == 'empresa':
        pedidos_pendientes = pedido_empresa.objects.filter(
            id_carrito_fk__id_empresa_fk=current_user,
            estado_pedido='pendiente'
        ).exists()
    else:
        pedidos_pendientes = pedido_usuario.objects.filter(
            id_carrito_fk__id_usuario_fk=current_user,
            estado_pedido='pendiente'
        ).exists()
    
    # Verificar si hay cambios de precio para mostrar notificación
    cambios_precio_info = None
    if 'cambios_precio' in locals() and cambios_precio:
        cambios_precio_info = cambios_precio
    
    context = {
        'user_info': user_info,
        'account_type': account_type,
        'productos_carrito': productos_carrito,
        'servicios_carrito': servicios_carrito,
        'total_productos': total_productos,
        'total_servicios': total_servicios,
        'total_general': total_general,
        'cantidad_productos': len(productos_carrito),
        'cantidad_servicios': len(servicios_carrito),
        'carrito_info': carrito_info,
        'pedidos_pendientes': pedidos_pendientes,
        'cambios_precio': cambios_precio_info
    }
    
    return render(request, 'ecommerce_app/carrito.html', context)

def vista_items(request):
    try:
        # Obtener información del usuario autenticado
        user_info = None
        current_user = get_current_user(request)
        if current_user:
            account_type = request.session.get('account_type', 'usuario')
            
            if account_type == 'empresa':
                user_info = {
                    'id': current_user.id_empresa,
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'tipo': current_user.rol_empresa,
                    'is_authenticated': True
                }
            else:
                user_info = {
                    'id': current_user.id_usuario,
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'tipo': current_user.rol_usuario,
                    'is_authenticated': True
                }
        
        item_id = request.GET.get('id')
        item_tipo = request.GET.get('tipo')
        item_origen = request.GET.get('origen', 'empresa')  # Por defecto empresa para compatibilidad
        
        print(f"DEBUG: vista_items - id: {item_id}, tipo: {item_tipo}, origen: {item_origen}")
        
        if not item_id or not item_tipo:
            print(f"DEBUG: Parámetros faltantes - id: {item_id}, tipo: {item_tipo}")
            return redirect('/ecommerce/index/')
        
        item_data = None
        imagenes = []
        
        if item_tipo == 'producto':
            if item_origen == 'empresa':
                # Buscar por producto_sucursal primero (desde búsqueda)
                try:
                    print(f"DEBUG: Buscando producto_sucursal con id: {item_id}")
                    producto_sucursal_obj = producto_sucursal.objects.get(id_producto_sucursal=item_id)
                    producto = producto_sucursal_obj.id_producto_fk
                    print(f"DEBUG: Producto encontrado: {producto.nombre_producto_empresa}")
                    
                    # Obtener imágenes del producto
                    imagenes_producto = imagen_producto_empresa.objects.filter(id_producto_fk=producto)
                    imagenes = [img.ruta_imagen_producto_empresa.url for img in imagenes_producto if img.ruta_imagen_producto_empresa]
                    
                    sucursal_info = {
                        'nombre': producto_sucursal_obj.id_sucursal_fk.nombre_sucursal,
                        'direccion': producto_sucursal_obj.id_sucursal_fk.direccion_sucursal,
                        'precio': producto_sucursal_obj.precio_producto_sucursal,
                        'stock': producto_sucursal_obj.stock_producto_sucursal,
                        'condicion': producto_sucursal_obj.condicion_producto_sucursal,
                        'estatus': producto_sucursal_obj.estatus_producto_sucursal,
                        'latitud': getattr(producto_sucursal_obj.id_sucursal_fk, 'latitud_sucursal', None),
                        'longitud': getattr(producto_sucursal_obj.id_sucursal_fk, 'longitud_sucursal', None),
                        'unidad_presentacion': getattr(producto_sucursal_obj, 'unidad_presentacion_producto_sucursal', 'unidad'),
                        'cantidad_por_presentacion': getattr(producto_sucursal_obj, 'cantidad_por_presentacion_producto_sucursal', None)
                    }
                    
                    item_data = {
                        'id': producto_sucursal_obj.id_producto_sucursal,  # Usar ID del producto_sucursal
                        'nombre': producto.nombre_producto_empresa,
                        'descripcion': producto.descripcion_producto_empresa,

                        'caracteristicas': producto.caracteristicas_generales_empresa,
                        'tipo': 'producto',
                        'tipo_propietario': 'empresa',
                        'empresa': producto.id_empresa_fk.nombre_empresa,
                        'producto_empresa_id': producto.id_producto_empresa,
                        'sucursal': sucursal_info
                    }
                except producto_sucursal.DoesNotExist:
                    print(f"DEBUG: No se encontró producto_sucursal con id: {item_id}, buscando en producto_empresa")
                    # Si no se encuentra por producto_sucursal, buscar directamente por producto_empresa
                    try:
                        producto = producto_empresa.objects.get(id_producto_empresa=item_id)
                        print(f"DEBUG: Producto encontrado directamente: {producto.nombre_producto_empresa}")
                        # Obtener imágenes del producto
                        imagenes_producto = imagen_producto_empresa.objects.filter(id_producto_fk=producto)
                        imagenes = [img.ruta_imagen_producto_empresa.url for img in imagenes_producto if img.ruta_imagen_producto_empresa]
                        
                        # Obtener información de la sucursal si está asociado
                        producto_sucursal_obj = producto_sucursal.objects.filter(id_producto_fk=producto).first()
                        sucursal_info = None
                        if producto_sucursal_obj:
                            sucursal_info = {
                                'nombre': producto_sucursal_obj.id_sucursal_fk.nombre_sucursal,
                                'direccion': producto_sucursal_obj.id_sucursal_fk.direccion_sucursal,
                                'precio': producto_sucursal_obj.precio_producto_sucursal,
                                'stock': producto_sucursal_obj.stock_producto_sucursal,
                                'condicion': producto_sucursal_obj.condicion_producto_sucursal,
                                'estatus': producto_sucursal_obj.estatus_producto_sucursal,
                                'latitud': getattr(producto_sucursal_obj.id_sucursal_fk, 'latitud_sucursal', None),
                                'longitud': getattr(producto_sucursal_obj.id_sucursal_fk, 'longitud_sucursal', None),
                                'unidad_presentacion': getattr(producto_sucursal_obj, 'unidad_presentacion_producto_sucursal', 'unidad'),
                                'cantidad_por_presentacion': getattr(producto_sucursal_obj, 'cantidad_por_presentacion_producto_sucursal', None)
                            }
                        
                        # Solo permitir agregar al carrito si existe producto_sucursal
                        if producto_sucursal_obj:
                            item_data = {
                                'id': producto_sucursal_obj.id_producto_sucursal,  # Usar ID del producto_sucursal
                                'nombre': producto.nombre_producto_empresa,
                                'descripcion': producto.descripcion_producto_empresa,
                                'tipo_propietario': 'empresa',

                                'caracteristicas': producto.caracteristicas_generales_empresa,
                                'tipo': 'producto',
                                'empresa': producto.id_empresa_fk.nombre_empresa,
                                'producto_empresa_id': producto.id_producto_empresa,
                                'sucursal': sucursal_info
                            }
                        else:
                            # Si no hay producto_sucursal, no se puede agregar al carrito
                            print(f"DEBUG: Producto {producto.nombre_producto_empresa} no tiene sucursal asociada")
                            return redirect('/ecommerce/index/')
                    except producto_empresa.DoesNotExist:
                        print(f"DEBUG: No se encontró producto_empresa con id: {item_id}")
                        return redirect('/ecommerce/index/')
            else:  # item_origen == 'usuario'
                try:
                    print(f"DEBUG: Buscando producto_usuario con id: {item_id}")
                    producto = producto_usuario.objects.get(id_producto_usuario=item_id)
                    print(f"DEBUG: Producto de usuario encontrado: {producto.nombre_producto_usuario}")
                    # Obtener imágenes del producto de usuario
                    imagenes_producto = imagen_producto_usuario.objects.filter(id_producto_fk=producto)
                    imagenes = [img.ruta_imagen_producto_usuario.url for img in imagenes_producto if img.ruta_imagen_producto_usuario]
                    
                    # Para productos de usuario, la información está directamente en el producto
                    sucursal_info = {
                        'nombre': f"Usuario: {producto.id_usuario_fk.nombre_usuario}",
                        'direccion': 'Información de contacto disponible',
                        'precio': producto.precio_producto_usuario,
                        'stock': producto.stock_producto_usuario,
                        'condicion': producto.condicion_producto_usuario,
                        'estatus': producto.estatus_producto_usuario,
                        'latitud': getattr(producto, 'latitud_entrega_producto', None),
                        'longitud': getattr(producto, 'longitud_entrega_producto', None),
                        'unidad_presentacion': getattr(producto, 'unidad_presentacion_producto_usuario', 'unidad'),
                        'cantidad_por_presentacion': getattr(producto, 'cantidad_por_presentacion_producto_usuario', None)
                    }
                    
                    item_data = {
                        'id': producto.id_producto_usuario,
                        'nombre': producto.nombre_producto_usuario,
                        'descripcion': producto.descripcion_producto_usuario,

                        'caracteristicas': producto.caracteristicas_generales_usuario,
                        'tipo': 'producto',
                        'tipo_propietario': 'usuario',
                        'empresa': f"Usuario: {producto.id_usuario_fk.nombre_usuario}",
                        'sucursal': sucursal_info
                    }
                except producto_usuario.DoesNotExist:
                    print(f"DEBUG: No se encontró producto_usuario con id: {item_id}")
                    return redirect('/ecommerce/index/')
                
        elif item_tipo == 'servicio':
            if item_origen == 'empresa':
                # Buscar por servicio_sucursal primero (desde búsqueda)
                try:
                    print(f"DEBUG: Buscando servicio_sucursal con id: {item_id}")
                    servicio_sucursal_obj = servicio_sucursal.objects.get(id_servicio_sucursal=item_id)
                    servicio = servicio_sucursal_obj.id_servicio_fk
                    print(f"DEBUG: Servicio encontrado: {servicio.nombre_servicio_empresa}")
                    
                    # Obtener imágenes del servicio
                    imagenes_servicio = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio)
                    imagenes = [img.ruta_imagen_servicio_empresa.url for img in imagenes_servicio if img.ruta_imagen_servicio_empresa]
                    
                    sucursal_info = {
                        'nombre': servicio_sucursal_obj.id_sucursal_fk.nombre_sucursal,
                        'direccion': servicio_sucursal_obj.id_sucursal_fk.direccion_sucursal,
                        'precio': servicio_sucursal_obj.precio_servicio_sucursal,
                        'estatus': servicio_sucursal_obj.estatus_servicio_sucursal,
                        'id_sucursal': servicio_sucursal_obj.id_sucursal_fk.id_sucursal,
                        'latitud': getattr(servicio_sucursal_obj.id_sucursal_fk, 'latitud_sucursal', None),
                        'longitud': getattr(servicio_sucursal_obj.id_sucursal_fk, 'longitud_sucursal', None),
                        'id_servicio_fk': servicio.id_servicio_empresa
                    }
                    
                    item_data = {
                        'id': servicio_sucursal_obj.id_servicio_sucursal,
                        'nombre': servicio.nombre_servicio_empresa,
                        'descripcion': servicio.descripcion_servicio_empresa,
                        'caracteristicas': servicio.descripcion_servicio_empresa,
                        'tipo': 'servicio',
                        'tipo_propietario': 'empresa',
                        'empresa': servicio.id_empresa_fk.nombre_empresa,
                        'sucursal': sucursal_info
                    }
                except servicio_sucursal.DoesNotExist:
                    print(f"DEBUG: No se encontró servicio_sucursal con id: {item_id}, buscando en servicio_empresa")
                    # Si no se encuentra por servicio_sucursal, buscar directamente por servicio_empresa
                    try:
                        servicio = servicio_empresa.objects.get(id_servicio_empresa=item_id)
                        print(f"DEBUG: Servicio encontrado directamente: {servicio.nombre_servicio_empresa}")
                        # Obtener imágenes del servicio
                        imagenes_servicio = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio)
                        imagenes = [img.ruta_imagen_servicio_empresa.url for img in imagenes_servicio if img.ruta_imagen_servicio_empresa]
                        
                        # Obtener información de la sucursal si está asociado
                        servicio_sucursal_obj = servicio_sucursal.objects.filter(id_servicio_fk=servicio).first()
                        sucursal_info = None
                        if servicio_sucursal_obj:
                            sucursal_info = {
                                'nombre': servicio_sucursal_obj.id_sucursal_fk.nombre_sucursal,
                                'direccion': servicio_sucursal_obj.id_sucursal_fk.direccion_sucursal,
                                'precio': servicio_sucursal_obj.precio_servicio_sucursal,
                                'estatus': servicio_sucursal_obj.estatus_servicio_sucursal
                                , 'latitud': getattr(servicio_sucursal_obj.id_sucursal_fk, 'latitud_sucursal', None)
                                , 'longitud': getattr(servicio_sucursal_obj.id_sucursal_fk, 'longitud_sucursal', None)
                            }
                        
                        item_data = {
                            'id': servicio.id_servicio_empresa,
                            'nombre': servicio.nombre_servicio_empresa,
                            'descripcion': servicio.descripcion_servicio_empresa,
                            'caracteristicas': servicio.descripcion_servicio_empresa,
                            'tipo': 'servicio',
                            'tipo_propietario': 'empresa',
                            'empresa': servicio.id_empresa_fk.nombre_empresa,
                            'sucursal': sucursal_info
                        }
                    except servicio_empresa.DoesNotExist:
                        print(f"DEBUG: No se encontró servicio_empresa con id: {item_id}")
                        return redirect('/ecommerce/index/')
            else:  # item_origen == 'usuario'
                try:
                    print(f"DEBUG: Buscando servicio_usuario con id: {item_id}")
                    servicio = servicio_usuario.objects.get(id_servicio_usuario=item_id)
                    print(f"DEBUG: Servicio de usuario encontrado: {servicio.nombre_servicio_usuario}")
                    # Obtener imágenes del servicio de usuario
                    imagenes_servicio = imagen_servicio_usuario.objects.filter(id_servicio_fk=servicio)
                    imagenes = [img.ruta_imagen_servicio_usuario.url for img in imagenes_servicio if img.ruta_imagen_servicio_usuario]
                    
                    # Para servicios de usuario, la información está directamente en el servicio
                    sucursal_info = {
                        'nombre': f"Usuario: {servicio.id_usuario_fk.nombre_usuario}",
                        'direccion': 'Información de contacto disponible',
                        'precio': servicio.precio_servicio_usuario if servicio.precio_servicio_usuario else 'Consultar',
                        'estatus': servicio.estatus_servicio_usuario
                        , 'latitud': None
                        , 'longitud': None
                    }
                    
                    item_data = {
                        'id': servicio.id_servicio_usuario,
                        'nombre': servicio.nombre_servicio_usuario,
                        'descripcion': servicio.descripcion_servicio_usuario,
                        'caracteristicas': servicio.descripcion_servicio_usuario,
                        'tipo': 'servicio',
                        'tipo_propietario': 'usuario',
                        'empresa': f"Usuario: {servicio.id_usuario_fk.nombre_usuario}",
                        'sucursal': sucursal_info
                    }
                except servicio_usuario.DoesNotExist:
                    print(f"DEBUG: No se encontró servicio_usuario con id: {item_id}")
                    return redirect('/ecommerce/index/')
        else:
            print(f"DEBUG: Tipo de item no válido: {item_tipo}")
            return redirect('/ecommerce/index/')
        
        # Obtener atributos y valores asociados al producto
        atributos_producto = []
        if item_tipo == 'producto' and item_data:
            if item_data.get('tipo_propietario') == 'empresa':
                # Para productos de empresa, item_data['id'] puede ser el id de producto_sucursal.
                # Preferir producto_empresa_id si fue incluido en el contexto; si no, intentar resolverlo desde producto_sucursal.
                prod_empresa_id = item_data.get('producto_empresa_id')
                if not prod_empresa_id:
                    try:
                        prod_suc = producto_sucursal.objects.get(id_producto_sucursal=item_data['id'])
                        prod_empresa_id = prod_suc.id_producto_fk.id_producto_empresa
                    except Exception:
                        prod_empresa_id = None

                if prod_empresa_id:
                    valores_atributos = ValorAtributoProducto.objects.filter(producto_empresa__id_producto_empresa=prod_empresa_id)
                else:
                    valores_atributos = ValorAtributoProducto.objects.none()
            else:
                valores_atributos = ValorAtributoProducto.objects.filter(producto_usuario__id_producto_usuario=item_data['id'])
            atributos_producto = [
                {
                    'nombre': v.atributo.nombre,
                    'tipo_dato': v.atributo.tipo_dato,
                    'valor': v.valor_texto or v.valor_numero or v.valor_decimal or v.valor_fecha or v.valor_booleano
                }
                for v in valores_atributos
            ]
        
        # Verificar si el item está en favoritos del usuario
        es_favorito = False
        if current_user and account_type == 'usuario' and item_data:
            favorito_filter = {'id_usuario_fk': current_user}
            
            if item_tipo == 'producto':
                if item_origen == 'empresa':
                    favorito_filter['id_producto_sucursal_fk'] = item_data['id']
                else:
                    favorito_filter['id_producto_usuario_fk'] = item_data['id']
            elif item_tipo == 'servicio':
                if item_origen == 'empresa':
                    favorito_filter['id_servicio_sucursal_fk'] = item_data['id']
                else:
                    favorito_filter['id_servicio_usuario_fk'] = item_data['id']
            
            es_favorito = favorito_usuario.objects.filter(**favorito_filter).exists()
        
        context = {
            'item': item_data,
            'imagenes': imagenes,
            'user_info': user_info,
            'atributos_producto': atributos_producto,
            'es_favorito': es_favorito
        }

        # If the user's coordinates were provided (e.g. from search 'Cerca de mi'),
        # calculate distance (km) between user and the item's location and
        # include it in the context so the template can show it.
        try:
            user_lat = request.GET.get('latitud') or request.GET.get('lat')
            user_lng = request.GET.get('longitud') or request.GET.get('lng')
            if user_lat and user_lng and item_data:
                try:
                    user_lat_f = float(user_lat)
                    user_lng_f = float(user_lng)
                    target_lat = None
                    target_lng = None
                    # Determine target coordinates depending on item type and origin
                    if item_tipo == 'producto':
                        if item_origen == 'empresa':
                            try:
                                prod_suc = producto_sucursal.objects.select_related('id_sucursal_fk').get(id_producto_sucursal=item_data['id'])
                                suc = prod_suc.id_sucursal_fk
                                target_lat = getattr(suc, 'latitud_sucursal', None)
                                target_lng = getattr(suc, 'longitud_sucursal', None)
                            except Exception:
                                target_lat = target_lng = None
                        else:
                            try:
                                prod = producto_usuario.objects.get(id_producto_usuario=item_data['id'])
                                target_lat = getattr(prod, 'latitud_entrega_producto', None)
                                target_lng = getattr(prod, 'longitud_entrega_producto', None)
                            except Exception:
                                target_lat = target_lng = None
                    elif item_tipo == 'servicio':
                        if item_origen == 'empresa':
                            try:
                                serv_suc = servicio_sucursal.objects.select_related('id_sucursal_fk').get(id_servicio_sucursal=item_data['id'])
                                suc = serv_suc.id_sucursal_fk
                                target_lat = getattr(suc, 'latitud_sucursal', None)
                                target_lng = getattr(suc, 'longitud_sucursal', None)
                            except Exception:
                                target_lat = target_lng = None
                        else:
                            # Servicios de usuario no siempre tienen coordenadas; skip
                            target_lat = target_lng = None

                    if target_lat is not None and target_lng is not None and str(target_lat).strip() != '' and str(target_lng).strip() != '':
                        try:
                            tlat = float(target_lat)
                            tlng = float(target_lng)
                            # Haversine formula
                            import math
                            def haversine(lat1, lon1, lat2, lon2):
                                R = 6371.0
                                dlat = math.radians(lat2 - lat1)
                                dlon = math.radians(lon2 - lon1)
                                a = math.sin(dlat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2
                                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                                return R * c

                            distancia_km = round(haversine(user_lat_f, user_lng_f, tlat, tlng), 2)
                            # Add to both context and item for template convenience
                            context['distancia'] = distancia_km
                            if isinstance(context.get('item'), dict):
                                context['item']['distancia'] = distancia_km
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            # Non-fatal; ignore distance calculation errors
            pass

        # Cargar primeros 5 comentarios para renderizado inicial en la plantilla
        try:
            # Reusar lógica similar a obtener_comentarios
            comments_qs = comentario.objects.none()
            if item_tipo == 'producto':
                if item_origen == 'empresa':
                    comments_qs = comentario.objects.filter(producto_sucursal__id_producto_sucursal=item_data['id'])
                else:
                    comments_qs = comentario.objects.filter(producto_usuario__id_producto_usuario=item_data['id'])
            elif item_tipo == 'servicio':
                if item_origen == 'empresa':
                    comments_qs = comentario.objects.filter(servicio_sucursal__id_servicio_sucursal=item_data['id'])
                else:
                    comments_qs = comentario.objects.filter(servicio_usuario__id_servicio_usuario=item_data['id'])

            total_comments = comments_qs.count()
            initial_comments = comments_qs[:5]
            # Convertir a formato serializable simple para template
            iniciales = []
            for c in initial_comments:
                if c.id_usuario_autor:
                    autor = getattr(c.id_usuario_autor, 'nombre_usuario', 'Usuario')
                    avatar_field = getattr(c.id_usuario_autor, 'foto_usuario', None)
                else:
                    autor = getattr(c.id_empresa_autor, 'nombre_empresa', 'Empresa')
                    avatar_field = getattr(c.id_empresa_autor, 'logo_empresa', None)
                avatar_url = None
                try:
                    if avatar_field:
                        avatar_url = avatar_field.url if hasattr(avatar_field, 'url') else str(avatar_field)
                except Exception:
                    avatar_url = None
                if not avatar_url:
                    avatar_url = '/static/avatars/Cartoon Style Robot.jpg'
                # Determine if current_user is the author of this comment
                is_author = False
                try:
                    if current_user:
                        if hasattr(current_user, 'id_usuario') and c.id_usuario_autor and c.id_usuario_autor.id_usuario == getattr(current_user, 'id_usuario'):
                            is_author = True
                        if hasattr(current_user, 'id_empresa') and c.id_empresa_autor and c.id_empresa_autor.id_empresa == getattr(current_user, 'id_empresa'):
                            is_author = True
                except Exception:
                    is_author = False

                iniciales.append({'id': c.id_comentario, 'autor': autor, 'avatar': avatar_url, 'texto': c.texto, 'fecha': timezone.localtime(c.fecha_creacion).strftime('%Y-%m-%d %H:%M:%S'), 'is_author': is_author})

            context['initial_comments'] = iniciales
            context['comments_total_count'] = total_comments
        except Exception:
            context['initial_comments'] = []
            context['comments_total_count'] = 0

        print(f"DEBUG: Renderizando vista_items exitosamente para {item_data['tipo']}: {item_data['nombre']}")
        return render(request, 'ecommerce_app/vista_items.html', context)
        
    except Exception as e:
        print(f"Error en vista_items: {str(e)}")
        # En lugar de redirigir al index, mostrar un mensaje de error
        context = {
            'error': True,
            'error_message': f'Error al cargar el item: {str(e)}',
            'item': None,
            'imagenes': [],
            'user_info': user_info
        }
        return render(request, 'ecommerce_app/vista_items.html', context)


@csrf_exempt
def eliminar_comentario(request):
    """Eliminar un comentario. POST con: comentario_id. Solo el autor (usuario o empresa) puede eliminar su comentario."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    try:
        import json
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        comentario_id = data.get('comentario_id')
        if not comentario_id:
            return JsonResponse({'success': False, 'message': 'ID de comentario requerido'}, status=400)

        # Verificar autenticación
        if not is_user_authenticated(request):
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'}, status=403)

        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Sesión inválida'}, status=403)

        try:
            c = comentario.objects.get(id_comentario=comentario_id)
        except comentario.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Comentario no encontrado'}, status=404)

        # Verificar autoría
        is_author = False
        try:
            if hasattr(current_user, 'id_usuario') and c.id_usuario_autor and c.id_usuario_autor.id_usuario == getattr(current_user, 'id_usuario'):
                is_author = True
            if hasattr(current_user, 'id_empresa') and c.id_empresa_autor and c.id_empresa_autor.id_empresa == getattr(current_user, 'id_empresa'):
                is_author = True
        except Exception:
            is_author = False

        if not is_author:
            return JsonResponse({'success': False, 'message': 'No autorizado para eliminar este comentario'}, status=403)

        # Eliminar
        c.delete()
        return JsonResponse({'success': True, 'message': 'Comentario eliminado'})
    except Exception as e:
        logger.exception(f"Error en eliminar_comentario: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def editar_comentario(request):
    """Editar un comentario. POST con: comentario_id, texto. Solo el autor puede editar."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    try:
        import json
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        comentario_id = data.get('comentario_id')
        nuevo_texto = (data.get('texto') or '').strip()
        if not comentario_id or not nuevo_texto:
            return JsonResponse({'success': False, 'message': 'ID de comentario y texto requerido'}, status=400)

        if not is_user_authenticated(request):
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'}, status=403)

        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Sesión inválida'}, status=403)

        try:
            c = comentario.objects.get(id_comentario=comentario_id)
        except comentario.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Comentario no encontrado'}, status=404)

        # Verificar autoría
        is_author = False
        try:
            if hasattr(current_user, 'id_usuario') and c.id_usuario_autor and c.id_usuario_autor.id_usuario == getattr(current_user, 'id_usuario'):
                is_author = True
            if hasattr(current_user, 'id_empresa') and c.id_empresa_autor and c.id_empresa_autor.id_empresa == getattr(current_user, 'id_empresa'):
                is_author = True
        except Exception:
            is_author = False

        if not is_author:
            return JsonResponse({'success': False, 'message': 'No autorizado para editar este comentario'}, status=403)

        c.texto = nuevo_texto
        c.save()
        return JsonResponse({'success': True, 'message': 'Comentario actualizado', 'texto': c.texto, 'fecha': timezone.localtime(c.fecha_actualizacion).strftime('%Y-%m-%d %H:%M:%S')})
    except Exception as e:
        logger.exception(f"Error en editar_comentario: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



def perfil_usuario(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    usuario_obj = None
    
    # Verificar si se está solicitando un perfil específico por ID
    # Verificar si hay usuario autenticado primero
    current_user = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
    
    account_type = request.session.get('account_type', 'usuario')
    
    usuario_id = request.GET.get('id')
    if usuario_id:
        try:
            usuario_obj = usuario.objects.get(id_usuario=usuario_id)
            # Si el id solicitado es el del usuario autenticado, mostrar su perfil privado
            is_owner = False
            if current_user and hasattr(current_user, 'id_usuario') and str(current_user.id_usuario) == str(usuario_id):
                is_owner = True

            if is_owner:
                usuario_obj = current_user
                user_info = get_user_info_with_avatar(current_user, account_type)
                user_info['is_public_profile'] = False
            else:
                # Para perfiles públicos, verificar si hay usuario autenticado
                if current_user:
                    user_info = get_user_info_with_avatar(current_user, account_type)
                    user_info['is_public_profile'] = True
                    # Mostrar avatar del perfil que se está viendo
                    user_info['avatar_chatbot'] = usuario_obj.avatar_chatbot if getattr(usuario_obj, 'avatar_chatbot', None) else None
                else:
                    user_info = {
                        'is_authenticated': False,
                        'is_public_profile': True,
                        'avatar_chatbot': usuario_obj.avatar_chatbot if getattr(usuario_obj, 'avatar_chatbot', None) else None
                    }
        except usuario.DoesNotExist:
            # Si no existe el usuario, redirigir o mostrar error
            user_info = get_user_info_with_avatar(current_user, account_type) if current_user else {'is_authenticated': False}
            return render(request, 'ecommerce_app/perfil_usuario.html', {
                'error': 'Usuario no encontrado',
                'user_info': user_info
            })
    else:
        if current_user and account_type == 'usuario':
            # Para usuarios autenticados, current_user ya es el usuario
            usuario_obj = current_user
            user_info = get_user_info_with_avatar(current_user, account_type)
        elif current_user and account_type == 'empresa':
            # Si es empresa autenticada, redirigir al perfil de empresa
            return redirect('/ecommerce/perfil_empresa/')
        else:
            # Usuario no autenticado - mostrar información por defecto
            user_info = {
                'is_authenticated': False
            }
            # Obtener el primer usuario disponible para mostrar como ejemplo
            usuario_obj = usuario.objects.first()
            
    
    # Intentar cargar metodos de pago asociados al usuario mostrado (solo activos)
    metodos_pago = []
    try:
        from .models import MetodoPago
        if usuario_obj:
            metodos_pago_qs = MetodoPago.objects.filter(usuario=usuario_obj, activo=True)
            # Convertir a lista simple para pasar al template
            metodos_pago = list(metodos_pago_qs)
    except Exception:
        metodos_pago = []

    return render(request, 'ecommerce_app/perfil_usuario.html', {
        'user_info': user_info,
        'usuario': usuario_obj,
        'metodos_pago': metodos_pago
    })


def perfil_sucursales_asociadas(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    empresa_obj = None
    sucursales_empresa = []
    
    # Verificar si se está solicitando sucursales de una empresa específica
    empresa_id = request.GET.get('empresa_id')
    
    # Verificar si hay usuario autenticado
    current_user = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
    
    account_type = request.session.get('account_type', 'usuario')
    
    # Si se especifica una empresa_id, mostrar sucursales de esa empresa
    if empresa_id:
        try:
            empresa_obj = empresa.objects.get(id_empresa=empresa_id)
            sucursales_empresa = sucursal.objects.filter(id_empresa_fk=empresa_obj).order_by('nombre_sucursal')
            user_info = {
                'is_authenticated': bool(current_user),
                'is_public_profile': True
            }
            
            return render(request, 'ecommerce_app/perfil_sucursales_asociadas.html', {
                'user_info': user_info,
                'empresa_obj': empresa_obj,
                'sucursales_empresa': sucursales_empresa,
                'usuario': None
            })
        except empresa.DoesNotExist:
            # Si no existe la empresa, mostrar error
            return render(request, 'ecommerce_app/perfil_sucursales_asociadas.html', {
                'error': 'Empresa no encontrada',
                'user_info': {'is_authenticated': bool(current_user)},
                'empresa_obj': None,
                'sucursales_empresa': [],
                'usuario': None
            })
    
    elif current_user and account_type == 'empresa':
        # Para empresas autenticadas, current_user ya es la empresa
        empresa_obj = current_user
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True,
            'empresa_nombre': current_user.nombre_empresa
        }
        
        # Obtener todas las sucursales de esta empresa
        sucursales_empresa = sucursal.objects.filter(id_empresa_fk=empresa_obj).order_by('nombre_sucursal')
        
    elif current_user:
        # Para usuarios autenticados, buscar empresa asociada
        empresa_nombre = None
        try:
            empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
            if empresa_obj:
                empresa_nombre = empresa_obj.nombre_empresa
                # Obtener sucursales de la empresa asociada
                sucursales_empresa = sucursal.objects.filter(id_empresa_fk=empresa_obj).order_by('nombre_sucursal')
        except Exception as e:
            empresa_obj = None
            empresa_nombre = None
        
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True,
            'empresa_nombre': empresa_nombre
        }
    else:
        # Usuario no autenticado - mostrar información por defecto
        user_info = {
            'is_authenticated': False
        }
        # Obtener la primera empresa disponible para mostrar como ejemplo
        empresa_obj = empresa.objects.first()
        if empresa_obj:
            sucursales_empresa = sucursal.objects.filter(id_empresa_fk=empresa_obj).order_by('nombre_sucursal')
    
    return render(request, 'ecommerce_app/perfil_sucursales_asociadas.html', {
        'user_info': user_info,
        'empresa_obj': empresa_obj,
        'sucursales_empresa': sucursales_empresa,
        'usuario': current_user if current_user and account_type == 'usuario' else None
    })

@require_GET
def list_avatars(request):
    """
    Vista para listar los avatares disponibles en la carpeta estática
    """
    avatars_dir = os.path.join(settings.STATIC_ROOT, 'avatars')
    
    try:
        # Obtener lista de archivos en el directorio de avatares
        files = [f for f in os.listdir(avatars_dir) 
                if os.path.isfile(os.path.join(avatars_dir, f)) 
                and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
        
        return JsonResponse({
            'success': True,
            'files': files
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def prueba(request):
    return render(request, 'ecommerce_app/prueba.html')

def debug_user_info(request):
    # Verificar si hay usuario autenticado
    current_user = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
    
    # Obtener tipo de cuenta
    account_type = request.session.get('account_type', 'usuario')
    
    # Inicializar variables
    user_info = {
        'is_authenticated': bool(current_user),
        'tipo': 'empresa' if account_type == 'empresa' else 'persona'
    }
    
    if current_user and account_type != 'empresa':
        user_info.update({
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'id': current_user.id_usuario
        })
    elif current_user and account_type == 'empresa':
        user_info.update({
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'id': current_user.id_empresa
        })
    
    return render(request, 'ecommerce_app/debug_user_info.html', {
        'user_info': user_info
    })


def perfil_productos(request):
    from collections import defaultdict
    
    # Verificar si hay usuario autenticado
    current_user = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
    
    # Obtener tipo de cuenta
    account_type = request.session.get('account_type', 'usuario')
    
    # Verificar si se está solicitando productos de una empresa o usuario específico
    empresa_id = request.GET.get('empresa_id')
    usuario_id = request.GET.get('usuario_id')
    
    # Inicializar variables
    productos = []
    user_info = {
        'is_authenticated': bool(current_user),
        'tipo': 'empresa' if account_type == 'empresa' else 'persona'
    }
    
    # Si se especifica una empresa_id, mostrar productos de esa empresa
    if empresa_id:
        try:
            empresa_obj = empresa.objects.get(id_empresa=empresa_id)
            # Obtener productos a través de producto_sucursal para mostrar solo productos disponibles en sucursales
            productos_sucursal_query = producto_sucursal.objects.filter(
                id_sucursal_fk__id_empresa_fk=empresa_obj,
                estatus_producto_sucursal='Activo'
            ).select_related('id_producto_fk__id_categoria_prod_fk', 'id_sucursal_fk')
            
            productos_con_imagenes = []
            productos_por_categoria = defaultdict(list)
            productos_procesados = set()
            
            for prod_sucursal in productos_sucursal_query:
                prod = prod_sucursal.id_producto_fk
                
                # Solo procesar cada producto una vez
                if prod.id_producto_empresa not in productos_procesados:
                    primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
                    prod.primera_imagen = primera_imagen
                    
                    # Obtener todas las sucursales asociadas al producto
                    sucursales_producto = producto_sucursal.objects.filter(
                        id_producto_fk=prod,
                        id_sucursal_fk__id_empresa_fk=empresa_obj,
                        estatus_producto_sucursal='Activo'
                    ).select_related('id_sucursal_fk')
                    prod.sucursales_asociadas = sucursales_producto
                    
                    productos_con_imagenes.append(prod)
                    productos_procesados.add(prod.id_producto_empresa)
                    
                    # Agrupar por categoría
                    categoria_nombre = prod.id_categoria_prod_fk.nombre_categoria_prod_empresa if prod.id_categoria_prod_fk else 'Sin categoría'
                    productos_por_categoria[categoria_nombre].append(prod)
            
            entity_name = f'Productos de {empresa_obj.nombre_empresa}'
            
            # Configurar user_info para mostrar como empresa cuando se especifica empresa_id
            user_info['tipo'] = 'empresa'
            
            # Si hay un usuario autenticado, agregar su información al user_info
            if current_user and account_type == 'empresa':
                user_info.update({
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'id': current_user.id_empresa,
                    'empresa_nombre': current_user.nombre_empresa,
                    'avatar_chatbot': getattr(current_user, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
                })
            elif current_user:
                user_info.update({
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'id': current_user.id_usuario,
                    'avatar_chatbot': getattr(current_user, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
                })
            
            # Para el chatbot, usar el avatar de la empresa si está definido, si no fallback al avatar por defecto
            user_info['avatar_chatbot'] = getattr(empresa_obj, 'avatar_chatbot_empresa', None) or getattr(empresa_obj, 'avatar_chatbot', None) or 'avatars/Cartoon Style Robot.jpg'
            
            return render(request, 'ecommerce_app/perfil_productos.html', {
                'user_info': user_info,
                'empresa_obj': empresa_obj,
                'productos': productos_con_imagenes,
                'productos_por_categoria': dict(productos_por_categoria),
                'entity_name': entity_name
            })
        except empresa.DoesNotExist:
            # Si no existe la empresa, mostrar error
            return render(request, 'ecommerce_app/perfil_productos.html', {
                'error': 'Empresa no encontrada',
                'user_info': user_info,
                'productos': [],
                'entity_name': 'Error'
            })
    elif usuario_id:
        try:
            usuario_obj = usuario.objects.get(id_usuario=usuario_id)
            productos_query = producto_usuario.objects.filter(id_usuario_fk=usuario_obj).select_related('id_categoria_prod_fk')
            productos_con_imagenes = []
            productos_por_categoria = defaultdict(list)
            
            for prod in productos_query:
                primera_imagen = imagen_producto_usuario.objects.filter(id_producto_fk=prod).first()
                prod.primera_imagen = primera_imagen
                productos_con_imagenes.append(prod)
                
                # Agrupar por categoría
                categoria_nombre = prod.id_categoria_prod_fk.nombre_categoria_prod_usuario if prod.id_categoria_prod_fk else 'Sin categoría'
                productos_por_categoria[categoria_nombre].append(prod)
            
            entity_name = f'Productos de {usuario_obj.nombre_usuario}'
            
            # Configurar user_info para mostrar como persona cuando se especifica usuario_id
            user_info['tipo'] = 'persona'
            
            # Si hay un usuario autenticado, agregar su información al user_info
            if current_user and account_type == 'empresa':
                user_info.update({
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'id': current_user.id_empresa,
                    'empresa_nombre': current_user.nombre_empresa
                })
            elif current_user:
                user_info.update({
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'id': current_user.id_usuario,
                    'avatar_chatbot': getattr(current_user, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
                })
            
            # Para el chatbot, usar el avatar del usuario cuyo perfil se está viendo
            user_info['avatar_chatbot'] = getattr(usuario_obj, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
            
            return render(request, 'ecommerce_app/perfil_productos.html', {
                'user_info': user_info,
                'usuario_obj': usuario_obj,
                'productos': productos_con_imagenes,
                'productos_por_categoria': dict(productos_por_categoria),
                'entity_name': entity_name
            })
        except usuario.DoesNotExist:
            # Si no existe el usuario, mostrar error
            return render(request, 'ecommerce_app/perfil_productos.html', {
                'error': 'Usuario no encontrado',
                'user_info': user_info,
                'productos': [],
                'entity_name': 'Error'
            })
    
    elif current_user and account_type == 'empresa':
        # Usuario autenticado es empresa
        empresa_obj = current_user
        empresa_nombre = empresa_obj.nombre_empresa
        
        # Obtener productos de la empresa con sus imágenes
        productos_query = producto_empresa.objects.filter(id_empresa_fk=current_user).select_related('id_categoria_prod_fk')
        productos_con_imagenes = []
        productos_por_categoria = defaultdict(list)
        
        for prod in productos_query:
            primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
            prod.primera_imagen = primera_imagen
            
            # Obtener sucursales asociadas al producto
            sucursales_producto = producto_sucursal.objects.filter(id_producto_fk=prod).select_related('id_sucursal_fk')
            prod.sucursales_asociadas = sucursales_producto
            
            productos_con_imagenes.append(prod)
            
            # Agrupar por categoría
            categoria_nombre = prod.id_categoria_prod_fk.nombre_categoria_prod_empresa if prod.id_categoria_prod_fk else 'Sin categoría'
            productos_por_categoria[categoria_nombre].append(prod)
        
        user_info.update({
            'nombre': empresa_nombre,
            'email': empresa_obj.correo_empresa,
            'id': empresa_obj.id_empresa
        })
        
        return render(request, 'ecommerce_app/perfil_productos.html', {
            'user_info': user_info,
            'empresa_obj': empresa_obj,
            'productos': productos_con_imagenes,
            'productos_por_categoria': dict(productos_por_categoria),
            'entity_name': empresa_nombre
        })
    elif current_user:
        # Usuario autenticado es persona
        usuario_obj = current_user
        usuario_nombre = usuario_obj.nombre_usuario
        
        # Obtener productos del usuario con sus imágenes
        productos_query = producto_usuario.objects.filter(id_usuario_fk=current_user).select_related('id_categoria_prod_fk')
        productos_con_imagenes = []
        productos_por_categoria = defaultdict(list)
        
        for prod in productos_query:
            primera_imagen = imagen_producto_usuario.objects.filter(id_producto_fk=prod).first()
            prod.primera_imagen = primera_imagen
            productos_con_imagenes.append(prod)
            
            # Agrupar por categoría
            categoria_nombre = prod.id_categoria_prod_fk.nombre_categoria_prod_usuario if prod.id_categoria_prod_fk else 'Sin categoría'
            productos_por_categoria[categoria_nombre].append(prod)
        
        user_info.update({
            'nombre': usuario_nombre,
            'email': usuario_obj.correo_usuario,
            'id': usuario_obj.id_usuario
        })
        
        return render(request, 'ecommerce_app/perfil_productos.html', {
            'user_info': user_info,
            'usuario_obj': usuario_obj,
            'productos': productos_con_imagenes,
            'productos_por_categoria': dict(productos_por_categoria),
            'entity_name': usuario_nombre
        })
    else:
        # Usuario no autenticado - mostrar productos de ejemplo
        # Mostrar productos de la primera empresa disponible
        empresa_obj = empresa.objects.first()
        productos_con_imagenes = []
        entity_name = 'Productos Disponibles'
        
        if empresa_obj:
            productos_query = producto_empresa.objects.filter(id_empresa_fk=empresa_obj).select_related('id_categoria_prod_fk')[:5]  # Limitar a 5 productos
            productos_por_categoria = defaultdict(list)
            
            for prod in productos_query:
                primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
                prod.primera_imagen = primera_imagen
                productos_con_imagenes.append(prod)
                
                # Agrupar por categoría
                categoria_nombre = prod.id_categoria_prod_fk.nombre_categoria_prod_empresa if prod.id_categoria_prod_fk else 'Sin categoría'
                productos_por_categoria[categoria_nombre].append(prod)
            entity_name = f'Productos de {empresa_obj.nombre_empresa}'
        else:
            productos_por_categoria = {}
        
        return render(request, 'ecommerce_app/perfil_productos.html', {
            'user_info': user_info,
            'empresa_obj': empresa_obj,
            'productos': productos_con_imagenes,
            'productos_por_categoria': dict(productos_por_categoria),
            'entity_name': entity_name
        })


def perfil_servicios(request):
    from collections import defaultdict
    
    # Verificar si hay usuario autenticado
    current_user = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
    
    # Obtener tipo de cuenta
    account_type = request.session.get('account_type', 'usuario')
    
    # Verificar si se está solicitando servicios de una empresa o usuario específico
    empresa_id = request.GET.get('empresa_id')
    usuario_id = request.GET.get('usuario_id')
    
    # Inicializar variables
    servicios = []
    user_info = {
        'is_authenticated': bool(current_user),
        'tipo': 'empresa' if account_type == 'empresa' else 'persona'
    }
    
    # Si se especifica una empresa_id, mostrar servicios de esa empresa
    if empresa_id:
        try:
            empresa_obj = empresa.objects.get(id_empresa=empresa_id)
            servicios_query = servicio_empresa.objects.filter(id_empresa_fk=empresa_obj).select_related('id_categoria_servicios_fk')
            servicios_con_imagenes = []
            servicios_por_categoria = defaultdict(list)
            
            for serv in servicios_query:
                primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=serv).first()
                serv.primera_imagen = primera_imagen
                
                # Obtener sucursales asociadas al servicio
                sucursales_servicio = servicio_sucursal.objects.filter(id_servicio_fk=serv).select_related('id_sucursal_fk')
                serv.sucursales_asociadas = sucursales_servicio
                
                servicios_con_imagenes.append(serv)
                
                # Agrupar por categoría
                categoria_nombre = serv.id_categoria_servicios_fk.nombre_categoria_serv_empresa if serv.id_categoria_servicios_fk else 'Sin categoría'
                servicios_por_categoria[categoria_nombre].append(serv)
            
            entity_name = f'Servicios de {empresa_obj.nombre_empresa}'
            
            # Configurar user_info para mostrar como empresa cuando se especifica empresa_id
            user_info['tipo'] = 'empresa'
            
            # Si hay un usuario autenticado, agregar su información al user_info
            if current_user and account_type == 'empresa':
                user_info.update({
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'id': current_user.id_empresa,
                    'empresa_nombre': current_user.nombre_empresa,
                    'avatar_chatbot': getattr(current_user, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
                })
            elif current_user:
                user_info.update({
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'id': current_user.id_usuario,
                    'avatar_chatbot': getattr(current_user, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
                })
            
            # Para el chatbot, usar el avatar por defecto cuando se ve perfil de empresa
            user_info['avatar_chatbot'] = 'avatars/Cartoon Style Robot.jpg'
            
            return render(request, 'ecommerce_app/perfil_servicios.html', {
                'user_info': user_info,
                'empresa_obj': empresa_obj,
                'servicios': servicios_con_imagenes,
                'servicios_por_categoria': dict(servicios_por_categoria),
                'entity_name': entity_name
            })
        except empresa.DoesNotExist:
            # Si no existe la empresa, mostrar error
            return render(request, 'ecommerce_app/perfil_servicios.html', {
                'error': 'Empresa no encontrada',
                'user_info': user_info,
                'servicios': [],
                'entity_name': 'Error'
            })
    elif usuario_id:
        try:
            usuario_obj = usuario.objects.get(id_usuario=usuario_id)
            servicios_query = servicio_usuario.objects.filter(id_usuario_fk=usuario_obj).select_related('id_categoria_servicios_fk')
            servicios_con_imagenes = []
            servicios_por_categoria = defaultdict(list)
            
            for serv in servicios_query:
                primera_imagen = imagen_servicio_usuario.objects.filter(id_servicio_fk=serv).first()
                serv.primera_imagen = primera_imagen
                servicios_con_imagenes.append(serv)
                
                # Agrupar por categoría
                categoria_nombre = serv.id_categoria_servicios_fk.nombre_categoria_serv_usuario if serv.id_categoria_servicios_fk else 'Sin categoría'
                servicios_por_categoria[categoria_nombre].append(serv)
            
            entity_name = f'Servicios de {usuario_obj.nombre_usuario}'
            
            # Configurar user_info para mostrar como persona cuando se especifica usuario_id
            user_info['tipo'] = 'persona'
            
            # Si hay un usuario autenticado, agregar su información al user_info
            if current_user and account_type == 'empresa':
                user_info.update({
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'id': current_user.id_empresa,
                    'empresa_nombre': current_user.nombre_empresa
                })
            elif current_user:
                user_info.update({
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'id': current_user.id_usuario,
                    'avatar_chatbot': getattr(current_user, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
                })
            
            # Para el chatbot, usar el avatar del usuario cuyo perfil se está viendo
            user_info['avatar_chatbot'] = getattr(usuario_obj, 'avatar_chatbot', 'avatars/Cartoon Style Robot.jpg')
            
            return render(request, 'ecommerce_app/perfil_servicios.html', {
                'user_info': user_info,
                'usuario_obj': usuario_obj,
                'servicios': servicios_con_imagenes,
                'servicios_por_categoria': dict(servicios_por_categoria),
                'entity_name': entity_name
            })
        except usuario.DoesNotExist:
            # Si no existe el usuario, mostrar error
            return render(request, 'ecommerce_app/perfil_servicios.html', {
                'error': 'Usuario no encontrado',
                'user_info': user_info,
                'servicios': [],
                'entity_name': 'Error'
            })
    
    elif current_user and account_type == 'empresa':
        # Usuario autenticado es empresa
        empresa_obj = current_user
        empresa_nombre = empresa_obj.nombre_empresa
        
        # Obtener servicios de la empresa con sus imágenes
        servicios_query = servicio_empresa.objects.filter(id_empresa_fk=current_user).select_related('id_categoria_servicios_fk')
        servicios_con_imagenes = []
        servicios_por_categoria = defaultdict(list)
        
        for serv in servicios_query:
            primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=serv).first()
            serv.primera_imagen = primera_imagen
            
            # Obtener sucursales asociadas al servicio
            sucursales_servicio = servicio_sucursal.objects.filter(id_servicio_fk=serv).select_related('id_sucursal_fk')
            serv.sucursales_asociadas = sucursales_servicio
            
            servicios_con_imagenes.append(serv)
            
            # Agrupar por categoría
            categoria_nombre = serv.id_categoria_servicios_fk.nombre_categoria_serv_empresa if serv.id_categoria_servicios_fk else 'Sin categoría'
            servicios_por_categoria[categoria_nombre].append(serv)
        
        user_info.update({
            'nombre': empresa_nombre,
            'email': empresa_obj.correo_empresa,
            'id': empresa_obj.id_empresa
        })
        
        return render(request, 'ecommerce_app/perfil_servicios.html', {
            'user_info': user_info,
            'empresa_obj': empresa_obj,
            'servicios': servicios_con_imagenes,
            'servicios_por_categoria': dict(servicios_por_categoria),
            'entity_name': empresa_nombre
        })
    elif current_user:
        # Usuario autenticado es persona
        usuario_obj = current_user
        usuario_nombre = usuario_obj.nombre_usuario
        
        # Obtener servicios del usuario con sus imágenes
        servicios_query = servicio_usuario.objects.filter(id_usuario_fk=current_user).select_related('id_categoria_servicios_fk')
        servicios_con_imagenes = []
        servicios_por_categoria = defaultdict(list)
        
        for serv in servicios_query:
            primera_imagen = imagen_servicio_usuario.objects.filter(id_servicio_fk=serv).first()
            serv.primera_imagen = primera_imagen
            servicios_con_imagenes.append(serv)
            
            # Agrupar por categoría
            categoria_nombre = serv.id_categoria_servicios_fk.nombre_categoria_serv_usuario if serv.id_categoria_servicios_fk else 'Sin categoría'
            servicios_por_categoria[categoria_nombre].append(serv)
        
        user_info.update({
            'nombre': usuario_nombre,
            'email': usuario_obj.correo_usuario,
            'id': usuario_obj.id_usuario
        })
        
        return render(request, 'ecommerce_app/perfil_servicios.html', {
            'user_info': user_info,
            'usuario_obj': usuario_obj,
            'servicios': servicios_con_imagenes,
            'servicios_por_categoria': dict(servicios_por_categoria),
            'entity_name': usuario_nombre
        })
    else:
        # Usuario no autenticado - mostrar servicios de ejemplo
        # Mostrar servicios de la primera empresa disponible
        empresa_obj = empresa.objects.first()
        servicios_con_imagenes = []
        entity_name = 'Servicios Disponibles'
        
        if empresa_obj:
            servicios_query = servicio_empresa.objects.filter(id_empresa_fk=empresa_obj).select_related('id_categoria_servicios_fk')[:5]  # Limitar a 5 servicios
            servicios_por_categoria = defaultdict(list)
            
            for serv in servicios_query:
                primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=serv).first()
                serv.primera_imagen = primera_imagen
                
                # Obtener sucursales asociadas al servicio
                sucursales_servicio = servicio_sucursal.objects.filter(id_servicio_fk=serv).select_related('id_sucursal_fk')
                serv.sucursales_asociadas = sucursales_servicio
                
                servicios_con_imagenes.append(serv)
                
                # Agrupar por categoría
                categoria_nombre = serv.id_categoria_servicios_fk.nombre_categoria_serv_empresa if serv.id_categoria_servicios_fk else 'Sin categoría'
                servicios_por_categoria[categoria_nombre].append(serv)
            entity_name = f'Servicios de {empresa_obj.nombre_empresa}'
        else:
            servicios_por_categoria = {}
        
        return render(request, 'ecommerce_app/perfil_servicios.html', {
            'user_info': user_info,
            'empresa_obj': empresa_obj,
            'servicios': servicios_con_imagenes,
            'servicios_por_categoria': dict(servicios_por_categoria),
            'entity_name': entity_name
        })

@require_login
def detalle_carrito(request):
    # Obtener información del usuario autenticado
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    # Determinar el tipo de cuenta
    account_type = request.session.get('account_type', 'usuario')
    
    # Inicializar variables para el carrito
    productos_carrito = []
    total_productos = 0
    cantidad_productos = 0
    
    if account_type == 'empresa':
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        
        # Obtener carrito activo o pendiente de la empresa
        carrito_empresa = carrito_compra_producto_empresa.objects.filter(
            id_empresa_fk=current_user,
            estatuscarrito_prod_empresa__in=['activo', 'pendiente']
        ).first()
        
        if carrito_empresa:
            # Obtener detalles del carrito
            detalles_carrito = detalle_compra_producto_empresa.objects.filter(
                id_fk_carritocompra_empresa=carrito_empresa
            ).select_related('id_fk_producto_sucursal_empresa__id_producto_fk', 'idproducto_fk_usuario')
            
            for detalle in detalles_carrito:
                # Procesar productos de empresa
                if detalle.id_fk_producto_sucursal_empresa:
                    producto_sucursal = detalle.id_fk_producto_sucursal_empresa
                    producto = producto_sucursal.id_producto_fk
                    
                    # Obtener la primera imagen del producto
                    imagen = imagen_producto_empresa.objects.filter(
                        id_producto_fk=producto
                    ).first()
                    
                    # Obtener información de la sucursal
                    sucursal_info = producto_sucursal.id_sucursal_fk
                    
                    productos_carrito.append({
                        'id': producto.id_producto_empresa,
                        'detalle_id': detalle.id_deta_carrito_prod_empresa,
                        'nombre': producto.nombre_producto_empresa,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_empresa,
                        'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                        'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                        'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                        'sucursal': sucursal_info.nombre_sucursal if sucursal_info else 'N/A',
                        'estatus_carrito': carrito_empresa.estatuscarrito_prod_empresa,
                        'fecha_creacion_carrito': carrito_empresa.fecha_creacion_carrito_prod_empresa
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_empresa
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_empresa
                
                # Procesar productos de usuario
                elif detalle.idproducto_fk_usuario:
                    producto = detalle.idproducto_fk_usuario
                    
                    # Obtener la primera imagen del producto
                    imagen = imagen_producto_usuario.objects.filter(
                        id_producto_fk=producto
                    ).first()
                    
                    productos_carrito.append({
                        'id': producto.id_producto_usuario,
                        'detalle_id': detalle.id_deta_carrito_prod_empresa,
                        'nombre': producto.nombre_producto_usuario,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_empresa,
                        'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                        'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                        'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None,
                        'sucursal': 'Usuario Individual',  # Los productos de usuario no tienen sucursal
                        'estatus_carrito': carrito_empresa.estatuscarrito_prod_empresa,
                        'fecha_creacion_carrito': carrito_empresa.fecha_creacion_carrito_prod_empresa
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_empresa
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_empresa
            
    else:
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        
        # Obtener carrito activo o pendiente del usuario
        carrito_usuario = carrito_compra_producto_usuario.objects.filter(
            id_usuario_fk=current_user,
            estatuscarrito_prod_usuario__in=['activo', 'pendiente']
        ).first()
        
        if carrito_usuario:
            # Obtener detalles del carrito
            detalles_carrito = detalle_compra_producto_usuario.objects.filter(
                id_fk_carritocompra_usuario=carrito_usuario
            ).select_related('idproducto_fk_usuario', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            for detalle in detalles_carrito:
                # Manejar productos de empresa (a través de producto_sucursal)
                if detalle.id_fk_producto_sucursal_empresa:
                    producto_sucursal = detalle.id_fk_producto_sucursal_empresa
                    producto = producto_sucursal.id_producto_fk
                    
                    # Obtener la primera imagen del producto
                    imagen = imagen_producto_empresa.objects.filter(
                        id_producto_fk=producto
                    ).first()
                    
                    # Obtener información de la sucursal
                    sucursal_info = producto_sucursal.id_sucursal_fk
                    
                    productos_carrito.append({
                        'id': producto.id_producto_empresa,
                        'detalle_id': detalle.id_deta_carrito_prod_usuario,
                        'nombre': producto.nombre_producto_empresa,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_usuario,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                        'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                        'sucursal': sucursal_info.nombre_sucursal if sucursal_info else 'N/A',
                        'estatus_carrito': carrito_usuario.estatuscarrito_prod_usuario,
                        'fecha_creacion_carrito': carrito_usuario.fecha_creacion_carrito_prod_usuario
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_usuario
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_usuario
                
                elif detalle.idproducto_fk_usuario:
                    producto = detalle.idproducto_fk_usuario
                    
                    # Obtener la primera imagen del producto
                    imagen = imagen_producto_usuario.objects.filter(
                        id_producto_fk=producto
                    ).first()
                    
                    productos_carrito.append({
                        'id': producto.id_producto_usuario,
                        'detalle_id': detalle.id_deta_carrito_prod_usuario,
                        'nombre': producto.nombre_producto_usuario,
                        'precio_unitario': detalle.precio_unit_deta_carrito_prod_usuario,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                        'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None,
                        'sucursal': 'Producto de Usuario',
                        'estatus_carrito': carrito_usuario.estatuscarrito_prod_usuario,
                        'fecha_creacion_carrito': carrito_usuario.fecha_creacion_carrito_prod_usuario
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_usuario
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_usuario
    
    # Información adicional del carrito
    carrito_info = None
    if account_type == 'empresa' and 'carrito_empresa' in locals() and carrito_empresa is not None:
        carrito_info = {
            'id': carrito_empresa.id_carrito_prod_empresa,
            'estatus': carrito_empresa.estatuscarrito_prod_empresa,
            'fecha_creacion': carrito_empresa.fecha_creacion_carrito_prod_empresa,
            'total': carrito_empresa.total_carrito_prod_empresa,
            'propietario': {
                'tipo': 'empresa',
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'id': current_user.id_empresa
            }
        }
    elif account_type == 'usuario' and 'carrito_usuario' in locals() and carrito_usuario is not None:
        carrito_info = {
            'id': carrito_usuario.id_carrito_prod_usuario,
            'estatus': carrito_usuario.estatuscarrito_prod_usuario,
            'fecha_creacion': carrito_usuario.fecha_creacion_carrito_prod_usuario,
            'total': carrito_usuario.total_carrito_prod_usuario,
            'propietario': {
                'tipo': 'usuario',
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'id': current_user.id_usuario
            }
        }
    
    context = {
        'user_info': user_info,
        'account_type': account_type,
        'productos_carrito': productos_carrito,
        'total_productos': total_productos,
        'cantidad_productos': cantidad_productos,
        'carrito_info': carrito_info
    }
    
    return render(request, 'ecommerce_app/detalle_carrito.html', context)


def validar_precios_carrito_usuario(carrito):
    """Valida los precios del carrito de usuario y retorna información sobre cambios"""
    cambios_precio = []
    
    # Validar productos de empresa en carrito de usuario
    detalles_empresa = detalle_compra_producto_usuario.objects.filter(
        id_fk_carritocompra_usuario=carrito,
        id_fk_producto_sucursal_empresa__isnull=False
    )
    
    for detalle in detalles_empresa:
        precio_actual = detalle.id_fk_producto_sucursal_empresa.precio_producto_sucursal
        precio_original = detalle.precio_original_deta_carrito_prod_usuario
        
        if precio_original and precio_actual != precio_original:
            # Actualizar precio y subtotal
            detalle.precio_unit_deta_carrito_prod_usuario = precio_actual
            detalle.subtotal_deta_carrito_prod_usuario = detalle.cantidad_deta_carrito_prod_usuario * precio_actual
            detalle.save()
            
            cambios_precio.append({
                'producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                'precio_original': float(precio_original),
                'precio_actual': float(precio_actual),
                'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                'tipo': 'empresa'
            })
    
    # Validar productos de usuario en carrito de usuario
    detalles_usuario = detalle_compra_producto_usuario.objects.filter(
        id_fk_carritocompra_usuario=carrito,
        idproducto_fk_usuario__isnull=False
    )
    
    for detalle in detalles_usuario:
        precio_actual = detalle.idproducto_fk_usuario.precio_producto_usuario
        precio_original = detalle.precio_original_deta_carrito_prod_usuario
        
        if precio_original and precio_actual != precio_original:
            # Actualizar precio y subtotal
            detalle.precio_unit_deta_carrito_prod_usuario = precio_actual
            detalle.subtotal_deta_carrito_prod_usuario = detalle.cantidad_deta_carrito_prod_usuario * precio_actual
            detalle.save()
            
            cambios_precio.append({
                'producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                'precio_original': float(precio_original),
                'precio_actual': float(precio_actual),
                'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                'tipo': 'usuario'
            })
    
    # Actualizar total del carrito si hubo cambios
    if cambios_precio:
        total = sum(
            detalle.subtotal_deta_carrito_prod_usuario 
            for detalle in carrito.detalles.all()
        )
        carrito.total_carrito_prod_usuario = total
        carrito.save()
    
    return cambios_precio

def recalcular_total_carrito(carrito_obj, account_type):
    """Recalcula el total del carrito después de cambios en los productos"""
    if account_type == 'empresa':
        nuevo_total = sum(
            detalle.subtotal_deta_carrito_prod_empresa 
            for detalle in carrito_obj.detalles.all()
        )
        carrito_obj.total_carrito_prod_empresa = nuevo_total
        carrito_obj.save()
        print(f"Total del carrito recalculado (empresa): ${nuevo_total}")
        return nuevo_total
    else:
        nuevo_total = sum(
            detalle.subtotal_deta_carrito_prod_usuario 
            for detalle in carrito_obj.detalles.all()
        )
        carrito_obj.total_carrito_prod_usuario = nuevo_total
        carrito_obj.save()
        print(f"Total del carrito recalculado (usuario): ${nuevo_total}")
        return nuevo_total

def validar_precios_carrito_empresa(carrito):
    """Valida los precios del carrito de empresa y retorna información sobre cambios"""
    cambios_precio = []
    
    # Validar productos de empresa en carrito de empresa
    detalles_empresa = detalle_compra_producto_empresa.objects.filter(
        id_fk_carritocompra_empresa=carrito,
        id_fk_producto_sucursal_empresa__isnull=False
    )
    
    for detalle in detalles_empresa:
        precio_actual = detalle.id_fk_producto_sucursal_empresa.precio_producto_sucursal
        precio_original = detalle.precio_original_deta_carrito_prod_empresa
        
        if precio_original and precio_actual != precio_original:
            # Actualizar precio y subtotal
            detalle.precio_unit_deta_carrito_prod_empresa = precio_actual
            detalle.subtotal_deta_carrito_prod_empresa = detalle.cantidad_deta_carrito_prod_empresa * precio_actual
            detalle.save()
            
            cambios_precio.append({
                'producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                'precio_original': float(precio_original),
                'precio_actual': float(precio_actual),
                'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                'tipo': 'empresa'
            })
    
    # Validar productos de usuario en carrito de empresa
    detalles_usuario = detalle_compra_producto_empresa.objects.filter(
        id_fk_carritocompra_empresa=carrito,
        idproducto_fk_usuario__isnull=False
    )
    
    for detalle in detalles_usuario:
        precio_actual = detalle.idproducto_fk_usuario.precio_producto_usuario
        precio_original = detalle.precio_original_deta_carrito_prod_empresa
        
        if precio_original and precio_actual != precio_original:
            # Actualizar precio y subtotal
            detalle.precio_unit_deta_carrito_prod_empresa = precio_actual
            detalle.subtotal_deta_carrito_prod_empresa = detalle.cantidad_deta_carrito_prod_empresa * precio_actual
            detalle.save()
            
            cambios_precio.append({
                'producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                'precio_original': float(precio_original),
                'precio_actual': float(precio_actual),
                'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                'tipo': 'usuario'
            })
    
    # Actualizar total del carrito si hubo cambios
    if cambios_precio:
        total = sum(
            detalle.subtotal_deta_carrito_prod_empresa 
            for detalle in carrito.detalles.all()
        )
        carrito.total_carrito_prod_empresa = total
        carrito.save()
    
    return cambios_precio

@csrf_exempt
@require_POST
def agregar_al_carrito(request):
    """Vista para agregar productos al carrito - Permite a cualquier usuario agregar productos de cualquier tipo"""
    try:
        # Verificar autenticación
        if not is_user_authenticated(request):
            return JsonResponse({
                'success': False,
                'message': 'Usuario no autenticado'
            }, status=401)
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            }, status=404)
        
        # Obtener datos del request (soportar JSON o form-encoded)
        producto_id = None
        tipo_producto = None
        cantidad = 1
        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body)
                producto_id = payload.get('producto_id')
                tipo_producto = payload.get('tipo_propietario')  # 'empresa' o 'usuario'
                cantidad = int(payload.get('cantidad', 1) or 1)
            except Exception:
                # Fall back to POST parsing below
                producto_id = request.POST.get('producto_id')
                tipo_producto = request.POST.get('tipo_propietario')
                cantidad = int(request.POST.get('cantidad', 1))
        else:
            producto_id = request.POST.get('producto_id')
            tipo_producto = request.POST.get('tipo_propietario')  # 'empresa' o 'usuario'
            cantidad = int(request.POST.get('cantidad', 1))
        
        if not producto_id or not tipo_producto:
            return JsonResponse({
                'success': False,
                'message': 'Datos incompletos'
            }, status=400)
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Validar y obtener información del producto
        producto_info = None
        if tipo_producto == 'empresa':
            try:
                producto_sucursal_obj = producto_sucursal.objects.get(id_producto_sucursal=producto_id)
                producto_info = {
                    'objeto': producto_sucursal_obj,
                    'precio': producto_sucursal_obj.precio_producto_sucursal,
                    'stock': producto_sucursal_obj.stock_producto_sucursal,
                    'tipo': 'empresa'
                }
            except producto_sucursal.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto de empresa no encontrado'
                }, status=404)
        elif tipo_producto == 'usuario':
            try:
                producto_usuario_obj = producto_usuario.objects.get(id_producto_usuario=producto_id)
                producto_info = {
                    'objeto': producto_usuario_obj,
                    'precio': producto_usuario_obj.precio_producto_usuario,
                    'stock': producto_usuario_obj.stock_producto_usuario,
                    'tipo': 'usuario'
                }
            except producto_usuario.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto de usuario no encontrado'
                }, status=404)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Tipo de producto no válido'
            }, status=400)
        
        # Validar stock disponible (considerando stock reservado)
        stock_disponible = 0
        if producto_info['tipo'] == 'empresa':
            stock_disponible = producto_info['objeto'].stock_producto_sucursal - producto_info['objeto'].stock_reservado_sucursal
        else:
            stock_disponible = producto_info['objeto'].stock_producto_usuario - producto_info['objeto'].stock_reservado_usuario
            
        if cantidad > stock_disponible:
            return JsonResponse({
                'success': False,
                'message': f'La cantidad solicitada ({cantidad}) excede el stock disponible ({stock_disponible} unidades)',
                'stock_insuficiente': True
            }, status=400)
        
        # Lógica para empresas
        if account_type == 'empresa':
            # Buscar carrito existente (activo o pendiente)
            carrito = carrito_compra_producto_empresa.objects.filter(
                id_empresa_fk=current_user,
                estatuscarrito_prod_empresa__in=['activo', 'pendiente']
            ).first()
            
            created = False
            if not carrito:
                # Buscar carrito completado para reutilizar
                carrito_completado = carrito_compra_producto_empresa.objects.filter(
                    id_empresa_fk=current_user,
                    estatuscarrito_prod_empresa='completado'
                ).first()
                
                if carrito_completado:
                    # Reutilizar carrito completado: cambiar estado, limpiar total y actualizar fecha
                    carrito_completado.estatuscarrito_prod_empresa = 'activo'
                    carrito_completado.total_carrito_prod_empresa = 0
                    carrito_completado.fecha_carrito_prod_empresa = timezone.now()
                    carrito_completado.save()
                    carrito = carrito_completado
                    created = False
                else:
                    # Si no existe carrito, crear uno nuevo con estatus activo
                    carrito = carrito_compra_producto_empresa.objects.create(
                        id_empresa_fk=current_user,
                        estatuscarrito_prod_empresa='activo',
                        total_carrito_prod_empresa=0
                    )
                    created = True
            
            # Agregar producto al carrito de empresa
            if producto_info['tipo'] == 'empresa':
                # Verificar si ya existe en el carrito
                detalle_existente = detalle_compra_producto_empresa.objects.filter(
                    id_fk_carritocompra_empresa=carrito,
                    id_fk_producto_sucursal_empresa=producto_info['objeto']
                ).first()
                
                if detalle_existente:
                    # Validar stock con cantidad existente en carrito
                    nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_empresa + cantidad
                    if nueva_cantidad_total > producto_info['stock']:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({producto_info["stock"]} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Actualizar cantidad
                    detalle_existente.cantidad_deta_carrito_prod_empresa += cantidad
                    detalle_existente.subtotal_deta_carrito_prod_empresa = (
                        detalle_existente.cantidad_deta_carrito_prod_empresa * producto_info['precio']
                    )
                    detalle_existente.save()

                    # Incrementar stock reservado (producto de sucursal)
                    try:
                        producto_sucursal_obj = producto_info['objeto']
                        producto_sucursal_obj.stock_reservado_sucursal += cantidad
                        producto_sucursal_obj.save(update_fields=['stock_reservado_sucursal'])
                    except Exception:
                        logger.exception('No se pudo actualizar stock_reservado_sucursal al aumentar cantidad detalle (empresa)')
                else:
                    # Crear nuevo detalle
                    detalle_compra_producto_empresa.objects.create(
                        id_fk_carritocompra_empresa=carrito,
                        id_fk_producto_sucursal_empresa=producto_info['objeto'],
                        cantidad_deta_carrito_prod_empresa=cantidad,
                        precio_unit_deta_carrito_prod_empresa=producto_info['precio'],
                        precio_original_deta_carrito_prod_empresa=producto_info['precio'],
                        subtotal_deta_carrito_prod_empresa=cantidad * producto_info['precio']
                    )
                    
                    # Incrementar stock reservado
                    producto_sucursal_obj = producto_info['objeto']
                    producto_sucursal_obj.stock_reservado_sucursal += cantidad
                    producto_sucursal_obj.save()
            
            elif producto_info['tipo'] == 'usuario':
                # Verificar si ya existe en el carrito
                detalle_existente = detalle_compra_producto_empresa.objects.filter(
                    id_fk_carritocompra_empresa=carrito,
                    idproducto_fk_usuario=producto_info['objeto']
                ).first()
                
                if detalle_existente:
                    # Validar stock con cantidad existente en carrito
                    nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_empresa + cantidad
                    if nueva_cantidad_total > producto_info['stock']:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({producto_info["stock"]} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Actualizar cantidad
                    detalle_existente.cantidad_deta_carrito_prod_empresa += cantidad
                    detalle_existente.subtotal_deta_carrito_prod_empresa = (
                        detalle_existente.cantidad_deta_carrito_prod_empresa * producto_info['precio']
                    )
                    detalle_existente.save()
                    # Incrementar stock reservado para producto usuario (si ya existía detalle)
                    try:
                        producto_usuario_obj = producto_info['objeto']
                        producto_usuario_obj.stock_reservado_usuario += cantidad
                        producto_usuario_obj.save(update_fields=['stock_reservado_usuario'])
                    except Exception:
                        logger.exception('No se pudo actualizar stock_reservado_usuario al aumentar cantidad detalle (empresa->usuario)')
                else:
                    # Crear nuevo detalle
                    detalle_compra_producto_empresa.objects.create(
                        id_fk_carritocompra_empresa=carrito,
                        idproducto_fk_usuario=producto_info['objeto'],
                        cantidad_deta_carrito_prod_empresa=cantidad,
                        precio_unit_deta_carrito_prod_empresa=producto_info['precio'],
                        precio_original_deta_carrito_prod_empresa=producto_info['precio'],
                        subtotal_deta_carrito_prod_empresa=cantidad * producto_info['precio']
                    )
                    
                    # Incrementar stock reservado
                    producto_usuario_obj = producto_info['objeto']
                    producto_usuario_obj.stock_reservado_usuario += cantidad
                    producto_usuario_obj.save()
            
            # Actualizar total del carrito
            recalcular_total_carrito(carrito, 'empresa')
        
        # Lógica para usuarios
        else:
            # Buscar carrito existente (activo o pendiente)
            carrito = carrito_compra_producto_usuario.objects.filter(
                id_usuario_fk=current_user,
                estatuscarrito_prod_usuario__in=['activo', 'pendiente']
            ).first()
            
            created = False
            if not carrito:
                # Buscar carrito completado para reutilizar
                carrito_completado = carrito_compra_producto_usuario.objects.filter(
                    id_usuario_fk=current_user,
                    estatuscarrito_prod_usuario='completado'
                ).first()
                
                if carrito_completado:
                    # Reutilizar carrito completado: cambiar estado, limpiar total y actualizar fecha
                    carrito_completado.estatuscarrito_prod_usuario = 'activo'
                    carrito_completado.total_carrito_prod_usuario = 0
                    carrito_completado.fecha_carrito_prod_usuario = timezone.now()
                    carrito_completado.save()
                    carrito = carrito_completado
                    created = False
                else:
                    # Si no existe carrito, crear uno nuevo con estatus activo
                    carrito = carrito_compra_producto_usuario.objects.create(
                        id_usuario_fk=current_user,
                        estatuscarrito_prod_usuario='activo',
                        total_carrito_prod_usuario=0
                    )
                    created = True
            
            # Agregar producto al carrito de usuario
            if producto_info['tipo'] == 'empresa':
                # Verificar si ya existe en el carrito
                detalle_existente = detalle_compra_producto_usuario.objects.filter(
                    id_fk_carritocompra_usuario=carrito,
                    id_fk_producto_sucursal_empresa=producto_info['objeto']
                ).first()
                
                if detalle_existente:
                    # Validar stock con cantidad existente en carrito
                    nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_usuario + cantidad
                    if nueva_cantidad_total > producto_info['stock']:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({producto_info["stock"]} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Actualizar cantidad
                    detalle_existente.cantidad_deta_carrito_prod_usuario += cantidad
                    detalle_existente.subtotal_deta_carrito_prod_usuario = (
                        detalle_existente.cantidad_deta_carrito_prod_usuario * producto_info['precio']
                    )
                    detalle_existente.save()
                    # Incrementar stock reservado para producto de sucursal (usuario comprando a sucursal)
                    try:
                        producto_sucursal_obj = producto_info['objeto']
                        producto_sucursal_obj.stock_reservado_sucursal += cantidad
                        producto_sucursal_obj.save(update_fields=['stock_reservado_sucursal'])
                    except Exception:
                        logger.exception('No se pudo actualizar stock_reservado_sucursal al aumentar cantidad detalle (usuario->sucursal)')
                else:
                    # Crear nuevo detalle
                    detalle_compra_producto_usuario.objects.create(
                        id_fk_carritocompra_usuario=carrito,
                        id_fk_producto_sucursal_empresa=producto_info['objeto'],
                        cantidad_deta_carrito_prod_usuario=cantidad,
                        precio_unit_deta_carrito_prod_usuario=producto_info['precio'],
                        precio_original_deta_carrito_prod_usuario=producto_info['precio'],
                        subtotal_deta_carrito_prod_usuario=cantidad * producto_info['precio']
                    )
                    # Incrementar stock reservado para nuevo detalle (producto sucursal)
                    try:
                        producto_sucursal_obj = producto_info['objeto']
                        producto_sucursal_obj.stock_reservado_sucursal += cantidad
                        producto_sucursal_obj.save(update_fields=['stock_reservado_sucursal'])
                    except Exception:
                        logger.exception('No se pudo actualizar stock_reservado_sucursal al crear detalle (usuario->sucursal)')
            
            elif producto_info['tipo'] == 'usuario':
                # Verificar si ya existe en el carrito
                detalle_existente = detalle_compra_producto_usuario.objects.filter(
                    id_fk_carritocompra_usuario=carrito,
                    idproducto_fk_usuario=producto_info['objeto']
                ).first()
                
                if detalle_existente:
                    # Validar stock con cantidad existente en carrito
                    nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_usuario + cantidad
                    if nueva_cantidad_total > producto_info['stock']:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({producto_info["stock"]} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Actualizar cantidad
                    detalle_existente.cantidad_deta_carrito_prod_usuario += cantidad
                    detalle_existente.subtotal_deta_carrito_prod_usuario = (
                        detalle_existente.cantidad_deta_carrito_prod_usuario * producto_info['precio']
                    )
                    detalle_existente.save()
                    # Incrementar stock reservado para producto usuario
                    try:
                        producto_usuario_obj = producto_info['objeto']
                        producto_usuario_obj.stock_reservado_usuario += cantidad
                        producto_usuario_obj.save(update_fields=['stock_reservado_usuario'])
                    except Exception:
                        logger.exception('No se pudo actualizar stock_reservado_usuario al aumentar cantidad detalle (usuario->usuario)')
                else:
                    # Crear nuevo detalle
                    detalle_compra_producto_usuario.objects.create(
                        id_fk_carritocompra_usuario=carrito,
                        idproducto_fk_usuario=producto_info['objeto'],
                        cantidad_deta_carrito_prod_usuario=cantidad,
                        precio_unit_deta_carrito_prod_usuario=producto_info['precio'],
                        precio_original_deta_carrito_prod_usuario=producto_info['precio'],
                        subtotal_deta_carrito_prod_usuario=cantidad * producto_info['precio']
                    )
                    # Incrementar stock reservado para nuevo detalle (producto usuario)
                    try:
                        producto_usuario_obj = producto_info['objeto']
                        producto_usuario_obj.stock_reservado_usuario += cantidad
                        producto_usuario_obj.save(update_fields=['stock_reservado_usuario'])
                    except Exception:
                        logger.exception('No se pudo actualizar stock_reservado_usuario al crear detalle (usuario->usuario)')
            
            # Actualizar total del carrito
            recalcular_total_carrito(carrito, 'usuario')
        
        # Calcular cantidad total de items (suma de cantidades) para respuesta
        try:
            from django.db.models import Sum
            if account_type == 'empresa':
                total_items = detalle_compra_producto_empresa.objects.filter(
                    id_fk_carritocompra_empresa=carrito
                ).aggregate(total=Sum('cantidad_deta_carrito_prod_empresa'))['total'] or 0
            else:
                total_items = detalle_compra_producto_usuario.objects.filter(
                    id_fk_carritocompra_usuario=carrito
                ).aggregate(total=Sum('cantidad_deta_carrito_prod_usuario'))['total'] or 0
            total_items = int(total_items)
        except Exception:
            total_items = 0

        return JsonResponse({
            'success': True,
            'message': 'Producto agregado al carrito exitosamente',
            'carrito_created': created,
            'total_items': total_items
        })
        
    except Exception as e:
        logger.error(f"Error al agregar producto al carrito: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        }, status=500)

@require_POST
def actualizar_cantidad_carrito(request):
    """Función para actualizar la cantidad de un producto en el carrito"""
    
    # Verificar autenticación usando el sistema personalizado
    if not is_user_authenticated(request):
        return JsonResponse({
            'success': False,
            'message': 'Usuario no autenticado'
        }, status=401)
    
    try:
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        nueva_cantidad = data.get('cantidad')
        
        if not producto_id or not nueva_cantidad:
            return JsonResponse({
                'success': False,
                'message': 'ID del producto y cantidad son requeridos'
            }, status=400)
        
        if int(nueva_cantidad) <= 0:
            return JsonResponse({
                'success': False,
                'message': 'La cantidad debe ser mayor a 0'
            }, status=400)
        
        # Obtener el usuario actual del sistema personalizado
        current_user = get_current_user(request)
        account_type = request.session.get('account_type', 'usuario')
        
        if account_type == 'empresa':
            # Buscar el carrito de empresa
            try:
                carrito = carrito_compra_producto_empresa.objects.get(
                    id_empresa_fk=current_user,
                    estatuscarrito_prod_empresa='activo'
                )
            except carrito_compra_producto_empresa.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró el carrito'
                }, status=404)
            
            # Buscar el detalle del carrito para el producto específico
            detalle = None
            try:
                detalle = detalle_compra_producto_empresa.objects.get(
                    id_fk_carritocompra_empresa=carrito,
                    id_fk_producto_sucursal_empresa_id=producto_id
                )
            except detalle_compra_producto_empresa.DoesNotExist:
                try:
                    detalle = detalle_compra_producto_empresa.objects.get(
                        id_fk_carritocompra_empresa=carrito,
                        idproducto_fk_usuario_id=producto_id
                    )
                except detalle_compra_producto_empresa.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado en el carrito'
                    }, status=404)
            
            # Ajustar stock reservado según la diferencia entre nueva y vieja cantidad
            try:
                old_qty = int(detalle.cantidad_deta_carrito_prod_empresa or 0)
                new_qty = int(nueva_cantidad)
                delta = new_qty - old_qty

                # Si el detalle corresponde a un producto de sucursal
                if detalle.id_fk_producto_sucursal_empresa:
                    prod = producto_sucursal.objects.select_for_update().get(pk=detalle.id_fk_producto_sucursal_empresa.pk)
                    if delta > 0:
                        available = prod.stock_producto_sucursal - prod.stock_reservado_sucursal
                        if delta > available:
                            return JsonResponse({'success': False, 'message': 'Stock insuficiente para la actualización'}, status=400)
                    prod.stock_reservado_sucursal = max(0, prod.stock_reservado_sucursal + delta)
                    prod.save(update_fields=['stock_reservado_sucursal'])

                # Si el detalle corresponde a un producto de usuario
                elif detalle.idproducto_fk_usuario:
                    prod = producto_usuario.objects.select_for_update().get(pk=detalle.idproducto_fk_usuario.pk)
                    if delta > 0:
                        available = prod.stock_producto_usuario - prod.stock_reservado_usuario
                        if delta > available:
                            return JsonResponse({'success': False, 'message': 'Stock insuficiente para la actualización'}, status=400)
                    prod.stock_reservado_usuario = max(0, prod.stock_reservado_usuario + delta)
                    prod.save(update_fields=['stock_reservado_usuario'])

                # Actualizar la cantidad y subtotal del detalle
                detalle.cantidad_deta_carrito_prod_empresa = new_qty
                detalle.subtotal_deta_carrito_prod_empresa = detalle.cantidad_deta_carrito_prod_empresa * detalle.precio_unit_deta_carrito_prod_empresa
                detalle.save()
            except Exception as e:
                logger.exception('Error al ajustar stock reservado al actualizar cantidad (empresa)')
                return JsonResponse({'success': False, 'message': 'Error al actualizar cantidad'}, status=500)
            
            # Recalcular el total del carrito
            recalcular_total_carrito(carrito, 'empresa')
        
        else:  # account_type == 'usuario'
            # Buscar el carrito de usuario
            try:
                carrito = carrito_compra_producto_usuario.objects.get(
                    id_usuario_fk=current_user,
                    estatuscarrito_prod_usuario='activo'
                )
            except carrito_compra_producto_usuario.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró el carrito'
                }, status=404)
            
            # Buscar el detalle del carrito para el producto específico
            detalle = None
            try:
                detalle = detalle_compra_producto_usuario.objects.get(
                    id_fk_carritocompra_usuario=carrito,
                    idproducto_fk_usuario_id=producto_id
                )
            except detalle_compra_producto_usuario.DoesNotExist:
                try:
                    detalle = detalle_compra_producto_usuario.objects.get(
                        id_fk_carritocompra_usuario=carrito,
                        id_fk_producto_sucursal_empresa_id=producto_id
                    )
                except detalle_compra_producto_usuario.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado en el carrito'
                    }, status=404)
            
            # Ajustar stock reservado según la diferencia entre nueva y vieja cantidad
            try:
                old_qty = int(detalle.cantidad_deta_carrito_prod_usuario or 0)
                new_qty = int(nueva_cantidad)
                delta = new_qty - old_qty

                # Si el detalle corresponde a un producto de sucursal
                if detalle.id_fk_producto_sucursal_empresa:
                    prod = producto_sucursal.objects.select_for_update().get(pk=detalle.id_fk_producto_sucursal_empresa.pk)
                    if delta > 0:
                        available = prod.stock_producto_sucursal - prod.stock_reservado_sucursal
                        if delta > available:
                            return JsonResponse({'success': False, 'message': 'Stock insuficiente para la actualización'}, status=400)
                    prod.stock_reservado_sucursal = max(0, prod.stock_reservado_sucursal + delta)
                    prod.save(update_fields=['stock_reservado_sucursal'])

                # Si el detalle corresponde a un producto de usuario
                elif detalle.idproducto_fk_usuario:
                    prod = producto_usuario.objects.select_for_update().get(pk=detalle.idproducto_fk_usuario.pk)
                    if delta > 0:
                        available = prod.stock_producto_usuario - prod.stock_reservado_usuario
                        if delta > available:
                            return JsonResponse({'success': False, 'message': 'Stock insuficiente para la actualización'}, status=400)
                    prod.stock_reservado_usuario = max(0, prod.stock_reservado_usuario + delta)
                    prod.save(update_fields=['stock_reservado_usuario'])

                # Actualizar la cantidad y subtotal del detalle
                detalle.cantidad_deta_carrito_prod_usuario = new_qty
                detalle.subtotal_deta_carrito_prod_usuario = detalle.cantidad_deta_carrito_prod_usuario * detalle.precio_unit_deta_carrito_prod_usuario
                detalle.save()
            except Exception as e:
                logger.exception('Error al ajustar stock reservado al actualizar cantidad (usuario)')
                return JsonResponse({'success': False, 'message': 'Error al actualizar cantidad'}, status=500)
            
            # Recalcular el total del carrito
            recalcular_total_carrito(carrito, 'usuario')
        
        return JsonResponse({
            'success': True,
            'message': 'Cantidad actualizada exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        print(f"Error al actualizar cantidad del carrito: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@require_POST
def eliminar_del_carrito(request):
    """
    Elimina un producto específico del carrito de compras
    """
    # Usar el sistema de autenticación personalizado
    if not is_user_authenticated(request):
        return JsonResponse({
            'success': False,
            'message': 'Usuario no autenticado'
        }, status=401)
    
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no autenticado'
        }, status=401)
    
    try:
        data = json.loads(request.body)
        detalle_id = data.get('detalle_id')
        
        # Log de depuración
        print(f"[DEBUG] eliminar_del_carrito - detalle_id recibido: {detalle_id}")
        
        if not detalle_id:
            return JsonResponse({
                'success': False,
                'message': 'ID del detalle es requerido'
            }, status=400)
        
        # Obtener el usuario actual del sistema personalizado
        current_user = get_current_user(request)
        account_type = request.session.get('account_type', 'usuario')
        
        if account_type == 'empresa':
            # Buscar el carrito de empresa
            try:
                carrito = carrito_compra_producto_empresa.objects.get(
                    id_empresa_fk=current_user,
                    estatuscarrito_prod_empresa__in=['activo', 'pendiente']
                )
            except carrito_compra_producto_empresa.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró el carrito'
                }, status=404)
            
            # Buscar y eliminar el detalle directamente por su ID
            try:
                detalle = detalle_compra_producto_empresa.objects.get(
                    id_deta_carrito_prod_empresa=detalle_id,
                    id_fk_carritocompra_empresa=carrito
                )
                # Antes de eliminar, ajustar el stock reservado si aplica
                try:
                    # Si el detalle está asociado a una sucursal (producto_sucursal)
                    if detalle.id_fk_producto_sucursal_empresa:
                        producto = detalle.id_fk_producto_sucursal_empresa
                        cantidad = detalle.cantidad_deta_carrito_prod_empresa or 0
                        new_reserved = max(0, producto.stock_reservado_sucursal - cantidad)
                        producto.stock_reservado_sucursal = new_reserved
                        producto.save(update_fields=['stock_reservado_sucursal'])
                        logger.info(f"Stock reservado sucursal actualizado: {producto.id_producto_sucursal} - reservado ahora: {new_reserved}")
                    # Si el detalle está asociado a un producto de usuario
                    elif detalle.idproducto_fk_usuario:
                        producto_u = detalle.idproducto_fk_usuario
                        cantidad = detalle.cantidad_deta_carrito_prod_empresa or 0
                        new_reserved = max(0, producto_u.stock_reservado_usuario - cantidad)
                        producto_u.stock_reservado_usuario = new_reserved
                        producto_u.save(update_fields=['stock_reservado_usuario'])
                        logger.info(f"Stock reservado usuario actualizado: {producto_u.id_producto_usuario} - reservado ahora: {new_reserved}")
                except Exception as e:
                    logger.error(f"Error al actualizar stock reservado antes de eliminar detalle empresa {detalle_id}: {str(e)}")

                detalle.delete()
                print(f"[DEBUG] Detalle de empresa eliminado exitosamente: {detalle_id}")
                
            except detalle_compra_producto_empresa.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Detalle no encontrado en el carrito'
                }, status=404)
            
            # Recalcular el total del carrito
            total = sum(
                d.subtotal_deta_carrito_prod_empresa 
                for d in carrito.detalles.all()
            )
            carrito.total_carrito_prod_empresa = total
            carrito.save()
        
        else:  # account_type == 'usuario'
            # Buscar el carrito de usuario
            try:
                carrito = carrito_compra_producto_usuario.objects.get(
                    id_usuario_fk=current_user,
                    estatuscarrito_prod_usuario__in=['activo', 'pendiente']
                )
                print(f"[DEBUG] Carrito de usuario encontrado: {carrito.id_carrito_prod_usuario}")
            except carrito_compra_producto_usuario.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró el carrito'
                }, status=404)
            
            # Buscar y eliminar el detalle directamente por su ID
            try:
                detalle = detalle_compra_producto_usuario.objects.get(
                    id_deta_carrito_prod_usuario=detalle_id,
                    id_fk_carritocompra_usuario=carrito
                )
                # Antes de eliminar, ajustar el stock reservado si aplica
                try:
                    if detalle.id_fk_producto_sucursal_empresa:
                        producto = detalle.id_fk_producto_sucursal_empresa
                        cantidad = detalle.cantidad_deta_carrito_prod_usuario or 0
                        new_reserved = max(0, producto.stock_reservado_sucursal - cantidad)
                        producto.stock_reservado_sucursal = new_reserved
                        producto.save(update_fields=['stock_reservado_sucursal'])
                        logger.info(f"Stock reservado sucursal actualizado: {producto.id_producto_sucursal} - reservado ahora: {new_reserved}")
                    elif detalle.idproducto_fk_usuario:
                        producto_u = detalle.idproducto_fk_usuario
                        cantidad = detalle.cantidad_deta_carrito_prod_usuario or 0
                        new_reserved = max(0, producto_u.stock_reservado_usuario - cantidad)
                        producto_u.stock_reservado_usuario = new_reserved
                        producto_u.save(update_fields=['stock_reservado_usuario'])
                        logger.info(f"Stock reservado usuario actualizado: {producto_u.id_producto_usuario} - reservado ahora: {new_reserved}")
                except Exception as e:
                    logger.error(f"Error al actualizar stock reservado antes de eliminar detalle usuario {detalle_id}: {str(e)}")

                detalle.delete()
                print(f"[DEBUG] Detalle de usuario eliminado exitosamente: {detalle_id}")
                
            except detalle_compra_producto_usuario.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Detalle no encontrado en el carrito'
                }, status=404)
            
            # Recalcular el total del carrito
            total = sum(
                d.subtotal_deta_carrito_prod_usuario 
                for d in carrito.detalles.all()
            )
            carrito.total_carrito_prod_usuario = total
            carrito.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado del carrito exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error al eliminar producto del carrito: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)

@require_login
def pedido(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        
        # Información del usuario
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
        
        # Obtener productos del carrito
        productos_por_vendedor = {}
        total_productos = 0
        
        if account_type == 'empresa':
            # Lógica para empresas
            carrito_empresa = carrito_compra_producto_empresa.objects.filter(
                id_empresa_fk=current_user,
                estatuscarrito_prod_empresa__in=['activo', 'pendiente']
            ).first()
            
            if carrito_empresa:
                detalles_carrito = detalle_compra_producto_empresa.objects.filter(
                    id_fk_carritocompra_empresa=carrito_empresa
                ).select_related('id_fk_producto_sucursal_empresa__id_producto_fk', 'idproducto_fk_usuario')
                
                # Diccionarios para agrupar por vendedor específico
                productos_por_empresa = {}
                productos_por_usuario = {}
                
                for detalle in detalles_carrito:
                    if detalle.id_fk_producto_sucursal_empresa:
                        # Producto de empresa
                        producto_sucursal_obj = detalle.id_fk_producto_sucursal_empresa
                        producto = producto_sucursal_obj.id_producto_fk
                        
                        # Obtener la primera imagen del producto
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=producto
                        ).first()
                        
                        sucursal_id = producto_sucursal_obj.id_sucursal_fk.id_sucursal
                        sucursal_nombre = f"{producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.nombre_empresa} - {producto_sucursal_obj.id_sucursal_fk.nombre_sucursal}"
                        
                        if sucursal_id not in productos_por_empresa:
                            productos_por_empresa[sucursal_id] = []
                        
                        productos_por_empresa[sucursal_id].append({
                            'id': producto.id_producto_empresa,
                            'nombre': producto.nombre_producto_empresa,
                            'descripcion': producto.descripcion_producto_empresa,
                            'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                            'precio_unitario': detalle.precio_unit_deta_carrito_prod_empresa,
                            'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                            'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                            'vendedor_id': sucursal_id,
                            'vendedor_nombre': sucursal_nombre
                        })
                    
                    elif detalle.idproducto_fk_usuario:
                        # Producto de usuario
                        producto = detalle.idproducto_fk_usuario
                        
                        # Obtener la primera imagen del producto
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=producto
                        ).first()
                        
                        vendedor_id = producto.id_usuario_fk.id_usuario
                        vendedor_nombre = producto.id_usuario_fk.nombre_usuario
                        
                        if vendedor_id not in productos_por_usuario:
                            productos_por_usuario[vendedor_id] = []
                        
                        productos_por_usuario[vendedor_id].append({
                            'id': producto.id_producto_usuario,
                            'nombre': producto.nombre_producto_usuario,
                            'descripcion': producto.descripcion_producto_usuario,
                            'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                            'precio_unitario': detalle.precio_unit_deta_carrito_prod_empresa,
                            'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                            'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None,
                            'vendedor_id': vendedor_id,
                            'vendedor_nombre': vendedor_nombre
                        })
                
                # Agregar cada sucursal como un vendedor separado
                for sucursal_id, productos in productos_por_empresa.items():
                    productos_por_vendedor[f'empresa_{sucursal_id}'] = productos
                
                # Agregar cada usuario como un vendedor separado
                for usuario_id, productos in productos_por_usuario.items():
                    productos_por_vendedor[f'usuario_{usuario_id}'] = productos
                
                total_productos = carrito_empresa.total_carrito_prod_empresa
        
        else:
            # Lógica para usuarios
            carrito_usuario = carrito_compra_producto_usuario.objects.filter(
                id_usuario_fk=current_user,
                estatuscarrito_prod_usuario__in=['activo', 'pendiente']
            ).first()
            
            if carrito_usuario:
                detalles_carrito = detalle_compra_producto_usuario.objects.filter(
                    id_fk_carritocompra_usuario=carrito_usuario
                ).select_related('id_fk_producto_sucursal_empresa__id_producto_fk', 'idproducto_fk_usuario')
                
                # Diccionarios para agrupar por vendedor específico
                productos_por_empresa = {}
                productos_por_usuario = {}
                
                for detalle in detalles_carrito:
                    if detalle.id_fk_producto_sucursal_empresa:
                        # Producto de empresa
                        producto_sucursal_obj = detalle.id_fk_producto_sucursal_empresa
                        producto = producto_sucursal_obj.id_producto_fk
                        
                        # Obtener la primera imagen del producto
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=producto
                        ).first()
                        
                        sucursal_id = producto_sucursal_obj.id_sucursal_fk.id_sucursal
                        sucursal_nombre = f"{producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.nombre_empresa} - {producto_sucursal_obj.id_sucursal_fk.nombre_sucursal}"
                        
                        if sucursal_id not in productos_por_empresa:
                            productos_por_empresa[sucursal_id] = []
                        
                        productos_por_empresa[sucursal_id].append({
                            'id': producto.id_producto_empresa,
                            'nombre': producto.nombre_producto_empresa,
                            'descripcion': producto.descripcion_producto_empresa,
                            'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                            'precio_unitario': detalle.precio_unit_deta_carrito_prod_usuario,
                            'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                            'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                            'vendedor_id': sucursal_id,
                            'vendedor_nombre': sucursal_nombre
                        })
                    
                    elif detalle.idproducto_fk_usuario:
                        # Producto de usuario
                        producto = detalle.idproducto_fk_usuario
                        
                        # Obtener la primera imagen del producto
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=producto
                        ).first()
                        
                        vendedor_id = producto.id_usuario_fk.id_usuario
                        vendedor_nombre = producto.id_usuario_fk.nombre_usuario
                        
                        if vendedor_id not in productos_por_usuario:
                            productos_por_usuario[vendedor_id] = []
                        
                        productos_por_usuario[vendedor_id].append({
                            'id': producto.id_producto_usuario,
                            'nombre': producto.nombre_producto_usuario,
                            'descripcion': producto.descripcion_producto_usuario,
                            'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                            'precio_unitario': detalle.precio_unit_deta_carrito_prod_usuario,
                            'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                            'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None,
                            'vendedor_id': vendedor_id,
                            'vendedor_nombre': vendedor_nombre
                        })
                
                # Agregar cada sucursal como un vendedor separado
                for sucursal_id, productos in productos_por_empresa.items():
                    productos_por_vendedor[f'empresa_{sucursal_id}'] = productos
                
                # Agregar cada usuario como un vendedor separado
                for usuario_id, productos in productos_por_usuario.items():
                    productos_por_vendedor[f'usuario_{usuario_id}'] = productos
                
                total_productos = carrito_usuario.total_carrito_prod_usuario
        
        # Crear lista de productos para el template (compatibilidad)
        productos_carrito = []
        for tipo_vendedor, productos in productos_por_vendedor.items():
            productos_carrito.extend(productos)
        

        # Convertir Decimal a float para serialización JSON
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {key: convert_decimals(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return convert_decimals(obj.__dict__)
            elif str(type(obj)) == "<class 'decimal.Decimal'>":
                return float(obj)
            else:
                return obj
        
        productos_por_vendedor_serializable = convert_decimals(productos_por_vendedor)
        productos_carrito_serializable = convert_decimals(productos_carrito)
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'productos_por_vendedor': productos_por_vendedor,
            'productos_carrito': productos_carrito,
            'total_productos': total_productos,
            'productos_por_vendedor_json': json.dumps(productos_por_vendedor_serializable),
            'productos_carrito_json': json.dumps(productos_carrito_serializable)
        }
        
        return render(request, 'ecommerce_app/pedido.html', context)
        
    except Exception as e:
        logger.error(f"Error en función pedido: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}',
            'error': str(e)
        })


@csrf_exempt
@require_POST
def procesar_pedido(request):
    try:
        print("=== INICIO PROCESAR PEDIDO ===")
        
        # Obtener información del usuario actual
        current_user = get_current_user(request)
        print(f"Usuario actual: {current_user}")
        if not current_user:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'})
        
        # Obtener el tipo de cuenta
        account_type = request.session.get('account_type')
        print(f"Tipo de cuenta: {account_type}")
        
        # Obtener datos del formulario
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Datos del formulario HTML
            data = {
                'nombre': request.POST.get('nombre', ''),
                'email': request.POST.get('email', ''),
                'telefono': request.POST.get('telefono', ''),
                'direccionEntrega': request.POST.get('direccion_envio', ''),
                'metodoPago': request.POST.get('metodo_pago', ''),
                'notasAdicionales': request.POST.get('notas_pedido', ''),
                'vendedoresSeleccionados': request.POST.get('vendedores_seleccionados', ''),
                'finalizarTodos': request.POST.get('finalizar_todos', 'false')
            }
        
        # Obtener archivo de comprobante de pago si existe
        comprobante_pago = request.FILES.get('comprobante_pago')
        print(f"Archivo comprobante recibido: {comprobante_pago}")
        
        print(f"Datos del formulario: {data}")
        
        # Procesar vendedores seleccionados si no es "finalizar todos"
        vendedores_a_procesar = []
        if data.get('finalizarTodos', 'false').lower() == 'true':
            # Procesar todos los vendedores
            vendedores_a_procesar = None  # None significa todos
        else:
            # Procesar solo vendedores seleccionados
            vendedores_str = data.get('vendedoresSeleccionados', '')
            if vendedores_str:
                try:
                    vendedores_a_procesar = json.loads(vendedores_str)
                except json.JSONDecodeError:
                    vendedores_a_procesar = []
        
        print(f"Vendedores a procesar: {vendedores_a_procesar}")
        print(f"Tipo de vendedores_a_procesar: {type(vendedores_a_procesar)}")
        if vendedores_a_procesar:
            print(f"Contenido de vendedores_a_procesar: {vendedores_a_procesar}")
            print(f"Longitud de vendedores_a_procesar: {len(vendedores_a_procesar)}")
            for i, vendedor in enumerate(vendedores_a_procesar):
                print(f"  Vendedor {i}: '{vendedor}' (tipo: {type(vendedor)})")
        else:
            print("vendedores_a_procesar es None o vacío")
        
        # Generar número de pedido único
        import uuid
        numero_pedido = f"PED-{uuid.uuid4().hex[:8].upper()}"
        
        # Obtener información del carrito desde la base de datos (igual que en la función pedido)
        productos_carrito = []
        total_productos = 0
        cantidad_productos = 0
        carrito_obj = None
        
        if account_type == 'empresa':
            # Obtener carrito activo o pendiente de la empresa
            carrito_obj = carrito_compra_producto_empresa.objects.filter(
                id_empresa_fk=current_user,
                estatuscarrito_prod_empresa__in=['activo', 'pendiente']
            ).first()
            carrito_empresa = carrito_obj  # Asignar para uso posterior
            
            if not carrito_obj:
                return JsonResponse({'success': False, 'error': 'No hay carrito disponible para la empresa'})
            
            # Obtener detalles del carrito
            detalles_carrito = detalle_compra_producto_empresa.objects.filter(
                id_fk_carritocompra_empresa=carrito_obj
            ).select_related('id_fk_producto_sucursal_empresa__id_producto_fk', 'idproducto_fk_usuario')
            
            for detalle in detalles_carrito:
                if detalle.id_fk_producto_sucursal_empresa:
                    producto_sucursal_obj = detalle.id_fk_producto_sucursal_empresa
                    producto = producto_sucursal_obj.id_producto_fk
                    sucursal_info = producto_sucursal_obj.id_sucursal_fk
                    
                    productos_carrito.append({
                        'detalle_obj': detalle,
                        'id': producto.id_producto_empresa,
                        'tipo': 'empresa',
                        'nombre': producto.nombre_producto_empresa,
                        'precio': detalle.precio_unit_deta_carrito_prod_empresa,
                        'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                        'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                        'producto_sucursal_obj': producto_sucursal_obj
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_empresa
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_empresa
                
                elif detalle.idproducto_fk_usuario:
                    producto = detalle.idproducto_fk_usuario
                    
                    productos_carrito.append({
                        'detalle_obj': detalle,
                        'id': producto.id_producto_usuario,
                        'tipo': 'usuario',
                        'nombre': producto.nombre_producto_usuario,
                        'precio': detalle.precio_unit_deta_carrito_prod_empresa,
                        'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                        'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                        'producto_usuario_obj': producto
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_empresa
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_empresa
        
        else:  # account_type == 'usuario'
            # Obtener carrito activo o pendiente del usuario
            carrito_obj = carrito_compra_producto_usuario.objects.filter(
                id_usuario_fk=current_user,
                estatuscarrito_prod_usuario__in=['activo', 'pendiente']
            ).first()
            carrito_usuario = carrito_obj  # Asignar para uso posterior
            
            if not carrito_obj:
                return JsonResponse({'success': False, 'error': 'No hay carrito disponible para el usuario'})
            
            # Obtener detalles del carrito
            detalles_carrito = detalle_compra_producto_usuario.objects.filter(
                id_fk_carritocompra_usuario=carrito_obj
            ).select_related('idproducto_fk_usuario', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            for detalle in detalles_carrito:
                if detalle.id_fk_producto_sucursal_empresa:
                    producto_sucursal_obj = detalle.id_fk_producto_sucursal_empresa
                    producto = producto_sucursal_obj.id_producto_fk
                    sucursal_info = producto_sucursal_obj.id_sucursal_fk
                    
                    productos_carrito.append({
                        'detalle_obj': detalle,
                        'id': producto.id_producto_empresa,
                        'tipo': 'empresa',
                        'nombre': producto.nombre_producto_empresa,
                        'precio': detalle.precio_unit_deta_carrito_prod_usuario,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                        'producto_sucursal_obj': producto_sucursal_obj
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_usuario
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_usuario
                
                elif detalle.idproducto_fk_usuario:
                    producto = detalle.idproducto_fk_usuario
                    
                    productos_carrito.append({
                        'detalle_obj': detalle,
                        'id': producto.id_producto_usuario,
                        'tipo': 'usuario',
                        'nombre': producto.nombre_producto_usuario,
                        'precio': detalle.precio_unit_deta_carrito_prod_usuario,
                        'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                        'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                        'producto_usuario_obj': producto
                    })
                    
                    total_productos += detalle.subtotal_deta_carrito_prod_usuario
                    cantidad_productos += detalle.cantidad_deta_carrito_prod_usuario
        
        print(f"Productos encontrados en carrito: {len(productos_carrito)}")
        print(f"Total productos: {total_productos}")
        
        if not productos_carrito:
            return JsonResponse({'success': False, 'error': 'Carrito vacío'})
        
        # Separar productos por vendedor (sucursal/usuario) para crear pedidos agrupados
        print(f"Separando productos por vendedor (sucursal)...")
        print(f"Total productos en carrito antes del filtrado: {len(productos_carrito)}")
        for i, prod in enumerate(productos_carrito[:3]):  # Solo mostrar los primeros 3
            print(f"Producto {i+1}: tipo={prod.get('tipo')}, id={prod.get('id')}, nombre={prod.get('nombre')}")
            if prod['tipo'] == 'empresa' and 'producto_sucursal_obj' in prod:
                sucursal_id = prod['producto_sucursal_obj'].id_sucursal_fk.id_sucursal
                empresa_id = prod['producto_sucursal_obj'].id_sucursal_fk.id_empresa_fk.id_empresa
                print(f"  -> Sucursal ID: {sucursal_id}, Empresa ID: {empresa_id}, vendedor_key: sucursal_{sucursal_id}")
            elif prod['tipo'] == 'usuario' and 'producto_usuario_obj' in prod:
                usuario_id = prod['producto_usuario_obj'].id_usuario_fk.id_usuario
                print(f"  -> Usuario ID: {usuario_id}, vendedor_key: usuario_{usuario_id}")
        productos_por_sucursal = {}
        productos_por_usuario = {}
        
        for producto in productos_carrito:
            if producto['tipo'] == 'empresa':
                # Agrupar por sucursal
                if 'producto_sucursal_obj' in producto:
                    sucursal_id = producto['producto_sucursal_obj'].id_sucursal_fk.id_sucursal
                    empresa_id = producto['producto_sucursal_obj'].id_sucursal_fk.id_empresa_fk.id_empresa
                    
                    # Filtrar por vendedores seleccionados si no es "finalizar todos"
                    if vendedores_a_procesar is not None:
                        # Verificar tanto 'sucursal_' como 'empresa_' para compatibilidad
                        vendedor_key_sucursal = f"sucursal_{sucursal_id}"
                        vendedor_key_empresa = f"empresa_{sucursal_id}"
                        print(f"Comparando vendedor_keys '{vendedor_key_sucursal}' y '{vendedor_key_empresa}' con vendedores_a_procesar: {vendedores_a_procesar}")
                        
                        if vendedor_key_sucursal not in vendedores_a_procesar and vendedor_key_empresa not in vendedores_a_procesar:
                            print(f"SALTANDO producto de sucursal {sucursal_id} porque ni '{vendedor_key_sucursal}' ni '{vendedor_key_empresa}' están en vendedores seleccionados")
                            continue  # Saltar este producto si la sucursal no está seleccionada
                        else:
                            print(f"INCLUYENDO producto de sucursal {sucursal_id} porque está en vendedores seleccionados")
                    
                    if sucursal_id not in productos_por_sucursal:
                        productos_por_sucursal[sucursal_id] = {
                            'sucursal_obj': producto['producto_sucursal_obj'].id_sucursal_fk,
                            'empresa_obj': producto['producto_sucursal_obj'].id_sucursal_fk.id_empresa_fk,
                            'productos': [],
                            'total': 0
                        }
                    
                    productos_por_sucursal[sucursal_id]['productos'].append(producto)
                    productos_por_sucursal[sucursal_id]['total'] += producto['subtotal']
            
            elif producto['tipo'] == 'usuario':
                # Agrupar por usuario vendedor
                if 'producto_usuario_obj' in producto:
                    usuario_id = producto['producto_usuario_obj'].id_usuario_fk.id_usuario
                    
                    # Filtrar por vendedores seleccionados si no es "finalizar todos"
                    if vendedores_a_procesar is not None:
                        vendedor_key = f"usuario_{usuario_id}"
                        print(f"Comparando vendedor_key '{vendedor_key}' con vendedores_a_procesar: {vendedores_a_procesar}")
                        print(f"¿'{vendedor_key}' está en vendedores_a_procesar? {vendedor_key in vendedores_a_procesar}")
                        if vendedor_key not in vendedores_a_procesar:
                            print(f"SALTANDO producto de usuario {usuario_id} porque '{vendedor_key}' no está en vendedores seleccionados")
                            continue  # Saltar este producto si el vendedor no está seleccionado
                        else:
                            print(f"INCLUYENDO producto de usuario {usuario_id} porque '{vendedor_key}' SÍ está en vendedores seleccionados")
                    
                    if usuario_id not in productos_por_usuario:
                        productos_por_usuario[usuario_id] = {
                            'usuario_obj': producto['producto_usuario_obj'].id_usuario_fk,
                            'productos': [],
                            'total': 0
                        }
                    
                    productos_por_usuario[usuario_id]['productos'].append(producto)
                    productos_por_usuario[usuario_id]['total'] += producto['subtotal']
        
        print(f"Productos agrupados (filtrados) - Sucursales: {len(productos_por_sucursal)}, Usuarios: {len(productos_por_usuario)}")
        
        # Verificar que hay productos para procesar
        if not productos_por_sucursal and not productos_por_usuario:
            return JsonResponse({'success': False, 'error': 'No hay productos seleccionados para procesar'})
        
        # Crear pedidos según el tipo de cuenta del comprador
        pedidos_creados = []
        
        with transaction.atomic():
            if account_type == 'empresa':
                print("Creando pedidos para empresa compradora...")
                
                # Crear pedidos de empresa para productos de sucursales
                for sucursal_id, grupo in productos_por_sucursal.items():
                    nuevo_pedido = pedido_empresa.objects.create(
                        id_carrito_fk=carrito_empresa,
                        numero_pedido=f"{numero_pedido}-SUC{sucursal_id}",
                        direccion_envio=data.get('direccionEntrega', ''),
                        metodo_pago=data.get('metodoPago', ''),
                        total_pedido=grupo['total'],
                        notas_pedido=data.get('notasAdicionales', ''),
                        comprobante_pago=comprobante_pago
                    )
                    
                    # Crear detalles del pedido
                    for producto in grupo['productos']:
                        detalle_pedido_empresa.objects.create(
                            id_pedido_fk=nuevo_pedido,
                            id_fk_producto_sucursal_empresa=producto['producto_sucursal_obj'],
                            cantidad_detalle_pedido=producto['cantidad'],
                            precio_unitario_pedido=producto['precio'],
                            subtotal_detalle_pedido=producto['subtotal']
                        )
                    
                    # Notificar al vendedor (empresa) sobre el nuevo pedido
                    notificar_nuevo_pedido(nuevo_pedido)
                    
                    pedidos_creados.append({
                        'tipo': 'empresa',
                        'id': nuevo_pedido.id_pedido_empresa,
                        'vendedor': f"{grupo['empresa_obj'].nombre_empresa} - {grupo['sucursal_obj'].nombre_sucursal}",
                        'total': float(grupo['total'])
                    })
                
                # Crear pedidos de empresa para productos de usuarios
                for usuario_id, grupo in productos_por_usuario.items():
                    nuevo_pedido = pedido_empresa.objects.create(
                        id_carrito_fk=carrito_empresa,
                        numero_pedido=f"{numero_pedido}-USR{usuario_id}",
                        direccion_envio=data.get('direccionEntrega', ''),
                        metodo_pago=data.get('metodoPago', ''),
                        total_pedido=grupo['total'],
                        notas_pedido=data.get('notasAdicionales', ''),
                        comprobante_pago=comprobante_pago
                    )
                    
                    # Crear detalles del pedido
                    for producto in grupo['productos']:
                        detalle_pedido_empresa.objects.create(
                            id_pedido_fk=nuevo_pedido,
                            idproducto_fk_usuario=producto['producto_usuario_obj'],
                            cantidad_detalle_pedido=producto['cantidad'],
                            precio_unitario_pedido=producto['precio'],
                            subtotal_detalle_pedido=producto['subtotal']
                        )
                    
                    # Notificar al vendedor (usuario) sobre el nuevo pedido
                    notificar_nuevo_pedido(nuevo_pedido)
                    
                    pedidos_creados.append({
                        'tipo': 'empresa',
                        'id': nuevo_pedido.id_pedido_empresa,
                        'vendedor': grupo['usuario_obj'].nombre_usuario,
                        'total': float(grupo['total'])
                    })
            
            else:  # account_type == 'usuario'
                print("Creando pedidos para usuario comprador...")
                
                # Crear pedidos de usuario para productos de sucursales
                for sucursal_id, grupo in productos_por_sucursal.items():
                    nuevo_pedido = pedido_usuario.objects.create(
                        id_carrito_fk=carrito_usuario,
                        numero_pedido=f"{numero_pedido}-SUC{sucursal_id}",
                        direccion_envio=data.get('direccionEntrega', ''),
                        metodo_pago=data.get('metodoPago', ''),
                        total_pedido=grupo['total'],
                        notas_pedido=data.get('notasAdicionales', ''),
                        comprobante_pago=comprobante_pago
                    )
                    
                    # Crear detalles del pedido
                    for producto in grupo['productos']:
                        detalle_pedido_usuario.objects.create(
                            id_pedido_fk=nuevo_pedido,
                            id_fk_producto_sucursal_empresa=producto['producto_sucursal_obj'],
                            cantidad_detalle_pedido=producto['cantidad'],
                            precio_unitario_pedido=producto['precio'],
                            subtotal_detalle_pedido=producto['subtotal']
                        )
                    
                    # Notificar al vendedor (empresa) sobre el nuevo pedido
                    notificar_nuevo_pedido(nuevo_pedido)
                    
                    pedidos_creados.append({
                        'tipo': 'usuario',
                        'id': nuevo_pedido.id_pedido_usuario,
                        'vendedor': f"{grupo['empresa_obj'].nombre_empresa} - {grupo['sucursal_obj'].nombre_sucursal}",
                        'total': float(grupo['total'])
                    })
                
                # Crear pedidos de usuario para productos de usuarios
                for usuario_id, grupo in productos_por_usuario.items():
                    nuevo_pedido = pedido_usuario.objects.create(
                        id_carrito_fk=carrito_usuario,
                        numero_pedido=f"{numero_pedido}-USR{usuario_id}",
                        direccion_envio=data.get('direccionEntrega', ''),
                        metodo_pago=data.get('metodoPago', ''),
                        total_pedido=grupo['total'],
                        notas_pedido=data.get('notasAdicionales', ''),
                        comprobante_pago=comprobante_pago
                    )
                    
                    # Crear detalles del pedido
                    for producto in grupo['productos']:
                        detalle_pedido_usuario.objects.create(
                            id_pedido_fk=nuevo_pedido,
                            idproducto_fk_usuario=producto['producto_usuario_obj'],
                            cantidad_detalle_pedido=producto['cantidad'],
                            precio_unitario_pedido=producto['precio'],
                            subtotal_detalle_pedido=producto['subtotal']
                        )
                    
                    # Notificar al vendedor (usuario) sobre el nuevo pedido
                    notificar_nuevo_pedido(nuevo_pedido)
                    
                    pedidos_creados.append({
                        'tipo': 'usuario',
                        'id': nuevo_pedido.id_pedido_usuario,
                        'vendedor': grupo['usuario_obj'].nombre_usuario,
                        'total': float(grupo['total'])
                    })
            
            # Verificar si todos los productos del carrito fueron procesados
            print("Verificando si todos los productos fueron procesados...")
            
            # Obtener todos los productos del carrito
            if account_type == 'empresa':
                todos_productos_carrito = detalle_compra_producto_empresa.objects.filter(
                    id_fk_carritocompra_empresa=carrito_obj
                ).count()
            else:
                todos_productos_carrito = detalle_compra_producto_usuario.objects.filter(
                    id_fk_carritocompra_usuario=carrito_obj
                ).count()
            
            # Contar productos procesados en esta transacción
            productos_procesados = sum(len(grupo['productos']) for grupo in productos_por_sucursal.values()) + \
                                 sum(len(grupo['productos']) for grupo in productos_por_usuario.values())
            
            print(f"Total productos en carrito: {todos_productos_carrito}")
            print(f"Productos procesados en esta transacción: {productos_procesados}")
            
            # Determinar el nuevo estatus del carrito
            if productos_procesados >= todos_productos_carrito:
                # Todos los productos fueron procesados
                nuevo_estatus = 'completado'
                print("Marcando carrito como completado - todos los productos procesados")
            else:
                # Solo algunos productos fueron procesados
                nuevo_estatus = 'pendiente'
                print("Marcando carrito como pendiente - productos parcialmente procesados")
            
            # Actualizar el estatus del carrito
            if account_type == 'empresa':
                carrito_obj.estatuscarrito_prod_empresa = nuevo_estatus
            else:
                carrito_obj.estatuscarrito_prod_usuario = nuevo_estatus
            carrito_obj.save()
            
            # Eliminar productos procesados del carrito
            productos_eliminados = 0
            
            # Eliminar productos de sucursales procesados
            for sucursal_id, grupo in productos_por_sucursal.items():
                for producto in grupo['productos']:
                    if account_type == 'empresa':
                        detalle_compra_producto_empresa.objects.filter(
                            id_fk_carritocompra_empresa=carrito_obj,
                            id_fk_producto_sucursal_empresa=producto['producto_sucursal_obj']
                        ).delete()
                    else:
                        detalle_compra_producto_usuario.objects.filter(
                            id_fk_carritocompra_usuario=carrito_obj,
                            id_fk_producto_sucursal_empresa=producto['producto_sucursal_obj']
                        ).delete()
                    productos_eliminados += 1
            
            # Eliminar productos de usuarios procesados
            for usuario_id, grupo in productos_por_usuario.items():
                for producto in grupo['productos']:
                    if account_type == 'empresa':
                        detalle_compra_producto_empresa.objects.filter(
                            id_fk_carritocompra_empresa=carrito_obj,
                            idproducto_fk_usuario=producto['producto_usuario_obj']
                        ).delete()
                    else:
                        detalle_compra_producto_usuario.objects.filter(
                            id_fk_carritocompra_usuario=carrito_obj,
                            idproducto_fk_usuario=producto['producto_usuario_obj']
                        ).delete()
                    productos_eliminados += 1
            
            print(f"Pedidos creados exitosamente: {len(pedidos_creados)}")
            print(f"Productos eliminados del carrito: {productos_eliminados}")
            
            # Recalcular el total del carrito después de eliminar productos
            recalcular_total_carrito(carrito_obj, account_type)
            
            # Guardar datos en la sesión para mostrar en la página de confirmación
            request.session['pedidos_confirmacion'] = pedidos_creados
            request.session['datos_cliente_confirmacion'] = {
                'nombre': data.get('nombre', ''),
                'email': data.get('email', ''),
                'telefono': data.get('telefono', ''),
                'direccion_envio': data.get('direccionEntrega', ''),
                'metodo_pago': data.get('metodoPago', ''),
                'notas': data.get('notasAdicionales', '')
            }
            request.session['total_general_confirmacion'] = float(total_productos)
            
            # Redirigir a la página de confirmación
            return JsonResponse({
                'success': True,
                'redirect_url': '/ecommerce/confirmacion_pedido/',
                'message': f'Se crearon {len(pedidos_creados)} pedidos exitosamente'
            })
            
    except Exception as e:
        print(f"ERROR en procesar_pedido: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': str(e)})


def confirmacion_pedido(request):
    """Vista para mostrar la confirmación de pedido después de procesarlo exitosamente"""
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        
        # Obtener datos de la sesión (guardados después de procesar el pedido)
        pedidos_data = request.session.get('pedidos_confirmacion')
        datos_cliente = request.session.get('datos_cliente_confirmacion')
        total_general = request.session.get('total_general_confirmacion')
        
        if not pedidos_data or not datos_cliente:
            # Si no hay datos en la sesión, redirigir al carrito
            return redirect('/ecommerce/carrito')
            
        # Procesar y mostrar los datos de confirmación
        context = {
            'pedidos_data': pedidos_data,
            'datos_cliente': datos_cliente,
            'total_general': total_general,
            'account_type': account_type
        }
        
        return render(request, 'ecommerce_app/confirmacion_pedido.html', context)
        
    except Exception as e:
        print(f"Error en confirmacion_pedido: {str(e)}")
        return redirect('/ecommerce/carrito')

def obtener_ventas_pendientes_como_notificaciones(current_user, account_type):
    """Función auxiliar para obtener ventas pendientes y convertirlas en formato de notificaciones"""
    ventas_notificaciones = []
    
    try:
        if account_type == 'usuario':
            # Pedidos de usuarios que compraron productos de este usuario (solo pendientes)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Pedidos de empresas que compraron productos de este usuario (solo pendientes)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'pedido': pedido,
                        'comprador_nombre': comprador.nombre_usuario,
                        'comprador_tipo': 'usuario',
                        'total': pedido.total_pedido,
                        'productos_count': 0
                    }
                pedidos_dict[pedido.numero_pedido]['productos_count'] += 1
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'pedido': pedido,
                        'comprador_nombre': comprador.nombre_empresa,
                        'comprador_tipo': 'empresa',
                        'total': pedido.total_pedido,
                        'productos_count': 0
                    }
                pedidos_dict[pedido.numero_pedido]['productos_count'] += 1
            
            # Convertir a formato de notificaciones
            for pedido_info in pedidos_dict.values():
                pedido = pedido_info['pedido']
                ventas_notificaciones.append({
                    'id_notificacion': f"venta_{pedido.numero_pedido}",
                    'tipo_notificacion': 'venta_pendiente',
                    'titulo': f"Nueva Venta - Pedido #{pedido.numero_pedido}",
                    'mensaje': f"¡Tienes una nueva venta! {pedido_info['comprador_nombre']} ({pedido_info['comprador_tipo']}) compró {pedido_info['productos_count']} producto(s) por ${pedido_info['total']}. Confirma la venta para proceder.",
                    'estado': 'no_leida',
                    'fecha_creacion': pedido.fecha_pedido,
                    'fecha_leida': None,
                    'es_venta_pendiente': True,
                    'numero_pedido': pedido.numero_pedido,
                    'total_venta': pedido_info['total']
                })
                
        elif account_type == 'empresa':
            current_empresa = current_user
            
            # Pedidos de usuarios que compraron productos de esta empresa (solo pendientes)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Pedidos de empresas que compraron productos de esta empresa (solo pendientes)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'pedido': pedido,
                        'comprador_nombre': comprador.nombre_usuario,
                        'comprador_tipo': 'usuario',
                        'total': pedido.total_pedido,
                        'productos_count': 0
                    }
                pedidos_dict[pedido.numero_pedido]['productos_count'] += 1
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'pedido': pedido,
                        'comprador_nombre': comprador.nombre_empresa,
                        'comprador_tipo': 'empresa',
                        'total': pedido.total_pedido,
                        'productos_count': 0
                    }
                pedidos_dict[pedido.numero_pedido]['productos_count'] += 1
            
            # Convertir a formato de notificaciones
            for pedido_info in pedidos_dict.values():
                pedido = pedido_info['pedido']
                ventas_notificaciones.append({
                    'id_notificacion': f"venta_{pedido.numero_pedido}",
                    'tipo_notificacion': 'venta_pendiente',
                    'titulo': f"Nueva Venta - Pedido #{pedido.numero_pedido}",
                    'mensaje': f"¡Tienen una nueva venta! {pedido_info['comprador_nombre']} ({pedido_info['comprador_tipo']}) compró {pedido_info['productos_count']} producto(s) por ${pedido_info['total']}. Confirmen la venta para proceder.",
                    'estado': 'no_leida',
                    'fecha_creacion': pedido.fecha_pedido,
                    'fecha_leida': None,
                    'es_venta_pendiente': True,
                    'numero_pedido': pedido.numero_pedido,
                    'total_venta': pedido_info['total']
                })
    
    except Exception as e:
        logger.error(f"Error al obtener ventas pendientes: {str(e)}")
    
    return ventas_notificaciones


def notificaciones(request):
    """Vista para mostrar las notificaciones del usuario incluyendo ventas pendientes"""
    current_user = get_current_user(request)
    if not current_user:
        # Para pruebas, crear un usuario temporal
        try:
            current_user = usuario.objects.first()
            if current_user:
                request.session['is_authenticated'] = True
                request.session['user_id'] = current_user.id_usuario
                request.session['account_type'] = 'usuario'
            else:
                return redirect('/ecommerce/login')
        except:
            return redirect('/ecommerce/login')
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        
        # Obtener información del usuario
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': 'empresa',
                'is_authenticated': True
            }
            
            # Obtener notificaciones de empresa
            from .models import notificacion_empresa
            notificaciones_list = list(notificacion_empresa.objects.filter(
                id_empresa_fk=current_user
            ).order_by('-fecha_creacion'))
            
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
            
            # Obtener notificaciones de usuario
            from .models import notificacion_usuario
            notificaciones_list = list(notificacion_usuario.objects.filter(
                id_usuario_fk=current_user
            ).order_by('-fecha_creacion'))
        
        # Obtener ventas pendientes como notificaciones
        ventas_pendientes = obtener_ventas_pendientes_como_notificaciones(current_user, account_type)

        # Build set of pedido numbers from ventas_pendientes to avoid duplicate notifications
        ventas_pedidos_nums = set()
        for vp in ventas_pendientes:
            try:
                num = vp.get('numero_pedido')
                if num:
                    ventas_pedidos_nums.add(num)
            except Exception:
                continue

        # Combinar notificaciones regulares con ventas pendientes, omitiendo duplicados
        todas_notificaciones = []

        # Agregar notificaciones regulares (omitir 'nuevo_pedido' que ya aparece en ventas_pendientes)
        for notif in notificaciones_list:
            # obtener número de pedido asociado a la notificación (si existe)
            notif_pedido_num = None
            if account_type == 'empresa':
                pedido_fk = getattr(notif, 'id_pedido_empresa_fk', None)
            else:
                pedido_fk = getattr(notif, 'id_pedido_usuario_fk', None)

            if pedido_fk:
                notif_pedido_num = getattr(pedido_fk, 'numero_pedido', None)

            # Si la notificación es tipo 'nuevo_pedido' y ya existe una venta pendiente para el mismo pedido,
            # la omitimos para evitar duplicados en la lista de notificaciones.
            if getattr(notif, 'tipo_notificacion', '') == 'nuevo_pedido' and notif_pedido_num in ventas_pedidos_nums:
                continue

            todas_notificaciones.append({
                'id_notificacion': notif.id_notificacion_empresa if account_type == 'empresa' else notif.id_notificacion_usuario,
                'tipo_notificacion': notif.tipo_notificacion,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'estado': notif.estado,
                'fecha_creacion': notif.fecha_creacion,
                'fecha_leida': notif.fecha_leida,
                'es_venta_pendiente': False,
                'id_pedido_usuario_fk': getattr(notif, 'id_pedido_usuario_fk', None),
                'id_pedido_empresa_fk': getattr(notif, 'id_pedido_empresa_fk', None)
            })

        # Agregar ventas pendientes (después de las notificaciones regulares filtradas)
        todas_notificaciones.extend(ventas_pendientes)
        
        # Ordenar todas las notificaciones por fecha de creación (más recientes primero)
        todas_notificaciones.sort(key=lambda x: x['fecha_creacion'], reverse=True)
        
        # Contar notificaciones no leídas (incluyendo ventas pendientes)
        total_no_leidas = sum(1 for notif in todas_notificaciones if notif['estado'] == 'no_leida')
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'notificaciones': todas_notificaciones,
            'total_no_leidas': total_no_leidas,
            'total_notificaciones': len(todas_notificaciones),
            'ventas_pendientes_count': len(ventas_pendientes)
        }
        
        return render(request, 'ecommerce_app/notificaciones.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en función notificaciones: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"ERROR EN NOTIFICACIONES: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        return redirect('/ecommerce/index')
        
        # Obtener los pedidos reales de la base de datos para mostrar información actualizada
        pedidos_creados = []
        
        for pedido_info in pedidos_data:
            if pedido_info['tipo'] == 'usuario':
                try:
                    pedido_obj = pedido_usuario.objects.get(id_pedido_usuario=pedido_info['id'])
                    detalles = detalle_pedido_usuario.objects.filter(id_pedido_fk=pedido_obj)
                    
                    detalles_list = []
                    for detalle in detalles:
                        if detalle.id_fk_producto_sucursal_empresa:
                            nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        elif detalle.idproducto_fk_usuario:
                            nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        else:
                            nombre_producto = "Producto no disponible"
                        
                        detalles_list.append({
                            'nombre_producto': nombre_producto,
                            'cantidad': detalle.cantidad_detalle_pedido,
                            'precio_unitario': float(detalle.precio_unitario_pedido),
                            'subtotal': float(detalle.subtotal_detalle_pedido)
                        })
                    
                    pedidos_creados.append({
                        'numero_pedido': pedido_obj.numero_pedido,
                        'fecha_pedido': pedido_obj.fecha_pedido.isoformat() if pedido_obj.fecha_pedido else None,
                        'estado_pedido': pedido_obj.estado_pedido,
                        'total_pedido': float(pedido_obj.total_pedido),
                        'vendedor_nombre': pedido_info['vendedor'],
                        'detalles': detalles_list
                    })
                except pedido_usuario.DoesNotExist:
                    continue
                    
            elif pedido_info['tipo'] == 'empresa':
                try:
                    pedido_obj = pedido_empresa.objects.get(id_pedido_empresa=pedido_info['id'])
                    detalles = detalle_pedido_empresa.objects.filter(id_pedido_fk=pedido_obj)
                    
                    detalles_list = []
                    for detalle in detalles:
                        if detalle.id_fk_producto_sucursal_empresa:
                            nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        elif detalle.idproducto_fk_usuario:
                            nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        else:
                            nombre_producto = "Producto no disponible"
                        
                        detalles_list.append({
                            'nombre_producto': nombre_producto,
                            'cantidad': detalle.cantidad_detalle_pedido,
                            'precio_unitario': float(detalle.precio_unitario_pedido),
                            'subtotal': float(detalle.subtotal_detalle_pedido)
                        })
                    
                    pedidos_creados.append({
                        'numero_pedido': pedido_obj.numero_pedido,
                        'fecha_pedido': pedido_obj.fecha_pedido.isoformat() if pedido_obj.fecha_pedido else None,
                        'estado_pedido': pedido_obj.estado_pedido,
                        'total_pedido': float(pedido_obj.total_pedido),
                        'vendedor_nombre': pedido_info['vendedor'],
                        'detalles': detalles_list
                    })
                except pedido_empresa.DoesNotExist:
                    continue
        
        # Limpiar datos de la sesión después de mostrarlos
        if 'pedidos_confirmacion' in request.session:
            del request.session['pedidos_confirmacion']
        if 'datos_cliente_confirmacion' in request.session:
            del request.session['datos_cliente_confirmacion']
        if 'total_general_confirmacion' in request.session:
            del request.session['total_general_confirmacion']
        
        context = {
            'account_type': account_type,
            'pedidos_creados': pedidos_creados,
            'datos_cliente': datos_cliente,
            'total_general': total_general
        }
        
        return render(request, 'ecommerce_app/confirmacion_pedido.html', context)
        
    except Exception as e:
        logger.error(f"Error en función confirmacion_pedido: {str(e)}")
        return redirect('/ecommerce/carrito')

# Funciones para manejar cambios de estado en servicios
def actualizar_estado_servicio_usuario(request):
    """Actualiza el estado de una solicitud de servicio de usuario"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        solicitud_id = data.get('solicitud_id')
        nuevo_estado = data.get('nuevo_estado')
        precio_cotizado = data.get('precio_cotizado')
        comentario = data.get('comentario', '')
        
        if not solicitud_id or not nuevo_estado:
            return JsonResponse({'success': False, 'message': 'Datos incompletos'})
        
        # Obtener la solicitud
        solicitud = solicitud_servicio_usuario.objects.get(id_solicitud_servicio_usuario=solicitud_id)
        
        # Verificar permisos (solo el proveedor del servicio puede cambiar el estado)
        if solicitud.id_servicio_usuario_fk:
            if solicitud.id_servicio_usuario_fk.id_usuario_fk != current_user:
                return JsonResponse({'success': False, 'message': 'No tienes permisos para actualizar esta solicitud'})
        elif solicitud.id_servicio_sucursal_fk:
            if solicitud.id_servicio_sucursal_fk.id_servicio_fk.id_empresa_fk != current_user:
                return JsonResponse({'success': False, 'message': 'No tienes permisos para actualizar esta solicitud'})
        
        # Actualizar estado
        estado_anterior = solicitud.estado
        solicitud.estado = nuevo_estado
        solicitud.save()
        
        # Crear notificación para el solicitante
        cliente = solicitud.id_usuario_fk
        
        if nuevo_estado == 'cotizada':
            titulo = "Servicio Cotizado"
            mensaje = f"Tu solicitud de servicio ha sido cotizada. Precio: ${precio_cotizado}"
        elif nuevo_estado == 'aceptada':
            titulo = "Servicio Aceptado"
            mensaje = f"Tu solicitud de servicio ha sido aceptada y está en proceso."
        elif nuevo_estado == 'completada':
            titulo = "Servicio Completado"
            mensaje = f"Tu servicio ha sido completado exitosamente."
        elif nuevo_estado == 'rechazada':
            titulo = "Servicio Rechazado"
            mensaje = f"Tu solicitud de servicio ha sido rechazada. {comentario}"
        else:
            titulo = "Estado de Servicio Actualizado"
            mensaje = f"El estado de tu servicio ha cambiado a {nuevo_estado}."
        
        # Mapear tipos a notificaciones concretas para que coincidan con TIPOS_NOTIFICACION
        tipo_map_usuario = {
            'cotizada': 'servicio_cotizado',
            'aceptada': 'servicio_aceptado',
            'completada': 'servicio_completado',
            'rechazada': 'pedido_rechazado'
        }
        tipo_notif = tipo_map_usuario.get(nuevo_estado, 'servicio_cotizado')

        crear_notificacion_usuario(
            usuario=cliente,
            tipo_notificacion=tipo_notif,
            titulo=titulo,
            mensaje=mensaje,
            solicitud_servicio=solicitud
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Estado actualizado a {nuevo_estado}',
            'estado_anterior': estado_anterior,
            'nuevo_estado': nuevo_estado
        })
        
    except solicitud_servicio_usuario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Solicitud no encontrada'})
    except Exception as e:
        logger.error(f"Error al actualizar estado de servicio: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'})

def marcar_notificacion_leida_vista(request):
    """Vista para marcar una notificación como leída vía AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        notificacion_id = data.get('notificacion_id')
        es_empresa = data.get('es_empresa', False)
        
        if not notificacion_id:
            return JsonResponse({'success': False, 'message': 'ID de notificación requerido'})
        
        # Verificar que la notificación pertenece al usuario actual
        if es_empresa:
            from .models import notificacion_empresa
            try:
                notificacion = notificacion_empresa.objects.get(
                    id_notificacion_empresa=notificacion_id,
                    id_empresa_fk=current_user
                )
            except notificacion_empresa.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Notificación no encontrada o no autorizada'})
        else:
            from .models import notificacion_usuario
            try:
                notificacion = notificacion_usuario.objects.get(
                    id_notificacion_usuario=notificacion_id,
                    id_usuario_fk=current_user
                )
            except notificacion_usuario.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Notificación no encontrada o no autorizada'})
        
        # Marcar como leída
        resultado = marcar_notificacion_leida(notificacion_id, es_empresa)
        
        if resultado:
            return JsonResponse({
                'success': True, 
                'message': 'Notificación marcada como leída'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Error al marcar la notificación como leída'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Datos JSON inválidos'})
    except Exception as e:
        logger.error(f"Error en marcar_notificacion_leida_vista: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'})

def obtener_notificaciones_usuario(request):
    """Vista para obtener las notificaciones del usuario actual incluyendo ventas pendientes"""
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        notificaciones = []
        
        if account_type == 'empresa':
            from .models import notificacion_empresa
            notifs = notificacion_empresa.objects.filter(
                id_empresa_fk=current_user
            ).order_by('-fecha_creacion')[:20]  # Últimas 20 notificaciones
            
            for notif in notifs:
                notificaciones.append({
                    'id': notif.id_notificacion_empresa,
                    'tipo': notif.tipo_notificacion,
                    'titulo': notif.titulo,
                    'mensaje': notif.mensaje,
                    'estado': notif.estado,
                    'fecha_creacion': notif.fecha_creacion.isoformat(),
                    'fecha_leida': notif.fecha_leida.isoformat() if notif.fecha_leida else None,
                    'es_empresa': True
                })
        else:
            from .models import notificacion_usuario
            notifs = notificacion_usuario.objects.filter(
                id_usuario_fk=current_user
            ).order_by('-fecha_creacion')[:20]  # Últimas 20 notificaciones
            
            for notif in notifs:
                notificaciones.append({
                    'id': notif.id_notificacion_usuario,
                    'tipo': notif.tipo_notificacion,
                    'titulo': notif.titulo,
                    'mensaje': notif.mensaje,
                    'estado': notif.estado,
                    'fecha_creacion': notif.fecha_creacion.isoformat(),
                    'fecha_leida': notif.fecha_leida.isoformat() if notif.fecha_leida else None,
                    'es_empresa': False
                })
        
        # Obtener ventas pendientes como notificaciones
        ventas_pendientes = obtener_ventas_pendientes_como_notificaciones(current_user, account_type)
        
        # Contar notificaciones no leídas regulares
        notificaciones_no_leidas = len([n for n in notificaciones if n['estado'] == 'no_leida'])
        
        # Contar ventas pendientes (todas se consideran no leídas)
        ventas_pendientes_count = len(ventas_pendientes)
        
        # Total de notificaciones no leídas
        total_no_leidas = notificaciones_no_leidas + ventas_pendientes_count
        
        return JsonResponse({
            'success': True,
            'notificaciones': notificaciones,
            'ventas_pendientes': ventas_pendientes,
            'total_no_leidas': total_no_leidas,
            'ventas_pendientes_count': ventas_pendientes_count
        })
        
    except Exception as e:
        logger.error(f"Error al obtener notificaciones: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'})

def actualizar_estado_servicio_empresa(request):
    """Actualiza el estado de una solicitud de servicio de empresa"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
    
    try:
        data = json.loads(request.body)
        solicitud_id = data.get('solicitud_id')
        nuevo_estado = data.get('nuevo_estado')
        precio_cotizado = data.get('precio_cotizado')
        comentario = data.get('comentario', '')
        
        if not solicitud_id or not nuevo_estado:
            return JsonResponse({'success': False, 'message': 'Datos incompletos'})
        
        # Obtener la solicitud
        solicitud = solicitud_servicio_empresa.objects.get(id_solicitud_servicio_empresa=solicitud_id)
        
        # Verificar permisos (solo el proveedor del servicio puede cambiar el estado)
        if solicitud.id_servicio_usuario_fk:
            if solicitud.id_servicio_usuario_fk.id_usuario_fk != current_user:
                return JsonResponse({'success': False, 'message': 'No tienes permisos para actualizar esta solicitud'})
        elif solicitud.id_servicio_sucursal_fk:
            if solicitud.id_servicio_sucursal_fk.id_servicio_fk.id_empresa_fk != current_user:
                return JsonResponse({'success': False, 'message': 'No tienes permisos para actualizar esta solicitud'})
        
        # Actualizar estado
        estado_anterior = solicitud.estado
        solicitud.estado = nuevo_estado
        solicitud.save()
        
        # Crear notificación para el solicitante
        cliente = solicitud.id_empresa_fk
        
        if nuevo_estado == 'cotizada':
            titulo = "Servicio Cotizado"
            mensaje = f"Su solicitud de servicio ha sido cotizada. Precio: ${precio_cotizado}"
        elif nuevo_estado == 'aceptada':
            titulo = "Servicio Aceptado"
            mensaje = f"Su solicitud de servicio ha sido aceptada y está en proceso."
        elif nuevo_estado == 'completada':
            titulo = "Servicio Completado"
            mensaje = f"Su servicio ha sido completado exitosamente."
        elif nuevo_estado == 'rechazada':
            titulo = "Servicio Rechazado"
            mensaje = f"Su solicitud de servicio ha sido rechazada. {comentario}"
        else:
            titulo = "Estado de Servicio Actualizado"
            mensaje = f"El estado de su servicio ha cambiado a {nuevo_estado}."
        
        # Mapear tipos a notificaciones concretas para empresas. Algunas claves pueden
        # no existir exactamente en TIPOS_NOTIFICACION de la empresa; ajustamos a valores
        # cercanos para mantener compatibilidad.
        tipo_map_empresa = {
            'cotizada': 'solicitud_servicio',
            'aceptada': 'servicio_pagado',
            'completada': 'servicio_pagado',
            'rechazada': 'venta_rechazada'
        }
        tipo_notif_emp = tipo_map_empresa.get(nuevo_estado, 'solicitud_servicio')

        crear_notificacion_empresa(
            empresa=cliente,
            tipo_notificacion=tipo_notif_emp,
            titulo=titulo,
            mensaje=mensaje,
            solicitud_servicio=solicitud
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Estado actualizado a {nuevo_estado}',
            'estado_anterior': estado_anterior,
            'nuevo_estado': nuevo_estado
        })
        
    except solicitud_servicio_empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Solicitud no encontrada'})
    except Exception as e:
        logger.error(f"Error al actualizar estado de servicio: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'})


# ============================================================================
# FUNCIONES AUXILIARES PARA NOTIFICACIONES
# ============================================================================

def crear_notificacion_usuario(usuario, tipo_notificacion, titulo, mensaje, pedido=None, solicitud_servicio=None):
    """
    Función auxiliar para crear notificaciones para usuarios.
    
    Args:
        usuario: Instancia del modelo usuario
        tipo_notificacion: Tipo de notificación (debe estar en TIPOS_NOTIFICACION)
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        pedido: Instancia del pedido relacionado (opcional)
        solicitud_servicio: Instancia de la solicitud de servicio relacionada (opcional)
    """
    try:
        from .models import notificacion_usuario
        
        notificacion = notificacion_usuario.objects.create(
            id_usuario_fk=usuario,
            tipo_notificacion=tipo_notificacion,
            titulo=titulo,
            mensaje=mensaje,
            id_pedido_usuario_fk=pedido,
            id_solicitud_servicio_usuario_fk=solicitud_servicio,
            estado='no_leida'
        )
        
        logger.info(f"Notificación creada para usuario {usuario.nombre_usuario}: {titulo}")
        return notificacion
        
    except Exception as e:
        logger.error(f"Error al crear notificación para usuario {usuario.nombre_usuario}: {str(e)}")
        return None


def crear_notificacion_empresa(empresa, tipo_notificacion, titulo, mensaje, pedido=None, solicitud_servicio=None):
    """
    Función auxiliar para crear notificaciones para empresas.
    
    Args:
        empresa: Instancia del modelo empresa
        tipo_notificacion: Tipo de notificación (debe estar en TIPOS_NOTIFICACION)
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        pedido: Instancia del pedido relacionado (opcional)
        solicitud_servicio: Instancia de la solicitud de servicio relacionada (opcional)
    """
    try:
        from .models import notificacion_empresa
        
        notificacion = notificacion_empresa.objects.create(
            id_empresa_fk=empresa,
            tipo_notificacion=tipo_notificacion,
            titulo=titulo,
            mensaje=mensaje,
            id_pedido_empresa_fk=pedido,
            id_solicitud_servicio_empresa_fk=solicitud_servicio,
            estado='no_leida'
        )
        
        logger.info(f"Notificación creada para empresa {empresa.nombre_empresa}: {titulo}")
        return notificacion
        
    except Exception as e:
        logger.error(f"Error al crear notificación para empresa {empresa.nombre_empresa}: {str(e)}")
        return None


def notificar_pedido_confirmado(pedido):
    """
    Crear notificación cuando un pedido es confirmado.
    Notifica al comprador que su pedido fue confirmado.
    """
    try:
        # Obtener el comprador del pedido
        comprador = None
        if hasattr(pedido, 'id_carrito_fk'):
            if hasattr(pedido.id_carrito_fk, 'id_usuario_fk'):
                # Pedido de usuario
                comprador = pedido.id_carrito_fk.id_usuario_fk
                titulo = f"Pedido #{pedido.numero_pedido} Confirmado"
                mensaje = f"¡Excelente! Tu pedido #{pedido.numero_pedido} por ${pedido.total_pedido} ha sido confirmado y será procesado pronto."
                
                crear_notificacion_usuario(
                    usuario=comprador,
                    tipo_notificacion='pedido_confirmado',
                    titulo=titulo,
                    mensaje=mensaje,
                    pedido=pedido
                )
                
            elif hasattr(pedido.id_carrito_fk, 'id_empresa_fk'):
                # Pedido de empresa
                comprador = pedido.id_carrito_fk.id_empresa_fk
                titulo = f"Pedido #{pedido.numero_pedido} Confirmado"
                mensaje = f"¡Excelente! Su pedido #{pedido.numero_pedido} por ${pedido.total_pedido} ha sido confirmado y será procesado pronto."
                
                crear_notificacion_empresa(
                    empresa=comprador,
                    tipo_notificacion='venta_confirmada',
                    titulo=titulo,
                    mensaje=mensaje,
                    pedido=pedido
                )
                
    except Exception as e:
        logger.error(f"Error al notificar pedido confirmado {pedido.numero_pedido}: {str(e)}")


def notificar_pedido_cancelado(pedido, motivo_rechazo):
    """
    Crear notificación cuando un pedido es cancelado/rechazado.
    Notifica al comprador que su pedido fue rechazado.
    """
    try:
        # Obtener el comprador del pedido
        comprador = None
        if hasattr(pedido, 'id_carrito_fk'):
            if hasattr(pedido.id_carrito_fk, 'id_usuario_fk'):
                # Pedido de usuario
                comprador = pedido.id_carrito_fk.id_usuario_fk
                titulo = f"Pedido #{pedido.numero_pedido} Rechazado"
                mensaje = f"Lamentamos informarte que tu pedido #{pedido.numero_pedido} ha sido rechazado. Motivo: {motivo_rechazo}"
                
                crear_notificacion_usuario(
                    usuario=comprador,
                    tipo_notificacion='pedido_rechazado',
                    titulo=titulo,
                    mensaje=mensaje,
                    pedido=pedido
                )
                
            elif hasattr(pedido.id_carrito_fk, 'id_empresa_fk'):
                # Pedido de empresa
                comprador = pedido.id_carrito_fk.id_empresa_fk
                titulo = f"Pedido #{pedido.numero_pedido} Rechazado"
                mensaje = f"Lamentamos informarle que su pedido #{pedido.numero_pedido} ha sido rechazado. Motivo: {motivo_rechazo}"
                
                crear_notificacion_empresa(
                    empresa=comprador,
                    tipo_notificacion='venta_rechazada',
                    titulo=titulo,
                    mensaje=mensaje,
                    pedido=pedido
                )
                
    except Exception as e:
        logger.error(f"Error al notificar pedido cancelado {pedido.numero_pedido}: {str(e)}")


def notificar_nuevo_pedido(pedido):
    """
    Crear notificación cuando se recibe un nuevo pedido.
    Notifica al vendedor que tiene un nuevo pedido pendiente.
    """
    try:
        # Obtener los detalles del pedido para identificar a los vendedores
        from .models import detalle_pedido_usuario, detalle_pedido_empresa
        
        vendedores_notificados = set()
        
        # Buscar en detalles de pedidos de usuario
        if hasattr(pedido, 'detalles'):
            detalles = pedido.detalles.all()
            
            for detalle in detalles:
                vendedor = None
                
                # Verificar si es producto de usuario
                if hasattr(detalle, 'idproducto_fk_usuario') and detalle.idproducto_fk_usuario:
                    vendedor = detalle.idproducto_fk_usuario.id_usuario_fk
                    if vendedor.id_usuario not in vendedores_notificados:
                        titulo = f"Nuevo Pedido #{pedido.numero_pedido}"
                        mensaje = f"¡Tienes un nuevo pedido! Pedido #{pedido.numero_pedido} por ${pedido.total_pedido}. Revisa los detalles y confirma la venta."
                        
                        crear_notificacion_usuario(
                            usuario=vendedor,
                            tipo_notificacion='pedido_confirmado',
                            titulo=titulo,
                            mensaje=mensaje,
                            pedido=pedido
                        )
                        vendedores_notificados.add(vendedor.id_usuario)
                
                # Verificar si es producto de empresa
                elif hasattr(detalle, 'id_fk_producto_sucursal_empresa') and detalle.id_fk_producto_sucursal_empresa:
                    vendedor = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.id_empresa_fk
                    if vendedor.id_empresa not in vendedores_notificados:
                        titulo = f"Nuevo Pedido #{pedido.numero_pedido}"
                        mensaje = f"¡Tienen un nuevo pedido! Pedido #{pedido.numero_pedido} por ${pedido.total_pedido}. Revisen los detalles y confirmen la venta."
                        
                        crear_notificacion_empresa(
                            empresa=vendedor,
                            tipo_notificacion='nuevo_pedido',
                            titulo=titulo,
                            mensaje=mensaje,
                            pedido=pedido
                        )
                        vendedores_notificados.add(vendedor.id_empresa)
                        
    except Exception as e:
        logger.error(f"Error al notificar nuevo pedido {pedido.numero_pedido}: {str(e)}")


def notificar_servicio_cotizado(solicitud_servicio, precio_cotizado):
    """
    Crear notificación cuando un servicio es cotizado.
    """
    try:
        if hasattr(solicitud_servicio, 'id_usuario_fk'):
            # Solicitud de usuario
            titulo = f"Servicio Cotizado"
            mensaje = f"Tu solicitud de servicio ha sido cotizada por ${precio_cotizado}. Revisa los detalles y acepta si estás de acuerdo."
            
            crear_notificacion_usuario(
                usuario=solicitud_servicio.id_usuario_fk,
                tipo_notificacion='servicio_cotizado',
                titulo=titulo,
                mensaje=mensaje,
                solicitud_servicio=solicitud_servicio
            )
            
        elif hasattr(solicitud_servicio, 'id_empresa_fk'):
            # Solicitud de empresa
            titulo = f"Servicio Cotizado"
            mensaje = f"Su solicitud de servicio ha sido cotizada por ${precio_cotizado}. Revisen los detalles y acepten si están de acuerdo."
            
            crear_notificacion_empresa(
                empresa=solicitud_servicio.id_empresa_fk,
                tipo_notificacion='servicio_cotizado',
                titulo=titulo,
                mensaje=mensaje,
                solicitud_servicio=solicitud_servicio
            )
            
    except Exception as e:
        logger.error(f"Error al notificar servicio cotizado: {str(e)}")


def marcar_notificacion_leida(notificacion_id, es_empresa=False):
    """
    Marcar una notificación como leída.
    
    Args:
        notificacion_id: ID de la notificación
        es_empresa: True si es notificación de empresa, False si es de usuario
    """
    try:
        if es_empresa:
            from .models import notificacion_empresa
            notificacion = notificacion_empresa.objects.get(id_notificacion_empresa=notificacion_id)
        else:
            from .models import notificacion_usuario
            notificacion = notificacion_usuario.objects.get(id_notificacion_usuario=notificacion_id)
        
        notificacion.estado = 'leida'
        notificacion.fecha_leida = timezone.now()
        notificacion.save()
        
        logger.info(f"Notificación {notificacion_id} marcada como leída")
        return True
        
    except Exception as e:
        logger.error(f"Error al marcar notificación {notificacion_id} como leída: {str(e)}")
        return False
        
        # Obtener los pedidos reales de la base de datos para mostrar información actualizada
        pedidos_creados = []
        
        for pedido_info in pedidos_data:
            if pedido_info['tipo'] == 'usuario':
                try:
                    pedido_obj = pedido_usuario.objects.get(id_pedido_usuario=pedido_info['id'])
                    detalles = detalle_pedido_usuario.objects.filter(id_pedido_fk=pedido_obj)
                    
                    detalles_list = []
                    for detalle in detalles:
                        if detalle.id_fk_producto_sucursal_empresa:
                            nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        elif detalle.idproducto_fk_usuario:
                            nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        else:
                            nombre_producto = "Producto no disponible"
                        
                        detalles_list.append({
                            'nombre_producto': nombre_producto,
                            'cantidad': detalle.cantidad_detalle_pedido,
                            'precio_unitario': float(detalle.precio_unitario_pedido),
                            'subtotal': float(detalle.subtotal_detalle_pedido)
                        })
                    
                    pedidos_creados.append({
                        'numero_pedido': pedido_obj.numero_pedido,
                        'fecha_pedido': pedido_obj.fecha_pedido.isoformat() if pedido_obj.fecha_pedido else None,
                        'estado_pedido': pedido_obj.estado_pedido,
                        'total_pedido': float(pedido_obj.total_pedido),
                        'vendedor_nombre': pedido_info['vendedor'],
                        'detalles': detalles_list
                    })
                except pedido_usuario.DoesNotExist:
                    continue
            elif pedido_info['tipo'] == 'empresa':
                try:
                    pedido_obj = pedido_empresa.objects.get(id_pedido_empresa=pedido_info['id'])
                    detalles = detalle_pedido_empresa.objects.filter(id_pedido_fk=pedido_obj)
                    
                    detalles_list = []
                    for detalle in detalles:
                        if detalle.id_fk_producto_sucursal_empresa:
                            nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        elif detalle.idproducto_fk_usuario:
                            nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        else:
                            nombre_producto = "Producto no disponible"
                        
                        detalles_list.append({
                            'nombre_producto': nombre_producto,
                            'cantidad': detalle.cantidad_detalle_pedido,
                            'precio_unitario': float(detalle.precio_unitario_pedido),
                            'subtotal': float(detalle.subtotal_detalle_pedido)
                        })
                    
                    pedidos_creados.append({
                        'numero_pedido': pedido_obj.numero_pedido,
                        'fecha_pedido': pedido_obj.fecha_pedido.isoformat() if pedido_obj.fecha_pedido else None,
                        'estado_pedido': pedido_obj.estado_pedido,
                        'total_pedido': float(pedido_obj.total_pedido),
                        'vendedor_nombre': pedido_info['vendedor'],
                        'detalles': detalles_list
                    })
                except pedido_empresa.DoesNotExist:
                    continue
        
        # Limpiar datos de la sesión después de mostrarlos
        if 'pedidos_confirmacion' in request.session:
            del request.session['pedidos_confirmacion']
        if 'datos_cliente_confirmacion' in request.session:
            del request.session['datos_cliente_confirmacion']
        if 'total_general_confirmacion' in request.session:
            del request.session['total_general_confirmacion']
        
        context = {
            'account_type': account_type,
            'pedidos_creados': pedidos_creados,
            'datos_cliente': datos_cliente,
            'total_general': total_general
        }
        
        return render(request, 'ecommerce_app/confirmacion_pedido.html', context)
        
    except Exception as e:
        logger.error(f"Error en función confirmacion_pedido: {str(e)}")
        return redirect('/ecommerce/carrito')


@require_login
def ventas_confirmadas(request):
    """
    Vista para mostrar las ventas confirmadas realizadas por el usuario o empresa.
    Muestra los pedidos donde vendieron productos con estado 'confirmado'.
    """
    try:
        current_user = get_current_user(request)
        logger.info(f"ventas_confirmadas - current_user: {current_user}")
        
        if not current_user:
            logger.error("ventas_confirmadas - No current_user found")
            return redirect('/ecommerce/iniciar_sesion/')
        
        # Obtener account_type de la sesión
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"ventas_confirmadas - account_type: {account_type}")
        ventas_confirmadas = []
        
        if account_type == 'usuario':
            # current_user ya es el objeto usuario
            
            # Pedidos de usuarios que compraron productos de este usuario (solo confirmados)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='confirmado'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Pedidos de empresas que compraron productos de este usuario (solo confirmados)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='confirmado'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_usuario,
                        'email_comprador': comprador.correo_usuario,
                        'telefono_comprador': comprador.telefono_usuario,
                        'tipo_comprador': 'usuario',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_usuario.objects.filter(
                    id_producto_fk=detalle.idproducto_fk_usuario
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None
                })
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_empresa,
                        'email_comprador': comprador.correo_empresa,
                        'telefono_comprador': 'No disponible',
                        'tipo_comprador': 'empresa',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_usuario.objects.filter(
                    id_producto_fk=detalle.idproducto_fk_usuario
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None
                })
            
            # Convertir diccionario a lista
            ventas_confirmadas = list(pedidos_dict.values())
                
        elif account_type == 'empresa':
            # current_user ya es el objeto empresa
            current_empresa = current_user
            
            # Pedidos de usuarios que compraron productos de esta empresa (solo confirmados)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='confirmado'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Pedidos de empresas que compraron productos de esta empresa (solo confirmados)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='confirmado'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_usuario,
                        'email_comprador': comprador.correo_usuario,
                        'telefono_comprador': comprador.telefono_usuario,
                        'tipo_comprador': 'usuario',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_empresa.objects.filter(
                    id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None
                })
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_empresa,
                        'email_comprador': comprador.correo_empresa,
                        'telefono_comprador': 'No disponible',
                        'tipo_comprador': 'empresa',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_empresa.objects.filter(
                    id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None
                })
            
            # Convertir diccionario a lista
            ventas_confirmadas = list(pedidos_dict.values())
        
        # Ordenar por fecha más reciente
        ventas_confirmadas.sort(key=lambda x: x['fecha_pedido'], reverse=True)
        
        # Crear user_info para compatibilidad con el template
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
        
        context = {
            'current_user': current_user,
            'user_info': user_info,
            'account_type': account_type,
            'ventas_confirmadas': ventas_confirmadas,
            'total_ventas': len(ventas_confirmadas)
        }
        
        return render(request, 'ecommerce_app/ventas_confirmadas.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en función ventas_confirmadas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return redirect('/ecommerce/index/')


@require_login
def ventas_rechazadas(request):
    """
    Vista para mostrar las ventas rechazadas realizadas por el usuario o empresa.
    Muestra los pedidos donde vendieron productos con estado 'rechazado'.
    """
    try:
        current_user = get_current_user(request)
        logger.info(f"ventas_rechazadas - current_user: {current_user}")
        
        if not current_user:
            logger.error("ventas_rechazadas - No current_user found")
            return redirect('/ecommerce/iniciar_sesion/')
        
        # Obtener account_type de la sesión
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"ventas_rechazadas - account_type: {account_type}")
        ventas_rechazadas = []
        
        if account_type == 'usuario':
            # current_user ya es el objeto usuario
            
            # Pedidos de usuarios que compraron productos de este usuario (solo rechazados)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='cancelado'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Pedidos de empresas que compraron productos de este usuario (solo rechazados)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='cancelado'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_usuario,
                        'email_comprador': comprador.correo_usuario,
                        'telefono_comprador': comprador.telefono_usuario,
                        'tipo_comprador': 'usuario',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'fecha_rechazo': pedido.fecha_rechazo if hasattr(pedido, 'fecha_rechazo') else pedido.fecha_pedido,
                        'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None),
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_usuario.objects.filter(
                    id_producto_fk=detalle.idproducto_fk_usuario
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None
                })
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_empresa,
                        'email_comprador': comprador.correo_empresa,
                        'telefono_comprador': 'No disponible',
                        'tipo_comprador': 'empresa',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'fecha_rechazo': pedido.fecha_rechazo if hasattr(pedido, 'fecha_rechazo') else pedido.fecha_pedido,
                        'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None),
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_usuario.objects.filter(
                    id_producto_fk=detalle.idproducto_fk_usuario
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None
                })
            
            # Convertir diccionario a lista
            ventas_rechazadas = list(pedidos_dict.values())
                
        elif account_type == 'empresa':
            # current_user ya es el objeto empresa
            current_empresa = current_user
            
            # Pedidos de usuarios que compraron productos de esta empresa (solo rechazados)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='cancelado'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Pedidos de empresas que compraron productos de esta empresa (solo rechazados)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='cancelado'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_usuario,
                        'email_comprador': comprador.correo_usuario,
                        'telefono_comprador': comprador.telefono_usuario,
                        'tipo_comprador': 'usuario',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'fecha_rechazo': pedido.fecha_rechazo if hasattr(pedido, 'fecha_rechazo') else pedido.fecha_pedido,
                        'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None),
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_empresa.objects.filter(
                    id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None
                })
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_empresa,
                        'email_comprador': comprador.correo_empresa,
                        'telefono_comprador': 'No disponible',
                        'tipo_comprador': 'empresa',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'fecha_rechazo': pedido.fecha_rechazo if hasattr(pedido, 'fecha_rechazo') else pedido.fecha_pedido,
                        'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None),
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_empresa.objects.filter(
                    id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None
                })
            
            # Convertir diccionario a lista
            ventas_rechazadas = list(pedidos_dict.values())
        
        # Ordenar por fecha más reciente
        ventas_rechazadas.sort(key=lambda x: x['fecha_pedido'], reverse=True)
        
        # Crear user_info para compatibilidad con el template
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
        
        context = {
            'current_user': current_user,
            'user_info': user_info,
            'account_type': account_type,
            'ventas_rechazadas': ventas_rechazadas,
            'total_ventas': len(ventas_rechazadas)
        }
        
        return render(request, 'ecommerce_app/ventas_rechazadas.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en función ventas_rechazadas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return redirect('/ecommerce/index/')
            
        # Resto de la lógica de confirmación_pedido aquí...
        # Por ahora retornamos una respuesta básica
        return render(request, 'ecommerce_app/confirmacion_pedido.html', {
            'pedidos_data': pedidos_data,
            'datos_cliente': datos_cliente,
            'total_general': total_general
        })
        
    except Exception as e:
        logger.error(f"Error en confirmacion_pedido: {str(e)}")
        return redirect('/ecommerce/carrito')

@require_login
@require_login
def ventas_pendientes(request):
    """
    Vista para mostrar las ventas realizadas por el usuario o empresa.
    Muestra los pedidos donde vendieron productos con datos del comprador y comprobante.
    """
    try:
        current_user = get_current_user(request)
        logger.info(f"mis_ventas - current_user: {current_user}")
        
        if not current_user:
            logger.error("mis_ventas - No current_user found")
            return redirect('/ecommerce/iniciar_sesion/')
        
        # Obtener account_type de la sesión
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"mis_ventas - account_type: {account_type}")
        ventas_realizadas = []
        
        if account_type == 'usuario':
            # current_user ya es el objeto usuario
            
            # Pedidos de usuarios que compraron productos de este usuario (solo pendientes)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Pedidos de empresas que compraron productos de este usuario (solo pendientes)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'idproducto_fk_usuario')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_usuario,
                        'email_comprador': comprador.correo_usuario,
                        'telefono_comprador': comprador.telefono_usuario,
                        'tipo_comprador': 'usuario',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_usuario.objects.filter(
                    id_producto_fk=detalle.idproducto_fk_usuario
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None
                })
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_empresa,
                        'email_comprador': comprador.correo_empresa,
                        'telefono_comprador': 'No disponible',
                        'tipo_comprador': 'empresa',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_usuario.objects.filter(
                    id_producto_fk=detalle.idproducto_fk_usuario
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.idproducto_fk_usuario.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_usuario.url if imagen else None
                })
            
            # Convertir diccionario a lista
            ventas_realizadas = list(pedidos_dict.values())
                
        elif account_type == 'empresa':
            # current_user ya es el objeto empresa
            current_empresa = current_user
            
            # Pedidos de usuarios que compraron productos de esta empresa (solo pendientes)
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Pedidos de empresas que compraron productos de esta empresa (solo pendientes)
            detalles_empresa = detalle_pedido_empresa.objects.filter(
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_empresa,
                id_pedido_fk__estado_pedido='pendiente'
            ).select_related('id_pedido_fk', 'id_fk_producto_sucursal_empresa__id_producto_fk')
            
            # Agrupar detalles por pedido
            pedidos_dict = {}
            
            # Procesar pedidos de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_usuario_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_usuario,
                        'email_comprador': comprador.correo_usuario,
                        'telefono_comprador': comprador.telefono_usuario,
                        'tipo_comprador': 'usuario',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_empresa.objects.filter(
                    id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None
                })
            
            # Procesar pedidos de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                comprador = pedido.id_carrito_fk.id_empresa_fk
                
                if pedido.numero_pedido not in pedidos_dict:
                    pedidos_dict[pedido.numero_pedido] = {
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'nombre_comprador': comprador.nombre_empresa,
                        'email_comprador': comprador.correo_empresa,
                        'telefono_comprador': 'No disponible',
                        'tipo_comprador': 'empresa',
                        'direccion_envio': pedido.direccion_envio,
                        'metodo_pago': pedido.metodo_pago,
                        'comprobante_pago': pedido.comprobante_pago,
                        'notas_pedido': pedido.notas_pedido,
                        'total_pedido': pedido.total_pedido,
                        'detalles': []
                    }
                
                # Obtener imagen del producto
                imagen = imagen_producto_empresa.objects.filter(
                    id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                ).first()
                
                pedidos_dict[pedido.numero_pedido]['detalles'].append({
                    'nombre_producto': detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': detalle.precio_unitario_pedido,
                    'subtotal': detalle.subtotal_detalle_pedido,
                    'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None
                })
            
            # Convertir diccionario a lista
            ventas_realizadas = list(pedidos_dict.values())
        
        # Ordenar por fecha más reciente
        ventas_realizadas.sort(key=lambda x: x['fecha_pedido'], reverse=True)
        
        # Crear user_info para compatibilidad con el template y modal de sesiones
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
        
        context = {
            'current_user': current_user,
            'user_info': user_info,
            'account_type': account_type,
            'ventas_realizadas': ventas_realizadas,
            'total_ventas': len(ventas_realizadas)
        }
        
        return render(request, 'ecommerce_app/ventas_pendientes.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en función mis_ventas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return redirect('/ecommerce/index/')


@require_login
def mis_pedidos(request):
    """Vista para mostrar el historial de pedidos completados del usuario"""
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        pedidos_historial = []
        
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
            
            # Obtener pedidos de empresa (como comprador)
            pedidos_empresa = pedido_empresa.objects.filter(
                id_carrito_fk__id_empresa_fk=current_user
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_empresa:
                # Obtener detalles del pedido
                detalles = detalle_pedido_empresa.objects.filter(id_pedido_fk=pedido)
                
                detalles_list = []
                for detalle in detalles:
                    if detalle.id_fk_producto_sucursal_empresa:
                        nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                        empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        sucursal = detalle.idproducto_fk_usuario.sucursal_usuario.nombre_sucursal if hasattr(detalle.idproducto_fk_usuario, 'sucursal_usuario') and detalle.idproducto_fk_usuario.sucursal_usuario else "Sin sucursal"
                        empresa = detalle.idproducto_fk_usuario.sucursal_usuario.id_empresa_fk.nombre_empresa if hasattr(detalle.idproducto_fk_usuario, 'sucursal_usuario') and detalle.idproducto_fk_usuario.sucursal_usuario and hasattr(detalle.idproducto_fk_usuario.sucursal_usuario, 'id_empresa_fk') and detalle.idproducto_fk_usuario.sucursal_usuario.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                    else:
                        nombre_producto = "Producto no disponible"
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen_url = None
                    
                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url,
                        'sucursal': sucursal,
                        'empresa': empresa
                    })
                
                pedidos_historial.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha_pedido': pedido.fecha_pedido,
                    'estado_pedido': pedido.estado_pedido,
                    'total_pedido': float(pedido.total_pedido),
                    'metodo_pago': pedido.metodo_pago,
                    'direccion_entrega': pedido.direccion_envio,
                    'direccion_envio': pedido.direccion_envio,
                    'notas_pedido': pedido.notas_pedido,
                    'detalles': detalles_list,
                    'tipo_pedido': 'empresa',
                    'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None,
                    'fecha_rechazo': pedido.fecha_pedido,
                    'motivo_rechazo': pedido.comentario_rechazo if hasattr(pedido, 'comentario_rechazo') else None
                })
        
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
            
            # Obtener pedidos de usuario (como comprador)
            pedidos_usuario = pedido_usuario.objects.filter(
                id_carrito_fk__id_usuario_fk=current_user
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_usuario:
                # Obtener detalles del pedido
                detalles = detalle_pedido_usuario.objects.filter(id_pedido_fk=pedido)
                
                detalles_list = []
                for detalle in detalles:
                    if detalle.id_fk_producto_sucursal_empresa:
                        nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                        empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        sucursal = detalle.idproducto_fk_usuario.sucursal_usuario.nombre_sucursal if hasattr(detalle.idproducto_fk_usuario, 'sucursal_usuario') and detalle.idproducto_fk_usuario.sucursal_usuario else "Sin sucursal"
                        empresa = detalle.idproducto_fk_usuario.sucursal_usuario.id_empresa_fk.nombre_empresa if hasattr(detalle.idproducto_fk_usuario, 'sucursal_usuario') and detalle.idproducto_fk_usuario.sucursal_usuario and hasattr(detalle.idproducto_fk_usuario.sucursal_usuario, 'id_empresa_fk') and detalle.idproducto_fk_usuario.sucursal_usuario.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                    else:
                        nombre_producto = "Producto no disponible"
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen_url = None
                    
                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url,
                        'sucursal': sucursal,
                        'empresa': empresa
                    })
                
                pedidos_historial.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha_pedido': pedido.fecha_pedido,
                    'estado_pedido': pedido.estado_pedido,
                    'total_pedido': float(pedido.total_pedido),
                    'metodo_pago': pedido.metodo_pago,
                    'direccion_entrega': pedido.direccion_envio,
                    'direccion_envio': pedido.direccion_envio,
                    'notas_pedido': pedido.notas_pedido,
                    'detalles': detalles_list,
                    'tipo_pedido': 'usuario',
                    'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None,
                    'fecha_rechazo': pedido.fecha_pedido,
                    'motivo_rechazo': pedido.comentario_rechazo if hasattr(pedido, 'comentario_rechazo') else None
                })
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'pedidos_confirmados': pedidos_historial,
            'total_pedidos': len(pedidos_historial)
        }
        
        return render(request, 'ecommerce_app/mis_pedidos.html', context)
        
    except Exception as e:
        logger.error(f"Error en función mis_pedidos: {str(e)}")
        return redirect('/ecommerce/carrito')


@require_login
def mis_solicitudes(request):
    """Mostrar todas las solicitudes de servicios relacionadas con el usuario actual.
    Para account_type 'usuario' muestra solicitudes hechas por el usuario (solicitud_servicio_usuario).
    Para account_type 'empresa' muestra solicitudes dirigidas a la empresa (solicitud_servicio_empresa).
    """
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    try:
        account_type = request.session.get('account_type', 'usuario')
        solicitudes_list = []

        if account_type == 'empresa':
            # solicitudes dirigidas a la empresa
            solicitudes_qs = solicitud_servicio_empresa.objects.filter(id_empresa_fk=current_user).order_by('-fecha_solicitud')
            for s in solicitudes_qs:
                # resolver nombre del servicio y obtener imágenes si aplica
                nombre_servicio = resolve_service_name_strict(s) or ''
                imagenes = []
                if s.id_servicio_usuario_fk:
                    imagenes = collect_service_images(s.id_servicio_usuario_fk)
                elif s.id_servicio_sucursal_fk:
                    # intentar obtener imágenes desde el servicio asociado en la sucursal
                    svc = getattr(s.id_servicio_sucursal_fk, 'id_servicio_fk', None)
                    imagenes = collect_service_images(svc)

                solicitudes_list.append({
                    'id': s.id_solicitud_servicio_empresa,
                    'fecha_solicitud': s.fecha_solicitud,
                    'fecha_requerida': s.fecha_requerida,
                    'direccion': s.direccion,
                    'descripcion': s.descripcion_detallada,
                    'estado': s.estado,
                    'presupuesto': s.presupuesto_cotizacion,
                    'descripcion_cotizacion': s.descripcion_cotizacion,
                    'archivo_cotizacion': s.archivo_cotizacion.url if s.archivo_cotizacion else None,
                    'motivo_rechazo': s.motivo_rechazo,
                    'fecha_rechazo': s.fecha_rechazo,
                    'nombre_servicio': nombre_servicio,
                    'imagenes': imagenes,
                    'tipo': 'empresa'
                })

        else:
            # solicitudes creadas por el usuario
            solicitudes_qs = solicitud_servicio_usuario.objects.filter(id_usuario_fk=current_user).order_by('-fecha_solicitud')
            for s in solicitudes_qs:
                nombre_servicio = resolve_service_name_strict(s) or ''
                imagenes = []
                if s.id_servicio_usuario_fk:
                    imagenes = collect_service_images(s.id_servicio_usuario_fk)
                elif s.id_servicio_sucursal_fk:
                    svc = getattr(s.id_servicio_sucursal_fk, 'id_servicio_fk', None)
                    imagenes = collect_service_images(svc)

                solicitudes_list.append({
                    'id': s.id_solicitud_servicio_usuario,
                    'fecha_solicitud': s.fecha_solicitud,
                    'fecha_requerida': s.fecha_requerida,
                    'direccion': s.direccion,
                    'descripcion': s.descripcion_detallada,
                    'estado': s.estado,
                    'presupuesto': s.presupuesto_cotizacion,
                    'descripcion_cotizacion': s.descripcion_cotizacion,
                    'archivo_cotizacion': s.archivo_cotizacion.url if s.archivo_cotizacion else None,
                    'motivo_rechazo': s.motivo_rechazo,
                    'fecha_rechazo': s.fecha_rechazo,
                    'nombre_servicio': nombre_servicio,
                    'imagenes': imagenes,
                    'tipo': 'usuario'
                })

        # preparar user_info compatible con templates
        user_info = get_user_info_with_avatar(current_user, account_type)

        context = {
            'user_info': user_info,
            'account_type': account_type,
            'solicitudes': solicitudes_list,
            'total_solicitudes': len(solicitudes_list)
        }

        return render(request, 'ecommerce_app/mis_solicitudes.html', context)

    except Exception as e:
        logger.error(f"Error en mis_solicitudes: {str(e)}")
        return redirect('/ecommerce/index/')


@require_login
def liberar_carritos_expirados():
    """
    Función para liberar el stock reservado de carritos expirados.
    Esta función debe ejecutarse periódicamente mediante un cronjob o tarea programada.
    """
    from datetime import timedelta
    from django.utils import timezone
    from django.db import transaction
    
    # Definir tiempo de expiración (por ejemplo, 24 horas)
    tiempo_expiracion = timezone.now() - timedelta(hours=24)
    
    # Procesar carritos de empresas expirados
    carritos_empresa_expirados = carrito_compra_producto_empresa.objects.filter(
        estatuscarrito_prod_empresa='activo',
        fecha_carrito_prod_empresa__lt=tiempo_expiracion
    )
    
    for carrito in carritos_empresa_expirados:
        with transaction.atomic():
            # Obtener todos los detalles del carrito
            detalles = detalle_compra_producto_empresa.objects.filter(id_fk_carritocompra_empresa=carrito)
            
            # Liberar stock reservado para cada producto
            for detalle in detalles:
                if detalle.id_fk_producto_sucursal_empresa:
                    producto = detalle.id_fk_producto_sucursal_empresa
                    producto.stock_reservado_sucursal = max(0, producto.stock_reservado_sucursal - detalle.cantidad_deta_carrito_prod_empresa)
                    producto.save()
                elif detalle.idproducto_fk_usuario:
                    producto = detalle.idproducto_fk_usuario
                    producto.stock_reservado_usuario = max(0, producto.stock_reservado_usuario - detalle.cantidad_deta_carrito_prod_usuario)
                    producto.save()
            
            # Marcar carrito como expirado
            carrito.estatuscarrito_prod_empresa = 'expirado'
            carrito.save()
    
    # Procesar carritos de usuarios expirados
    carritos_usuario_expirados = carrito_compra_producto_usuario.objects.filter(
        estatuscarrito_prod_usuario='activo',
        fecha_carrito_prod_usuario__lt=tiempo_expiracion
    )
    
    for carrito in carritos_usuario_expirados:
        with transaction.atomic():
            # Obtener todos los detalles del carrito
            detalles = detalle_compra_producto_usuario.objects.filter(id_fk_carritocompra_usuario=carrito)
            
            # Liberar stock reservado para cada producto
            for detalle in detalles:
                if detalle.id_fk_producto_sucursal_empresa:
                    producto = detalle.id_fk_producto_sucursal_empresa
                    producto.stock_reservado_sucursal = max(0, producto.stock_reservado_sucursal - detalle.cantidad_deta_carrito_prod_usuario)
                    producto.save()
                elif detalle.idproducto_fk_usuario:
                    producto = detalle.idproducto_fk_usuario
                    producto.stock_reservado_usuario = max(0, producto.stock_reservado_usuario - detalle.cantidad_deta_carrito_prod_usuario)
                    producto.save()
            
            # Marcar carrito como expirado
            carrito.estatuscarrito_prod_usuario = 'expirado'
            carrito.save()


def confirmar_venta(request):
    """
    Vista para confirmar una venta cambiando el estado del pedido de 'pendiente' a 'confirmado'.
    Solo acepta peticiones POST con AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    try:
        import json
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Leer datos JSON del cuerpo de la petición
        try:
            data = json.loads(request.body)
            numero_pedido = data.get('numero_pedido')
        except json.JSONDecodeError:
            # Fallback a request.POST si no es JSON
            numero_pedido = request.POST.get('numero_pedido')
        
        if not numero_pedido:
            return JsonResponse({'success': False, 'message': 'Número de pedido requerido'})
        
        # Buscar el pedido según el tipo de cuenta
        pedido_encontrado = None
        
        if account_type == 'usuario':
            # Buscar en pedidos de usuarios donde el vendedor es el usuario actual
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_pedido_fk__numero_pedido=numero_pedido,
                idproducto_fk_usuario__id_usuario_fk=current_user
            ).select_related('id_pedido_fk').first()
            
            if detalles_usuario:
                pedido_encontrado = detalles_usuario.id_pedido_fk
            else:
                # Buscar en pedidos de empresas donde el vendedor es el usuario actual
                detalles_empresa = detalle_pedido_empresa.objects.filter(
                    id_pedido_fk__numero_pedido=numero_pedido,
                    idproducto_fk_usuario__id_usuario_fk=current_user
                ).select_related('id_pedido_fk').first()
                
                if detalles_empresa:
                    pedido_encontrado = detalles_empresa.id_pedido_fk
        
        elif account_type == 'empresa':
            # Buscar en pedidos de usuarios donde el vendedor es la empresa actual
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_pedido_fk__numero_pedido=numero_pedido,
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_user
            ).select_related('id_pedido_fk').first()
            
            if detalles_usuario:
                pedido_encontrado = detalles_usuario.id_pedido_fk
            else:
                # Buscar en pedidos de empresas donde el vendedor es la empresa actual
                detalles_empresa = detalle_pedido_empresa.objects.filter(
                    id_pedido_fk__numero_pedido=numero_pedido,
                    id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_user
                ).select_related('id_pedido_fk').first()
                
                if detalles_empresa:
                    pedido_encontrado = detalles_empresa.id_pedido_fk
        
        if not pedido_encontrado:
            return JsonResponse({'success': False, 'message': 'Pedido no encontrado o no tienes permisos para confirmarlo'})
        
        # Verificar que el pedido esté en estado 'pendiente'
        if pedido_encontrado.estado_pedido != 'pendiente':
            return JsonResponse({
                'success': False, 
                'message': f'El pedido ya está en estado: {pedido_encontrado.estado_pedido}'
            })
        
        # Realizar la actualización de stock y cambio de estado dentro de una transacción
        try:
            with transaction.atomic():
                # Re-obtener y bloquear el pedido para evitar condiciones de carrera
                if isinstance(pedido_encontrado, pedido_usuario) or hasattr(pedido_encontrado, 'id_pedido_usuario'):
                    pedido = pedido_usuario.objects.select_for_update().get(pk=pedido_encontrado.pk)
                    detalles = detalle_pedido_usuario.objects.select_for_update().filter(id_pedido_fk=pedido).select_related('id_fk_producto_sucursal_empresa', 'idproducto_fk_usuario')
                elif isinstance(pedido_encontrado, pedido_empresa) or hasattr(pedido_encontrado, 'id_pedido_empresa'):
                    pedido = pedido_empresa.objects.select_for_update().get(pk=pedido_encontrado.pk)
                    detalles = detalle_pedido_empresa.objects.select_for_update().filter(id_pedido_fk=pedido).select_related('id_fk_producto_sucursal_empresa', 'idproducto_fk_usuario')
                else:
                    logger.error(f"Tipo de pedido no reconocido: {type(pedido_encontrado)}")
                    return JsonResponse({'success': False, 'message': 'Tipo de pedido no reconocido', 'error': 'Tipo de pedido no reconocido'})

                # Verificar estado nuevamente dentro de la transacción
                if pedido.estado_pedido != 'pendiente':
                    return JsonResponse({'success': False, 'message': f'El pedido ya está en estado: {pedido.estado_pedido}', 'error': 'Estado inválido'})

                logger.info(f"Procesando pedido (bloqueado): {pedido.numero_pedido} - detalles: {detalles.count()}")

                # Actualizar stock por cada detalle (bloqueando también los productos)
                for detalle in detalles:
                    cantidad = detalle.cantidad_detalle_pedido
                    if detalle.id_fk_producto_sucursal_empresa:
                        prod_pk = detalle.id_fk_producto_sucursal_empresa.pk
                        producto = producto_sucursal.objects.select_for_update().get(pk=prod_pk)

                        logger.info(f"Actualizando stock de producto sucursal (bloqueado): {producto.id_producto_sucursal} - stock actual: {producto.stock_producto_sucursal} reservado: {producto.stock_reservado_sucursal} - restar: {cantidad}")

                        # Validar stock disponible
                        if producto.stock_producto_sucursal < cantidad:
                            raise Exception(f"Stock insuficiente para producto sucursal {producto.id_producto_sucursal}")

                        # Calcular valores en Python para evitar underflow en campos unsigned
                        new_stock = producto.stock_producto_sucursal - cantidad
                        new_reserved = max(0, producto.stock_reservado_sucursal - cantidad)

                        producto.stock_producto_sucursal = new_stock
                        producto.stock_reservado_sucursal = new_reserved
                        producto.save(update_fields=['stock_producto_sucursal', 'stock_reservado_sucursal'])
                        producto.refresh_from_db()

                    elif detalle.idproducto_fk_usuario:
                        prod_pk = detalle.idproducto_fk_usuario.pk
                        producto = producto_usuario.objects.select_for_update().get(pk=prod_pk)

                        logger.info(f"Actualizando stock de producto usuario (bloqueado): {producto.id_producto_usuario} - stock actual: {producto.stock_producto_usuario} reservado: {producto.stock_reservado_usuario} - restar: {cantidad}")

                        if producto.stock_producto_usuario < cantidad:
                            raise Exception(f"Stock insuficiente para producto usuario {producto.id_producto_usuario}")

                        new_stock = producto.stock_producto_usuario - cantidad
                        new_reserved = max(0, producto.stock_reservado_usuario - cantidad)

                        producto.stock_producto_usuario = new_stock
                        producto.stock_reservado_usuario = new_reserved
                        producto.save(update_fields=['stock_producto_usuario', 'stock_reservado_usuario'])
                        producto.refresh_from_db()

                # Si todo va bien, cambiar estado a confirmado y guardar
                pedido.estado_pedido = 'confirmado'
                pedido.save(update_fields=['estado_pedido'])

        except Exception as e:
            # El with transaction.atomic() hará rollback automáticamente
            logger.error(f"Error al actualizar stock en confirmar_venta: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error al confirmar la venta: {str(e)}', 'error': str(e)})

        # Crear notificación automática para el comprador
        notificar_pedido_confirmado(pedido)

        logger.info(f"Pedido {numero_pedido} confirmado por {account_type} {current_user}")

        return JsonResponse({
            'success': True,
            'message': 'Venta confirmada exitosamente',
            'nuevo_estado': 'confirmado'
        })
        
    except Exception as e:
        logger.error(f"Error en función confirmar_venta: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'})


@require_login
def rechazar_venta(request):
    """
    Vista para rechazar una venta cambiando el estado del pedido de 'pendiente' a 'cancelado'
    y guardando el comentario de rechazo. Solo acepta peticiones POST con AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    try:
        import json
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Leer datos JSON del cuerpo de la petición
        try:
            data = json.loads(request.body)
            numero_pedido = data.get('numero_pedido')
            comentario_rechazo = data.get('comentario_rechazo', '').strip()
        except json.JSONDecodeError:
            # Fallback a request.POST si no es JSON
            numero_pedido = request.POST.get('numero_pedido')
            comentario_rechazo = request.POST.get('comentario_rechazo', '').strip()
        
        if not numero_pedido:
            return JsonResponse({'success': False, 'message': 'Número de pedido requerido'})
        
        if not comentario_rechazo:
            return JsonResponse({'success': False, 'message': 'El comentario de rechazo es obligatorio'})
        
        # Buscar el pedido según el tipo de cuenta
        pedido_encontrado = None
        
        if account_type == 'usuario':
            # Buscar en pedidos de usuarios donde el vendedor es el usuario actual
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_pedido_fk__numero_pedido=numero_pedido,
                idproducto_fk_usuario__id_usuario_fk=current_user
            ).select_related('id_pedido_fk').first()
            
            if detalles_usuario:
                pedido_encontrado = detalles_usuario.id_pedido_fk
            else:
                # Buscar en pedidos de empresas donde el vendedor es el usuario actual
                detalles_empresa = detalle_pedido_empresa.objects.filter(
                    id_pedido_fk__numero_pedido=numero_pedido,
                    idproducto_fk_usuario__id_usuario_fk=current_user
                ).select_related('id_pedido_fk').first()
                
                if detalles_empresa:
                    pedido_encontrado = detalles_empresa.id_pedido_fk
        
        elif account_type == 'empresa':
            # Buscar en pedidos de usuarios donde el vendedor es la empresa actual
            detalles_usuario = detalle_pedido_usuario.objects.filter(
                id_pedido_fk__numero_pedido=numero_pedido,
                id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_user
            ).select_related('id_pedido_fk').first()
            
            if detalles_usuario:
                pedido_encontrado = detalles_usuario.id_pedido_fk
            else:
                # Buscar en pedidos de empresas donde el vendedor es la empresa actual
                detalles_empresa = detalle_pedido_empresa.objects.filter(
                    id_pedido_fk__numero_pedido=numero_pedido,
                    id_fk_producto_sucursal_empresa__id_producto_fk__id_empresa_fk=current_user
                ).select_related('id_pedido_fk').first()
                
                if detalles_empresa:
                    pedido_encontrado = detalles_empresa.id_pedido_fk
        
        if not pedido_encontrado:
            return JsonResponse({'success': False, 'message': 'Pedido no encontrado o no tienes permisos para rechazarlo'})
        
        # Verificar que el pedido esté en estado 'pendiente'
        if pedido_encontrado.estado_pedido != 'pendiente':
            return JsonResponse({
                'success': False, 
                'message': f'El pedido ya está en estado: {pedido_encontrado.estado_pedido}'
            })
        
        # Cambiar el estado a 'cancelado' y guardar el comentario de rechazo
        pedido_encontrado.estado_pedido = 'cancelado'
        pedido_encontrado.comentario_rechazo = comentario_rechazo
        pedido_encontrado.save()
        
        # Crear notificación automática para el comprador
        notificar_pedido_cancelado(pedido_encontrado, comentario_rechazo)
        
        logger.info(f"Pedido {numero_pedido} rechazado por {account_type} {current_user} con comentario: {comentario_rechazo}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Venta rechazada exitosamente',
            'nuevo_estado': 'cancelado'
        })
        
    except Exception as e:
        logger.error(f"Error en función rechazar_venta: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'})


def favoritos(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    current_user = None
    
    if is_user_authenticated(request):
        current_user = get_current_user(request)
    
    account_type = request.session.get('account_type', 'usuario')
    
    if current_user:
        user_info = get_user_info_with_avatar(current_user, account_type)
        # Para favoritos, usar siempre el avatar por defecto del chatbot (chatbot general del ecommerce)
        user_info['avatar_chatbot'] = 'avatars/Cartoon Style Robot.jpg'
    else:
        user_info = {
            'is_authenticated': False
        }
    
    # Obtener los favoritos del usuario o de la empresa según el tipo de cuenta
    favoritos = []
    if current_user:
        if account_type == 'usuario':
            favoritos_query = favorito_usuario.objects.filter(id_usuario_fk=current_user)

            for favorito in favoritos_query:
                item_data = None

                # Producto de usuario
                if favorito.id_producto_usuario_fk:
                    producto = favorito.id_producto_usuario_fk
                    imagenes = imagen_producto_usuario.objects.filter(id_producto_fk=producto)
                    item_data = {
                        'id': producto.id_producto_usuario,
                        'nombre': producto.nombre_producto_usuario,
                        'descripcion': producto.descripcion_producto_usuario,
                        'precio': producto.precio_producto_usuario,
                        'tipo': 'producto',
                        'tipo_propietario': 'usuario',
                        'propietario': producto.id_usuario_fk.nombre_usuario,
                        'imagen': imagenes.first().ruta_imagen_producto_usuario.url if imagenes.exists() else None,
                        'categoria': producto.id_categoria_prod_fk.nombre_categoria_prod_usuario if producto.id_categoria_prod_fk else 'Sin categoría'
                    }

                # Servicio de usuario
                elif favorito.id_servicio_usuario_fk:
                    servicio = favorito.id_servicio_usuario_fk
                    imagenes = imagen_servicio_usuario.objects.filter(id_servicio_fk=servicio)
                    item_data = {
                        'id': servicio.id_servicio_usuario,
                        'nombre': servicio.nombre_servicio_usuario,
                        'descripcion': servicio.descripcion_servicio_usuario,
                        'precio': servicio.precio_servicio_usuario,
                        'tipo': 'servicio',
                        'tipo_propietario': 'usuario',
                        'propietario': servicio.id_usuario_fk.nombre_usuario,
                        'imagen': imagenes.first().ruta_imagen_servicio_usuario.url if imagenes.exists() else None,
                        'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_usuario if servicio.id_categoria_servicios_fk else 'Sin categoría'
                    }

                # Producto de sucursal
                elif favorito.id_producto_sucursal_fk:
                    producto_suc = favorito.id_producto_sucursal_fk
                    producto = producto_suc.id_producto_fk
                    imagenes = imagen_producto_empresa.objects.filter(id_producto_fk=producto)
                    item_data = {
                        'id': producto_suc.id_producto_sucursal,
                        'nombre': producto.nombre_producto_empresa,
                        'descripcion': producto.descripcion_producto_empresa,
                        'precio': producto_suc.precio_producto_sucursal,
                        'tipo': 'producto',
                        'tipo_propietario': 'empresa',
                        'propietario': producto_suc.id_sucursal_fk.id_empresa_fk.nombre_empresa,
                        'sucursal': producto_suc.id_sucursal_fk.nombre_sucursal,
                        'imagen': imagenes.first().ruta_imagen_producto_empresa.url if imagenes.exists() else None,
                        'categoria': producto.id_categoria_prod_fk.nombre_categoria_prod_empresa if producto.id_categoria_prod_fk else 'Sin categoría'
                    }

                # Servicio de sucursal
                elif favorito.id_servicio_sucursal_fk:
                    servicio_suc = favorito.id_servicio_sucursal_fk
                    servicio = servicio_suc.id_servicio_fk
                    imagenes = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio)
                    item_data = {
                        'id': servicio_suc.id_servicio_sucursal,
                        'nombre': servicio.nombre_servicio_empresa,
                        'descripcion': servicio.descripcion_servicio_empresa,
                        'precio': servicio_suc.precio_servicio_sucursal,
                        'tipo': 'servicio',
                        'tipo_propietario': 'empresa',
                        'propietario': servicio_suc.id_sucursal_fk.id_empresa_fk.nombre_empresa,
                        'sucursal': servicio_suc.id_sucursal_fk.nombre_sucursal,
                        'imagen': imagenes.first().ruta_imagen_servicio_empresa.url if imagenes.exists() else None,
                        'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_empresa if servicio.id_categoria_servicios_fk else 'Sin categoría'
                    }

                if item_data:
                    favoritos.append(item_data)

        elif account_type == 'empresa':
            favoritos_query = favorito_empresa_sucursal.objects.filter(id_empresa_fk=current_user)

            for favorito in favoritos_query:
                item_data = None

                # Producto de usuario
                if favorito.id_producto_usuario_fk:
                    producto = favorito.id_producto_usuario_fk
                    imagenes = imagen_producto_usuario.objects.filter(id_producto_fk=producto)
                    item_data = {
                        'id': producto.id_producto_usuario,
                        'nombre': producto.nombre_producto_usuario,
                        'descripcion': producto.descripcion_producto_usuario,
                        'precio': producto.precio_producto_usuario,
                        'tipo': 'producto',
                        'tipo_propietario': 'usuario',
                        'propietario': producto.id_usuario_fk.nombre_usuario,
                        'imagen': imagenes.first().ruta_imagen_producto_usuario.url if imagenes.exists() else None,
                        'categoria': producto.id_categoria_prod_fk.nombre_categoria_prod_usuario if producto.id_categoria_prod_fk else 'Sin categoría'
                    }

                # Servicio de usuario
                elif favorito.id_servicio_usuario_fk:
                    servicio = favorito.id_servicio_usuario_fk
                    imagenes = imagen_servicio_usuario.objects.filter(id_servicio_fk=servicio)
                    item_data = {
                        'id': servicio.id_servicio_usuario,
                        'nombre': servicio.nombre_servicio_usuario,
                        'descripcion': servicio.descripcion_servicio_usuario,
                        'precio': servicio.precio_servicio_usuario,
                        'tipo': 'servicio',
                        'tipo_propietario': 'usuario',
                        'propietario': servicio.id_usuario_fk.nombre_usuario,
                        'imagen': imagenes.first().ruta_imagen_servicio_usuario.url if imagenes.exists() else None,
                        'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_usuario if servicio.id_categoria_servicios_fk else 'Sin categoría'
                    }

                # Producto de sucursal
                elif favorito.id_producto_sucursal_fk:
                    producto_suc = favorito.id_producto_sucursal_fk
                    producto = producto_suc.id_producto_fk
                    imagenes = imagen_producto_empresa.objects.filter(id_producto_fk=producto)
                    item_data = {
                        'id': producto_suc.id_producto_sucursal,
                        'nombre': producto.nombre_producto_empresa,
                        'descripcion': producto.descripcion_producto_empresa,
                        'precio': producto_suc.precio_producto_sucursal,
                        'tipo': 'producto',
                        'tipo_propietario': 'empresa',
                        'propietario': producto_suc.id_sucursal_fk.id_empresa_fk.nombre_empresa,
                        'sucursal': producto_suc.id_sucursal_fk.nombre_sucursal,
                        'imagen': imagenes.first().ruta_imagen_producto_empresa.url if imagenes.exists() else None,
                        'categoria': producto.id_categoria_prod_fk.nombre_categoria_prod_empresa if producto.id_categoria_prod_fk else 'Sin categoría'
                    }

                # Servicio de sucursal
                elif favorito.id_servicio_sucursal_fk:
                    servicio_suc = favorito.id_servicio_sucursal_fk
                    servicio = servicio_suc.id_servicio_fk
                    imagenes = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio)
                    item_data = {
                        'id': servicio_suc.id_servicio_sucursal,
                        'nombre': servicio.nombre_servicio_empresa,
                        'descripcion': servicio.descripcion_servicio_empresa,
                        'precio': servicio_suc.precio_servicio_sucursal,
                        'tipo': 'servicio',
                        'tipo_propietario': 'empresa',
                        'propietario': servicio_suc.id_sucursal_fk.id_empresa_fk.nombre_empresa,
                        'sucursal': servicio_suc.id_sucursal_fk.nombre_sucursal,
                        'imagen': imagenes.first().ruta_imagen_servicio_empresa.url if imagenes.exists() else None,
                        'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_empresa if servicio.id_categoria_servicios_fk else 'Sin categoría'
                    }

                if item_data:
                    favoritos.append(item_data)
    
    context = {
        'user_info': user_info,
        'favoritos': favoritos
    }
    
    return render(request, 'ecommerce_app/favoritos.html', context)


@require_http_methods(["POST"])
def agregar_quitar_favorito(request):
    """Vista para agregar o quitar un item de favoritos"""
    try:
        # Verificar autenticación
        if not is_user_authenticated(request):
            return JsonResponse({
                'success': False,
                'message': 'Debes iniciar sesión para agregar favoritos'
            })
        
        current_user = get_current_user(request)
        account_type = request.session.get('account_type', 'usuario')
        
        # Permitir que tanto usuarios individuales como empresas agreguen favoritos
        if account_type not in ['usuario', 'empresa']:
            return JsonResponse({
                'success': False,
                'message': 'Solo usuarios o empresas pueden agregar favoritos'
            })
        
        data = json.loads(request.body)
        item_id = data.get('item_id')
        tipo_propietario = data.get('tipo_propietario')
        tipo_item = data.get('tipo_item', 'producto')  # 'producto' o 'servicio'
        
        if not item_id or not tipo_propietario:
            return JsonResponse({
                'success': False,
                'message': 'Faltan datos requeridos'
            })
        
        # Construir datos del favorito según el tipo de cuenta (usuario o empresa)
        if account_type == 'usuario':
            favorito_data = {'id_usuario_fk': current_user}

            if tipo_propietario == 'usuario':
                if tipo_item == 'producto':
                    try:
                        producto = producto_usuario.objects.get(id_producto_usuario=item_id)
                        favorito_data['id_producto_usuario_fk'] = producto
                    except producto_usuario.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Producto no encontrado'})
                else:  # servicio
                    try:
                        servicio = servicio_usuario.objects.get(id_servicio_usuario=item_id)
                        favorito_data['id_servicio_usuario_fk'] = servicio
                    except servicio_usuario.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})

            elif tipo_propietario == 'empresa':
                if tipo_item == 'producto':
                    try:
                        producto_suc = producto_sucursal.objects.get(id_producto_sucursal=item_id)
                        favorito_data['id_producto_sucursal_fk'] = producto_suc
                    except producto_sucursal.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Producto de sucursal no encontrado'})
                else:
                    try:
                        servicio_suc = servicio_sucursal.objects.get(id_servicio_sucursal=item_id)
                        favorito_data['id_servicio_sucursal_fk'] = servicio_suc
                    except servicio_sucursal.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Servicio de sucursal no encontrado'})

            favorito_existente = favorito_usuario.objects.filter(**favorito_data).first()
            if favorito_existente:
                favorito_existente.delete()
                return JsonResponse({'success': True, 'action': 'removed', 'message': 'Eliminado de favoritos'})
            else:
                favorito_usuario.objects.create(**favorito_data)
                return JsonResponse({'success': True, 'action': 'added', 'message': 'Agregado a favoritos'})

        else:  # account_type == 'empresa'
            favorito_data = {'id_empresa_fk': current_user}

            if tipo_propietario == 'usuario':
                if tipo_item == 'producto':
                    try:
                        producto = producto_usuario.objects.get(id_producto_usuario=item_id)
                        favorito_data['id_producto_usuario_fk'] = producto
                    except producto_usuario.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Producto no encontrado'})
                else:
                    try:
                        servicio = servicio_usuario.objects.get(id_servicio_usuario=item_id)
                        favorito_data['id_servicio_usuario_fk'] = servicio
                    except servicio_usuario.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Servicio no encontrado'})

            elif tipo_propietario == 'empresa':
                if tipo_item == 'producto':
                    try:
                        producto_suc = producto_sucursal.objects.get(id_producto_sucursal=item_id)
                        favorito_data['id_producto_sucursal_fk'] = producto_suc
                    except producto_sucursal.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Producto de sucursal no encontrado'})
                else:
                    try:
                        servicio_suc = servicio_sucursal.objects.get(id_servicio_sucursal=item_id)
                        favorito_data['id_servicio_sucursal_fk'] = servicio_suc
                    except servicio_sucursal.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Servicio de sucursal no encontrado'})

            favorito_existente = favorito_empresa_sucursal.objects.filter(**favorito_data).first()
            if favorito_existente:
                favorito_existente.delete()
                return JsonResponse({'success': True, 'action': 'removed', 'message': 'Eliminado de favoritos'})
            else:
                favorito_empresa_sucursal.objects.create(**favorito_data)
                return JsonResponse({'success': True, 'action': 'added', 'message': 'Agregado a favoritos'})
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error interno: {str(e)}'
        })


@require_login
def productos_sucursal(request):
    user_info = None
    productos_sucursales = []
    sucursales_list = []
    
    current_user = get_current_user(request)
    if current_user and is_user_authenticated(request):
        account_type = request.session.get('account_type', 'usuario')
        
        if account_type == 'empresa':
            user_info = get_user_info_with_avatar(current_user, account_type, current_user.nombre_empresa)
            
            # Obtener parámetros de filtro
            nombre_producto = request.GET.get('nombre_producto', '').strip()
            sucursal_filtro = request.GET.get('sucursal_filtro', '')
            estado_filtro = request.GET.get('estado_filtro', '')
            
            # Obtener lista de sucursales para el combobox
            sucursales_list = sucursal.objects.filter(
                id_empresa_fk=current_user
            ).values('id_sucursal', 'nombre_sucursal').order_by('nombre_sucursal')
            
            # Construir query base
            productos_sucursales_qs = producto_sucursal.objects.filter(
                id_sucursal_fk__id_empresa_fk=current_user
            ).select_related(
                'id_producto_fk', 'id_sucursal_fk'
            ).prefetch_related(
                'id_producto_fk__imagenes'
            )
            
            # Aplicar filtros
            if nombre_producto:
                productos_sucursales_qs = productos_sucursales_qs.filter(
                    id_producto_fk__nombre_producto_empresa__icontains=nombre_producto
                )
            
            if sucursal_filtro:
                productos_sucursales_qs = productos_sucursales_qs.filter(
                    id_sucursal_fk__id_sucursal=sucursal_filtro
                )
            
            if estado_filtro:
                productos_sucursales_qs = productos_sucursales_qs.filter(
                    estatus_producto_sucursal=estado_filtro
                )
            
            for prod_suc in productos_sucursales_qs:
                # Obtener la primera imagen del producto
                primera_imagen = prod_suc.id_producto_fk.imagenes.first()
                imagen_url = primera_imagen.ruta_imagen_producto_empresa.url if primera_imagen else None
                
                productos_sucursales.append({
                    'id_producto_sucursal': prod_suc.id_producto_sucursal,
                    'nombre_producto': prod_suc.id_producto_fk.nombre_producto_empresa,
                    'descripcion_producto': prod_suc.id_producto_fk.descripcion_producto_empresa,

                    'precio': prod_suc.precio_producto_sucursal,
                    'stock': prod_suc.stock_producto_sucursal,
                    'condicion': prod_suc.condicion_producto_sucursal,
                    'estatus': prod_suc.estatus_producto_sucursal,
                    'nombre_sucursal': prod_suc.id_sucursal_fk.nombre_sucursal,
                    'direccion_sucursal': prod_suc.id_sucursal_fk.direccion_sucursal,
                    'imagen_url': imagen_url,
                    'categoria': prod_suc.id_producto_fk.id_categoria_prod_fk.nombre_categoria_prod_empresa if prod_suc.id_producto_fk.id_categoria_prod_fk else 'Sin categoría'
                })
                
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
    else:
        user_info = {
            'is_authenticated': False
        }
    
    return render(request, 'ecommerce_app/productos_sucursal.html', {
        'user_info': user_info,
        'productos_sucursales': productos_sucursales,
        'sucursales_list': sucursales_list,
        'filtros': {
            'nombre_producto': request.GET.get('nombre_producto', ''),
            'sucursal_filtro': request.GET.get('sucursal_filtro', ''),
            'estado_filtro': request.GET.get('estado_filtro', '')
        }
    })

@require_login
def editar_producto_sucursal(request):
    if request.method == 'POST':
        try:
            id_producto_sucursal = request.POST.get('id_producto_sucursal')
            precio = request.POST.get('precio')
            stock = request.POST.get('stock')
            estatus = request.POST.get('estatus')
            condicion = request.POST.get('condicion')
            
            # Validar que todos los campos estén presentes
            if not all([id_producto_sucursal, precio, stock, estatus, condicion]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son requeridos'
                })
            
            # Obtener empresa_id de la sesión
            empresa_id = request.session.get('empresa_id')
            if not empresa_id:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró la empresa en la sesión'
                })
            
            # Buscar el producto usando solo el ID principal
            try:
                producto_sucursal_obj = producto_sucursal.objects.get(id_producto_sucursal=id_producto_sucursal)
                
                # Verificar si pertenece a la empresa actual
                if producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.id_empresa != empresa_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'No tienes permisos para editar este producto'
                    })
                    
            except producto_sucursal.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado'
                })
            
            # Validar valores numéricos
            try:
                precio_float = float(precio)
                stock_int = int(stock)
                
                if precio_float < 0 or stock_int < 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'El precio y stock deben ser valores positivos'
                    })
                    
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Precio y stock deben ser valores numéricos válidos'
                })
            
            # Validar estatus y condición
            if estatus not in ['Activo', 'Inactivo']:
                return JsonResponse({
                    'success': False,
                    'message': 'Estado inválido'
                })
                
            if condicion not in ['Nuevo', 'Usado']:
                return JsonResponse({
                    'success': False,
                    'message': 'Condición inválida'
                })
            
            # Actualizar el producto
            producto_sucursal_obj.precio_producto_sucursal = precio_float
            producto_sucursal_obj.stock_producto_sucursal = stock_int
            producto_sucursal_obj.estatus_producto_sucursal = estatus
            producto_sucursal_obj.condicion_producto_sucursal = condicion
            producto_sucursal_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Producto actualizado exitosamente'
            })
            
        except producto_sucursal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Producto no encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@require_login
def eliminar_producto_sucursal(request):
    if request.method == 'POST':
        try:
            id_producto_sucursal = request.POST.get('id_producto_sucursal')
            
            if not id_producto_sucursal:
                return JsonResponse({
                    'success': False,
                    'message': 'ID del producto es requerido'
                })
            
            # Obtener empresa_id de la sesión
            empresa_id = request.session.get('empresa_id')
            if not empresa_id:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró la empresa en la sesión'
                })
            
            # Buscar el producto usando solo el ID principal
            try:
                producto_sucursal_obj = producto_sucursal.objects.get(id_producto_sucursal=id_producto_sucursal)
                
                # Verificar si pertenece a la empresa actual
                if producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.id_empresa != empresa_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'No tienes permisos para eliminar este producto'
                    })
                    
            except producto_sucursal.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado'
                })
            
            # Eliminar el producto de la sucursal
            producto_sucursal_obj.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Producto eliminado exitosamente de la sucursal'
            })
            
        except producto_sucursal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Producto no encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })



@require_login
def servicios_sucursal(request):
    user_info = None
    servicios_sucursales = []
    sucursales_list = []
    
    current_user = get_current_user(request)
    if current_user and is_user_authenticated(request):
        account_type = request.session.get('account_type', 'usuario')
        
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True,
                'empresa_nombre': current_user.nombre_empresa
            }
            
            # Obtener parámetros de filtro
            nombre_servicio = request.GET.get('nombre_servicio', '').strip()
            sucursal_filtro = request.GET.get('sucursal_filtro', '')
            estado_filtro = request.GET.get('estado_filtro', '')
            
            # Obtener lista de sucursales para el combobox
            sucursales_list = sucursal.objects.filter(
                id_empresa_fk=current_user
            ).values('id_sucursal', 'nombre_sucursal').order_by('nombre_sucursal')
            
            # Construir query base
            servicios_sucursales_qs = servicio_sucursal.objects.filter(
                id_sucursal_fk__id_empresa_fk=current_user
            ).select_related(
                'id_servicio_fk', 'id_sucursal_fk'
            ).prefetch_related(
                'id_servicio_fk__imagenes'
            )
            
            # Aplicar filtros
            if nombre_servicio:
                servicios_sucursales_qs = servicios_sucursales_qs.filter(
                    id_servicio_fk__nombre_servicio_empresa__icontains=nombre_servicio
                )
            
            if sucursal_filtro:
                servicios_sucursales_qs = servicios_sucursales_qs.filter(
                    id_sucursal_fk__id_sucursal=sucursal_filtro
                )
            
            if estado_filtro:
                servicios_sucursales_qs = servicios_sucursales_qs.filter(
                    estatus_servicio_sucursal=estado_filtro
                )
            
            for serv_suc in servicios_sucursales_qs:
                # Obtener la primera imagen del servicio
                primera_imagen = serv_suc.id_servicio_fk.imagenes.first()
                imagen_url = primera_imagen.ruta_imagen_servicio_empresa.url if primera_imagen else None
                
                servicios_sucursales.append({
                    'id_servicio_sucursal': serv_suc.id_servicio_sucursal,
                    'nombre_servicio': serv_suc.id_servicio_fk.nombre_servicio_empresa,
                    'descripcion_servicio': serv_suc.id_servicio_fk.descripcion_servicio_empresa,
                    'precio': serv_suc.precio_servicio_sucursal,
                    'estatus': serv_suc.estatus_servicio_sucursal,
                    'nombre_sucursal': serv_suc.id_sucursal_fk.nombre_sucursal,
                    'direccion_sucursal': serv_suc.id_sucursal_fk.direccion_sucursal,
                    'imagen_url': imagen_url,
                    'categoria': serv_suc.id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa if serv_suc.id_servicio_fk.id_categoria_servicios_fk else 'Sin categoría'
                })
                
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
    else:
        user_info = {
            'is_authenticated': False
        }
    
    return render(request, 'ecommerce_app/servicios_sucursal.html', {
        'user_info': user_info,
        'servicios_sucursales': servicios_sucursales,
        'sucursales_list': sucursales_list,
        'filtros': {
            'nombre_servicio': request.GET.get('nombre_servicio', ''),
            'sucursal_filtro': request.GET.get('sucursal_filtro', ''),
            'estado_filtro': request.GET.get('estado_filtro', '')
        }
    })

@require_login
def editar_servicio_sucursal(request):
    if request.method == 'POST':
        try:
            id_servicio_sucursal = request.POST.get('id')
            precio = request.POST.get('precio')
            estatus = request.POST.get('estatus')
            
            # Validar que todos los campos estén presentes
            if not all([id_servicio_sucursal, precio, estatus]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son requeridos'
                })
            
            # Obtener empresa_id de la sesión
            empresa_id = request.session.get('empresa_id')
            if not empresa_id:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró la empresa en la sesión'
                })
            
            # Buscar el servicio usando solo el ID principal
            try:
                servicio_sucursal_obj = servicio_sucursal.objects.get(id_servicio_sucursal=id_servicio_sucursal)
                
                # Verificar si pertenece a la empresa actual
                if servicio_sucursal_obj.id_sucursal_fk.id_empresa_fk.id_empresa != empresa_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'No tienes permisos para editar este servicio'
                    })
                    
            except servicio_sucursal.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Servicio no encontrado'
                })
            
            # Validar valores numéricos
            try:
                precio_float = float(precio)
                
                if precio_float < 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'El precio no puede ser negativo'
                    })
                    
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'El precio debe ser un valor numérico válido'
                })
            
            # Validar estatus
            if estatus not in ['Activo', 'Inactivo']:
                return JsonResponse({
                    'success': False,
                    'message': 'Estado inválido'
                })
            
            # Actualizar el servicio
            servicio_sucursal_obj.precio_servicio_sucursal = precio_float
            servicio_sucursal_obj.estatus_servicio_sucursal = estatus
            servicio_sucursal_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Servicio actualizado exitosamente'
            })
            
        except servicio_sucursal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Servicio no encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@require_login
def eliminar_servicio_sucursal(request):
    if request.method == 'POST':
        try:
            id_servicio_sucursal = request.POST.get('id')
            
            if not id_servicio_sucursal:
                return JsonResponse({
                    'success': False,
                    'message': 'ID del servicio es requerido'
                })
            
            # Obtener empresa_id de la sesión
            empresa_id = request.session.get('empresa_id')
            if not empresa_id:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró la empresa en la sesión'
                })
            
            # Buscar el servicio usando solo el ID principal
            try:
                servicio_sucursal_obj = servicio_sucursal.objects.get(id_servicio_sucursal=id_servicio_sucursal)
                
                # Verificar si pertenece a la empresa actual
                if servicio_sucursal_obj.id_sucursal_fk.id_empresa_fk.id_empresa != empresa_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'No tienes permisos para eliminar este servicio'
                    })
                    
            except servicio_sucursal.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Servicio no encontrado'
                })
            
            # Eliminar el servicio de la sucursal
            servicio_sucursal_obj.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Servicio eliminado exitosamente de la sucursal'
            })
            
        except servicio_sucursal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Servicio no encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

def solicitud_servicio(request):
    # Obtener parámetros de la URL
    servicio_id = request.GET.get('servicio_id')
    tipo_propietario = request.GET.get('tipo_propietario')
    sucursal_id_preseleccionada = request.GET.get('sucursal_id')
    print(f"[DEBUG solicitud_servicio] servicio_id: {servicio_id}, tipo_propietario: {tipo_propietario}")
    
    # Verificar si hay usuario autenticado
    current_user = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
    
    # Obtener tipo de cuenta
    account_type = request.session.get('account_type', 'usuario')
    
    # Inicializar variables
    servicio_data = None
    error_message = None
    
    # Si se proporcionan parámetros, obtener datos del servicio
    if servicio_id and tipo_propietario:
        try:
            if tipo_propietario == 'empresa':
                # Primero intentar buscar como servicio_sucursal específico
                try:
                    servicio_sucursal_obj = servicio_sucursal.objects.get(id_servicio_sucursal=servicio_id)
                    servicio_obj = servicio_sucursal_obj.id_servicio_fk
                    
                    # Obtener imágenes del servicio
                    imagenes_servicio = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio_obj)
                    imagenes = [img.ruta_imagen_servicio_empresa.url for img in imagenes_servicio if img.ruta_imagen_servicio_empresa]
                    
                    # Solo mostrar la sucursal específica
                    servicio_data = {
                        'id': servicio_sucursal_obj.id_servicio_sucursal,  # Usar ID del servicio_sucursal
                        'nombre': servicio_obj.nombre_servicio_empresa,
                        'descripcion': servicio_obj.descripcion_servicio_empresa,
                        'tipo_propietario': 'empresa',
                        'empresa': servicio_obj.id_empresa_fk.nombre_empresa,
                        'empresa_id': servicio_obj.id_empresa_fk.id_empresa,
                        'categoria': servicio_obj.id_categoria_servicios_fk.nombre_categoria_serv_empresa if servicio_obj.id_categoria_servicios_fk else 'Sin categoría',
                        'imagenes': imagenes,
                        'sucursales': [{
                            'id': servicio_sucursal_obj.id_sucursal_fk.id_sucursal,
                            'nombre': servicio_sucursal_obj.id_sucursal_fk.nombre_sucursal,
                            'direccion': servicio_sucursal_obj.id_sucursal_fk.direccion_sucursal,
                            'precio': servicio_sucursal_obj.precio_servicio_sucursal if servicio_sucursal_obj.precio_servicio_sucursal else 'Consultar',
                            'telefono': servicio_sucursal_obj.id_sucursal_fk.telefono_sucursal,
                            'email': None,
                            'preseleccionada': True  # Siempre preseleccionada porque es específica
                        }]
                    }
                    
                except servicio_sucursal.DoesNotExist:
                    # Si no es un servicio_sucursal específico, buscar como servicio_empresa general
                    servicio_obj = servicio_empresa.objects.get(id_servicio_empresa=servicio_id)
                    
                    # Obtener imágenes del servicio
                    imagenes_servicio = imagen_servicio_empresa.objects.filter(id_servicio_fk=servicio_obj)
                    imagenes = [img.ruta_imagen_servicio_empresa.url for img in imagenes_servicio if img.ruta_imagen_servicio_empresa]
                    
                    # Obtener información de sucursales que ofrecen este servicio
                    servicios_sucursal = servicio_sucursal.objects.filter(id_servicio_fk=servicio_obj, estatus_servicio_sucursal='Activo')
                    
                    servicio_data = {
                        'id': servicio_obj.id_servicio_empresa,
                        'nombre': servicio_obj.nombre_servicio_empresa,
                        'descripcion': servicio_obj.descripcion_servicio_empresa,
                        'tipo_propietario': 'empresa',
                        'empresa': servicio_obj.id_empresa_fk.nombre_empresa,
                        'empresa_id': servicio_obj.id_empresa_fk.id_empresa,
                        'categoria': servicio_obj.id_categoria_servicios_fk.nombre_categoria_serv_empresa if servicio_obj.id_categoria_servicios_fk else 'Sin categoría',
                        'imagenes': imagenes,
                        'sucursales': [{
                            'id': ss.id_sucursal_fk.id_sucursal,
                            'nombre': ss.id_sucursal_fk.nombre_sucursal,
                            'direccion': ss.id_sucursal_fk.direccion_sucursal,
                            'precio': ss.precio_servicio_sucursal if ss.precio_servicio_sucursal else 'Consultar',
                            'telefono': ss.id_sucursal_fk.telefono_sucursal,
                            'email': None,
                            'preseleccionada': str(ss.id_sucursal_fk.id_sucursal) == str(sucursal_id_preseleccionada)
                        } for ss in servicios_sucursal]
                    }
                
            elif tipo_propietario == 'usuario':
                # Buscar servicio de usuario
                servicio_obj = servicio_usuario.objects.get(id_servicio_usuario=servicio_id)
                
                # Obtener imágenes del servicio
                imagenes_servicio = imagen_servicio_usuario.objects.filter(id_servicio_fk=servicio_obj)
                imagenes = [img.ruta_imagen_servicio_usuario.url for img in imagenes_servicio if img.ruta_imagen_servicio_usuario]
                
                servicio_data = {
                    'id': servicio_obj.id_servicio_usuario,
                    'nombre': servicio_obj.nombre_servicio_usuario,
                    'descripcion': servicio_obj.descripcion_servicio_usuario,
                    'tipo_propietario': 'usuario',
                    'precio': servicio_obj.precio_servicio_usuario if servicio_obj.precio_servicio_usuario else 'Consultar',
                    'usuario': servicio_obj.id_usuario_fk.nombre_usuario,
                    'usuario_id': servicio_obj.id_usuario_fk.id_usuario,
                    'categoria': servicio_obj.id_categoria_servicios_fk.nombre_categoria_serv_usuario if servicio_obj.id_categoria_servicios_fk else 'Sin categoría',
                    'imagenes': imagenes,
                    'telefono': servicio_obj.id_usuario_fk.telefono_usuario,
                    'email': servicio_obj.id_usuario_fk.correo_usuario
                }
                
        except (servicio_empresa.DoesNotExist, servicio_usuario.DoesNotExist):
            error_message = "El servicio solicitado no existe o no está disponible."
        except Exception as e:
            logger.error(f"Error al obtener datos del servicio: {str(e)}")
            error_message = "Error al cargar los datos del servicio."
    
    # Información del usuario actual
    user_info = {
        'is_authenticated': bool(current_user),
        'tipo': account_type
    }
    
    if current_user:
        if account_type == 'empresa':
            user_info.update({
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa
            })
        else:
            user_info.update({
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario
            })
    
    # Procesar formulario de solicitud
    if request.method == 'POST':
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Debe iniciar sesión para solicitar un servicio.'})
        
        try:
            # Obtener datos del formulario
            servicio_solicitado_id = request.POST.get('servicio_id')
            tipo_propietario_servicio = request.POST.get('tipo_propietario')
            sucursal_id = request.POST.get('sucursal_id')  # Solo para servicios de empresa
            descripcion_solicitud = request.POST.get('descripcion_solicitud', '').strip()
            fecha_preferida = request.POST.get('fecha_preferida')
            hora_preferida = request.POST.get('hora_preferida')
            
            # Validaciones
            if not servicio_solicitado_id or not tipo_propietario_servicio:
                return JsonResponse({'success': False, 'message': 'Datos del servicio incompletos.'})
            
            if not descripcion_solicitud:
                return JsonResponse({'success': False, 'message': 'La descripción de la solicitud es obligatoria.'})
            
            # Crear solicitud según el tipo de propietario del servicio
            if tipo_propietario_servicio == 'empresa':
                # Intentar obtener el servicio_sucursal
                try:
                    # Primero intentar como servicio_sucursal específico
                    servicio_sucursal_obj = servicio_sucursal.objects.get(id_servicio_sucursal=servicio_solicitado_id)
                except servicio_sucursal.DoesNotExist:
                    # Si no es un servicio_sucursal específico, buscar por servicio_empresa y sucursal
                    if not sucursal_id:
                        return JsonResponse({'success': False, 'message': 'Debe seleccionar una sucursal para servicios de empresa.'})
                    
                    try:
                        servicio_sucursal_obj = servicio_sucursal.objects.get(
                            id_servicio_fk__id_servicio_empresa=servicio_solicitado_id,
                            id_sucursal_fk__id_sucursal=sucursal_id
                        )
                    except servicio_sucursal.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'El servicio no está disponible en la sucursal seleccionada.'})
                
                # Combinar fecha y hora si están disponibles
                fecha_requerida = None
                if fecha_preferida:
                    try:
                        from datetime import datetime
                        if hora_preferida:
                            fecha_requerida = datetime.strptime(f"{fecha_preferida} {hora_preferida}", "%Y-%m-%d %H:%M")
                        else:
                            fecha_requerida = datetime.strptime(fecha_preferida, "%Y-%m-%d")
                    except ValueError:
                        fecha_requerida = None
                
                # Crear solicitud desde usuario a empresa
                if account_type == 'usuario':
                    solicitud = solicitud_servicio_usuario.objects.create(
                        id_usuario_fk=current_user,
                        id_servicio_sucursal_fk=servicio_sucursal_obj,
                        fecha_requerida=fecha_requerida or timezone.now(),
                        direccion=request.POST.get('direccion', ''),
                        descripcion_detallada=descripcion_solicitud,
                        estado='pendiente'
                    )
                    
                    # Notificar a la empresa sobre la nueva solicitud de servicio
                    empresa_proveedora = servicio_sucursal_obj.id_servicio_fk.id_empresa_fk
                    titulo = f"Nueva Solicitud de Servicio"
                    mensaje = f"Tienes una nueva solicitud para el servicio '{servicio_sucursal_obj.id_servicio_fk.nombre_servicio_empresa}' de {current_user.nombre_usuario}."
                    
                    crear_notificacion_empresa(
                        empresa=empresa_proveedora,
                        tipo_notificacion='solicitud_servicio',
                        titulo=titulo,
                        mensaje=mensaje,
                        solicitud_servicio=solicitud
                    )
                    
                else:
                    # Solicitud desde empresa a empresa
                    solicitud = solicitud_servicio_empresa.objects.create(
                        id_empresa_fk=current_user,
                        id_servicio_sucursal_fk=servicio_sucursal_obj,
                        fecha_requerida=fecha_requerida or timezone.now(),
                        direccion=request.POST.get('direccion', ''),
                        descripcion_detallada=descripcion_solicitud,
                        estado='pendiente'
                    )
                    
                    # Notificar a la empresa sobre la nueva solicitud de servicio
                    empresa_proveedora = servicio_sucursal_obj.id_servicio_fk.id_empresa_fk
                    titulo = f"Nueva Solicitud de Servicio"
                    mensaje = f"Tienen una nueva solicitud para el servicio '{servicio_sucursal_obj.id_servicio_fk.nombre_servicio_empresa}' de {current_user.nombre_empresa}."
                    
                    crear_notificacion_empresa(
                        empresa=empresa_proveedora,
                        tipo_notificacion='solicitud_servicio',
                        titulo=titulo,
                        mensaje=mensaje,
                        solicitud_servicio=solicitud
                    )
                    
            elif tipo_propietario_servicio == 'usuario':
                # Solicitud a servicio de usuario
                try:
                    servicio_obj = servicio_usuario.objects.get(id_servicio_usuario=servicio_solicitado_id)
                except servicio_usuario.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'El servicio solicitado no existe.'})
                
                # Combinar fecha y hora si están disponibles
                fecha_requerida = None
                if fecha_preferida:
                    try:
                        from datetime import datetime
                        if hora_preferida:
                            fecha_requerida = datetime.strptime(f"{fecha_preferida} {hora_preferida}", "%Y-%m-%d %H:%M")
                        else:
                            fecha_requerida = datetime.strptime(fecha_preferida, "%Y-%m-%d")
                    except ValueError:
                        fecha_requerida = None
                
                # Tanto usuarios como empresas pueden solicitar servicios a usuarios individuales
                if account_type == 'usuario':
                    solicitud = solicitud_servicio_usuario.objects.create(
                        id_usuario_fk=current_user,
                        id_servicio_usuario_fk=servicio_obj,
                        fecha_requerida=fecha_requerida or timezone.now(),
                        direccion=request.POST.get('direccion', ''),
                        descripcion_detallada=descripcion_solicitud,
                        estado='pendiente'
                    )
                    
                    # Notificar al usuario proveedor sobre la nueva solicitud de servicio
                    usuario_proveedor = servicio_obj.id_usuario_fk
                    titulo = f"Nueva Solicitud de Servicio"
                    mensaje = f"Tienes una nueva solicitud para tu servicio '{servicio_obj.nombre_servicio_usuario}' de {current_user.nombre_usuario}."
                    
                    crear_notificacion_usuario(
                        usuario=usuario_proveedor,
                        tipo_notificacion='solicitud_servicio',
                        titulo=titulo,
                        mensaje=mensaje,
                        solicitud_servicio=solicitud
                    )
                    
                else:  # account_type == 'empresa'
                    solicitud = solicitud_servicio_empresa.objects.create(
                        id_empresa_fk=current_user,
                        id_servicio_usuario_fk=servicio_obj,
                        fecha_requerida=fecha_requerida or timezone.now(),
                        direccion=request.POST.get('direccion', ''),
                        descripcion_detallada=descripcion_solicitud,
                        estado='pendiente'
                    )
                    
                    # Notificar al usuario proveedor sobre la nueva solicitud de servicio
                    usuario_proveedor = servicio_obj.id_usuario_fk
                    titulo = f"Nueva Solicitud de Servicio"
                    mensaje = f"Tienes una nueva solicitud para tu servicio '{servicio_obj.nombre_servicio_usuario}' de {current_user.nombre_empresa}."
                    
                    crear_notificacion_usuario(
                        usuario=usuario_proveedor,
                        tipo_notificacion='solicitud_servicio',
                        titulo=titulo,
                        mensaje=mensaje,
                        solicitud_servicio=solicitud
                    )
            
            logger.info(f"Solicitud de servicio creada exitosamente por {current_user}")
            return JsonResponse({'success': True, 'message': 'Solicitud de servicio enviada exitosamente.'})
            
        except Exception as e:
            logger.error(f"Error al crear solicitud de servicio: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Error al procesar la solicitud.'})
    
    return render(request, 'ecommerce_app/solicitud_servicio.html', {
        'servicio_data': servicio_data,
        'user_info': user_info,
        'error_message': error_message
    })

def gestion_servicio(request):
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')

    account_type = request.session.get('account_type', 'usuario')
    
    if account_type == 'empresa':
        # Para empresas, current_user ya es la empresa
        user_info = {
            'id': current_user.id_empresa,
            'nombre': current_user.nombre_empresa,
            'email': current_user.correo_empresa,
            'tipo': current_user.rol_empresa,
            'is_authenticated': True
        }
        # Obtener solicitudes de servicios de la empresa (solo pendientes y cotizadas)
        solicitudes_raw = solicitud_servicio_empresa.objects.filter(
            id_empresa_fk=current_user,
            estado__in=['pendiente', 'cotizada']
        ).select_related(
            'id_servicio_usuario_fk__id_usuario_fk',
            'id_servicio_sucursal_fk__id_servicio_fk__id_empresa_fk',
            'id_servicio_sucursal_fk__id_sucursal_fk'
        ).order_by('-fecha_solicitud')
        
        # Agregar información detallada a cada solicitud
        solicitudes = []
        for solicitud in solicitudes_raw:
            # Convertir el objeto solicitud a diccionario serializable
            solicitud_dict = {
                'id_solicitud_servicio_empresa': solicitud.id_solicitud_servicio_empresa,
                'fecha_solicitud': solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else None,
                'fecha_requerida': solicitud.fecha_requerida.isoformat() if solicitud.fecha_requerida else None,
                'estado': solicitud.estado,
                'descripcion_detallada': solicitud.descripcion_detallada,
                'direccion': solicitud.direccion,
                # Campos de cotización
                'presupuesto_cotizacion': float(solicitud.presupuesto_cotizacion) if solicitud.presupuesto_cotizacion else None,
                'descripcion_cotizacion': solicitud.descripcion_cotizacion,
                'fecha_cotizacion': solicitud.fecha_cotizacion.isoformat() if solicitud.fecha_cotizacion else None,
                'archivo_cotizacion': solicitud.archivo_cotizacion.url if solicitud.archivo_cotizacion else None
            }
            
            solicitud_data = {
                'solicitud': solicitud_dict,
                'sucursal_info': None,
                'proveedor_info': None,
                'servicio_info': None
            }
            
            # Información del servicio y proveedor
            if solicitud.id_servicio_usuario_fk:
                # Servicio de usuario individual
                servicio = solicitud.id_servicio_usuario_fk
                proveedor = servicio.id_usuario_fk
                solicitud_data['servicio_info'] = {
                    'nombre': servicio.nombre_servicio_usuario,
                    'descripcion': servicio.descripcion_servicio_usuario,
                    'precio': servicio.precio_servicio_usuario,
                    'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_usuario if servicio.id_categoria_servicios_fk else 'Sin categoría',
                    'tipo': 'usuario'
                }
                solicitud_data['proveedor_info'] = {
                    'nombre': proveedor.nombre_usuario,
                    'email': proveedor.correo_usuario,
                    'telefono': proveedor.telefono_usuario,
                    'tipo': 'Usuario Individual'
                }
            elif solicitud.id_servicio_sucursal_fk:
                # Servicio de empresa
                servicio_sucursal = solicitud.id_servicio_sucursal_fk
                servicio = servicio_sucursal.id_servicio_fk
                empresa_proveedor = servicio.id_empresa_fk
                sucursal = servicio_sucursal.id_sucursal_fk
                
                solicitud_data['servicio_info'] = {
                    'nombre': servicio.nombre_servicio_empresa,
                    'descripcion': servicio.descripcion_servicio_empresa,
                    'precio': servicio_sucursal.precio_servicio_sucursal,
                    'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_empresa if servicio.id_categoria_servicios_fk else 'Sin categoría',
                    'tipo': 'empresa'
                }
                solicitud_data['proveedor_info'] = {
                    'nombre': empresa_proveedor.nombre_empresa,
                    'email': empresa_proveedor.correo_empresa,
                    'telefono': 'No disponible',
                    'tipo': 'Empresa'
                }
                solicitud_data['sucursal_info'] = {
                    'nombre': sucursal.nombre_sucursal,
                    'direccion': sucursal.direccion_sucursal,
                    'telefono': sucursal.telefono_sucursal
                }
            
            solicitudes.append(solicitud_data)
    else:
        # Para usuarios individuales
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        # Obtener solicitudes de servicios del usuario (solo pendientes y cotizadas)
        solicitudes_raw = solicitud_servicio_usuario.objects.filter(
            id_usuario_fk=current_user,
            estado__in=['pendiente', 'cotizada']
        ).select_related(
            'id_servicio_usuario_fk__id_usuario_fk',
            'id_servicio_sucursal_fk__id_servicio_fk__id_empresa_fk',
            'id_servicio_sucursal_fk__id_sucursal_fk'
        ).order_by('-fecha_solicitud')
        
        # Agregar información detallada a cada solicitud
        solicitudes = []
        for solicitud in solicitudes_raw:
            # Convertir el objeto solicitud a diccionario serializable
            solicitud_dict = {
                'id_solicitud_servicio_usuario': solicitud.id_solicitud_servicio_usuario,
                'fecha_solicitud': solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else None,
                'fecha_requerida': solicitud.fecha_requerida.isoformat() if solicitud.fecha_requerida else None,
                'estado': solicitud.estado,
                'descripcion_detallada': solicitud.descripcion_detallada,
                'direccion': solicitud.direccion,
                # Campos de cotización
                'presupuesto_cotizacion': float(solicitud.presupuesto_cotizacion) if solicitud.presupuesto_cotizacion else None,
                'descripcion_cotizacion': solicitud.descripcion_cotizacion,
                'fecha_cotizacion': solicitud.fecha_cotizacion.isoformat() if solicitud.fecha_cotizacion else None,
                'archivo_cotizacion': solicitud.archivo_cotizacion.url if solicitud.archivo_cotizacion else None
            }
            
            solicitud_data = {
                'solicitud': solicitud_dict,
                'sucursal_info': None,
                'proveedor_info': None,
                'servicio_info': None
            }
            
            # Información del servicio y proveedor
            if solicitud.id_servicio_usuario_fk:
                # Servicio de usuario individual
                servicio = solicitud.id_servicio_usuario_fk
                proveedor = servicio.id_usuario_fk
                solicitud_data['servicio_info'] = {
                    'nombre': servicio.nombre_servicio_usuario,
                    'descripcion': servicio.descripcion_servicio_usuario,
                    'precio': servicio.precio_servicio_usuario,
                    'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_usuario if servicio.id_categoria_servicios_fk else 'Sin categoría',
                    'tipo': 'usuario'
                }
                solicitud_data['proveedor_info'] = {
                    'nombre': proveedor.nombre_usuario,
                    'email': proveedor.correo_usuario,
                    'telefono': proveedor.telefono_usuario,
                    'tipo': 'Usuario Individual'
                }
            elif solicitud.id_servicio_sucursal_fk:
                # Servicio de empresa
                servicio_sucursal = solicitud.id_servicio_sucursal_fk
                servicio = servicio_sucursal.id_servicio_fk
                empresa_proveedor = servicio.id_empresa_fk
                sucursal = servicio_sucursal.id_sucursal_fk
                
                solicitud_data['servicio_info'] = {
                    'nombre': servicio.nombre_servicio_empresa,
                    'descripcion': servicio.descripcion_servicio_empresa,
                    'precio': servicio_sucursal.precio_servicio_sucursal,
                    'categoria': servicio.id_categoria_servicios_fk.nombre_categoria_serv_empresa if servicio.id_categoria_servicios_fk else 'Sin categoría',
                    'tipo': 'empresa'
                }
                solicitud_data['proveedor_info'] = {
                    'nombre': empresa_proveedor.nombre_empresa,
                    'email': empresa_proveedor.correo_empresa,
                    'telefono': 'No disponible',
                    'tipo': 'Empresa'
                }
                solicitud_data['sucursal_info'] = {
                    'nombre': sucursal.nombre_sucursal,
                    'direccion': sucursal.direccion_sucursal,
                    'telefono': sucursal.telefono_sucursal
                }
            
            solicitudes.append(solicitud_data)
    
    context = {
        'user_info': user_info,
        'solicitudes': solicitudes,
    }
    return render(request, 'ecommerce_app/gestion_servicio.html', context)

# API para obtener datos dinámicos de filtros
@require_GET
def api_obtener_filtros_busqueda(request):
    try:

        
        # Obtener categorías de productos
        categorias_productos = categoria_producto_empresa.objects.values(
            'id_categoria_prod_empresa', 'nombre_categoria_prod_empresa'
        ).distinct()
        
        # Obtener categorías de servicios
        categorias_servicios = categoria_servicio_empresa.objects.values(
            'id_categoria_servicios_empresa', 'nombre_categoria_serv_empresa'
        ).distinct()
        
        # Obtener rangos de precios
        precios_productos_sucursal = producto_sucursal.objects.exclude(
            precio_producto_sucursal__isnull=True
        ).values_list('precio_producto_sucursal', flat=True)
        
        precios_productos_usuario = producto_usuario.objects.exclude(
            precio_producto_usuario__isnull=True
        ).values_list('precio_producto_usuario', flat=True)
        
        precios_servicios_sucursal = servicio_sucursal.objects.exclude(
            precio_servicio_sucursal__isnull=True
        ).values_list('precio_servicio_sucursal', flat=True)
        
        precios_servicios_usuario = servicio_usuario.objects.exclude(
            precio_servicio_usuario__isnull=True
        ).values_list('precio_servicio_usuario', flat=True)
        
        # Combinar todos los precios y calcular rangos
        todos_precios = list(precios_productos_sucursal) + list(precios_productos_usuario) + \
                       list(precios_servicios_sucursal) + list(precios_servicios_usuario)
        
        # Filtrar precios válidos (números)
        precios_numericos = []
        for precio in todos_precios:
            try:
                precio_float = float(precio)
                if precio_float > 0:
                    precios_numericos.append(precio_float)
            except (ValueError, TypeError):
                continue
        
        # Calcular rangos de precios
        rangos_precio = []
        if precios_numericos:
            precio_min = min(precios_numericos)
            precio_max = max(precios_numericos)
            
            # Crear rangos dinámicos
            if precio_max > 1000:
                rangos_precio = [
                    {'min': 0, 'max': 100, 'label': '$0 - $100'},
                    {'min': 100, 'max': 500, 'label': '$100 - $500'},
                    {'min': 500, 'max': 1000, 'label': '$500 - $1,000'},
                    {'min': 1000, 'max': 5000, 'label': '$1,000 - $5,000'},
                    {'min': 5000, 'max': None, 'label': 'Más de $5,000'}
                ]
            else:
                rangos_precio = [
                    {'min': 0, 'max': 50, 'label': '$0 - $50'},
                    {'min': 50, 'max': 200, 'label': '$50 - $200'},
                    {'min': 200, 'max': 500, 'label': '$200 - $500'},
                    {'min': 500, 'max': None, 'label': 'Más de $500'}
                ]
        
        return JsonResponse({
            'success': True,
            'filtros': {
                'categorias_productos': list(categorias_productos),
                'categorias_servicios': list(categorias_servicios),
                'rangos_precio': rangos_precio,
                'condiciones': ['Nuevo', 'Usado']
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener filtros: {str(e)}'
        })

# API para obtener conteos de filtros
@require_GET
def api_obtener_conteos_filtros(request):
    try:
        query = request.GET.get('query', '')
        
        # Filtros base para la búsqueda
        if query:
            # Productos de empresa
            productos_empresa_query = producto_sucursal.objects.filter(
                id_producto_fk__nombre_producto_empresa__icontains=query,
                estatus_producto_sucursal='Activo'
            ).select_related('id_producto_fk')
            
            # Productos de usuario
            productos_usuario_query = producto_usuario.objects.filter(
                nombre_producto_usuario__icontains=query,
                estatus_producto_usuario='Activo'
            )
            
            # Servicios de empresa
            servicios_empresa_query = servicio_sucursal.objects.filter(
                id_servicio_fk__nombre_servicio_empresa__icontains=query,
                estatus_servicio_sucursal='Activo'
            ).select_related('id_servicio_fk')
            
            # Servicios de usuario
            servicios_usuario_query = servicio_usuario.objects.filter(
                nombre_servicio_usuario__icontains=query,
                estatus_servicio_usuario='Activo'
            )
        else:
            # Si no hay query, obtener todos los activos
            productos_empresa_query = producto_sucursal.objects.filter(
                estatus_producto_sucursal='Activo'
            ).select_related('id_producto_fk')
            
            productos_usuario_query = producto_usuario.objects.filter(
                estatus_producto_usuario='Activo'
            )
            
            servicios_empresa_query = servicio_sucursal.objects.filter(
                estatus_servicio_sucursal='Activo'
            ).select_related('id_servicio_fk')
            
            servicios_usuario_query = servicio_usuario.objects.filter(
                estatus_servicio_usuario='Activo'
            )
        
        # Contar por condición
        conteo_nuevo = 0
        conteo_usado = 0
        
        for producto in productos_empresa_query:
            if producto.condicion_producto_sucursal == 'Nuevo':
                conteo_nuevo += 1
            elif producto.condicion_producto_sucursal == 'Usado':
                conteo_usado += 1
        
        for producto in productos_usuario_query:
            if producto.condicion_producto_usuario == 'Nuevo':
                conteo_nuevo += 1
            elif producto.condicion_producto_usuario == 'Usado':
                conteo_usado += 1
        

        
        return JsonResponse({
            'success': True,
            'conteos': {
                'condiciones': {
                    'Nuevo': conteo_nuevo,
                    'Usado': conteo_usado
                },
                'total_productos': productos_empresa_query.count() + productos_usuario_query.count(),
                'total_servicios': servicios_empresa_query.count() + servicios_usuario_query.count()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener conteos: {str(e)}'
        })

@require_login
def pedidos_confirmados(request):
    """Vista para mostrar pedidos confirmados del usuario"""
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        pedidos_historial = []
        
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
            
            # Obtener pedidos confirmados de empresa
            pedidos_empresa = pedido_empresa.objects.filter(
                id_carrito_fk__id_empresa_fk=current_user,
                estado_pedido='confirmado'
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_empresa:
                # Obtener detalles del pedido
                detalles = detalle_pedido_empresa.objects.filter(id_pedido_fk=pedido)
                
                detalles_list = []
                for detalle in detalles:
                    if detalle.id_fk_producto_sucursal_empresa:
                        nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                        empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                        # Producto perteneciente a empresa -> no hay usuario propietario
                        usuario_nombre = None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                        # Intentar obtener nombre del usuario propietario del producto (si existe)
                        try:
                            usuario_nombre = detalle.idproducto_fk_usuario.id_usuario_fk.nombre_usuario if detalle.idproducto_fk_usuario.id_usuario_fk else None
                        except Exception:
                            usuario_nombre = None
                    else:
                        nombre_producto = "Producto no disponible"
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen_url = None
                    
                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url,
                        'sucursal': sucursal,
                        'empresa': empresa,
                        'usuario': usuario_nombre
                    })
                
                pedidos_historial.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha_pedido': pedido.fecha_pedido,
                    'estado_pedido': pedido.estado_pedido,
                    'total_pedido': float(pedido.total_pedido),
                    'metodo_pago': pedido.metodo_pago,
                    'direccion_entrega': pedido.direccion_envio,
                    'notas_pedido': pedido.notas_pedido,
                    'detalles': detalles_list,
                    'tipo_pedido': 'empresa',
                    'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None,
                    'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None)
                })
        
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
            
            # Obtener pedidos confirmados de usuario
            pedidos_usuario = pedido_usuario.objects.filter(
                id_carrito_fk__id_usuario_fk=current_user,
                estado_pedido='confirmado'
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_usuario:
                # Obtener detalles del pedido
                detalles = detalle_pedido_usuario.objects.filter(id_pedido_fk=pedido)
                
                detalles_list = []
                for detalle in detalles:
                    if detalle.id_fk_producto_sucursal_empresa:
                        nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                        empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                        # Producto de empresa -> no usuario propietario
                        usuario_nombre = None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                        try:
                            usuario_nombre = detalle.idproducto_fk_usuario.id_usuario_fk.nombre_usuario if detalle.idproducto_fk_usuario.id_usuario_fk else None
                        except Exception:
                            usuario_nombre = None
                    else:
                        nombre_producto = "Producto no disponible"
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen_url = None
                        usuario_nombre = None

                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url,
                        'sucursal': sucursal,
                        'empresa': empresa,
                        'usuario': usuario_nombre
                    })
                
                pedidos_historial.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha_pedido': pedido.fecha_pedido,
                    'estado_pedido': pedido.estado_pedido,
                    'total_pedido': float(pedido.total_pedido),
                    'metodo_pago': pedido.metodo_pago,
                    'direccion_entrega': pedido.direccion_envio,
                    'notas_pedido': pedido.notas_pedido,
                    'detalles': detalles_list,
                    'tipo_pedido': 'usuario',
                    'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None,
                    'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None)
                })
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'pedidos_historial': pedidos_historial,
            'total_pedidos': len(pedidos_historial)
        }
        
        return render(request, 'ecommerce_app/pedidos_confirmados.html', context)
        
    except Exception as e:
        logger.error(f"Error en función pedidos_confirmados: {str(e)}")
        return redirect('/ecommerce/carrito')

@require_login
def pedidos_rechazados(request):
    """Vista para mostrar pedidos rechazados del usuario"""
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        pedidos_historial = []
        
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
            
            # Obtener pedidos rechazados de empresa
            pedidos_empresa = pedido_empresa.objects.filter(
                id_carrito_fk__id_empresa_fk=current_user,
                estado_pedido='cancelado'
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_empresa:
                # Obtener detalles del pedido
                detalles = detalle_pedido_empresa.objects.filter(id_pedido_fk=pedido)
                
                detalles_list = []
                for detalle in detalles:
                    if detalle.id_fk_producto_sucursal_empresa:
                        nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                        empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                        usuario_nombre = None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                        try:
                            usuario_nombre = detalle.idproducto_fk_usuario.id_usuario_fk.nombre_usuario if detalle.idproducto_fk_usuario.id_usuario_fk else None
                        except Exception:
                            usuario_nombre = None
                    else:
                        nombre_producto = "Producto no disponible"
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen_url = None
                        usuario_nombre = None

                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url,
                        'sucursal': sucursal,
                        'empresa': empresa,
                        'usuario': usuario_nombre
                    })
                
                pedidos_historial.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha_pedido': pedido.fecha_pedido,
                    'estado_pedido': pedido.estado_pedido,
                    'total_pedido': float(pedido.total_pedido),
                    'metodo_pago': pedido.metodo_pago,
                    'direccion_entrega': pedido.direccion_envio,
                    'notas_pedido': pedido.notas_pedido,
                    'detalles': detalles_list,
                    'tipo_pedido': 'empresa',
                    'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None,
                    'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None)
                })
        
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
            
            # Obtener pedidos rechazados de usuario
            pedidos_usuario = pedido_usuario.objects.filter(
                id_carrito_fk__id_usuario_fk=current_user,
                estado_pedido='cancelado'
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_usuario:
                # Obtener detalles del pedido
                detalles = detalle_pedido_usuario.objects.filter(id_pedido_fk=pedido)
                
                detalles_list = []
                for detalle in detalles:
                    if detalle.id_fk_producto_sucursal_empresa:
                        nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                        empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                        usuario_nombre = None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                        try:
                            usuario_nombre = detalle.idproducto_fk_usuario.id_usuario_fk.nombre_usuario if detalle.idproducto_fk_usuario.id_usuario_fk else None
                        except Exception:
                            usuario_nombre = None
                    else:
                        nombre_producto = "Producto no disponible"
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen_url = None
                        usuario_nombre = None

                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url,
                        'sucursal': sucursal,
                        'empresa': empresa,
                        'usuario': usuario_nombre
                    })
                
                pedidos_historial.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha_pedido': pedido.fecha_pedido,
                    'estado_pedido': pedido.estado_pedido,
                    'total_pedido': float(pedido.total_pedido),
                    'metodo_pago': pedido.metodo_pago,
                    'direccion_entrega': pedido.direccion_envio,
                    'notas_pedido': pedido.notas_pedido,
                    'detalles': detalles_list,
                    'tipo_pedido': 'usuario',
                    'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None,
                    'motivo_rechazo': getattr(pedido, 'comentario_rechazo', None)
                })
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'pedidos_historial': pedidos_historial,
            'total_pedidos': len(pedidos_historial)
        }
        
        return render(request, 'ecommerce_app/pedidos_rechazados.html', context)
        
    except Exception as e:
        logger.error(f"Error en función pedidos_rechazados: {str(e)}")
        return redirect('/ecommerce/carrito')

@require_login
def pedidos_pendientes(request):
    """Vista para mostrar pedidos pendientes del usuario"""
    current_user = get_current_user(request)
    if not current_user:
        return redirect('/ecommerce/iniciar_sesion')
    
    try:
        account_type = request.session.get('account_type', 'usuario')
        pedidos_historial = []
        
        if account_type == 'empresa':
            user_info = {
                'id': current_user.id_empresa,
                'nombre': current_user.nombre_empresa,
                'email': current_user.correo_empresa,
                'tipo': current_user.rol_empresa,
                'is_authenticated': True
            }
            
            # Obtener pedidos pendientes de empresa
            pedidos_empresa = pedido_empresa.objects.filter(
                id_carrito_fk__id_empresa_fk=current_user,
                estado_pedido='pendiente'
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_empresa:
                # Obtener detalles del pedido
                detalles = detalle_pedido_empresa.objects.filter(id_pedido_fk=pedido)
                
                detalles_list = []
                for detalle in detalles:
                    if detalle.id_fk_producto_sucursal_empresa:
                        nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                        sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                        empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                        usuario_nombre = None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                        try:
                            usuario_nombre = detalle.idproducto_fk_usuario.id_usuario_fk.nombre_usuario if detalle.idproducto_fk_usuario.id_usuario_fk else None
                        except Exception:
                            usuario_nombre = None
                    else:
                        nombre_producto = "Producto no disponible"
                        sucursal = "Sin sucursal"
                        empresa = "Sin empresa"
                        imagen_url = None
                        usuario_nombre = None

                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url,
                        'sucursal': sucursal,
                        'empresa': empresa,
                        'usuario': usuario_nombre
                    })
                
                pedidos_historial.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha_pedido': pedido.fecha_pedido,
                    'estado_pedido': pedido.estado_pedido,
                    'total_pedido': float(pedido.total_pedido),
                    'metodo_pago': pedido.metodo_pago,
                    'direccion_entrega': pedido.direccion_envio,
                    'notas_pedido': pedido.notas_pedido,
                    'detalles': detalles_list,
                    'tipo_pedido': 'empresa',
                    'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None
                })
        
        else:
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
            
            # Obtener pedidos pendientes de usuario
            pedidos_usuario = pedido_usuario.objects.filter(
                id_carrito_fk__id_usuario_fk=current_user,
                estado_pedido='pendiente'
            ).order_by('-fecha_pedido')
            
            for pedido in pedidos_usuario:
                try:
                    # Obtener detalles del pedido
                    detalles = detalle_pedido_usuario.objects.filter(id_pedido_fk=pedido)

                    detalles_list = []
                    for detalle in detalles:
                        try:
                            usuario_nombre = None
                            if detalle.id_fk_producto_sucursal_empresa:
                                nombre_producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk.nombre_producto_empresa
                                sucursal = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.nombre_sucursal if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk else "Sin sucursal"
                                empresa = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk.nombre_empresa if detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk and detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk.id_empresa_fk else "Sin empresa"
                                imagen = imagen_producto_empresa.objects.filter(
                                    id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                                ).first()
                                imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                            elif detalle.idproducto_fk_usuario:
                                nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                                sucursal = "Sin sucursal"
                                empresa = "Sin empresa"
                                imagen = imagen_producto_usuario.objects.filter(
                                    id_producto_fk=detalle.idproducto_fk_usuario
                                ).first()
                                imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                                try:
                                    usuario_nombre = detalle.idproducto_fk_usuario.id_usuario_fk.nombre_usuario if detalle.idproducto_fk_usuario.id_usuario_fk else None
                                except Exception:
                                    usuario_nombre = None
                            else:
                                nombre_producto = "Producto no disponible"
                                sucursal = "Sin sucursal"
                                empresa = "Sin empresa"
                                imagen_url = None
                                usuario_nombre = None

                            detalles_list.append({
                                'nombre_producto': nombre_producto,
                                'cantidad': detalle.cantidad_detalle_pedido,
                                'precio_unitario': float(detalle.precio_unitario_pedido),
                                'subtotal': float(detalle.subtotal_detalle_pedido),
                                'imagen': imagen_url,
                                'sucursal': sucursal,
                                'empresa': empresa,
                                'usuario': usuario_nombre
                            })
                        except Exception as e_det:
                            # Loguear error de detalle y continuar
                            import traceback as _tb_det
                            logger.error(f"Error procesando detalle de pedido {getattr(pedido,'numero_pedido', '?')}: {e_det}")
                            logger.error(_tb_det.format_exc())
                            continue

                    pedidos_historial.append({
                        'numero_pedido': pedido.numero_pedido,
                        'fecha_pedido': pedido.fecha_pedido,
                        'estado_pedido': pedido.estado_pedido,
                        'total_pedido': float(pedido.total_pedido),
                        'metodo_pago': pedido.metodo_pago,
                        'direccion_entrega': pedido.direccion_envio,
                        'notas_pedido': pedido.notas_pedido,
                        'detalles': detalles_list,
                        'tipo_pedido': 'usuario',
                        'comprobante_pago_url': pedido.comprobante_pago.url if pedido.comprobante_pago else None
                    })
                except Exception as e_ped:
                    import traceback as _tb_ped
                    logger.error(f"Error procesando pedido {getattr(pedido,'numero_pedido', '?')}: {e_ped}")
                    logger.error(_tb_ped.format_exc())
                    # continuar con el siguiente pedido en lugar de fallar toda la vista
                    continue
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'pedidos_pendientes': pedidos_historial,
            'total_pedidos': len(pedidos_historial)
        }
        
        return render(request, 'ecommerce_app/pedidos_pendientes.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en función pedidos_pendientes: {str(e)}")
        logger.error(traceback.format_exc())
        # No redirigimos silenciosamente al carrito para facilitar el debug; redirigimos al índice
        return redirect('/ecommerce/index/')


# API para obtener atributos asociados a una categoría
@require_GET
def api_obtener_atributos_categoria(request):
    """API para obtener los atributos de una categoría específica o un atributo individual"""
    try:
        categoria_id = request.GET.get('categoria_id')
        id_categoria_atributo = request.GET.get('id_categoria_atributo')
        account_type = request.session.get('account_type', 'usuario')
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        # Importar los modelos necesarios
        from .models import CategoriaAtributo, AtributoProducto
        
        # Si se solicita un atributo específico
        if id_categoria_atributo:
            try:
                cat_attr = CategoriaAtributo.objects.select_related('atributo').get(
                    id_categoria_atributo=id_categoria_atributo
                )
                atributo = cat_attr.atributo
                atributo_data = {
                    'id_categoria_atributo': cat_attr.id_categoria_atributo,
                    'id_atributo': atributo.id_atributo,
                    'nombre': atributo.nombre,
                    'tipo_dato': atributo.tipo_dato,
                    'opciones': atributo.opciones,
                    'obligatorio': atributo.obligatorio,
                    'descripcion': atributo.descripcion,
                    'orden': cat_attr.orden
                }
                return JsonResponse({
                    'success': True,
                    'atributo': atributo_data
                })
            except CategoriaAtributo.DoesNotExist:
                return JsonResponse({'error': 'Atributo no encontrado'}, status=404)
        
        # Si se solicitan todos los atributos de una categoría
        if not categoria_id:
            return JsonResponse({'error': 'ID de categoría requerido'}, status=400)
        
        # Optional explicit 'tipo' query param to disambiguate category origin (empresa|usuario)
        tipo_param = request.GET.get('tipo')

        # Obtener atributos según el tipo solicitado o según el tipo de cuenta
        if tipo_param == 'empresa':
            logger.info(f"Buscando atributos (request.tipo=empresa) - categoria_empresa_id={categoria_id}")
            atributos_categoria = CategoriaAtributo.objects.filter(
                categoria_empresa_id=categoria_id
            ).select_related('atributo').order_by('orden', 'fecha_asociacion')
            logger.info(f"Encontrados {atributos_categoria.count()} atributos para empresa (forced)")

        elif tipo_param == 'usuario':
            logger.info(f"Buscando atributos (request.tipo=usuario) - categoria_usuario_id={categoria_id}")
            atributos_categoria = CategoriaAtributo.objects.filter(
                categoria_usuario_id=categoria_id
            ).select_related('atributo').order_by('orden', 'fecha_asociacion')
            logger.info(f"Encontrados {atributos_categoria.count()} atributos para usuario (forced)")

        else:
            # Backwards-compatible behavior: use account_type from session
            if account_type == 'empresa':
                # Para empresas, buscar en categoria_empresa
                logger.info(f"Buscando atributos para empresa - categoria_empresa_id={categoria_id}")
                atributos_categoria = CategoriaAtributo.objects.filter(
                    categoria_empresa_id=categoria_id
                ).select_related('atributo').order_by('orden', 'fecha_asociacion')
                logger.info(f"Encontrados {atributos_categoria.count()} atributos para empresa")
            else:
                # Para usuarios, buscar en categoria_usuario
                logger.info(f"Buscando atributos para usuario - categoria_usuario_id={categoria_id}")
                atributos_categoria = CategoriaAtributo.objects.filter(
                    categoria_usuario_id=categoria_id
                ).select_related('atributo').order_by('orden', 'fecha_asociacion')
                logger.info(f"Encontrados {atributos_categoria.count()} atributos para usuario")
                
                # Si no hay atributos para usuario, intentar buscar en empresa (compatibility fallback)
                if atributos_categoria.count() == 0:
                    logger.warning(f"No se encontraron atributos en categoria_usuario. Intentando en categoria_empresa...")
                    atributos_categoria = CategoriaAtributo.objects.filter(
                        categoria_empresa_id=categoria_id
                    ).select_related('atributo').order_by('orden', 'fecha_asociacion')
                    logger.info(f"Encontrados {atributos_categoria.count()} atributos en categoria_empresa")
        
        # Construir la lista de atributos
        atributos_list = []
        for cat_attr in atributos_categoria:
            atributo = cat_attr.atributo
            atributo_data = {
                'id_categoria_atributo': cat_attr.id_categoria_atributo,
                'id_atributo': atributo.id_atributo,
                'nombre': atributo.nombre,
                'tipo_dato': atributo.tipo_dato,
                'obligatorio': atributo.obligatorio,
                'descripcion': atributo.descripcion,
                'opciones': atributo.opciones if atributo.tipo_dato == 'lista' else None,
                'orden': cat_attr.orden
            }
            atributos_list.append(atributo_data)
        
        return JsonResponse({
            'success': True,
            'atributos': atributos_list
        })
        
    except Exception as e:
        logger.error(f"Error al obtener atributos de categoría: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        })

def api_obtener_valores_atributos_producto(request):
    """API para obtener los valores de atributos de un producto específico"""
    try:
        producto_id = request.GET.get('producto_id')
        account_type = request.session.get('account_type', 'usuario')
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        if not producto_id:
            return JsonResponse({'error': 'ID de producto requerido'}, status=400)
        
        # Importar los modelos necesarios
        from .models import ValorAtributoProducto, producto_usuario, producto_empresa
        from .eav_helpers import EAVHelper
        
        valores_list = []
        
        # Determinar el tipo de producto y obtener los valores
        if account_type == 'empresa':
            # Para empresas, buscar en producto_empresa
            try:
                producto = producto_empresa.objects.get(id_producto_empresa=producto_id)
                valores = EAVHelper.obtener_valores_producto_empresa(producto)
            except producto_empresa.DoesNotExist:
                return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        else:
            # Para usuarios, buscar en producto_usuario
            try:
                producto = producto_usuario.objects.get(id_producto_usuario=producto_id)
                valores = EAVHelper.obtener_valores_producto_usuario(producto)
            except producto_usuario.DoesNotExist:
                return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        
        # Construir la lista de valores
        for valor in valores:
            atributo = valor.atributo
            valor_final = None
            
            # Obtener el valor según el tipo de dato
            if atributo.tipo_dato == 'texto' or atributo.tipo_dato == 'lista':
                valor_final = valor.valor_texto
            elif atributo.tipo_dato == 'numero':
                valor_final = valor.valor_numero
            elif atributo.tipo_dato == 'decimal':
                valor_final = float(valor.valor_decimal) if valor.valor_decimal else None
            elif atributo.tipo_dato == 'fecha':
                valor_final = valor.valor_fecha.isoformat() if valor.valor_fecha else None
            elif atributo.tipo_dato == 'booleano':
                valor_final = 'true' if valor.valor_booleano else 'false'
            
            if valor_final is not None:
                valores_list.append({
                    'atributo_id': atributo.id_atributo,
                    'nombre_atributo': atributo.nombre,
                    'tipo_dato': atributo.tipo_dato,
                    'valor': str(valor_final)
                })
        
        return JsonResponse({
            'success': True,
            'valores': valores_list
        })
        
    except Exception as e:
        logger.error(f"Error al obtener valores de atributos del producto: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        })

# API para obtener avatares dinámicamente
@require_GET
def api_get_avatars(request):
    """Devuelve todos los avatares disponibles en la carpeta static/avatars"""
    try:
        avatars_path = os.path.join(settings.BASE_DIR, 'ecommerce_app', 'static', 'avatars')
        avatars = []
        
        if os.path.exists(avatars_path):
            # Extensiones de imagen permitidas
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.svg', '.gif', '.webp'}
            
            for filename in os.listdir(avatars_path):
                file_path = os.path.join(avatars_path, filename)
                if os.path.isfile(file_path):
                    # Verificar si es una imagen
                    _, ext = os.path.splitext(filename.lower())
                    if ext in allowed_extensions:
                        # Generar nombre amigable (sin extensión y capitalizado)
                        name = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ').title()
                        
                        avatars.append({
                            'filename': filename,
                            'path': f'avatars/{filename}',
                            'name': name
                        })
            
            # Ordenar alfabéticamente por nombre
            avatars.sort(key=lambda x: x['name'])
        
        return JsonResponse({
            'success': True,
            'avatars': avatars
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        })

# Vista para la página Sobre Nosotros
def sobre_nosotros(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            account_type = request.session.get('account_type', 'usuario')
            
            # Buscar empresa asociada para usuarios
            empresa_nombre = None
            if account_type == 'usuario':
                try:
                    empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                    if empresa_obj:
                        empresa_nombre = empresa_obj.nombre_empresa
                except Exception as e:
                    empresa_nombre = None
            elif account_type == 'empresa':
                empresa_nombre = current_user.nombre_empresa
            
            user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
            # Para sobre nosotros, usar el avatar por defecto del chatbot
            user_info['avatar_chatbot'] = 'avatars/Cartoon Style Robot.jpg'
    
    return render(request, 'ecommerce_app/sobre_nosotros.html', {'user_info': user_info})

# Vista para la página de Términos y Condiciones
def condiciones(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            account_type = request.session.get('account_type', 'usuario')
            
            # Buscar empresa asociada para usuarios
            empresa_nombre = None
            if account_type == 'usuario':
                try:
                    empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                    if empresa_obj:
                        empresa_nombre = empresa_obj.nombre_empresa
                except Exception as e:
                    empresa_nombre = None
            elif account_type == 'empresa':
                empresa_nombre = current_user.nombre_empresa
            
            user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
    
    return render(request, 'ecommerce_app/condiciones.html', {'user_info': user_info})

# Vista para la página de Preguntas Frecuentes
def faq(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            account_type = request.session.get('account_type', 'usuario')
            
            # Buscar empresa asociada para usuarios
            empresa_nombre = None
            if account_type == 'usuario':
                try:
                    empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                    if empresa_obj:
                        empresa_nombre = empresa_obj.nombre_empresa
                except Exception as e:
                    empresa_nombre = None
            elif account_type == 'empresa':
                empresa_nombre = current_user.nombre_empresa
            
            user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
    
    return render(request, 'ecommerce_app/faq.html', {'user_info': user_info})

# Vista para la página de Contacto
def contactos(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            account_type = request.session.get('account_type', 'usuario')
            
            # Buscar empresa asociada para usuarios
            empresa_nombre = None
            if account_type == 'usuario':
                try:
                    empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                    if empresa_obj:
                        empresa_nombre = empresa_obj.nombre_empresa
                except Exception as e:
                    empresa_nombre = None
            elif account_type == 'empresa':
                empresa_nombre = current_user.nombre_empresa
            
            user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
    
    return render(request, 'ecommerce_app/contactos.html', {'user_info': user_info})

# Vista para la página de Políticas de Privacidad
def politicas_privacidad(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    if is_user_authenticated(request):
        current_user = get_current_user(request)
        if current_user:
            account_type = request.session.get('account_type', 'usuario')
            
            # Buscar empresa asociada para usuarios
            empresa_nombre = None
            if account_type == 'usuario':
                try:
                    empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                    if empresa_obj:
                        empresa_nombre = empresa_obj.nombre_empresa
                except Exception as e:
                    empresa_nombre = None
            elif account_type == 'empresa':
                empresa_nombre = current_user.nombre_empresa
            
            user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
    
    return render(request, 'ecommerce_app/politicas_privacidad.html', {'user_info': user_info})


def editar_perfil_usuario(request, usuario_id):
    '''Vista para editar el perfil de un usuario'''
    try:
        usuario_obj = usuario.objects.get(id_usuario=usuario_id)
    except usuario.DoesNotExist:
        return redirect('index')

    # Comprobar autenticación y obtener current_user de forma segura
    current_user = get_current_user(request)
    if not current_user:
        logger.info(f"editar_perfil_usuario: usuario no autenticado (session keys: {list(request.session.keys())})")
        return redirect('/ecommerce/iniciar_sesion/')

    # Obtener user_info para la barra de navegación (ahora current_user está garantizado)
    account_type = request.session.get('account_type', 'usuario')
    user_info = get_user_info_with_avatar(current_user, account_type)

    # Verificar que el usuario autenticado corresponde al perfil que se intenta editar
    if not hasattr(current_user, 'id_usuario') or current_user.id_usuario != usuario_obj.id_usuario:
        logger.info(f"editar_perfil_usuario: intento de editar perfil ajeno. current_user.id: {getattr(current_user, 'id_usuario', None)}, target: {usuario_obj.id_usuario}")
        return redirect('perfil_usuario')

    if request.method == 'POST':
        try:
            # Procesar formulario
            nombre_usuario = request.POST.get('nombre_usuario')
            telefono_usuario = request.POST.get('telefono_usuario')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            pais = request.POST.get('pais')
            estado = request.POST.get('estado')
            avatar_chatbot = request.POST.get('avatar_chatbot')
            
            # Actualizar campos
            if nombre_usuario:
                usuario_obj.nombre_usuario = nombre_usuario
            if telefono_usuario is not None:
                usuario_obj.telefono_usuario = telefono_usuario
            if fecha_nacimiento:
                usuario_obj.fecha_nacimiento = fecha_nacimiento
            if pais:
                usuario_obj.pais = pais
            if estado:
                usuario_obj.estado = estado
            if avatar_chatbot:
                usuario_obj.avatar_chatbot = avatar_chatbot
            
            # Procesar foto si se subió
            if 'foto_usuario' in request.FILES:
                usuario_obj.foto_usuario = request.FILES['foto_usuario']
            
            usuario_obj.save()

            # Si la petición viene por AJAX, devolver JSON para que el frontend muestre un SweetAlert y no haga redirect
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                resp = {'success': True, 'message': 'Perfil actualizado correctamente.'}
                try:
                    if usuario_obj.foto_usuario and hasattr(usuario_obj.foto_usuario, 'url'):
                        resp['foto_url'] = usuario_obj.foto_usuario.url
                except Exception:
                    pass
                try:
                    resp['avatar_chatbot'] = usuario_obj.avatar_chatbot or ''
                except Exception:
                    resp['avatar_chatbot'] = ''
                    # También procesar metodos de pago si vienen en el formulario (compatibilidad con UI nueva)
                    metodos_debug_extra = None
                    try:
                        metodos_json = request.POST.get('metodos_pago_json')
                        if metodos_json:
                            import json
                            from .models import MetodoPago

                            metodos_procesados = 0
                            metodos_creados = 0
                            metodos_actualizados = 0
                            metodos_eliminados = 0

                            try:
                                metodos_list = json.loads(metodos_json) if metodos_json else []
                                if not isinstance(metodos_list, list):
                                    metodos_list = []
                            except Exception:
                                metodos_list = []

                            existentes = MetodoPago.objects.filter(usuario=usuario_obj)
                            existentes_map = {str(m.id_metodo): m for m in existentes}
                            recibidos_ids = []

                            for m in metodos_list:
                                try:
                                    metodos_procesados += 1
                                    mid = m.get('id')
                                    if mid and str(mid) in existentes_map:
                                        mp = existentes_map[str(mid)]
                                        metodos_actualizados += 1
                                    else:
                                        mp = MetodoPago(usuario=usuario_obj)
                                        metodos_creados += 1

                                    mp.tipo = m.get('tipo') or (mp.tipo if hasattr(mp, 'tipo') else '')
                                    mp.activo = True
                                    mp.instrucciones = m.get('instrucciones') or ''
                                    mp.nombre_beneficiario = m.get('nombre_beneficiario') or ''
                                    mp.numero_cuenta = m.get('numero_cuenta') or ''
                                    mp.banco = m.get('banco') or ''
                                    mp.tipo_cuenta = m.get('tipo_cuenta') or ''
                                    mp.identificador = m.get('identificador') or ''
                                    dato_add = m.get('datos_adicionales')
                                    if dato_add:
                                        try:
                                            mp.datos_adicionales = dato_add
                                        except Exception:
                                            mp.datos_adicionales = None

                                    mp.save()
                                    if mp.id_metodo:
                                        recibidos_ids.append(mp.id_metodo)
                                except Exception:
                                    # continuar con los demás métodos en caso de fallo individual
                                    logger.exception('Error procesando metodo de pago para usuario')

                            if recibidos_ids:
                                qs_before = MetodoPago.objects.filter(usuario=usuario_obj)
                                to_delete_qs = qs_before.exclude(id_metodo__in=recibidos_ids)
                                metodos_eliminados = to_delete_qs.count()
                                to_delete_qs.delete()

                            metodos_debug_extra = {
                                'metodos_procesados': metodos_procesados,
                                'metodos_creados': metodos_creados,
                                'metodos_actualizados': metodos_actualizados,
                                'metodos_eliminados': metodos_eliminados
                            }
                    except Exception:
                        logger.exception('Error procesando metodos_pago_json en editar_perfil_usuario')

                    if metodos_debug_extra:
                        try:
                            resp.update(metodos_debug_extra)
                        except Exception:
                            pass

                    return JsonResponse(resp)

            return redirect('perfil_usuario')
            
        except Exception as e:
            # Si es AJAX, devolver JSON con error
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Error al actualizar perfil: {str(e)}'})
            return render(request, 'ecommerce_app/editar_perfil_usuario.html',
                         {'usuario': usuario_obj, 'user_info': user_info, 'error': f'Error al actualizar perfil: {str(e)}'})
            
    else:
        # GET request - mostrar formulario
        # Preload one MetodoPago per tipo to prefill the template sections (same UX as empresa)
        try:
            from .models import MetodoPago
            transferencia = MetodoPago.objects.filter(usuario=usuario_obj, tipo='transferencia').first()
            pago_movil = MetodoPago.objects.filter(usuario=usuario_obj, tipo='pago_movil').first()
            paypal = MetodoPago.objects.filter(usuario=usuario_obj, tipo='paypal').first()
        except Exception:
            transferencia = None
            pago_movil = None
            paypal = None

        return render(request, 'ecommerce_app/editar_perfil_usuario.html', {'usuario': usuario_obj, 'user_info': user_info, 'transferencia': transferencia, 'pago_movil': pago_movil, 'paypal': paypal})



def editar_perfil_empresa(request, empresa_id):
    '''Vista para editar el perfil de una empresa'''
    try:
        empresa_obj = empresa.objects.get(id_empresa=empresa_id)
    except empresa.DoesNotExist:
        return redirect('index')

    # Obtener user_info para la barra de navegación
    account_type = request.session.get('account_type', 'empresa')
    user_info = get_user_info_with_avatar(get_current_user(request), account_type)

    current_user = get_current_user(request)
    if not current_user or not hasattr(current_user, 'id_empresa') or current_user.id_empresa != empresa_obj.id_empresa:
        return redirect('perfil_empresa')

    if request.method == 'POST':
        try:
            # Procesar formulario
            nombre_empresa = request.POST.get('nombre_empresa')
            descripcion_empresa = request.POST.get('descripcion_empresa')
            tipo_empresa = request.POST.get('tipo_empresa')
            sector_empresa = request.POST.get('sector_empresa')
            pais_empresa = request.POST.get('pais_empresa')
            estado_empresa = request.POST.get('estado_empresa')
            direccion_empresa = request.POST.get('direccion_empresa')
            avatar_chatbot_empresa = request.POST.get('avatar_chatbot_empresa')
            
            # Actualizar campos
            if nombre_empresa:
                empresa_obj.nombre_empresa = nombre_empresa
            if descripcion_empresa is not None:
                empresa_obj.descripcion_empresa = descripcion_empresa
            if tipo_empresa:
                empresa_obj.tipo_empresa = tipo_empresa
            if sector_empresa is not None:
                empresa_obj.sector_empresa = sector_empresa
            if pais_empresa:
                empresa_obj.pais_empresa = pais_empresa
            if estado_empresa:
                empresa_obj.estado_empresa = estado_empresa
            if direccion_empresa:
                empresa_obj.direccion_empresa = direccion_empresa
            if avatar_chatbot_empresa:
                empresa_obj.avatar_chatbot_empresa = avatar_chatbot_empresa
            
            # Procesar logo si se subió
            if 'logo_empresa' in request.FILES:
                empresa_obj.logo_empresa = request.FILES['logo_empresa']
            
            empresa_obj.save()
            # Procesar métodos de pago enviados como JSON (mejor logging y feedback)
            metodos_procesados = 0
            metodos_creados = 0
            metodos_actualizados = 0
            metodos_eliminados = 0
            metodos_error = None
            metodos_raw = None
            try:
                metodos_json = request.POST.get('metodos_pago_json')
                if metodos_json:
                    import json
                    from .models import MetodoPago

                    metodos_raw = metodos_json[:2000]
                    try:
                        metodos_list = json.loads(metodos_json)
                        if not isinstance(metodos_list, list):
                            metodos_list = []
                    except Exception as ex:
                        metodos_list = []
                        metodos_error = f'JSON parse error: {str(ex)}'

                    # Mapear métodos existentes por id
                    existentes = MetodoPago.objects.filter(empresa=empresa_obj)
                    existentes_map = {str(m.id_metodo): m for m in existentes}
                    recibidos_ids = []

                    for m in metodos_list:
                        try:
                            mid = m.get('id')
                            if mid and str(mid) in existentes_map:
                                mp = existentes_map[str(mid)]
                                metodos_actualizados += 1
                            else:
                                mp = MetodoPago(empresa=empresa_obj)
                                metodos_creados += 1

                            mp.tipo = m.get('tipo') or (mp.tipo if hasattr(mp, 'tipo') else '')
                            mp.activo = True
                            mp.instrucciones = m.get('instrucciones') or ''
                            mp.nombre_beneficiario = m.get('nombre_beneficiario') or ''
                            mp.numero_cuenta = m.get('numero_cuenta') or ''
                            mp.banco = m.get('banco') or ''
                            mp.tipo_cuenta = m.get('tipo_cuenta') or ''
                            mp.identificador = m.get('identificador') or ''
                            dato_add = m.get('datos_adicionales')
                            if dato_add:
                                try:
                                    mp.datos_adicionales = dato_add
                                except Exception:
                                    mp.datos_adicionales = None

                            mp.save()
                            metodos_procesados += 1
                            if mp.id_metodo:
                                recibidos_ids.append(mp.id_metodo)
                        except Exception as ex_item:
                            # Registrar el error pero continuar con los demás
                            logger.exception(f"Error procesando metodo individual: {ex_item}")

                    # Eliminar métodos que no vinieron en la lista (si aplica)
                    if recibidos_ids:
                        qs_before = MetodoPago.objects.filter(empresa=empresa_obj)
                        to_delete_qs = qs_before.exclude(id_metodo__in=recibidos_ids)
                        metodos_eliminados = to_delete_qs.count()
                        to_delete_qs.delete()

            except Exception as ex:
                metodos_error = str(ex)
                logger.exception(f"Error procesando metodos_pago_json: {ex}")

            # Adjuntar info de debug a la respuesta AJAX si existe
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Preparar campos adicionales en la respuesta (no sensibles)
                extra = {
                    'metodos_procesados': metodos_procesados,
                    'metodos_creados': metodos_creados,
                    'metodos_actualizados': metodos_actualizados,
                    'metodos_eliminados': metodos_eliminados,
                }
                if metodos_error:
                    extra['metodos_error'] = metodos_error
                if metodos_raw:
                    extra['metodos_raw_preview'] = metodos_raw
                # Guardar en resp más abajo (añadiremos esto al resp existente)
                # Para facilidad, lo retornamos en el resp que se genera más abajo
                # Guardamos en la variable local para usar después
                metodos_debug_extra = extra
            # Si es AJAX, devolver JSON con datos de éxito y URLs relevantes
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                resp = {'success': True, 'message': 'Perfil de empresa actualizado correctamente.'}
                try:
                    if empresa_obj.logo_empresa and hasattr(empresa_obj.logo_empresa, 'url'):
                        resp['logo_url'] = empresa_obj.logo_empresa.url
                except Exception:
                    pass
                try:
                    resp['avatar_chatbot_empresa'] = empresa_obj.avatar_chatbot_empresa or ''
                except Exception:
                    resp['avatar_chatbot_empresa'] = ''
                # Añadir debug info de métodos si existe
                if 'metodos_debug_extra' in locals():
                    try:
                        resp.update(metodos_debug_extra)
                    except Exception:
                        pass
                return JsonResponse(resp)

            return redirect('perfil_empresa')

        except Exception as e:
            # Si es AJAX, devolver JSON con error
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Error al actualizar perfil: {str(e)}'})
            return render(request, 'ecommerce_app/editar_perfil_empresa.html',
                         {'empresa': empresa_obj, 'user_info': user_info, 'error': f'Error al actualizar perfil: {str(e)}'})
            
    else:
        # GET request - mostrar formulario
        return render(request, 'ecommerce_app/editar_perfil_empresa.html', {'empresa': empresa_obj, 'user_info': user_info})


@require_POST
def guardar_metodo_pago_ajax(request):
    """Guarda o actualiza un MetodoPago vía AJAX. Espera campos POST:
       id (opcional), tipo, instrucciones, nombre_beneficiario, numero_cuenta, banco, tipo_cuenta, identificador
    """
    try:
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado'})

        # Determinar si la sesión es empresa o usuario y usar la FK correspondiente
        account_type = request.session.get('account_type', 'usuario')
        empresa_obj = None
        usuario_obj = None
        if account_type == 'empresa' and hasattr(current_user, 'id_empresa'):
            empresa_obj = current_user
        elif account_type == 'usuario' and hasattr(current_user, 'id_usuario'):
            usuario_obj = current_user
        else:
            return JsonResponse({'success': False, 'message': 'Tipo de cuenta no válido para guardar métodos'})

        # Obtener campos: soportar JSON en el body (fetch con application/json) o form-encoded
        data = {}
        try:
            if request.content_type and 'application/json' in request.content_type:
                import json
                data = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            data = {}

        # Fallback a request.POST si no viene en JSON
        if not data:
            data = request.POST

        # Obtener campos
        mid = data.get('id') or data.get('id_metodo')
        tipo = data.get('tipo')
        instrucciones = data.get('instrucciones') or ''
        nombre_beneficiario = data.get('nombre_beneficiario') or ''
        numero_cuenta = data.get('numero_cuenta') or ''
        banco = data.get('banco') or ''
        tipo_cuenta = data.get('tipo_cuenta') or ''
        identificador = data.get('identificador') or ''

        # Validaciones por tipo
        errores = {}
        if tipo == 'pago_movil':
            if not identificador or not str(identificador).strip():
                errores['identificador'] = 'El identificador (Cédula/RIF/Teléfono) es obligatorio para Pago Móvil.'
            if not banco or not str(banco).strip():
                errores['banco'] = 'El banco es obligatorio para Pago Móvil.'
            if not numero_cuenta or not str(numero_cuenta).strip():
                errores['numero_cuenta'] = 'El número de cuenta es obligatorio para Pago Móvil.'

        # (Opcional) validación general para transferencia
        if tipo == 'transferencia':
            if not nombre_beneficiario or not str(nombre_beneficiario).strip():
                errores['nombre_beneficiario'] = 'El nombre del beneficiario es obligatorio para Transferencia.'
            if not numero_cuenta or not str(numero_cuenta).strip():
                errores['numero_cuenta'] = 'El número de cuenta es obligatorio para Transferencia.'
            if not banco or not str(banco).strip():
                errores['banco'] = 'El banco es obligatorio para Transferencia.'
            if not tipo_cuenta or not str(tipo_cuenta).strip():
                errores['tipo_cuenta'] = 'El tipo de cuenta es obligatorio para Transferencia.'

        if errores:
            return JsonResponse({'success': False, 'message': 'Faltan campos requeridos', 'errors': errores})

        from .models import MetodoPago

        if mid:
            try:
                if empresa_obj:
                    mp = MetodoPago.objects.get(id_metodo=mid, empresa=empresa_obj)
                else:
                    mp = MetodoPago.objects.get(id_metodo=mid, usuario=usuario_obj)
                creado = False
            except MetodoPago.DoesNotExist:
                if empresa_obj:
                    mp = MetodoPago(empresa=empresa_obj)
                else:
                    mp = MetodoPago(usuario=usuario_obj)
                creado = True
        else:
            if empresa_obj:
                mp = MetodoPago(empresa=empresa_obj)
            else:
                mp = MetodoPago(usuario=usuario_obj)
            creado = True

        if tipo:
            mp.tipo = tipo
        mp.instrucciones = instrucciones
        mp.nombre_beneficiario = nombre_beneficiario
        mp.numero_cuenta = numero_cuenta
        mp.banco = banco
        mp.tipo_cuenta = tipo_cuenta
        mp.identificador = identificador
        mp.activo = True

        mp.save()

        return JsonResponse({'success': True, 'message': 'Método guardado', 'id_metodo': mp.id_metodo, 'creado': creado})
    except Exception as e:
        logger.exception(f"Error en guardar_metodo_pago_ajax: {e}")
        return JsonResponse({'success': False, 'message': f'Error guardando método: {str(e)}'})

# =====================================================
# VISTAS PARA MIS VENTAS (SERVICIOS)
# =====================================================

@require_login
def servicios_ventas_pendientes(request):
    """
    Vista para mostrar los servicios pendientes de cotización donde el usuario/empresa es el proveedor.
    """
    try:
        logger.info("servicios_ventas_pendientes - Iniciando función")
        current_user = get_current_user(request)
        logger.info(f"servicios_ventas_pendientes - current_user: {current_user}")
        
        if not current_user:
            logger.error("servicios_ventas_pendientes - No current_user found")
            return redirect('/ecommerce/iniciar_sesion/')
        
        # Obtener account_type de la sesión
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"servicios_ventas_pendientes - account_type: {account_type}")
        servicios_pendientes = []
        
        logger.info("servicios_ventas_pendientes - Iniciando consultas a la base de datos")
        
        if account_type == 'usuario':
            # Solicitudes donde otros usuarios/empresas solicitan servicios de este usuario
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado='pendiente'
            ).select_related('id_usuario_fk', 'id_servicio_usuario_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado='pendiente'
            ).select_related('id_empresa_fk', 'id_servicio_usuario_fk')
            
            logger.info(f"servicios_ventas_pendientes - solicitudes_usuario count: {solicitudes_usuario.count()}")
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                logger.info(f"Procesando solicitud de usuario: {solicitud.id_solicitud_servicio_usuario}")
                servicio_obj = safe_get(solicitud, 'id_servicio_usuario_fk', None)
                cliente_nombre = safe_get(solicitud, 'id_usuario_fk.nombre_usuario', 'Sin nombre')
                cliente_email = safe_get(solicitud, 'id_usuario_fk.correo_usuario', 'Sin email')
                cliente_telefono = safe_get(solicitud, 'id_usuario_fk.telefono_usuario', 'Sin teléfono')
                servicios_pendientes.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': safe_get(servicio_obj, 'nombre_servicio_usuario', 'Sin nombre'),
                    'servicio_nombre': safe_get(servicio_obj, 'nombre_servicio_usuario', 'Sin nombre'),
                    'servicio_precio': safe_get(servicio_obj, 'precio_servicio_usuario', 0),
                    'categoria_servicio': 'Servicio de Usuario',
                    'tipo_cliente': 'usuario',
                    'cliente_nombre': cliente_nombre,
                    'cliente_email': cliente_email,
                    'cliente_telefono': cliente_telefono,
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(servicio_obj),
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
            
            logger.info(f"servicios_ventas_pendientes - solicitudes_empresa count: {solicitudes_empresa.count()}")
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                logger.info(f"Procesando solicitud de empresa: {solicitud.id_solicitud_servicio_empresa}")
                servicio_obj = safe_get(solicitud, 'id_servicio_usuario_fk', None)
                servicios_pendientes.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': safe_get(servicio_obj, 'nombre_servicio_usuario', 'Sin nombre'),
                    'servicio_nombre': safe_get(servicio_obj, 'nombre_servicio_usuario', 'Sin nombre'),
                    'servicio_precio': safe_get(servicio_obj, 'precio_servicio_usuario', 0),
                    'categoria_servicio': 'Servicio de Usuario',
                    'tipo_cliente': 'empresa',
                    'cliente_nombre': safe_get(solicitud, 'id_empresa_fk.nombre_empresa', 'Sin nombre'),
                    'cliente_email': safe_get(solicitud, 'id_empresa_fk.correo_empresa', 'Sin email'),
                    'cliente_telefono': 'No disponible',
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(servicio_obj),
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
        
        elif account_type == 'empresa':
            # Solicitudes donde otros usuarios/empresas solicitan servicios de sucursales de esta empresa
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado='pendiente'
            ).select_related('id_usuario_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado='pendiente'
            ).select_related('id_empresa_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            logger.info(f"servicios_ventas_pendientes - solicitudes_usuario count (empresa): {solicitudes_usuario.count()}")
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                logger.info(f"Empresa - Procesando solicitud de usuario: {solicitud.id_solicitud_servicio_usuario}")
                servicio_sucursal_obj = safe_get(solicitud, 'id_servicio_sucursal_fk', None)
                servicio_empresa_obj = safe_get(servicio_sucursal_obj, 'id_servicio_fk', None)
                servicios_pendientes.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': safe_get(servicio_sucursal_obj, 'nombre_servicio_sucursal', safe_get(servicio_empresa_obj, 'nombre_servicio_empresa', 'Sin nombre')),
                    'servicio_nombre': safe_get(servicio_sucursal_obj, 'nombre_servicio_sucursal', safe_get(servicio_empresa_obj, 'nombre_servicio_empresa', 'Sin nombre')),
                    'servicio_precio': safe_get(servicio_sucursal_obj, 'precio_servicio_sucursal', safe_get(servicio_empresa_obj, 'precio_servicio_empresa', 0)),
                    'categoria_servicio': safe_get(servicio_empresa_obj, 'id_categoria_servicios_fk.nombre_categoria_serv_empresa', 'Sin categoría'),
                    'tipo_cliente': 'usuario',
                    'sucursal_nombre': safe_get(servicio_sucursal_obj, 'id_sucursal_fk.nombre_sucursal', 'Sin sucursal'),
                    'cliente_nombre': safe_get(solicitud, 'id_usuario_fk.nombre_usuario', 'Sin nombre'),
                    'cliente_email': safe_get(solicitud, 'id_usuario_fk.correo_usuario', 'Sin email'),
                    'cliente_telefono': safe_get(solicitud, 'id_usuario_fk.telefono_usuario', 'Sin teléfono'),
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(servicio_empresa_obj),
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
            
            logger.info(f"servicios_ventas_pendientes - solicitudes_empresa count (empresa): {solicitudes_empresa.count()}")
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                logger.info(f"Empresa - Procesando solicitud de empresa: {solicitud.id_solicitud_servicio_empresa}")
                servicio_sucursal_obj = safe_get(solicitud, 'id_servicio_sucursal_fk', None)
                servicio_empresa_obj = safe_get(servicio_sucursal_obj, 'id_servicio_fk', None)
                servicios_pendientes.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': safe_get(servicio_sucursal_obj, 'nombre_servicio_sucursal', safe_get(servicio_empresa_obj, 'nombre_servicio_empresa', 'Sin nombre')),
                    'servicio_nombre': safe_get(servicio_sucursal_obj, 'nombre_servicio_sucursal', safe_get(servicio_empresa_obj, 'nombre_servicio_empresa', 'Sin nombre')),
                    'servicio_precio': safe_get(servicio_sucursal_obj, 'precio_servicio_sucursal', safe_get(servicio_empresa_obj, 'precio_servicio_empresa', 0)),
                    'categoria_servicio': safe_get(servicio_empresa_obj, 'id_categoria_servicios_fk.nombre_categoria_serv_empresa', 'Sin categoría'),
                    'tipo_cliente': 'empresa',
                    'sucursal_nombre': safe_get(servicio_sucursal_obj, 'id_sucursal_fk.nombre_sucursal', 'Sin sucursal'),
                    'cliente_nombre': safe_get(solicitud, 'id_empresa_fk.nombre_empresa', 'Sin nombre'),
                    'cliente_email': safe_get(solicitud, 'id_empresa_fk.correo_empresa', 'Sin email'),
                    'cliente_telefono': 'No disponible',
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(servicio_empresa_obj),
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
        
        # Ordenar por fecha de solicitud (más recientes primero)
        servicios_pendientes.sort(key=lambda x: x['fecha_solicitud'], reverse=True)
        
        # Obtener información del usuario para el template
        empresa_nombre = None
        if account_type == 'usuario':
            try:
                empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                if empresa_obj:
                    empresa_nombre = empresa_obj.nombre_empresa
            except Exception as e:
                empresa_nombre = None
        elif account_type == 'empresa':
            empresa_nombre = current_user.nombre_empresa
        
        user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'servicios_pendientes': servicios_pendientes,
            'total_servicios': len(servicios_pendientes)
        }
        
        return render(request, 'ecommerce_app/servicios_ventas_pendientes.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en servicios_ventas_pendientes: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return render(request, 'ecommerce_app/error.html', {'error_message': f'Error al cargar servicios pendientes: {str(e)}'})

@require_login
def servicios_ventas_confirmadas(request):
    """
    Vista para mostrar los servicios confirmados/completados donde el usuario/empresa es el proveedor.
    """
    try:
        current_user = get_current_user(request)
        logger.info(f"servicios_ventas_confirmadas - current_user: {current_user}")
        
        if not current_user:
            logger.error("servicios_ventas_confirmadas - No current_user found")
            return redirect('/ecommerce/iniciar_sesion/')
        
        # Obtener account_type de la sesión
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"servicios_ventas_confirmadas - account_type: {account_type}")
        servicios_confirmados = []
        
        if account_type == 'usuario':
            # Solicitudes confirmadas donde otros usuarios/empresas solicitan servicios de este usuario
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado__in=['aceptada', 'pagada', 'completada']
            ).select_related('id_usuario_fk', 'id_servicio_usuario_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado__in=['aceptada', 'pagada', 'completada']
            ).select_related('id_empresa_fk', 'id_servicio_usuario_fk')
            
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                servicio_obj = safe_get(solicitud, 'id_servicio_usuario_fk', None)
                # Debug: log service object and candidate names
                name_candidate_1 = safe_get(servicio_obj, 'nombre_servicio_usuario', None)
                name_candidate_2 = safe_get(servicio_obj, 'nombre_servicio_empresa', None)
                logger.info(f"servicios_confirmados(usuario) - solicitud {getattr(solicitud, 'id_solicitud_servicio_usuario', '?')}: servicio_obj={servicio_obj!r}, name1={name_candidate_1}, name2={name_candidate_2}")
                # Resolve name from solicitud model
                resolved_name = resolve_service_name_strict(solicitud) or name_candidate_1 or name_candidate_2 or 'Servicio sin nombre'
                servicios_confirmados.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': resolved_name,
                    'servicio_nombre': resolved_name,
                    'precio_servicio': safe_get(servicio_obj, 'precio_servicio_usuario', 0),
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(servicio_obj),
                    'categoria_servicio': safe_get(servicio_obj, 'id_categoria_servicios_fk.nombre_categoria_serv_usuario', 'Sin categoría'),
                    'tipo_cliente': 'usuario',
                    'nombre_cliente': safe_get(solicitud, 'id_usuario_fk.nombre_usuario', 'Sin nombre'),
                    'cliente_nombre': safe_get(solicitud, 'id_usuario_fk.nombre_usuario', 'Sin nombre'),
                    'email_cliente': safe_get(solicitud, 'id_usuario_fk.correo_usuario', 'Sin email'),
                    'cliente_email': safe_get(solicitud, 'id_usuario_fk.correo_usuario', 'Sin email'),
                    'telefono_cliente': safe_get(solicitud, 'id_usuario_fk.telefono_usuario', 'No proporcionado'),
                    'cliente_telefono': safe_get(solicitud, 'id_usuario_fk.telefono_usuario', 'No proporcionado'),
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
            
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                servicio_obj = safe_get(solicitud, 'id_servicio_usuario_fk', None)
                name_candidate_1 = safe_get(servicio_obj, 'nombre_servicio_usuario', None)
                name_candidate_2 = safe_get(servicio_obj, 'nombre_servicio_empresa', None)
                logger.info(f"servicios_confirmados(empresa->usuario) - solicitud {getattr(solicitud, 'id_solicitud_servicio_empresa', '?')}: servicio_obj={servicio_obj!r}, name1={name_candidate_1}, name2={name_candidate_2}")
                resolved_name = resolve_service_name_strict(solicitud) or name_candidate_1 or name_candidate_2 or 'Servicio sin nombre'
                servicios_confirmados.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': resolved_name,
                    'servicio_nombre': resolved_name,
                    'precio_servicio': safe_get(servicio_obj, 'precio_servicio_usuario', 0),
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(servicio_obj),
                    'categoria_servicio': safe_get(servicio_obj, 'id_categoria_servicios_fk.nombre_categoria_serv_usuario', 'Sin categoría'),
                    'tipo_cliente': 'empresa',
                    'nombre_cliente': safe_get(solicitud, 'id_empresa_fk.nombre_empresa', 'Sin nombre'),
                    'cliente_nombre': safe_get(solicitud, 'id_empresa_fk.nombre_empresa', 'Sin nombre'),
                    'email_cliente': safe_get(solicitud, 'id_empresa_fk.correo_empresa', 'Sin email'),
                    'cliente_email': safe_get(solicitud, 'id_empresa_fk.correo_empresa', 'Sin email'),
                    'telefono_cliente': 'No disponible',
                    'cliente_telefono': 'No disponible',
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
        
        elif account_type == 'empresa':
            # Solicitudes confirmadas donde otros usuarios/empresas solicitan servicios de sucursales de esta empresa
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado__in=['aceptada', 'pagada', 'completada']
            ).select_related('id_usuario_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado__in=['aceptada', 'pagada', 'completada']
            ).select_related('id_empresa_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                servicio_obj = safe_get(solicitud, 'id_servicio_sucursal_fk', None)
                servicio_empresa_obj = safe_get(servicio_obj, 'id_servicio_fk', None)
                name_sucursal = safe_get(servicio_obj, 'nombre_servicio_sucursal', None)
                name_empresa = safe_get(servicio_empresa_obj, 'nombre_servicio_empresa', None)
                # Prefer the empresa-level service name when present (servicio_sucursal -> id_servicio_fk)
                resolved_name = name_empresa or name_sucursal or 'Servicio sin nombre'
                logger.info(f"servicios_confirmados(empresa->sucursal usuario) - solicitud {getattr(solicitud, 'id_solicitud_servicio_usuario', '?')}: sucursal_obj={servicio_obj!r}, empresa_obj={servicio_empresa_obj!r}, name_sucursal={name_sucursal}, name_empresa={name_empresa}, resolved_name={resolved_name}")
                servicios_confirmados.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': resolved_name,
                    'servicio_nombre': resolved_name,
                    'precio_servicio': safe_get(servicio_obj, 'precio_servicio_sucursal', 0),
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(safe_get(servicio_obj, 'id_servicio_fk', None)),
                    'categoria_servicio': safe_get(servicio_obj, 'id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa', 'Sin categoría'),
                    'tipo_cliente': 'usuario',
                    'nombre_cliente': safe_get(solicitud, 'id_usuario_fk.nombre_usuario', 'Sin nombre'),
                    'cliente_nombre': safe_get(solicitud, 'id_usuario_fk.nombre_usuario', 'Sin nombre'),
                    'email_cliente': safe_get(solicitud, 'id_usuario_fk.correo_usuario', 'Sin email'),
                    'cliente_email': safe_get(solicitud, 'id_usuario_fk.correo_usuario', 'Sin email'),
                    'telefono_cliente': safe_get(solicitud, 'id_usuario_fk.telefono_usuario', 'No proporcionado'),
                    'cliente_telefono': safe_get(solicitud, 'id_usuario_fk.telefono_usuario', 'No proporcionado'),
                    'sucursal_nombre': safe_get(servicio_obj, 'id_sucursal_fk.nombre_sucursal', 'Sin sucursal'),
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
            
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                servicio_obj = safe_get(solicitud, 'id_servicio_sucursal_fk', None)
                servicio_empresa_obj = safe_get(servicio_obj, 'id_servicio_fk', None)
                name_sucursal = safe_get(servicio_obj, 'nombre_servicio_sucursal', None)
                name_empresa = safe_get(servicio_empresa_obj, 'nombre_servicio_empresa', None)
                # Prefer empresa-level name when present
                resolved_name = name_empresa or name_sucursal or 'Servicio sin nombre'
                logger.info(f"servicios_confirmados(empresa->sucursal empresa) - solicitud {getattr(solicitud, 'id_solicitud_servicio_empresa', '?')}: sucursal_obj={servicio_obj!r}, empresa_obj={servicio_empresa_obj!r}, name_sucursal={name_sucursal}, name_empresa={name_empresa}, resolved_name={resolved_name}")
                servicios_confirmados.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': resolved_name,
                    'servicio_nombre': resolved_name,
                    'precio_servicio': safe_get(servicio_obj, 'precio_servicio_sucursal', 0),
                    'presupuesto': safe_get(solicitud, 'presupuesto_cotizacion', None),
                    'descripcion_cotizacion': safe_get(solicitud, 'descripcion_cotizacion', None),
                    'fecha_aceptacion': safe_get(solicitud, 'fecha_cotizacion', None),
                    'imagenes': collect_service_images(safe_get(servicio_obj, 'id_servicio_fk', None)),
                    'categoria_servicio': safe_get(servicio_obj, 'id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa', 'Sin categoría'),
                    'tipo_cliente': 'empresa',
                    'nombre_cliente': safe_get(solicitud, 'id_empresa_fk.nombre_empresa', 'Sin nombre'),
                    'cliente_nombre': safe_get(solicitud, 'id_empresa_fk.nombre_empresa', 'Sin nombre'),
                    'email_cliente': safe_get(solicitud, 'id_empresa_fk.correo_empresa', 'Sin email'),
                    'cliente_email': safe_get(solicitud, 'id_empresa_fk.correo_empresa', 'Sin email'),
                    'telefono_cliente': 'No disponible',
                    'cliente_telefono': 'No disponible',
                    'sucursal_nombre': safe_get(servicio_obj, 'id_sucursal_fk.nombre_sucursal', 'Sin sucursal'),
                    'ubicacion': safe_get(solicitud, 'direccion', None),
                })
        
        # Ordenar por fecha de solicitud (más recientes primero)
        # Algunos registros pueden tener fecha_solicitud nula o de tipo distinto; usar un key seguro
        servicios_confirmados.sort(
            key=lambda x: (
                x.get('fecha_solicitud').timestamp()
                if x.get('fecha_solicitud') and hasattr(x.get('fecha_solicitud'), 'timestamp')
                else 0
            ),
            reverse=True
        )
        
        # Obtener información del usuario para el template
        empresa_nombre = None
        if account_type == 'usuario':
            try:
                empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                if empresa_obj:
                    empresa_nombre = empresa_obj.nombre_empresa
            except Exception as e:
                empresa_nombre = None
        elif account_type == 'empresa':
            empresa_nombre = current_user.nombre_empresa
        
        user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
        # Post-procesado: asegurar que cada entrada tenga 'nombre_servicio' útil
        for s in servicios_confirmados:
            if not s.get('nombre_servicio') or s.get('nombre_servicio') == 'Sin nombre':
                resolved = resolve_service_name_from_solicitud(safe_get(s, 'solicitud_obj', s)) if False else None
                # resolve_service_name_from_solicitud espera una solicitud model; we try candidates directly
                if not resolved:
                    # Try some direct fields that might be present in the dict
                    for candidate in ('servicio_nombre', 'nombre_servicio', 'precio_servicio'):
                        val = s.get(candidate)
                        if val and val != 'Sin nombre':
                            resolved = val
                            break
                if not resolved:
                    resolved = 'Servicio sin nombre'
                s['nombre_servicio'] = resolved

        context = {
            'user_info': user_info,
            'servicios_confirmados': servicios_confirmados,
            'total_servicios': len(servicios_confirmados)
        }
        
        return render(request, 'ecommerce_app/servicios_ventas_confirmadas.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en servicios_ventas_confirmadas: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return render(request, 'ecommerce_app/error.html', {'error_message': 'Error al cargar servicios confirmados'})

@require_login
def servicios_ventas_rechazadas(request):
    """
    Vista para mostrar los servicios rechazados donde el usuario/empresa es el proveedor.
    """
    try:
        current_user = get_current_user(request)
        logger.info(f"servicios_ventas_rechazadas - current_user: {current_user}")
        
        if not current_user:
            logger.error("servicios_ventas_rechazadas - No current_user found")
            return redirect('/ecommerce/iniciar_sesion/')
        
        # Obtener account_type de la sesión
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"servicios_ventas_rechazadas - account_type: {account_type}")
        servicios_rechazados = []
        
        if account_type == 'usuario':
            # Solicitudes rechazadas donde otros usuarios/empresas solicitan servicios de este usuario
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado='rechazada'
            ).select_related('id_usuario_fk', 'id_servicio_usuario_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado='rechazada'
            ).select_related('id_empresa_fk', 'id_servicio_usuario_fk')
            
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                # Resolvers seguros para campos que pueden ser null
                svc_user = solicitud.id_servicio_usuario_fk
                svc_sucursal = solicitud.id_servicio_sucursal_fk
                servicio_nombre = None
                servicio_precio = None
                categoria_servicio = None
                sucursal_nombre = None
                imagenes = []

                if svc_user:
                    # Preferir nombre_servicio_usuario y como fallback nombre_servicio_empresa
                    servicio_nombre = getattr(svc_user, 'nombre_servicio_usuario', None) or getattr(svc_user, 'nombre_servicio_empresa', None)
                    servicio_precio = getattr(svc_user, 'precio_servicio_usuario', None)
                    categoria_servicio = getattr(getattr(svc_user, 'id_categoria_servicios_fk', None), 'nombre_categoria_serv_usuario', None) or 'Sin categoría'
                    imagenes = collect_service_images(svc_user)
                elif svc_sucursal:
                    # Para sucursal, intentar nombre en la sucursal primero; luego en el servicio empresa asociado
                    servicio_nombre = getattr(svc_sucursal, 'nombre_servicio_sucursal', None)
                    if not servicio_nombre:
                        servicio_nombre = safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_empresa', None) or safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_usuario', None)
                    servicio_precio = getattr(svc_sucursal, 'precio_servicio_sucursal', None)
                    sucursal_nombre = getattr(getattr(svc_sucursal, 'id_sucursal_fk', None), 'nombre_sucursal', None)
                    # intentar categoría via id_servicio_fk si existe
                    categoria_servicio = safe_get(svc_sucursal, 'id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa', None) or 'Sin categoría'
                    imagenes = collect_service_images(svc_sucursal)

                cliente = solicitud.id_usuario_fk
                servicios_rechazados.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'ubicacion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': servicio_nombre or 'Servicio sin nombre',
                    'servicio_nombre': servicio_nombre or 'Servicio sin nombre',
                    'servicio_precio': servicio_precio,
                    'categoria_servicio': categoria_servicio,
                    'sucursal_nombre': sucursal_nombre,
                    'cliente_nombre': getattr(cliente, 'nombre_usuario', None),
                    'nombre_cliente': getattr(cliente, 'nombre_usuario', None),
                    'cliente_email': getattr(cliente, 'correo_usuario', None),
                    'email_cliente': getattr(cliente, 'correo_usuario', None),
                    'cliente_telefono': getattr(cliente, 'telefono_usuario', None),
                    'telefono_cliente': getattr(cliente, 'telefono_usuario', None),
                    'imagenes': imagenes,
                    'motivo_rechazo': solicitud.motivo_rechazo,
                    'fecha_rechazo': solicitud.fecha_rechazo,
                    'solicitud_obj': solicitud,
                })
                logger.debug(f"servicios_rechazados: appended usuario-solicitud id={solicitud.id_solicitud_servicio_usuario} nombre={servicio_nombre}")
            
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                svc_user = solicitud.id_servicio_usuario_fk
                svc_sucursal = solicitud.id_servicio_sucursal_fk
                servicio_nombre = None
                servicio_precio = None
                categoria_servicio = None
                imagenes = []

                if svc_user:
                    servicio_nombre = getattr(svc_user, 'nombre_servicio_usuario', None) or getattr(svc_user, 'nombre_servicio_empresa', None)
                    servicio_precio = getattr(svc_user, 'precio_servicio_usuario', None)
                    categoria_servicio = getattr(getattr(svc_user, 'id_categoria_servicios_fk', None), 'nombre_categoria_serv_usuario', None) or 'Sin categoría'
                    imagenes = collect_service_images(svc_user)
                elif svc_sucursal:
                    servicio_nombre = getattr(svc_sucursal, 'nombre_servicio_sucursal', None)
                    if not servicio_nombre:
                        servicio_nombre = safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_empresa', None) or safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_usuario', None)
                    servicio_precio = getattr(svc_sucursal, 'precio_servicio_sucursal', None)
                    categoria_servicio = safe_get(svc_sucursal, 'id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa', None) or 'Sin categoría'
                    imagenes = collect_service_images(svc_sucursal)

                cliente = solicitud.id_empresa_fk
                servicios_rechazados.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'ubicacion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': servicio_nombre or 'Servicio sin nombre',
                    'servicio_nombre': servicio_nombre or 'Servicio sin nombre',
                    'servicio_precio': servicio_precio,
                    'categoria_servicio': categoria_servicio,
                    'cliente_nombre': getattr(cliente, 'nombre_empresa', None),
                    'nombre_cliente': getattr(cliente, 'nombre_empresa', None),
                    'cliente_email': getattr(cliente, 'correo_empresa', None),
                    'email_cliente': getattr(cliente, 'correo_empresa', None),
                    'cliente_telefono': 'No disponible',
                    'telefono_cliente': 'No disponible',
                    'imagenes': imagenes,
                    'motivo_rechazo': solicitud.motivo_rechazo,
                    'fecha_rechazo': solicitud.fecha_rechazo,
                    'solicitud_obj': solicitud,
                })
                logger.debug(f"servicios_rechazados: appended empresa-solicitud id={solicitud.id_solicitud_servicio_empresa} nombre={servicio_nombre}")
        
        elif account_type == 'empresa':
            # Solicitudes rechazadas donde otros usuarios/empresas solicitan servicios de sucursales de esta empresa
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado='rechazada'
            ).select_related('id_usuario_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado='rechazada'
            ).select_related('id_empresa_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                svc_sucursal = solicitud.id_servicio_sucursal_fk
                svc_user = solicitud.id_servicio_usuario_fk
                servicio_nombre = None
                servicio_precio = None
                categoria_servicio = None
                sucursal_nombre = None
                imagenes = []

                if svc_sucursal:
                    servicio_nombre = getattr(svc_sucursal, 'nombre_servicio_sucursal', None)
                    if not servicio_nombre:
                        servicio_nombre = safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_empresa', None) or safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_usuario', None)
                    servicio_precio = getattr(svc_sucursal, 'precio_servicio_sucursal', None)
                    sucursal_nombre = getattr(getattr(svc_sucursal, 'id_sucursal_fk', None), 'nombre_sucursal', None)
                    categoria_servicio = safe_get(svc_sucursal, 'id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa', None) or 'Sin categoría'
                    imagenes = collect_service_images(svc_sucursal)
                elif svc_user:
                    servicio_nombre = getattr(svc_user, 'nombre_servicio_usuario', None) or getattr(svc_user, 'nombre_servicio_empresa', None)
                    servicio_precio = getattr(svc_user, 'precio_servicio_usuario', None)
                    categoria_servicio = getattr(getattr(svc_user, 'id_categoria_servicios_fk', None), 'nombre_categoria_serv_usuario', None) or 'Sin categoría'
                    imagenes = collect_service_images(svc_user)

                cliente = solicitud.id_usuario_fk
                servicios_rechazados.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'ubicacion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': servicio_nombre or 'Servicio sin nombre',
                    'servicio_nombre': servicio_nombre or 'Servicio sin nombre',
                    'servicio_precio': servicio_precio,
                    'categoria_servicio': categoria_servicio,
                    'sucursal_nombre': sucursal_nombre,
                    'cliente_nombre': getattr(cliente, 'nombre_usuario', None),
                    'nombre_cliente': getattr(cliente, 'nombre_usuario', None),
                    'cliente_email': getattr(cliente, 'correo_usuario', None),
                    'email_cliente': getattr(cliente, 'correo_usuario', None),
                    'cliente_telefono': getattr(cliente, 'telefono_usuario', None),
                    'telefono_cliente': getattr(cliente, 'telefono_usuario', None),
                    'imagenes': imagenes,
                    'motivo_rechazo': solicitud.motivo_rechazo,
                    'fecha_rechazo': solicitud.fecha_rechazo,
                    'solicitud_obj': solicitud,
                })
                logger.debug(f"servicios_rechazados: appended empresa-account usuario-solicitud id={solicitud.id_solicitud_servicio_usuario} nombre={servicio_nombre}")
            
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                svc_sucursal = solicitud.id_servicio_sucursal_fk
                svc_user = solicitud.id_servicio_usuario_fk
                servicio_nombre = None
                servicio_precio = None
                categoria_servicio = None
                sucursal_nombre = None
                imagenes = []

                if svc_sucursal:
                    servicio_nombre = getattr(svc_sucursal, 'nombre_servicio_sucursal', None)
                    if not servicio_nombre:
                        servicio_nombre = safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_empresa', None) or safe_get(svc_sucursal, 'id_servicio_fk.nombre_servicio_usuario', None)
                    servicio_precio = getattr(svc_sucursal, 'precio_servicio_sucursal', None)
                    sucursal_nombre = getattr(getattr(svc_sucursal, 'id_sucursal_fk', None), 'nombre_sucursal', None)
                    categoria_servicio = safe_get(svc_sucursal, 'id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa', None) or 'Sin categoría'
                    imagenes = collect_service_images(svc_sucursal)
                elif svc_user:
                    servicio_nombre = getattr(svc_user, 'nombre_servicio_usuario', None) or getattr(svc_user, 'nombre_servicio_empresa', None)
                    servicio_precio = getattr(svc_user, 'precio_servicio_usuario', None)
                    categoria_servicio = getattr(getattr(svc_user, 'id_categoria_servicios_fk', None), 'nombre_categoria_serv_usuario', None)
                    imagenes = collect_service_images(svc_user)

                cliente = solicitud.id_empresa_fk
                servicios_rechazados.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'direccion': solicitud.direccion,
                    'ubicacion': solicitud.direccion,
                    'descripcion_solicitud': solicitud.descripcion_detallada,
                    'descripcion': solicitud.descripcion_detallada,
                    'estado': solicitud.estado,
                    'nombre_servicio': servicio_nombre or 'Servicio sin nombre',
                    'servicio_nombre': servicio_nombre or 'Servicio sin nombre',
                    'servicio_precio': servicio_precio,
                    'categoria_servicio': categoria_servicio,
                    'sucursal_nombre': sucursal_nombre,
                    'cliente_nombre': getattr(cliente, 'nombre_empresa', None),
                    'nombre_cliente': getattr(cliente, 'nombre_empresa', None),
                    'cliente_email': getattr(cliente, 'correo_empresa', None),
                    'email_cliente': getattr(cliente, 'correo_empresa', None),
                    'cliente_telefono': 'No disponible',
                    'telefono_cliente': 'No disponible',
                    'imagenes': imagenes,
                    'motivo_rechazo': solicitud.motivo_rechazo,
                    'fecha_rechazo': solicitud.fecha_rechazo,
                    'solicitud_obj': solicitud,
                })
                logger.debug(f"servicios_rechazados: appended empresa-account empresa-solicitud id={solicitud.id_solicitud_servicio_empresa} nombre={servicio_nombre}")
        
        # Ordenar por fecha de solicitud (más recientes primero)
        servicios_rechazados.sort(key=lambda x: x['fecha_solicitud'], reverse=True)
        # Post-procesado: asegurar que cada entrada tenga 'nombre_servicio' útil (intentar resolver desde la solicitud)
        for s in servicios_rechazados:
            name_val = s.get('nombre_servicio')
            if not name_val or name_val in ('Sin nombre', 'Servicio sin nombre'):
                resolved = None
                try:
                    solicitud_obj = s.get('solicitud_obj')
                    if solicitud_obj:
                        resolved = resolve_service_name_strict(solicitud_obj)
                except Exception:
                    resolved = None
                if not resolved:
                    for candidate in ('servicio_nombre', 'nombre_servicio', 'servicio_precio'):
                        val = s.get(candidate)
                        if val and val != 'Sin nombre':
                            resolved = val
                            break
                if not resolved:
                    resolved = s.get('cliente_nombre') or s.get('nombre_cliente') or 'Servicio sin nombre'
                s['nombre_servicio'] = resolved
                s['servicio_nombre'] = resolved
        
        # Obtener información del usuario para el template
        empresa_nombre = None
        if account_type == 'usuario':
            try:
                empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                if empresa_obj:
                    empresa_nombre = empresa_obj.nombre_empresa
            except Exception as e:
                empresa_nombre = None
        elif account_type == 'empresa':
            empresa_nombre = current_user.nombre_empresa
        
        user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
        
        context = {
            'user_info': user_info,
            'servicios_rechazados': servicios_rechazados,
            'total_servicios': len(servicios_rechazados)
        }
        
        return render(request, 'ecommerce_app/servicios_ventas_rechazadas.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en servicios_ventas_rechazadas: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return render(request, 'ecommerce_app/error.html', {'error_message': 'Error al cargar servicios rechazados'})

@require_POST
@require_login
def cotizar_servicio(request):
    """
    Endpoint para enviar cotización de un servicio.
    Actualiza los campos de cotización en la solicitud correspondiente.
    """
    try:
        # Obtener datos del formulario
        servicio_id = request.POST.get('servicio_id')
        tipo_solicitud = request.POST.get('tipo_solicitud')
        presupuesto = request.POST.get('presupuesto')
        descripcion = request.POST.get('descripcion')
        archivo_cotizacion = request.FILES.get('archivo_cotizacion')
        
        logger.info(f"cotizar_servicio - servicio_id: {servicio_id}, tipo_solicitud: {tipo_solicitud}")
        
        # Validar datos requeridos
        if not all([servicio_id, tipo_solicitud, presupuesto, descripcion]):
            return JsonResponse({
                'success': False, 
                'message': 'Todos los campos son requeridos (ID, tipo, presupuesto y descripción)'
            })
        
        # Validar presupuesto
        try:
            presupuesto_decimal = float(presupuesto)
            if presupuesto_decimal <= 0:
                return JsonResponse({
                    'success': False, 
                    'message': 'El presupuesto debe ser mayor a 0'
                })
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False, 
                'message': 'El presupuesto debe ser un número válido'
            })
        
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({
                'success': False, 
                'message': 'Usuario no autenticado'
            })
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Buscar y actualizar la solicitud correspondiente
        solicitud_actualizada = False
        
        if tipo_solicitud == 'usuario':
            # Buscar en solicitud_servicio_usuario
            try:
                solicitud = solicitud_servicio_usuario.objects.get(
                    id_solicitud_servicio_usuario=servicio_id
                )
                
                # Verificar que el usuario actual sea el proveedor del servicio
                if account_type == 'usuario':
                    # Para usuarios, verificar que sea el dueño del servicio
                    if solicitud.id_servicio_usuario_fk and solicitud.id_servicio_usuario_fk.id_usuario_fk != current_user:
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para cotizar este servicio'
                        })
                elif account_type == 'empresa':
                    # Para empresas, verificar que sea la empresa dueña del servicio
                    if (solicitud.id_servicio_sucursal_fk and 
                        solicitud.id_servicio_sucursal_fk.id_sucursal_fk.id_empresa_fk != current_user):
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para cotizar este servicio'
                        })
                
                # Actualizar campos de cotización
                solicitud.presupuesto_cotizacion = presupuesto_decimal
                solicitud.descripcion_cotizacion = descripcion
                solicitud.fecha_cotizacion = timezone.now()
                solicitud.estado = 'cotizada'  # Cambiar estado a cotizada
                
                if archivo_cotizacion:
                    solicitud.archivo_cotizacion = archivo_cotizacion
                
                solicitud.save()
                solicitud_actualizada = True
                # Notificar al solicitante que la solicitud ha sido cotizada
                try:
                    notificar_servicio_cotizado(solicitud, presupuesto_decimal)
                except Exception as e:
                    logger.error(f"Error al notificar servicio cotizado (usuario): {str(e)}")
                
            except solicitud_servicio_usuario.DoesNotExist:
                pass
        
        elif tipo_solicitud == 'empresa':
            # Buscar en solicitud_servicio_empresa
            try:
                solicitud = solicitud_servicio_empresa.objects.get(
                    id_solicitud_servicio_empresa=servicio_id
                )
                
                # Verificar que el usuario actual sea el proveedor del servicio
                if account_type == 'usuario':
                    # Para usuarios, verificar que sea el dueño del servicio
                    if solicitud.id_servicio_usuario_fk and solicitud.id_servicio_usuario_fk.id_usuario_fk != current_user:
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para cotizar este servicio'
                        })
                elif account_type == 'empresa':
                    # Para empresas, verificar que sea la empresa dueña del servicio
                    if (solicitud.id_servicio_sucursal_fk and 
                        solicitud.id_servicio_sucursal_fk.id_sucursal_fk.id_empresa_fk != current_user):
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para cotizar este servicio'
                        })
                
                # Actualizar campos de cotización
                solicitud.presupuesto_cotizacion = presupuesto_decimal
                solicitud.descripcion_cotizacion = descripcion
                solicitud.fecha_cotizacion = timezone.now()
                solicitud.estado = 'cotizada'  # Cambiar estado a cotizada
                
                if archivo_cotizacion:
                    solicitud.archivo_cotizacion = archivo_cotizacion
                
                solicitud.save()
                solicitud_actualizada = True
                # Notificar al solicitante que la solicitud ha sido cotizada
                try:
                    notificar_servicio_cotizado(solicitud, presupuesto_decimal)
                except Exception as e:
                    logger.error(f"Error al notificar servicio cotizado (empresa): {str(e)}")
                
            except solicitud_servicio_empresa.DoesNotExist:
                pass
        
        if not solicitud_actualizada:
            return JsonResponse({
                'success': False, 
                'message': 'No se encontró la solicitud de servicio'
            })
        
        logger.info(f"Cotización enviada exitosamente para solicitud {servicio_id}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Cotización enviada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error en cotizar_servicio: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error interno del servidor'
        })


@require_POST
@require_login
def rechazar_servicio(request):
    """
    Endpoint para rechazar una solicitud de servicio.
    Actualiza el estado a 'rechazada' y guarda el motivo del rechazo.
    """
    try:
        # Obtener datos del formulario
        servicio_id = request.POST.get('servicio_id')
        tipo_solicitud = request.POST.get('tipo_solicitud')
        motivo_rechazo = request.POST.get('motivo_rechazo')
        
        logger.info(f"rechazar_servicio - servicio_id: {servicio_id}, tipo_solicitud: {tipo_solicitud}")
        
        # Validar datos requeridos
        if not all([servicio_id, tipo_solicitud, motivo_rechazo]):
            return JsonResponse({
                'success': False, 
                'message': 'Todos los campos son requeridos (ID, tipo y motivo de rechazo)'
            })
        
        # Validar longitud del motivo
        if len(motivo_rechazo.strip()) < 10:
            return JsonResponse({
                'success': False, 
                'message': 'El motivo del rechazo debe tener al menos 10 caracteres'
            })
        
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({
                'success': False, 
                'message': 'Usuario no autenticado'
            })
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Buscar y actualizar la solicitud correspondiente
        solicitud_actualizada = False
        
        if tipo_solicitud == 'usuario':
            # Buscar en solicitud_servicio_usuario
            try:
                solicitud = solicitud_servicio_usuario.objects.get(
                    id_solicitud_servicio_usuario=servicio_id
                )
                
                # Verificar que el usuario actual sea el proveedor del servicio
                if account_type == 'usuario':
                    # Para usuarios, verificar que sea el dueño del servicio
                    if solicitud.id_servicio_usuario_fk and solicitud.id_servicio_usuario_fk.id_usuario_fk != current_user:
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para rechazar este servicio'
                        })
                elif account_type == 'empresa':
                    # Para empresas, verificar que sea la empresa dueña del servicio
                    if (solicitud.id_servicio_sucursal_fk and 
                        solicitud.id_servicio_sucursal_fk.id_sucursal_fk.id_empresa_fk != current_user):
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para rechazar este servicio'
                        })
                
                # Actualizar campos de rechazo
                solicitud.motivo_rechazo = motivo_rechazo
                solicitud.fecha_rechazo = timezone.now()
                solicitud.estado = 'rechazada'  # Cambiar estado a rechazada
                
                solicitud.save()
                solicitud_actualizada = True
                
            except solicitud_servicio_usuario.DoesNotExist:
                pass
        
        elif tipo_solicitud == 'empresa':
            # Buscar en solicitud_servicio_empresa
            try:
                solicitud = solicitud_servicio_empresa.objects.get(
                    id_solicitud_servicio_empresa=servicio_id
                )
                
                # Verificar que el usuario actual sea el proveedor del servicio
                if account_type == 'usuario':
                    # Para usuarios, verificar que sea el dueño del servicio
                    if solicitud.id_servicio_usuario_fk and solicitud.id_servicio_usuario_fk.id_usuario_fk != current_user:
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para rechazar este servicio'
                        })
                elif account_type == 'empresa':
                    # Para empresas, verificar que sea la empresa dueña del servicio
                    if (solicitud.id_servicio_sucursal_fk and 
                        solicitud.id_servicio_sucursal_fk.id_sucursal_fk.id_empresa_fk != current_user):
                        return JsonResponse({
                            'success': False, 
                            'message': 'No tienes permisos para rechazar este servicio'
                        })
                
                # Actualizar campos de rechazo
                solicitud.motivo_rechazo = motivo_rechazo
                solicitud.fecha_rechazo = timezone.now()
                solicitud.estado = 'rechazada'  # Cambiar estado a rechazada
                
                solicitud.save()
                solicitud_actualizada = True
                
            except solicitud_servicio_empresa.DoesNotExist:
                pass
        
        if not solicitud_actualizada:
            return JsonResponse({
                'success': False, 
                'message': 'No se encontró la solicitud de servicio'
            })
        
        logger.info(f"Solicitud rechazada exitosamente: {servicio_id}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Solicitud rechazada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error en rechazar_servicio: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error interno del servidor'
        })

def servicios_ventas_cotizadas(request):
    """
    Vista para mostrar los servicios cotizados donde el usuario/empresa es el proveedor.
    """
    try:
        logger.info("servicios_ventas_cotizadas - Iniciando función")
        current_user = get_current_user(request)
        logger.info(f"servicios_ventas_cotizadas - current_user: {current_user}")
        
        if not current_user:
            logger.error("servicios_ventas_cotizadas - No current_user found")
            return redirect('/ecommerce/iniciar_sesion/')
        
        # Obtener account_type de la sesión
        account_type = request.session.get('account_type', 'usuario')
        logger.info(f"servicios_ventas_cotizadas - account_type: {account_type}")
        servicios_cotizados = []
        
        logger.info("servicios_ventas_cotizadas - Iniciando consultas a la base de datos")
        
        if account_type == 'usuario':
            # Solicitudes donde otros usuarios/empresas solicitan servicios de este usuario
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado='cotizada'
            ).select_related('id_usuario_fk', 'id_servicio_usuario_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_usuario_fk__id_usuario_fk=current_user,
                estado='cotizada'
            ).select_related('id_empresa_fk', 'id_servicio_usuario_fk')
            
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                logger.info(f"Procesando solicitud cotizada de usuario: {solicitud.id_solicitud_servicio_usuario}")
                servicios_cotizados.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'fecha_cotizacion': solicitud.fecha_cotizacion,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_cotizacion': solicitud.descripcion_cotizacion,
                    'presupuesto_cotizacion': solicitud.presupuesto_cotizacion,
                    'archivo_cotizacion': solicitud.archivo_cotizacion,
                    'estado': solicitud.estado,
                    'nombre_servicio': solicitud.id_servicio_usuario_fk.nombre_servicio_usuario,
                    'servicio_nombre': solicitud.id_servicio_usuario_fk.nombre_servicio_usuario,
                    'servicio_precio': solicitud.id_servicio_usuario_fk.precio_servicio_usuario,
                    'categoria_servicio': 'Servicio de Usuario',
                    'tipo_cliente': 'usuario',
                    'cliente_nombre': solicitud.id_usuario_fk.nombre_usuario if solicitud.id_usuario_fk else 'Sin nombre',
                    'cliente_email': solicitud.id_usuario_fk.correo_usuario if solicitud.id_usuario_fk else 'Sin email',
                    'cliente_telefono': solicitud.id_usuario_fk.telefono_usuario if solicitud.id_usuario_fk else 'Sin teléfono',
                })
            
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                logger.info(f"Procesando solicitud cotizada de empresa: {solicitud.id_solicitud_servicio_empresa}")
                servicios_cotizados.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'fecha_cotizacion': solicitud.fecha_cotizacion,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_cotizacion': solicitud.descripcion_cotizacion,
                    'presupuesto_cotizacion': solicitud.presupuesto_cotizacion,
                    'archivo_cotizacion': solicitud.archivo_cotizacion,
                    'estado': solicitud.estado,
                    'nombre_servicio': solicitud.id_servicio_usuario_fk.nombre_servicio_usuario,
                    'servicio_nombre': solicitud.id_servicio_usuario_fk.nombre_servicio_usuario,
                    'servicio_precio': solicitud.id_servicio_usuario_fk.precio_servicio_usuario,
                    'categoria_servicio': 'Servicio de Usuario',
                    'tipo_cliente': 'empresa',
                    'cliente_nombre': solicitud.id_empresa_fk.nombre_empresa if solicitud.id_empresa_fk else 'Sin nombre',
                    'cliente_email': solicitud.id_empresa_fk.correo_empresa if solicitud.id_empresa_fk else 'Sin email',
                    'cliente_telefono': 'No disponible',
                })
        
        elif account_type == 'empresa':
            # Solicitudes donde otros usuarios/empresas solicitan servicios de sucursales de esta empresa
            solicitudes_usuario = solicitud_servicio_usuario.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado='cotizada'
            ).select_related('id_usuario_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            solicitudes_empresa = solicitud_servicio_empresa.objects.filter(
                id_servicio_sucursal_fk__id_sucursal_fk__id_empresa_fk=current_user,
                estado='cotizada'
            ).select_related('id_empresa_fk', 'id_servicio_sucursal_fk__id_sucursal_fk')
            
            # Procesar solicitudes de usuarios
            for solicitud in solicitudes_usuario:
                logger.info(f"Empresa - Procesando solicitud cotizada de usuario: {solicitud.id_solicitud_servicio_usuario}")
                servicios_cotizados.append({
                    'id': solicitud.id_solicitud_servicio_usuario,
                    'id_solicitud': solicitud.id_solicitud_servicio_usuario,
                    'tipo_solicitud': 'usuario',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'fecha_cotizacion': solicitud.fecha_cotizacion,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_cotizacion': solicitud.descripcion_cotizacion,
                    'presupuesto_cotizacion': solicitud.presupuesto_cotizacion,
                    'archivo_cotizacion': solicitud.archivo_cotizacion,
                    'estado': solicitud.estado,
                    'nombre_servicio': solicitud.id_servicio_sucursal_fk.id_servicio_fk.nombre_servicio_empresa,
                    'servicio_nombre': solicitud.id_servicio_sucursal_fk.id_servicio_fk.nombre_servicio_empresa,
                    'servicio_precio': solicitud.id_servicio_sucursal_fk.precio_servicio_sucursal,
                    'categoria_servicio': solicitud.id_servicio_sucursal_fk.id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa if solicitud.id_servicio_sucursal_fk.id_servicio_fk.id_categoria_servicios_fk else 'Sin categoría',
                    'tipo_cliente': 'usuario',
                    'sucursal_nombre': solicitud.id_servicio_sucursal_fk.id_sucursal_fk.nombre_sucursal,
                    'cliente_nombre': solicitud.id_usuario_fk.nombre_usuario if solicitud.id_usuario_fk else 'Sin nombre',
                    'cliente_email': solicitud.id_usuario_fk.correo_usuario if solicitud.id_usuario_fk else 'Sin email',
                    'cliente_telefono': solicitud.id_usuario_fk.telefono_usuario if solicitud.id_usuario_fk else 'Sin teléfono',
                })
            
            # Procesar solicitudes de empresas
            for solicitud in solicitudes_empresa:
                logger.info(f"Empresa - Procesando solicitud cotizada de empresa: {solicitud.id_solicitud_servicio_empresa}")
                servicios_cotizados.append({
                    'id': solicitud.id_solicitud_servicio_empresa,
                    'id_solicitud': solicitud.id_solicitud_servicio_empresa,
                    'tipo_solicitud': 'empresa',
                    'fecha_solicitud': solicitud.fecha_solicitud,
                    'fecha_requerida': solicitud.fecha_requerida,
                    'fecha_cotizacion': solicitud.fecha_cotizacion,
                    'direccion': solicitud.direccion,
                    'descripcion': solicitud.descripcion_detallada,
                    'descripcion_cotizacion': solicitud.descripcion_cotizacion,
                    'presupuesto_cotizacion': solicitud.presupuesto_cotizacion,
                    'archivo_cotizacion': solicitud.archivo_cotizacion,
                    'estado': solicitud.estado,
                    'nombre_servicio': solicitud.id_servicio_sucursal_fk.id_servicio_fk.nombre_servicio_empresa,
                    'servicio_nombre': solicitud.id_servicio_sucursal_fk.id_servicio_fk.nombre_servicio_empresa,
                    'servicio_precio': solicitud.id_servicio_sucursal_fk.precio_servicio_sucursal,
                    'categoria_servicio': solicitud.id_servicio_sucursal_fk.id_servicio_fk.id_categoria_servicios_fk.nombre_categoria_serv_empresa if solicitud.id_servicio_sucursal_fk.id_servicio_fk.id_categoria_servicios_fk else 'Sin categoría',
                    'tipo_cliente': 'empresa',
                    'sucursal_nombre': solicitud.id_servicio_sucursal_fk.id_sucursal_fk.nombre_sucursal,
                    'cliente_nombre': solicitud.id_empresa_fk.nombre_empresa if solicitud.id_empresa_fk else 'Sin nombre',
                    'cliente_email': solicitud.id_empresa_fk.correo_empresa if solicitud.id_empresa_fk else 'Sin email',
                    'cliente_telefono': 'No disponible',
                })
        
        # Ordenar por fecha de cotización (más recientes primero)
        servicios_cotizados.sort(key=lambda x: x['fecha_cotizacion'] if x['fecha_cotizacion'] else x['fecha_solicitud'], reverse=True)
        
        # Obtener información del usuario para el template
        empresa_nombre = None
        if account_type == 'usuario':
            try:
                empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                if empresa_obj:
                    empresa_nombre = empresa_obj.nombre_empresa
            except Exception as e:
                empresa_nombre = None
        elif account_type == 'empresa':
            empresa_nombre = current_user.nombre_empresa
        
        user_info = get_user_info_with_avatar(current_user, account_type, empresa_nombre)
        
        context = {
            'user_info': user_info,
            'servicios_cotizados': servicios_cotizados,
            'total_servicios': len(servicios_cotizados)
        }
        
        return render(request, 'ecommerce_app/servicios_ventas_cotizadas.html', context)
        
    except Exception as e:
        import traceback
        logger.error(f"Error en servicios_ventas_cotizadas: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return render(request, 'ecommerce_app/error.html', {'error_message': f'Error al cargar servicios cotizados: {str(e)}'})


@require_http_methods(["POST"])
def procesar_pago_servicio(request):
    logger.info(f"SESION AL PROCESAR PAGO: {dict(request.session)}")
    
    # Verificar autenticación usando el sistema personalizado
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'success': False, 'error': 'Usuario no autenticado.'}, status=401)
    
    try:
        from .models import pago_servicio, solicitud_servicio_usuario, solicitud_servicio_empresa
        # Intentar obtener el ID con ambos nombres posibles
        servicio_id = request.POST.get('solicitud_id') or request.POST.get('servicio_id')
        tipo_solicitud = request.POST.get('tipo_solicitud')  # 'usuario' o 'empresa'
        metodo_pago = request.POST.get('metodo_pago')
        comprobante_pago = request.FILES.get('comprobante_pago')
        notas_pago = request.POST.get('notas', '') or request.POST.get('notas_pago', '')

        if not (servicio_id and tipo_solicitud and metodo_pago):
            return JsonResponse({'success': False, 'error': 'Faltan datos requeridos para procesar el pago.'})

        # Buscar la solicitud correspondiente
        solicitud = None
        if tipo_solicitud == 'usuario':
            try:
                solicitud = solicitud_servicio_usuario.objects.get(id_solicitud_servicio_usuario=servicio_id)
            except solicitud_servicio_usuario.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Solicitud de servicio de usuario no encontrada.'})
        elif tipo_solicitud == 'empresa':
            try:
                solicitud = solicitud_servicio_empresa.objects.get(id_solicitud_servicio_empresa=servicio_id)
            except solicitud_servicio_empresa.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Solicitud de servicio de empresa no encontrada.'})
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de solicitud inválido.'})

        # Validar que la solicitud esté cotizada y no pagada
        if solicitud.estado != 'cotizada':
            return JsonResponse({'success': False, 'error': 'Solo se puede procesar el pago de solicitudes cotizadas.'})

        # Crear el pago
        pago = pago_servicio(
            metodo_pago=metodo_pago,
            comprobante_pago=comprobante_pago,
            notas_pago=notas_pago,
            estado_pago='pendiente',
        )
        if tipo_solicitud == 'usuario':
            pago.solicitud_servicio_usuario = solicitud
        else:
            pago.solicitud_servicio_empresa = solicitud
        pago.save()

        # Cambiar estado de la solicitud a 'pagada'
        solicitud.estado = 'pagada'
        solicitud.save()

        # Notificar al proveedor que la solicitud fue pagada/confirmada
        try:
            proveedor_usuario = None
            proveedor_empresa = None
            # solicitud puede ser instancia de solicitud_servicio_usuario o solicitud_servicio_empresa
            if hasattr(solicitud, 'id_servicio_usuario_fk') and solicitud.id_servicio_usuario_fk:
                # proveedor es un usuario (dueño del servicio)
                proveedor_usuario = getattr(solicitud.id_servicio_usuario_fk, 'id_usuario_fk', None)
            if hasattr(solicitud, 'id_servicio_sucursal_fk') and solicitud.id_servicio_sucursal_fk:
                # proveedor es una empresa (sucursal -> empresa)
                suc = getattr(solicitud.id_servicio_sucursal_fk, 'id_sucursal_fk', None)
                proveedor_empresa = getattr(suc, 'id_empresa_fk', None) if suc else None

            titulo_prov = f"Solicitud #{getattr(solicitud, 'id_solicitud_servicio_usuario', getattr(solicitud, 'id_solicitud_servicio_empresa', ''))} - Pago recibido"
            mensaje_prov = f"La solicitud de servicio ha sido pagada por el cliente. Revisa los detalles y procede con la prestación del servicio."

            if proveedor_usuario:
                try:
                    crear_notificacion_usuario(
                        usuario=proveedor_usuario,
                        tipo_notificacion='servicio_aceptado',
                        titulo=titulo_prov,
                        mensaje=mensaje_prov,
                        solicitud_servicio=solicitud
                    )
                except Exception as e:
                    logger.error(f"Error creando notificación usuario proveedor (pago): {str(e)}")

            if proveedor_empresa:
                try:
                    crear_notificacion_empresa(
                        empresa=proveedor_empresa,
                        tipo_notificacion='servicio_pagado',
                        titulo=titulo_prov,
                        mensaje=mensaje_prov,
                        solicitud_servicio=solicitud
                    )
                except Exception as e:
                    logger.error(f"Error creando notificación empresa proveedor (pago): {str(e)}")
        except Exception as e:
            logger.error(f"Error al notificar proveedor sobre pago de solicitud: {str(e)}")

        return JsonResponse({'success': True, 'message': 'Pago procesado correctamente. Queda pendiente de confirmación.'})
    except Exception as e:
        import traceback
        logger.error(f"Error en procesar_pago_servicio: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error interno del servidor: {str(e)}'})


# ==================== REPORTES DE VENTAS ====================

@require_login
def reporte_ventas(request):
    """
    Vista principal para el reporte de ventas con filtros personalizables
    """
    try:
        current_user = get_current_user(request)
        if not current_user:
            return redirect('/ecommerce/iniciar_sesion/')
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Obtener user_info
        user_info = get_user_info_with_avatar(current_user, account_type)
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
        }
        
        return render(request, 'ecommerce_app/reporte_ventas.html', context)
        
    except Exception as e:
        logger.error(f"Error en reporte_ventas: {str(e)}")
        return redirect('/ecommerce/index/')


@require_http_methods(["GET"])
def api_obtener_datos_reporte(request):
    """
    API para obtener los datos del reporte de ventas según los filtros aplicados
    """
    try:
        from datetime import datetime, timedelta
        from django.db.models import Sum, Count, Avg, Q
        from decimal import Decimal
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'})
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Obtener parámetros de filtro
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipo_reporte = request.GET.get('tipo_reporte', 'personalizado')  # diario, semanal, mensual, personalizado
        sucursal_id = request.GET.get('sucursal_id')
        
        # Configurar fechas según el tipo de reporte
        if tipo_reporte == 'diario':
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=1)
        elif tipo_reporte == 'semanal':
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=7)
        elif tipo_reporte == 'mensual':
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=30)
        else:
            # Personalizado - usar las fechas proporcionadas
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fecha_inicio = timezone.make_aware(fecha_inicio)
            else:
                fecha_inicio = timezone.now() - timedelta(days=30)
            
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
                fecha_fin = timezone.make_aware(fecha_fin.replace(hour=23, minute=59, second=59))
            else:
                fecha_fin = timezone.now()
        
        # Inicializar variables
        ventas_data = []
        total_ventas = Decimal('0.00')
        total_pedidos = 0
        ticket_promedio = Decimal('0.00')
        productos_vendidos = []
        ventas_por_dia = []
        
        if account_type == 'empresa':
            # Filtrar ventas de la empresa
            query_usuario = Q(
                id_fk_producto_sucursal_empresa__id_sucursal_fk__id_empresa_fk=current_user,
                id_pedido_fk__fecha_pedido__range=[fecha_inicio, fecha_fin],
                id_pedido_fk__estado_pedido__in=['confirmado', 'enviado', 'entregado']
            )
            
            query_empresa = Q(
                id_fk_producto_sucursal_empresa__id_sucursal_fk__id_empresa_fk=current_user,
                id_pedido_fk__fecha_pedido__range=[fecha_inicio, fecha_fin],
                id_pedido_fk__estado_pedido__in=['confirmado', 'enviado', 'entregado']
            )
            
            # Si se especifica sucursal, filtrar por ella
            if sucursal_id:
                query_usuario &= Q(id_fk_producto_sucursal_empresa__id_sucursal_fk__id_sucursal=sucursal_id)
                query_empresa &= Q(id_fk_producto_sucursal_empresa__id_sucursal_fk__id_sucursal=sucursal_id)
            
            # Obtener detalles de pedidos de usuarios
            detalles_usuario = detalle_pedido_usuario.objects.filter(query_usuario).select_related(
                'id_pedido_fk',
                'id_fk_producto_sucursal_empresa__id_producto_fk',
                'id_fk_producto_sucursal_empresa__id_sucursal_fk'
            )
            
            # Obtener detalles de pedidos de empresas
            detalles_empresa = detalle_pedido_empresa.objects.filter(query_empresa).select_related(
                'id_pedido_fk',
                'id_fk_producto_sucursal_empresa__id_producto_fk',
                'id_fk_producto_sucursal_empresa__id_sucursal_fk'
            )
            
            # Procesar detalles de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                sucursal_venta = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk
                
                ventas_data.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha': pedido.fecha_pedido.strftime('%Y-%m-%d %H:%M'),
                    'producto': producto.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': float(detalle.precio_unitario_pedido),
                    'subtotal': float(detalle.subtotal_detalle_pedido),
                    'estado': pedido.estado_pedido,
                    'sucursal': sucursal_venta.nombre_sucursal,
                    'tipo_comprador': 'Usuario'
                })
                
                total_ventas += detalle.subtotal_detalle_pedido
            
            # Procesar detalles de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                producto = detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                sucursal_venta = detalle.id_fk_producto_sucursal_empresa.id_sucursal_fk
                
                ventas_data.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha': pedido.fecha_pedido.strftime('%Y-%m-%d %H:%M'),
                    'producto': producto.nombre_producto_empresa,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': float(detalle.precio_unitario_pedido),
                    'subtotal': float(detalle.subtotal_detalle_pedido),
                    'estado': pedido.estado_pedido,
                    'sucursal': sucursal_venta.nombre_sucursal,
                    'tipo_comprador': 'Empresa'
                })
                
                total_ventas += detalle.subtotal_detalle_pedido
            
            # Calcular productos más vendidos
            productos_vendidos_query = detalle_pedido_usuario.objects.filter(query_usuario).values(
                'id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido')
            ).order_by('-total_cantidad')[:5]
            
            productos_vendidos_query_empresa = detalle_pedido_empresa.objects.filter(query_empresa).values(
                'id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido')
            ).order_by('-total_cantidad')[:5]
            
            # Combinar productos vendidos
            productos_dict = {}
            for p in productos_vendidos_query:
                nombre = p['id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa']
                if nombre in productos_dict:
                    productos_dict[nombre]['cantidad'] += p['total_cantidad']
                    productos_dict[nombre]['ingresos'] += float(p['total_ingresos'])
                else:
                    productos_dict[nombre] = {
                        'nombre': nombre,
                        'cantidad': p['total_cantidad'],
                        'ingresos': float(p['total_ingresos'])
                    }
            
            for p in productos_vendidos_query_empresa:
                nombre = p['id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa']
                if nombre in productos_dict:
                    productos_dict[nombre]['cantidad'] += p['total_cantidad']
                    productos_dict[nombre]['ingresos'] += float(p['total_ingresos'])
                else:
                    productos_dict[nombre] = {
                        'nombre': nombre,
                        'cantidad': p['total_cantidad'],
                        'ingresos': float(p['total_ingresos'])
                    }
            
            productos_vendidos = sorted(productos_dict.values(), key=lambda x: x['cantidad'], reverse=True)[:5]
            
            # Obtener pedidos únicos
            pedidos_unicos_usuario = detalle_pedido_usuario.objects.filter(query_usuario).values('id_pedido_fk').distinct()
            pedidos_unicos_empresa = detalle_pedido_empresa.objects.filter(query_empresa).values('id_pedido_fk').distinct()
            total_pedidos = pedidos_unicos_usuario.count() + pedidos_unicos_empresa.count()
            
        else:
            # Usuario individual
            query_usuario = Q(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__fecha_pedido__range=[fecha_inicio, fecha_fin],
                id_pedido_fk__estado_pedido__in=['confirmado', 'enviado', 'entregado']
            )
            
            query_empresa = Q(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__fecha_pedido__range=[fecha_inicio, fecha_fin],
                id_pedido_fk__estado_pedido__in=['confirmado', 'enviado', 'entregado']
            )
            
            # Obtener detalles de pedidos de usuarios
            detalles_usuario = detalle_pedido_usuario.objects.filter(query_usuario).select_related(
                'id_pedido_fk',
                'idproducto_fk_usuario'
            )
            
            # Obtener detalles de pedidos de empresas
            detalles_empresa = detalle_pedido_empresa.objects.filter(query_empresa).select_related(
                'id_pedido_fk',
                'idproducto_fk_usuario'
            )
            
            # Procesar detalles de usuarios
            for detalle in detalles_usuario:
                pedido = detalle.id_pedido_fk
                producto = detalle.idproducto_fk_usuario
                
                ventas_data.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha': pedido.fecha_pedido.strftime('%Y-%m-%d %H:%M'),
                    'producto': producto.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': float(detalle.precio_unitario_pedido),
                    'subtotal': float(detalle.subtotal_detalle_pedido),
                    'estado': pedido.estado_pedido,
                    'tipo_comprador': 'Usuario'
                })
                
                total_ventas += detalle.subtotal_detalle_pedido
            
            # Procesar detalles de empresas
            for detalle in detalles_empresa:
                pedido = detalle.id_pedido_fk
                producto = detalle.idproducto_fk_usuario
                
                ventas_data.append({
                    'numero_pedido': pedido.numero_pedido,
                    'fecha': pedido.fecha_pedido.strftime('%Y-%m-%d %H:%M'),
                    'producto': producto.nombre_producto_usuario,
                    'cantidad': detalle.cantidad_detalle_pedido,
                    'precio_unitario': float(detalle.precio_unitario_pedido),
                    'subtotal': float(detalle.subtotal_detalle_pedido),
                    'estado': pedido.estado_pedido,
                    'tipo_comprador': 'Empresa'
                })
                
                total_ventas += detalle.subtotal_detalle_pedido
            
            # Calcular productos más vendidos
            productos_vendidos_query = detalle_pedido_usuario.objects.filter(query_usuario).values(
                'idproducto_fk_usuario__nombre_producto_usuario'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido')
            ).order_by('-total_cantidad')[:5]
            
            productos_vendidos_query_empresa = detalle_pedido_empresa.objects.filter(query_empresa).values(
                'idproducto_fk_usuario__nombre_producto_usuario'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido')
            ).order_by('-total_cantidad')[:5]
            
            # Combinar productos vendidos
            productos_dict = {}
            for p in productos_vendidos_query:
                nombre = p['idproducto_fk_usuario__nombre_producto_usuario']
                if nombre in productos_dict:
                    productos_dict[nombre]['cantidad'] += p['total_cantidad']
                    productos_dict[nombre]['ingresos'] += float(p['total_ingresos'])
                else:
                    productos_dict[nombre] = {
                        'nombre': nombre,
                        'cantidad': p['total_cantidad'],
                        'ingresos': float(p['total_ingresos'])
                    }
            
            for p in productos_vendidos_query_empresa:
                nombre = p['idproducto_fk_usuario__nombre_producto_usuario']
                if nombre in productos_dict:
                    productos_dict[nombre]['cantidad'] += p['total_cantidad']
                    productos_dict[nombre]['ingresos'] += float(p['total_ingresos'])
                else:
                    productos_dict[nombre] = {
                        'nombre': nombre,
                        'cantidad': p['total_cantidad'],
                        'ingresos': float(p['total_ingresos'])
                    }
            
            productos_vendidos = sorted(productos_dict.values(), key=lambda x: x['cantidad'], reverse=True)[:5]
            
            # Obtener pedidos únicos
            pedidos_unicos_usuario = detalle_pedido_usuario.objects.filter(query_usuario).values('id_pedido_fk').distinct()
            pedidos_unicos_empresa = detalle_pedido_empresa.objects.filter(query_empresa).values('id_pedido_fk').distinct()
            total_pedidos = pedidos_unicos_usuario.count() + pedidos_unicos_empresa.count()
        
        # Calcular ticket promedio
        if total_pedidos > 0:
            ticket_promedio = total_ventas / total_pedidos
        
        # Calcular ventas por día para el gráfico
        ventas_por_dia_dict = {}
        for venta in ventas_data:
            fecha_venta = venta['fecha'].split(' ')[0]
            if fecha_venta in ventas_por_dia_dict:
                ventas_por_dia_dict[fecha_venta] += venta['subtotal']
            else:
                ventas_por_dia_dict[fecha_venta] = venta['subtotal']
        
        ventas_por_dia = [{'fecha': k, 'total': v} for k, v in sorted(ventas_por_dia_dict.items())]
        
        # Obtener sucursales (solo para empresas)
        sucursales_list = []
        if account_type == 'empresa':
            sucursales_obj = sucursal.objects.filter(id_empresa_fk=current_user)
            sucursales_list = [{'id': s.id_sucursal, 'nombre': s.nombre_sucursal} for s in sucursales_obj]
        
        return JsonResponse({
            'success': True,
            'data': {
                'ventas': ventas_data,
                'total_ventas': float(total_ventas),
                'total_pedidos': total_pedidos,
                'ticket_promedio': float(ticket_promedio),
                'productos_vendidos': productos_vendidos,
                'ventas_por_dia': ventas_por_dia,
                'sucursales': sucursales_list,
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error en api_obtener_datos_reporte: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al obtener datos del reporte: {str(e)}'})


@require_login
def reporte_productos(request):
    """
    Vista principal para el reporte de ventas por producto
    """
    try:
        current_user = get_current_user(request)
        if not current_user:
            return redirect('/ecommerce/iniciar_sesion/')
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Obtener user_info
        user_info = get_user_info_with_avatar(current_user, account_type)
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
        }
        
        return render(request, 'ecommerce_app/reporte_productos.html', context)
        
    except Exception as e:
        logger.error(f"Error en reporte_productos: {str(e)}")
        return redirect('/ecommerce/index/')


@require_login
def reporte_servicios(request):
    """
    Vista principal para el reporte de servicios (renderiza la plantilla de servicios)
    """
    try:
        current_user = get_current_user(request)
        if not current_user:
            return redirect('/ecommerce/iniciar_sesion/')
        
        account_type = request.session.get('account_type', 'usuario')
        user_info = get_user_info_with_avatar(current_user, account_type)
        context = {
            'user_info': user_info,
            'account_type': account_type,
        }
        return render(request, 'ecommerce_app/reporte_servicios.html', context)
    except Exception as e:
        logger.error(f"Error en reporte_servicios: {str(e)}")
        return redirect('/ecommerce/index/')


@require_http_methods(["GET"])
def api_obtener_datos_reporte_productos(request):
    """
    API para obtener datos del reporte de productos
    """
    try:
        from datetime import datetime, timedelta
        from django.db.models import Sum, Count, Avg, Q, F
        from decimal import Decimal
        
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'})
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Obtener parámetros de filtro
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipo_reporte = request.GET.get('tipo_reporte', 'mensual')
        sucursal_id = request.GET.get('sucursal_id')
        categoria_id = request.GET.get('categoria_id')
        
        # Configurar fechas según el tipo de reporte
        if tipo_reporte == 'semanal':
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=7)
        elif tipo_reporte == 'mensual':
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=30)
        elif tipo_reporte == 'trimestral':
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=90)
        else:
            # Personalizado
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fecha_inicio = timezone.make_aware(fecha_inicio)
            else:
                fecha_inicio = timezone.now() - timedelta(days=30)
            
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
                fecha_fin = timezone.make_aware(fecha_fin.replace(hour=23, minute=59, second=59))
            else:
                fecha_fin = timezone.now()
        
        productos_data = []
        productos_mas_vendidos = []
        productos_menos_vendidos = []
        productos_sin_movimiento = []
        
        if account_type == 'empresa':
            # Filtrar por empresa
            query_base = Q(
                id_fk_producto_sucursal_empresa__id_sucursal_fk__id_empresa_fk=current_user,
                id_pedido_fk__fecha_pedido__range=[fecha_inicio, fecha_fin],
                id_pedido_fk__estado_pedido__in=['confirmado', 'enviado', 'entregado']
            )
            
            if sucursal_id:
                query_base &= Q(id_fk_producto_sucursal_empresa__id_sucursal_fk__id_sucursal=sucursal_id)
            
            if categoria_id:
                query_base &= Q(id_fk_producto_sucursal_empresa__id_producto_fk__id_categoria_prod_fk__id_categoria_prod_empresa=categoria_id)
            
            # Obtener ventas de productos de usuarios que compraron
            ventas_usuario = detalle_pedido_usuario.objects.filter(query_base).values(
                'id_fk_producto_sucursal_empresa__id_producto_fk__id_producto_empresa',
                'id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido'),
                num_ventas=Count('id_detalle_pedido_usuario')
            )
            
            # Obtener ventas de productos de empresas que compraron
            ventas_empresa = detalle_pedido_empresa.objects.filter(query_base).values(
                'id_fk_producto_sucursal_empresa__id_producto_fk__id_producto_empresa',
                'id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido'),
                num_ventas=Count('id_detalle_pedido_empresa')
            )
            
            # Combinar resultados
            productos_dict = {}
            for venta in ventas_usuario:
                prod_id = venta['id_fk_producto_sucursal_empresa__id_producto_fk__id_producto_empresa']
                if prod_id in productos_dict:
                    productos_dict[prod_id]['cantidad'] += venta['total_cantidad']
                    productos_dict[prod_id]['ingresos'] += float(venta['total_ingresos'])
                    productos_dict[prod_id]['num_ventas'] += venta['num_ventas']
                else:
                    productos_dict[prod_id] = {
                        'id': prod_id,
                        'nombre': venta['id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa'],
                        'cantidad': venta['total_cantidad'],
                        'ingresos': float(venta['total_ingresos']),
                        'num_ventas': venta['num_ventas']
                    }
            
            for venta in ventas_empresa:
                prod_id = venta['id_fk_producto_sucursal_empresa__id_producto_fk__id_producto_empresa']
                if prod_id in productos_dict:
                    productos_dict[prod_id]['cantidad'] += venta['total_cantidad']
                    productos_dict[prod_id]['ingresos'] += float(venta['total_ingresos'])
                    productos_dict[prod_id]['num_ventas'] += venta['num_ventas']
                else:
                    productos_dict[prod_id] = {
                        'id': prod_id,
                        'nombre': venta['id_fk_producto_sucursal_empresa__id_producto_fk__nombre_producto_empresa'],
                        'cantidad': venta['total_cantidad'],
                        'ingresos': float(venta['total_ingresos']),
                        'num_ventas': venta['num_ventas']
                    }
            
            # Calcular precio promedio y rentabilidad
            for prod_id, data in productos_dict.items():
                data['precio_promedio'] = data['ingresos'] / data['cantidad'] if data['cantidad'] > 0 else 0
                data['rentabilidad'] = (data['ingresos'] / data['num_ventas']) if data['num_ventas'] > 0 else 0
            
            productos_data = list(productos_dict.values())
            
            # Productos sin movimiento (productos que existen pero no tienen ventas)
            query_sin_movimiento = Q(id_sucursal_fk__id_empresa_fk=current_user)
            
            if sucursal_id:
                query_sin_movimiento &= Q(id_sucursal_fk__id_sucursal=sucursal_id)
            
            if categoria_id:
                query_sin_movimiento &= Q(id_producto_fk__id_categoria_prod_fk__id_categoria_prod_empresa=categoria_id)
            
            productos_sucursal = producto_sucursal.objects.filter(
                query_sin_movimiento
            ).exclude(
                id_producto_fk__id_producto_empresa__in=productos_dict.keys()
            ).select_related('id_producto_fk')[:10]
            
            productos_sin_movimiento = [
                {
                    'id': p.id_producto_fk.id_producto_empresa,
                    'nombre': p.id_producto_fk.nombre_producto_empresa,
                    'stock': p.stock_producto_sucursal,
                    'precio': float(p.precio_producto_sucursal)
                }
                for p in productos_sucursal
            ]
            
        else:
            # Usuario individual
            query_base = Q(
                idproducto_fk_usuario__id_usuario_fk=current_user,
                id_pedido_fk__fecha_pedido__range=[fecha_inicio, fecha_fin],
                id_pedido_fk__estado_pedido__in=['confirmado', 'enviado', 'entregado']
            )
            
            if categoria_id:
                query_base &= Q(idproducto_fk_usuario__id_categoria_prod_fk__id_categoria_prod_usuario=categoria_id)
            
            # Ventas de usuarios
            ventas_usuario = detalle_pedido_usuario.objects.filter(query_base).values(
                'idproducto_fk_usuario__id_producto_usuario',
                'idproducto_fk_usuario__nombre_producto_usuario'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido'),
                num_ventas=Count('id_detalle_pedido_usuario')
            )
            
            # Ventas de empresas
            ventas_empresa = detalle_pedido_empresa.objects.filter(query_base).values(
                'idproducto_fk_usuario__id_producto_usuario',
                'idproducto_fk_usuario__nombre_producto_usuario'
            ).annotate(
                total_cantidad=Sum('cantidad_detalle_pedido'),
                total_ingresos=Sum('subtotal_detalle_pedido'),
                num_ventas=Count('id_detalle_pedido_empresa')
            )
            
            # Combinar resultados
            productos_dict = {}
            for venta in ventas_usuario:
                prod_id = venta['idproducto_fk_usuario__id_producto_usuario']
                if prod_id in productos_dict:
                    productos_dict[prod_id]['cantidad'] += venta['total_cantidad']
                    productos_dict[prod_id]['ingresos'] += float(venta['total_ingresos'])
                    productos_dict[prod_id]['num_ventas'] += venta['num_ventas']
                else:
                    productos_dict[prod_id] = {
                        'id': prod_id,
                        'nombre': venta['idproducto_fk_usuario__nombre_producto_usuario'],
                        'cantidad': venta['total_cantidad'],
                        'ingresos': float(venta['total_ingresos']),
                        'num_ventas': venta['num_ventas']
                    }
            
            for venta in ventas_empresa:
                prod_id = venta['idproducto_fk_usuario__id_producto_usuario']
                if prod_id in productos_dict:
                    productos_dict[prod_id]['cantidad'] += venta['total_cantidad']
                    productos_dict[prod_id]['ingresos'] += float(venta['total_ingresos'])
                    productos_dict[prod_id]['num_ventas'] += venta['num_ventas']
                else:
                    productos_dict[prod_id] = {
                        'id': prod_id,
                        'nombre': venta['idproducto_fk_usuario__nombre_producto_usuario'],
                        'cantidad': venta['total_cantidad'],
                        'ingresos': float(venta['total_ingresos']),
                        'num_ventas': venta['num_ventas']
                    }
            
            # Calcular métricas
            for prod_id, data in productos_dict.items():
                data['precio_promedio'] = data['ingresos'] / data['cantidad'] if data['cantidad'] > 0 else 0
                data['rentabilidad'] = (data['ingresos'] / data['num_ventas']) if data['num_ventas'] > 0 else 0
            
            productos_data = list(productos_dict.values())
            
            # Productos sin movimiento
            query_sin_movimiento_usuario = Q(id_usuario_fk=current_user)
            
            if categoria_id:
                query_sin_movimiento_usuario &= Q(id_categoria_prod_fk__id_categoria_prod_usuario=categoria_id)
            
            productos_usuario = producto_usuario.objects.filter(
                query_sin_movimiento_usuario
            ).exclude(
                id_producto_usuario__in=productos_dict.keys()
            )[:10]
            
            productos_sin_movimiento = [
                {
                    'id': p.id_producto_usuario,
                    'nombre': p.nombre_producto_usuario,
                    'stock': p.stock_producto_usuario,
                    'precio': float(p.precio_producto_usuario)
                }
                for p in productos_usuario
            ]
        
        # Ordenar productos
        productos_mas_vendidos = sorted(productos_data, key=lambda x: x['cantidad'], reverse=True)[:10]
        productos_menos_vendidos = sorted(productos_data, key=lambda x: x['cantidad'])[:10]
        
        # Obtener sucursales (solo para empresas)
        sucursales_list = []
        if account_type == 'empresa':
            sucursales_obj = sucursal.objects.filter(id_empresa_fk=current_user)
            sucursales_list = [{'id': s.id_sucursal, 'nombre': s.nombre_sucursal} for s in sucursales_obj]
        
        # Obtener categorías de productos
        categorias_list = []
        if account_type == 'empresa':
            # Incluir categorías propias de la empresa y las categóricas marcadas como genéricas (generico='s')
            categorias_obj = categoria_producto_empresa.objects.filter(Q(id_empresa_fk=current_user) | Q(generico='s')).distinct()
            categorias_list = [{'id': c.id_categoria_prod_empresa, 'nombre': c.nombre_categoria_prod_empresa} for c in categorias_obj]
        else:
            # Incluir categorías propias del usuario y las genéricas
            categorias_obj = categoria_producto_usuario.objects.filter(Q(id_usuario_fk=current_user) | Q(generico='s')).distinct()
            categorias_list = [{'id': c.id_categoria_prod_usuario, 'nombre': c.nombre_categoria_prod_usuario} for c in categorias_obj]
        
        return JsonResponse({
            'success': True,
            'data': {
                'productos_mas_vendidos': productos_mas_vendidos,
                'productos_menos_vendidos': productos_menos_vendidos,
                'productos_sin_movimiento': productos_sin_movimiento,
                'todos_productos': productos_data,
                'sucursales': sucursales_list,
                'categorias': categorias_list,
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error en api_obtener_datos_reporte_productos: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al obtener datos del reporte: {str(e)}'})
    


@require_http_methods(["GET"])
def api_obtener_datos_reporte_servicios(request):
    """
    API para obtener datos del reporte de servicios.
    Implementación dedicada para servicios: agrupa solicitudes de servicio (usuario/empresa) por servicio,
    calcula cantidad, ingresos estimados (usa presupuesto_cotizacion cuando esté disponible) y devuelve
    la estructura que espera el frontend de `reporte_servicios.js`.
    """
    try:
        from datetime import datetime, timedelta
        from django.db.models import Q

        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'})

        account_type = request.session.get('account_type', 'usuario')

        # Parámetros de filtro
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipo_reporte = request.GET.get('tipo_reporte', 'mensual')
        sucursal_id = request.GET.get('sucursal_id')
        categoria_id = request.GET.get('categoria_id')

        # Normalizar fechas (similar a productos)
        if tipo_reporte == 'semanal':
            fecha_fin_dt = timezone.now()
            fecha_inicio_dt = fecha_fin_dt - timedelta(days=7)
        elif tipo_reporte == 'mensual':
            fecha_fin_dt = timezone.now()
            fecha_inicio_dt = fecha_fin_dt - timedelta(days=30)
        elif tipo_reporte == 'trimestral':
            fecha_fin_dt = timezone.now()
            fecha_inicio_dt = fecha_fin_dt - timedelta(days=90)
        else:
            # personalizado
            try:
                fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d') if fecha_inicio else (timezone.now() - timedelta(days=30))
                fecha_inicio_dt = timezone.make_aware(fecha_inicio_dt)
            except Exception:
                fecha_inicio_dt = timezone.now() - timedelta(days=30)
            try:
                fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else timezone.now()
                fecha_fin_dt = timezone.make_aware(fecha_fin_dt.replace(hour=23, minute=59, second=59))
            except Exception:
                fecha_fin_dt = timezone.now()

        # Estados que consideramos como 'prestado' / cobrado
        estados_validos = ['pagada', 'completada']

        # Recolectar solicitudes que entran en el rango
        solicitudes_qs = []
        # Solicitudes de usuarios (realizadas por usuarios a proveedores que pueden ser empresas o usuarios)
        solicitudes_usuario = solicitud_servicio_usuario.objects.filter(fecha_solicitud__range=[fecha_inicio_dt, fecha_fin_dt], estado__in=estados_validos)
        solicitudes_empresa = solicitud_servicio_empresa.objects.filter(fecha_solicitud__range=[fecha_inicio_dt, fecha_fin_dt], estado__in=estados_validos)

        # Filtrar por propietario (empresa o usuario) según el account_type
        def solicitud_pertenece_a_usuario(solicitud, user, account_type_check):
            """Devuelve True si la solicitud está asociada a los servicios del `user` según account_type_check."""
            try:
                if account_type_check == 'empresa':
                    # Verificar si la solicitud referencia un servicio de sucursal perteneciente a la empresa
                    svc_suc = getattr(solicitud, 'id_servicio_sucursal_fk', None)
                    if svc_suc:
                        suc = getattr(svc_suc, 'id_sucursal_fk', None)
                        if suc and getattr(suc, 'id_empresa_fk', None) == user:
                            return True
                        # También revisar si la FK del servicio apunta a una empresa
                        svc_emp = getattr(svc_suc, 'id_servicio_fk', None)
                        if svc_emp and getattr(svc_emp, 'id_empresa_fk', None) == user:
                            return True
                    # Revisar si la solicitud referencia directamente un servicio_empresa
                    svc_emp_direct = getattr(solicitud, 'id_servicio_usuario_fk', None)
                    if svc_emp_direct:
                        # servicio usuario/empresa puede tener id_empresa_fk
                        if getattr(svc_emp_direct, 'id_empresa_fk', None) == user:
                            return True
                else:
                    # Para usuario, verificar si el servicio pertenece al usuario
                    svc_user = getattr(solicitud, 'id_servicio_usuario_fk', None)
                    if svc_user and getattr(svc_user, 'id_usuario_fk', None) == user:
                        return True
                    # También si el servicio está en servicio_empresa pero vinculado a un usuario (poco probable)
                    svc_suc = getattr(solicitud, 'id_servicio_sucursal_fk', None)
                    if svc_suc:
                        svc_emp = getattr(svc_suc, 'id_servicio_fk', None)
                        if svc_emp and getattr(svc_emp, 'id_empresa_fk', None) == user:
                            return True
            except Exception:
                return False
            return False

        # Construir lista combinada de solicitudes que pertenezcan al current_user según account_type
        solicitudes = []
        for s in solicitudes_usuario:
            # Para solicitudes_usuario, la prestación la da un usuario (id_servicio_usuario_fk) o una sucursal (id_servicio_sucursal_fk)
            if account_type == 'empresa':
                if solicitud_pertenece_a_usuario(s, current_user, 'empresa'):
                    solicitudes.append(s)
            else:
                if solicitud_pertenece_a_usuario(s, current_user, 'usuario'):
                    solicitudes.append(s)

        for s in solicitudes_empresa:
            if account_type == 'empresa':
                if solicitud_pertenece_a_usuario(s, current_user, 'empresa'):
                    solicitudes.append(s)
            else:
                if solicitud_pertenece_a_usuario(s, current_user, 'usuario'):
                    solicitudes.append(s)

        # Agregar todas las categorías y sucursales para poblar selects
        categorias = []
        if account_type == 'empresa':
            categorias_qs = categoria_servicio_empresa.objects.filter(id_empresa_fk=current_user)
            categorias = [{'id': c.id_categoria_serv_empresa, 'nombre': c.nombre_categoria_serv_empresa} for c in categorias_qs]
            sucursales_qs = sucursal.objects.filter(id_empresa_fk=current_user)
            sucursales = [{'id': s.id_sucursal, 'nombre': s.nombre_sucursal} for s in sucursales_qs]
        else:
            categorias_qs = categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user)
            categorias = [{'id': c.id_categoria_serv_usuario, 'nombre': c.nombre_categoria_serv_usuario} for c in categorias_qs]
            sucursales = []

        # Agregar posible filtro de sucursal/categoría (si fueron enviados)
        if sucursal_id:
            try:
                sucursal_id = int(sucursal_id)
            except Exception:
                sucursal_id = None
        if categoria_id:
            try:
                categoria_id = int(categoria_id)
            except Exception:
                categoria_id = None

        # Agregamos un mapeo por nombre de servicio
        servicios_dict = {}

        for s in solicitudes:
            try:
                nombre = resolve_service_name_strict(s) or resolve_service_name_from_solicitud(s) or 'Servicio desconocido'
                # Aplicar filtros por sucursal (si aplica)
                if sucursal_id:
                    svc_suc = getattr(s, 'id_servicio_sucursal_fk', None)
                    if not svc_suc or getattr(svc_suc.id_sucursal_fk, 'id_sucursal', None) != sucursal_id:
                        continue

                # Filtrar por categoría si la solicitud referencia un servicio con categoría
                if categoria_id:
                    svc_obj = getattr(s, 'id_servicio_usuario_fk', None) or getattr(s, 'id_servicio_sucursal_fk', None)
                    cat_ok = True
                    try:
                        # intentar leer categoría en varios caminos
                        cat_id = None
                        if hasattr(svc_obj, 'id_categoria_servicios_fk') and getattr(svc_obj, 'id_categoria_servicios_fk'):
                            cat_id = getattr(svc_obj, 'id_categoria_servicios_fk').id_categoria_serv_empresa if hasattr(getattr(svc_obj, 'id_categoria_servicios_fk'), 'id_categoria_serv_empresa') else getattr(svc_obj, 'id_categoria_servicios_fk')
                        if cat_id and int(cat_id) != categoria_id:
                            cat_ok = False
                    except Exception:
                        cat_ok = True
                    if not cat_ok:
                        continue

                precio = 0.0
                try:
                    precio = float(getattr(s, 'presupuesto_cotizacion', 0) or 0)
                except Exception:
                    precio = 0.0

                if nombre in servicios_dict:
                    servicios_dict[nombre]['cantidad'] += 1
                    servicios_dict[nombre]['ingresos'] += precio
                else:
                    servicios_dict[nombre] = {
                        'nombre': nombre,
                        'cantidad': 1,
                        'ingresos': precio,
                        'precio_promedio': precio,
                        'num_prestaciones': 1
                    }
            except Exception:
                continue

        # Calcular precios promedio y convertir a listas ordenadas
        todos_servicios = []
        for nombre, obj in servicios_dict.items():
            if obj['cantidad'] > 0:
                obj['precio_promedio'] = round((obj['ingresos'] / obj['cantidad']) if obj['cantidad'] else 0, 2)
            else:
                obj['precio_promedio'] = 0
            todos_servicios.append(obj)

        servicios_mas_prestados = sorted(todos_servicios, key=lambda x: x['cantidad'], reverse=True)
        servicios_menos_prestados = sorted(todos_servicios, key=lambda x: x['cantidad'])

        # Servicios sin prestaciones: obtener lista de servicios del propietario y restar los que tuvieron movimiento
        servicios_sin_movimiento = []
        try:
            if account_type == 'empresa':
                servicios_propios = servicio_empresa.objects.filter(id_empresa_fk=current_user)
                # incluir servicios asociados a sucursales
                servicios_suc = servicio_sucursal.objects.filter(id_sucursal_fk__id_empresa_fk=current_user)
                # Construir conjunto de nombres
                nombres_propios = set([s.nombre_servicio_empresa for s in servicios_propios] + [s.id_servicio_fk.nombre_servicio_empresa for s in servicios_suc if s.id_servicio_fk])
            else:
                servicios_propios = servicio_usuario.objects.filter(id_usuario_fk=current_user)
                nombres_propios = set([s.nombre_servicio_usuario for s in servicios_propios])

            nombres_con_movimiento = set([s['nombre'] for s in todos_servicios])
            sin_mov = nombres_propios - nombres_con_movimiento
            for n in sin_mov:
                # buscar objeto de servicio para mostrar estado/precio si es posible
                servicios_sin_movimiento.append({'nombre': n, 'estado': 'Activo', 'precio': 0})
        except Exception:
            servicios_sin_movimiento = []

        # Responder con la estructura esperada por el frontend
        return JsonResponse({'success': True, 'data': {
            'servicios_mas_prestados': servicios_mas_prestados,
            'servicios_menos_prestados': servicios_menos_prestados,
            'servicios_sin_prestaciones': servicios_sin_movimiento,
            'todos_servicios': todos_servicios,
            'sucursales': sucursales,
            'categorias': categorias,
            'fecha_inicio': fecha_inicio_dt.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin_dt.strftime('%Y-%m-%d')
        }})

    except Exception as e:
        import traceback
        logger.error(f"Error en api_obtener_datos_reporte_servicios: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al obtener datos del reporte de servicios: {str(e)}'})



def editar_perfil_usuario(request, usuario_id):
    """Vista para editar el perfil de un usuario usando la sesión personalizada"""
    try:
        usuario_obj = usuario.objects.get(id_usuario=usuario_id)
    except usuario.DoesNotExist:
        return redirect('index')

    # Obtener current_user desde la sesión personalizada
    current_user = get_current_user(request)
    if not current_user:
        logger.info(f"editar_perfil_usuario (lower): usuario no autenticado. session keys: {list(request.session.keys())}")
        return redirect('/ecommerce/iniciar_sesion/')

    # Verificar que el usuario autenticado corresponda al perfil
    if not hasattr(current_user, 'id_usuario') or current_user.id_usuario != usuario_obj.id_usuario:
        logger.info(f"editar_perfil_usuario (lower): intento de editar perfil ajeno. current_user.id: {getattr(current_user, 'id_usuario', None)}, target: {usuario_obj.id_usuario}")
        return redirect('perfil_usuario')

    # Construir user_info para la barra
    account_type = request.session.get('account_type', 'usuario')
    user_info = get_user_info_with_avatar(current_user, account_type)

    if request.method == 'POST':
        try:
            nombre_usuario = request.POST.get('nombre_usuario')
            telefono_usuario = request.POST.get('telefono_usuario')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            pais = request.POST.get('pais')
            estado = request.POST.get('estado')
            avatar_chatbot = request.POST.get('avatar_chatbot')

            if nombre_usuario:
                usuario_obj.nombre_usuario = nombre_usuario
            if telefono_usuario is not None:
                usuario_obj.telefono_usuario = telefono_usuario
            if fecha_nacimiento:
                usuario_obj.fecha_nacimiento = fecha_nacimiento
            if pais:
                usuario_obj.pais = pais
            if estado:
                usuario_obj.estado = estado
            if avatar_chatbot:
                usuario_obj.avatar_chatbot = avatar_chatbot

            if 'foto_usuario' in request.FILES:
                usuario_obj.foto_usuario = request.FILES['foto_usuario']

            usuario_obj.save()
            # Si la petición viene por AJAX, devolver JSON para que el frontend muestre un SweetAlert y no haga redirect
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                resp = {'success': True, 'message': 'Perfil actualizado correctamente.'}
                try:
                    if usuario_obj.foto_usuario and hasattr(usuario_obj.foto_usuario, 'url'):
                        resp['foto_url'] = usuario_obj.foto_usuario.url
                except Exception:
                    pass
                try:
                    resp['avatar_chatbot'] = usuario_obj.avatar_chatbot or ''
                except Exception:
                    resp['avatar_chatbot'] = ''
                return JsonResponse(resp)

            return redirect('perfil_usuario')
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Error al actualizar perfil: {str(e)}'})
            return render(request, 'ecommerce_app/editar_perfil_usuario.html',
                          {'usuario': usuario_obj, 'user_info': user_info, 'error': f'Error al actualizar perfil: {str(e)}'})
    else:
        return render(request, 'ecommerce_app/editar_perfil_usuario.html', {'usuario': usuario_obj, 'user_info': user_info})



def editar_perfil_empresa(request, empresa_id):
    """Vista para editar el perfil de una empresa usando la sesión personalizada"""
    try:
        empresa_obj = empresa.objects.get(id_empresa=empresa_id)
    except empresa.DoesNotExist:
        return redirect('index')

    current_user = get_current_user(request)
    if not current_user:
        logger.info(f"editar_perfil_empresa (lower): usuario no autenticado. session keys: {list(request.session.keys())}")
        return redirect('/ecommerce/iniciar_sesion/')

    # Verificar que la empresa autenticada corresponde al perfil
    if not hasattr(current_user, 'id_empresa') or current_user.id_empresa != empresa_obj.id_empresa:
        logger.info(f"editar_perfil_empresa (lower): intento de editar perfil ajeno. current_user.id: {getattr(current_user, 'id_empresa', None)}, target: {empresa_obj.id_empresa}")
        return redirect('perfil_empresa', empresa_id=empresa_id)

    account_type = request.session.get('account_type', 'empresa')
    user_info = get_user_info_with_avatar(current_user, account_type)

    # Preload one MetodoPago per tipo to prefill the template sections
    try:
        from .models import MetodoPago
        transferencia = MetodoPago.objects.filter(empresa=empresa_obj, tipo='transferencia').first()
        pago_movil = MetodoPago.objects.filter(empresa=empresa_obj, tipo='pago_movil').first()
        paypal = MetodoPago.objects.filter(empresa=empresa_obj, tipo='paypal').first()
    except Exception:
        transferencia = None
        pago_movil = None
        paypal = None

    if request.method == 'POST':
        try:
            nombre_empresa = request.POST.get('nombre_empresa')
            descripcion_empresa = request.POST.get('descripcion_empresa')
            tipo_empresa = request.POST.get('tipo_empresa')
            sector_empresa = request.POST.get('sector_empresa')
            pais_empresa = request.POST.get('pais_empresa')
            estado_empresa = request.POST.get('estado_empresa')
            direccion_empresa = request.POST.get('direccion_empresa')
            avatar_chatbot_empresa = request.POST.get('avatar_chatbot_empresa')

            if nombre_empresa:
                empresa_obj.nombre_empresa = nombre_empresa
            if descripcion_empresa is not None:
                empresa_obj.descripcion_empresa = descripcion_empresa
            if tipo_empresa:
                empresa_obj.tipo_empresa = tipo_empresa
            if sector_empresa is not None:
                empresa_obj.sector_empresa = sector_empresa
            if pais_empresa:
                empresa_obj.pais_empresa = pais_empresa
            if estado_empresa:
                empresa_obj.estado_empresa = estado_empresa
            if direccion_empresa:
                empresa_obj.direccion_empresa = direccion_empresa
            if avatar_chatbot_empresa:
                empresa_obj.avatar_chatbot_empresa = avatar_chatbot_empresa

            if 'logo_empresa' in request.FILES:
                empresa_obj.logo_empresa = request.FILES['logo_empresa']

            empresa_obj.save()
            # Procesar métodos de pago enviados desde el formulario (JSON en hidden input)
            metodos_procesados = 0
            metodos_creados = 0
            metodos_actualizados = 0
            metodos_eliminados = 0
            metodos_error = None
            try:
                # Esperamos un input oculto llamado metodos_pago_json con un array de objetos
                metodos_raw = request.POST.get('metodos_pago_json') or ''
                if metodos_raw:
                    try:
                        lista = json.loads(metodos_raw)
                    except Exception:
                        lista = []

                    from .models import MetodoPago

                    # IDs entrantes para decidir eliminación de los otros
                    incoming_ids = set()
                    incoming_tipos = set()

                    for item in lista:
                        metodos_procesados += 1
                        mid = item.get('id') or item.get('id_metodo')
                        tipo = item.get('tipo') or ''
                        instrucciones = item.get('instrucciones') or ''
                        nombre_beneficiario = item.get('nombre_beneficiario') or ''
                        numero_cuenta = item.get('numero_cuenta') or ''
                        banco = item.get('banco') or ''
                        tipo_cuenta = item.get('tipo_cuenta') or ''
                        identificador = item.get('identificador') or ''

                        if mid:
                            try:
                                mp = MetodoPago.objects.get(id_metodo=mid, empresa=empresa_obj)
                                creado = False
                            except MetodoPago.DoesNotExist:
                                mp = MetodoPago(empresa=empresa_obj)
                                creado = True
                        else:
                            # Si no viene id, crear siempre un nuevo registro.
                            # Esto permite que la empresa tenga varios métodos distintos (por ejemplo
                            # transferencia, pago_movil y paypal) con sus propios ids, en lugar de
                            # actualizar por tipo y sobrescribir uno sólo.
                            mp = MetodoPago(empresa=empresa_obj)
                            creado = True

                        # Asignar campos
                        if tipo:
                            mp.tipo = tipo
                        mp.instrucciones = instrucciones
                        mp.nombre_beneficiario = nombre_beneficiario
                        mp.numero_cuenta = numero_cuenta
                        mp.banco = banco
                        mp.tipo_cuenta = tipo_cuenta
                        mp.identificador = identificador
                        mp.activo = True

                        mp.save()

                        if creado:
                            metodos_creados += 1
                        else:
                            metodos_actualizados += 1

                        if getattr(mp, 'id_metodo', None):
                            incoming_ids.add(str(mp.id_metodo))
                        if mp.tipo:
                            incoming_tipos.add(mp.tipo)

                    # Eliminar métodos que pertenecen a la empresa pero no están en la lista entrante
                    # Solo eliminamos cuando el cliente envía IDs (edición/ eliminación explícita).
                    try:
                        qs_existentes = MetodoPago.objects.filter(empresa=empresa_obj)
                        if incoming_ids:
                            to_delete = qs_existentes.exclude(id_metodo__in=list(incoming_ids))
                            deleted_count = to_delete.count()
                            if deleted_count:
                                to_delete.delete()
                                metodos_eliminados = deleted_count
                        else:
                            # No eliminar nada si el cliente no envió IDs (evita borrar métodos existentes al crear nuevos registros)
                            metodos_eliminados = 0
                    except Exception:
                        # No bloquear el guardado del perfil si falla eliminación
                        metodos_error = 'Error al limpiar métodos antiguos'

            except Exception as e:
                logger.exception(f"Error procesando metodos_pago_json: {e}")
                metodos_error = str(e)

            # Si es AJAX, devolver JSON con datos de éxito y URLs relevantes
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                resp = {'success': True, 'message': 'Perfil de empresa actualizado correctamente.'}
                try:
                    if empresa_obj.logo_empresa and hasattr(empresa_obj.logo_empresa, 'url'):
                        resp['logo_url'] = empresa_obj.logo_empresa.url
                except Exception:
                    pass
                try:
                    resp['avatar_chatbot_empresa'] = empresa_obj.avatar_chatbot_empresa or ''
                except Exception:
                    resp['avatar_chatbot_empresa'] = ''

                # Adjuntar info de metodos
                resp.update({
                    'metodos_procesados': metodos_procesados,
                    'metodos_creados': metodos_creados,
                    'metodos_actualizados': metodos_actualizados,
                    'metodos_eliminados': metodos_eliminados,
                })
                if metodos_error:
                    resp['metodos_error'] = metodos_error
                return JsonResponse(resp)

            return redirect('perfil_empresa')
        except Exception as e:
            # Si es AJAX, devolver JSON con error
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Error al actualizar perfil: {str(e)}'})
            return render(request, 'ecommerce_app/editar_perfil_empresa.html',
                         {'empresa': empresa_obj, 'user_info': user_info, 'error': f'Error al actualizar perfil: {str(e)}', 'transferencia': transferencia, 'pago_movil': pago_movil, 'paypal': paypal})
    else:
        return render(request, 'ecommerce_app/editar_perfil_empresa.html', {'empresa': empresa_obj, 'user_info': user_info, 'transferencia': transferencia, 'pago_movil': pago_movil, 'paypal': paypal})
