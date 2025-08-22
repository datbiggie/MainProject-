import json
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
from .models import producto_empresa, servicio_empresa, producto_sucursal, servicio_sucursal, sucursal, imagen_producto_empresa, imagen_servicio_empresa, categoria_servicio_usuario, categoria_servicio_empresa, imagen_producto_usuario, producto_usuario, categoria_producto_usuario, categoria_producto_empresa

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

# Vista para eliminar servicio
from django.views.decorators.csrf import csrf_exempt
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
                    
                servicios_list.append({
                    'id_servicio_empresa': serv.id_servicio_empresa,
                    'nombre_servicio_empresa': serv.nombre_servicio_empresa,
                    'descripcion_servicio_empresa': serv.descripcion_servicio_empresa or '',
                    'imagen_url': imagen_url,
                    'categoria_servicio': serv.id_categoria_servicios_fk.nombre_categoria_serv_empresa if serv.id_categoria_servicios_fk else '',
                    'caracteristicas_generales_empresa': '',
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
                
                productos_list.append({
                    'id_producto_empresa': prod.id_producto_empresa,
                    'nombre_producto_empresa': prod.nombre_producto_empresa,
                    'descripcion_producto_empresa': prod.descripcion_producto_empresa or '',
                    'marca_producto_empresa': prod.marca_producto_empresa or '',
                    'modelo_producto_empresa': prod.modelo_producto_empresa or '',
                    'caracteristicas_generales_empresa': prod.caracteristicas_generales_empresa or '',
                    'categoria_producto': prod.id_categoria_prod_fk.nombre_categoria_prod_empresa if prod.id_categoria_prod_fk else '',
                    'serial': idx,
                    'imagen_url': imagen_url
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
                    'marca_producto_usuario': prod.marca_producto_usuario or '',
                    'modelo_producto_usuario': prod.modelo_producto_usuario or '',
                    'caracteristicas_generales_usuario': prod.caracteristicas_generales_usuario or '',
                    'categoria_producto': prod.id_categoria_prod_fk.nombre_categoria_prod_usuario if prod.id_categoria_prod_fk else '',
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
        categorias = list(categoria_producto_empresa.objects.filter(id_empresa_fk=current_user).values_list('nombre_categoria_prod_empresa', flat=True))
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
        categorias = list(categoria_servicio_empresa.objects.filter(id_empresa_fk=current_user).values_list('nombre_categoria_serv_empresa', flat=True))
    else:
        categorias = list(categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user).values_list('nombre_categoria_serv_usuario', flat=True))
    
    return JsonResponse({'categorias': categorias})
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
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
                rol_usuario='persona',          
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
            nombre_empresa = request.POST.get('nombre_empresa')
            correo_empresa = request.POST.get('correo_empresa')
            password_empresa = request.POST.get('password_empresa')
            confirm_password = request.POST.get('confirm_password')
            descripcion_empresa = request.POST.get('descripcion_empresa')
            logo_empresa = request.FILES.get('logo_empresa')
            pais_empresa = request.POST.get('pais_empresa')
            estado_empresa = request.POST.get('estado_empresa')
            tipo_empresa = request.POST.get('tipo_empresa')
            direccion_empresa = request.POST.get('direccion_empresa')
            latitud = request.POST.get('latitud')
            longitud = request.POST.get('longitud')

            # Validar que todos los campos estén completos
            if not nombre_empresa or not correo_empresa or not password_empresa or not confirm_password or not descripcion_empresa or not pais_empresa or not estado_empresa or not tipo_empresa or not direccion_empresa or not latitud or not longitud:
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

            # Validar que el correo no exista en la tabla usuario
            if usuario.objects.filter(correo_usuario=correo_empresa).exists():
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
            if empresa.objects.filter(correo_empresa=correo_empresa).exists():
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
                direccion_empresa=direccion_empresa,
                latitud_empresa=latitud,
                longitud_empresa=longitud
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
        categoria_producto_all = categoria_producto_empresa.objects.filter(id_empresa_fk=empresa_obj)
    else:
        # Para usuarios, usar categorías de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        categoria_producto_all = categoria_producto_usuario.objects.filter(id_usuario_fk=current_user)

    if request.method == 'POST':
        try:
            logger.info(f"Datos recibidos: {request.POST}")
            if account_type == 'empresa':
                nombre_producto = request.POST.get('nombre_producto_empresa', '').strip()
                descripcion_producto = request.POST.get('descripcion_producto_empresa', '').strip()
                marca_producto = request.POST.get('marca_producto_empresa', '').strip()
                modelo_producto = request.POST.get('modelo_producto_empresa', '').strip()
            else:
                nombre_producto = request.POST.get('nombre_producto_usuario', '').strip()
                descripcion_producto = request.POST.get('descripcion_producto_usuario', '').strip()
                marca_producto = request.POST.get('marca_producto_usuario', '').strip()
                modelo_producto = request.POST.get('modelo_producto_usuario', '').strip()
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
                    marca_producto_empresa=marca_producto,
                    modelo_producto_empresa=modelo_producto,
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
            else:
                categoria_producto_consul = categoria_producto_usuario.objects.get(id_categoria_prod_usuario=categoria_id)
                
                # Obtener los campos adicionales para usuario
                stock_producto = request.POST.get('stock_producto_usuario', 0)
                precio_producto = request.POST.get('precio_producto_usuario', 0)
                condicion_producto = request.POST.get('condicion_producto_usuario', 'Nuevo')
                estatus_producto = request.POST.get('estatus_producto_usuario', 'Activo')
                
                # Crear el producto para usuario
                nuevo_producto = producto_usuario(
                    nombre_producto_usuario=nombre_producto,
                    descripcion_producto_usuario=descripcion_producto,
                    marca_producto_usuario=marca_producto,
                    modelo_producto_usuario=modelo_producto,
                    caracteristicas_generales_usuario=caracteristicas_generales,
                    stock_producto_usuario=stock_producto,
                    precio_producto_usuario=precio_producto,
                    condicion_producto_usuario=condicion_producto,
                    estatus_producto_usuario=estatus_producto,
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
        categoria_servicio_all = categoria_servicio_empresa.objects.filter(id_empresa_fk=empresa_obj)
    else:
        # Para usuarios, usar categorías de usuario directamente
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        categoria_servicio_all = categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user)

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
        categ_producto_all = categoria_producto_empresa.objects.filter(id_empresa_fk=empresa_obj).order_by('-fecha_creacion_prod_empresa')
    else:
        # Para usuarios, usar categorías de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        categ_producto_all = categoria_producto_usuario.objects.filter(id_usuario_fk=current_user).order_by('-fecha_creacion_prod_usuario')
    
    # Logging básico
    logger.info(f"Total de categorías encontradas: {categ_producto_all.count()}")

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
        
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            return JsonResponse({'error': 'Usuario no autenticado'}, status=401)
        
        account_type = request.session.get('account_type', 'usuario')
        
        if account_type == 'empresa':
            categorias_query = categoria_producto_empresa.objects.filter(id_empresa_fk=current_user)
            
            # Filtrar por nombre si se proporciona
            if nombre:
                categorias_query = categorias_query.filter(nombre_categoria_prod_empresa__icontains=nombre)
            
            # Filtrar por estatus si se proporciona y no es 'todos'
            if estatus and estatus.lower() != 'todos':
                categorias_query = categorias_query.filter(estatus_categoria_prod_empresa=estatus)
            
            # Convertir a lista de diccionarios para la respuesta JSON
            categorias_list = list(categorias_query.values(
                'id_categoria_prod_empresa', 
                'nombre_categoria_prod_empresa', 
                'descripcion_categoria_prod_empresa', 
                'estatus_categoria_prod_empresa'
            ))
        else:
            categorias_query = categoria_producto_usuario.objects.filter(id_usuario_fk=current_user)
            
            # Filtrar por nombre si se proporciona
            if nombre:
                categorias_query = categorias_query.filter(nombre_categoria_prod_usuario__icontains=nombre)
            
            # Filtrar por estatus si se proporciona y no es 'todos'
            if estatus and estatus.lower() != 'todos':
                categorias_query = categorias_query.filter(estatus_categoria_prod_usuario=estatus)
            
            # Convertir a lista de diccionarios para la respuesta JSON
            categorias_list = list(categorias_query.values(
                'id_categoria_prod_usuario', 
                'nombre_categoria_prod_usuario', 
                'descripcion_categoria_prod_usuario', 
                'estatus_categoria_prod_usuario'
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
            categorias_query = categoria_servicio_empresa.objects.filter(id_empresa_fk=current_user)
            
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
                'estatus_categoria_serv_empresa'
            ))
        else:
            categorias_query = categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user)
            
            # Filtrar por nombre si se proporciona
            if nombre:
                categorias_query = categorias_query.filter(nombre_categoria_serv_usuario__icontains=nombre)
            
            # Filtrar por estatus si se proporciona y no es 'todos'
            if estatus and estatus.lower() != 'todos':
                categorias_query = categorias_query.filter(estatus_categoria_serv_usuario=estatus)
            
            # Convertir a lista de diccionarios para la respuesta JSON
            categorias_list = list(categorias_query.values(
                'id_categoria_serv_usuario', 
                'nombre_categoria_serv_usuario', 
                'descripcion_categoria_serv_usuario', 
                'estatus_categoria_serv_usuario'
            ))
        
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
        categ_servicio_all = categoria_servicio_empresa.objects.filter(id_empresa_fk=empresa_obj)
    else:
        # Para usuarios, usar categorías de usuario
        user_info = {
            'id': current_user.id_usuario,
            'nombre': current_user.nombre_usuario,
            'email': current_user.correo_usuario,
            'tipo': current_user.rol_usuario,
            'is_authenticated': True
        }
        categ_servicio_all = categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user)

    return render(request, 'ecommerce_app/categ_servicio_config.html', {
        'categoria_servicio': categ_servicio_all,
        'user_info': user_info
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
        categoria_producto_all = categoria_producto_empresa.objects.filter(id_empresa_fk=empresa_obj)
        
        # Agregar la primera imagen de cada producto
        productos_con_imagenes = []
        for prod in productos_all:
            primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
            prod.primera_imagen = primera_imagen
            productos_con_imagenes.append(prod)
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
        categoria_producto_all = categoria_producto_usuario.objects.filter(id_usuario_fk=current_user)
        
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
        'user_info': user_info
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
        categoria_servicio_all = categoria_servicio_empresa.objects.filter(id_empresa_fk=empresa_obj)
        
        # Agregar la primera imagen de cada servicio
        servicios_con_imagenes = []
        for serv in servicios_all:
            primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=serv).first()
            serv.primera_imagen = primera_imagen
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
        categoria_servicio_all = categoria_servicio_usuario.objects.filter(id_usuario_fk=current_user)
        
        # Agregar la primera imagen de cada servicio
        servicios_con_imagenes = []
        for serv in servicios_all:
            primera_imagen = imagen_servicio_usuario.objects.filter(id_servicio_fk=serv).first()
            serv.primera_imagen = primera_imagen
            servicios_con_imagenes.append(serv)
    
    return render(request, 'ecommerce_app/servicio_config.html', {
        'servicio_all': servicios_con_imagenes,
        'categoria_servicio_all': categoria_servicio_all,
        'user_info': user_info
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
                    producto_obj.marca_producto_empresa = request.POST.get('marca_producto_empresa')
                    producto_obj.modelo_producto_empresa = request.POST.get('modelo_producto_empresa')
                    producto_obj.caracteristicas_generales_empresa = request.POST.get('caracteristicas_generales')
                    
                    # Actualizar categoría si se proporciona
                    categoria_id = request.POST.get('categoria_producto')
                    if categoria_id:
                        try:
                            categoria_obj = categoria_producto_empresa.objects.get(id_categoria_prod_empresa=categoria_id)
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
                    producto_obj.marca_producto_usuario = request.POST.get('marca_producto_usuario')
                    producto_obj.modelo_producto_usuario = request.POST.get('modelo_producto_usuario')
                    producto_obj.caracteristicas_generales_usuario = request.POST.get('caracteristicas_generales')
                    
                    # Actualizar campos adicionales para usuarios
                    producto_obj.stock_producto_usuario = request.POST.get('stock_producto_usuario', 0)
                    producto_obj.precio_producto_usuario = request.POST.get('precio_producto_usuario', 0)
                    producto_obj.condicion_producto_usuario = request.POST.get('condicion_producto_usuario', 'Nuevo')
                    producto_obj.estatus_producto_usuario = request.POST.get('estatus_producto_usuario', 'Activo')
                    
                    # Actualizar categoría si se proporciona
                    categoria_id = request.POST.get('categoria_producto')
                    if categoria_id:
                        try:
                            categoria_obj = categoria_producto_usuario.objects.get(id_categoria_prod_usuario=categoria_id)
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
            
            if account_type == 'empresa':
                user_info = {
                    'id': current_user.id_empresa,
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'tipo': current_user.rol_empresa,
                    'is_authenticated': True,
                    'empresa_nombre': current_user.nombre_empresa
                }
            else:
                # Buscar empresa asociada para usuarios
                empresa_nombre = None
                try:
                    empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                    if empresa_obj:
                        empresa_nombre = empresa_obj.nombre_empresa
                except Exception as e:
                    empresa_nombre = None
                user_info = {
                    'id': current_user.id_usuario,
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'tipo': current_user.rol_usuario,
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
            
            if current_user and account_type == 'empresa':
                # Para empresas autenticadas viendo otro perfil
                user_info = {
                    'id': current_user.id_empresa,
                    'nombre': current_user.nombre_empresa,
                    'email': current_user.correo_empresa,
                    'tipo': account_type,
                    'is_authenticated': True,
                    'empresa_nombre': current_user.nombre_empresa
                }
            elif current_user and account_type == 'usuario':
                # Para usuarios autenticados viendo perfil de empresa
                user_info = {
                    'id': current_user.id_usuario,
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'tipo': account_type,
                    'is_authenticated': True
                }
            else:
                # Para perfiles públicos sin autenticación
                user_info = {
                    'is_authenticated': False,
                    'is_public_profile': True
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
                'empresa_nombre': current_user.nombre_empresa
            }
        elif current_user:
            # Para usuarios autenticados, buscar empresa asociada
            empresa_nombre = None
            try:
                empresa_obj = empresa.objects.filter(correo_empresa=current_user.correo_usuario).first()
                if empresa_obj:
                    empresa_nombre = empresa_obj.nombre_empresa
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
    
    return render(request, 'ecommerce_app/perfil_empresa.html', {
        'user_info': user_info,
        'empresa': empresa_obj,
        'productos_recientes': productos_recientes,
        'servicios_recientes': servicios_recientes
    })


def busquedad(request):
    query = request.GET.get('query', '')
    resultados_productos = []
    resultados_servicios = []
    resultados_empresas = []
    resultados_usuarios = []
    
    if query:
        # Determinar el tipo de búsqueda
        query_lower = query.lower().strip()
        
        # Palabras clave que indican búsqueda de productos/servicios
        palabras_producto = ['laptop', 'computadora', 'celular', 'telefono', 'ropa', 'zapatos', 'libro', 'mueble', 'casa', 'carro', 'auto']
        palabras_servicio = ['reparacion', 'mantenimiento', 'limpieza', 'consultoria', 'asesoria', 'diseño', 'programacion', 'corte', 'pintura']
        
        # Buscar empresas por nombre (prioridad alta)
        empresas_list = empresa.objects.filter(
            nombre_empresa__icontains=query
        )
        
        # Buscar usuarios por nombre (prioridad alta)
        usuarios_list = usuario.objects.filter(
            nombre_usuario__icontains=query
        )
        
        # Determinar si la búsqueda es para productos/servicios o personas/empresas
        es_busqueda_producto_servicio = any(palabra in query_lower for palabra in palabras_producto + palabras_servicio)
        es_busqueda_persona_empresa = len(query) <= 3 or query_lower in ['juan', 'maria', 'carlos', 'ana', 'empresa', 'tienda', 'negocio']
        
        # Solo buscar productos y servicios si:
        # 1. La búsqueda es específica para productos/servicios, O
        # 2. No se encontraron empresas/usuarios específicos Y la búsqueda es suficientemente larga
        if es_busqueda_producto_servicio or (len(query) > 3 and not empresas_list.exists() and not usuarios_list.exists()):
            # Buscar en productos_sucursal con estado activo (productos de empresa)
            productos_sucursal_list = producto_sucursal.objects.filter(
                id_producto_fk__nombre_producto_empresa__icontains=query,
                estatus_producto_sucursal='Activo'
            ).select_related('id_producto_fk', 'id_sucursal_fk')
            
            # Buscar en productos de usuario con estado activo
            productos_usuario_list = producto_usuario.objects.filter(
                nombre_producto_usuario__icontains=query,
                estatus_producto_usuario='Activo'
            )
            
            # Buscar en servicios_sucursal con estado activo (servicios de empresa)
            servicios_sucursal_list = servicio_sucursal.objects.filter(
                id_servicio_fk__nombre_servicio_empresa__icontains=query,
                estatus_servicio_sucursal='Activo'
            ).select_related('id_servicio_fk', 'id_sucursal_fk')
            
            # Buscar en servicios de usuario con estado activo
            servicios_usuario_list = servicio_usuario.objects.filter(
                nombre_servicio_usuario__icontains=query,
                estatus_servicio_usuario='Activo'
            )
        else:
            # Si se encontraron empresas o usuarios, no mostrar productos/servicios
            productos_sucursal_list = producto_sucursal.objects.none()
            productos_usuario_list = producto_usuario.objects.none()
            servicios_sucursal_list = servicio_sucursal.objects.none()
            servicios_usuario_list = servicio_usuario.objects.none()
        
        # Formatear resultados de productos de empresa
        for ps in productos_sucursal_list:
            # Obtener la primera imagen del producto desde la nueva tabla
            primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=ps.id_producto_fk).first()
            imagen_url = primera_imagen.ruta_imagen_producto_empresa.url if primera_imagen and primera_imagen.ruta_imagen_producto_empresa else None
            
            resultados_productos.append({
                'id': ps.id_producto_sucursal,
                'nombre': ps.id_producto_fk.nombre_producto_empresa,
                'descripcion': ps.id_producto_fk.descripcion_producto_empresa,
                'precio': ps.precio_producto_sucursal,
                'stock': ps.stock_producto_sucursal,
                'condicion': ps.condicion_producto_sucursal,
                'imagen': imagen_url,
                'sucursal': ps.id_sucursal_fk.nombre_sucursal,
                'tipo': 'producto',
                'origen': 'empresa'
            })
        
        # Formatear resultados de productos de usuario
        for pu in productos_usuario_list:
            # Obtener la primera imagen del producto de usuario
            primera_imagen = imagen_producto_usuario.objects.filter(id_producto_fk=pu).first()
            imagen_url = primera_imagen.ruta_imagen_producto_usuario.url if primera_imagen and primera_imagen.ruta_imagen_producto_usuario else None
            
            resultados_productos.append({
                'id': pu.id_producto_usuario,
                'nombre': pu.nombre_producto_usuario,
                'descripcion': pu.descripcion_producto_usuario,
                'precio': pu.precio_producto_usuario,
                'stock': pu.stock_producto_usuario,
                'condicion': pu.condicion_producto_usuario,
                'imagen': imagen_url,
                'sucursal': f"Usuario: {pu.id_usuario_fk.nombre_usuario}",
                'tipo': 'producto',
                'origen': 'usuario'
            })
        
        # Formatear resultados de servicios de empresa
        for ss in servicios_sucursal_list:
            # Obtener la primera imagen del servicio desde la nueva tabla
            primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=ss.id_servicio_fk).first()
            imagen_url = primera_imagen.ruta_imagen_servicio_empresa.url if primera_imagen and primera_imagen.ruta_imagen_servicio_empresa else None
            
            resultados_servicios.append({
                'id': ss.id_servicio_sucursal,
                'nombre': ss.id_servicio_fk.nombre_servicio_empresa,
                'descripcion': ss.id_servicio_fk.descripcion_servicio_empresa,
                'precio': ss.precio_servicio_sucursal if ss.precio_servicio_sucursal else 'Consultar',
                'imagen': imagen_url,
                'sucursal': ss.id_sucursal_fk.nombre_sucursal,
                'tipo': 'servicio',
                'origen': 'empresa'
            })
        
        # Formatear resultados de servicios de usuario
        for su in servicios_usuario_list:
            # Obtener la primera imagen del servicio de usuario
            primera_imagen = imagen_servicio_usuario.objects.filter(id_servicio_fk=su).first()
            imagen_url = primera_imagen.ruta_imagen_servicio_usuario.url if primera_imagen and primera_imagen.ruta_imagen_servicio_usuario else None
            
            resultados_servicios.append({
                'id': su.id_servicio_usuario,
                'nombre': su.nombre_servicio_usuario,
                'descripcion': su.descripcion_servicio_usuario,
                'precio': su.precio_servicio_usuario if su.precio_servicio_usuario else 'Consultar',
                'imagen': imagen_url,
                'sucursal': f"Usuario: {su.id_usuario_fk.nombre_usuario}",
                'tipo': 'servicio',
                'origen': 'usuario'
            })
        
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
    
    # Combinar resultados
    resultados_combinados = resultados_productos + resultados_servicios + resultados_empresas + resultados_usuarios
    
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
        'resultados': resultados_combinados,
        'total_resultados': len(resultados_combinados),
        'resultados_productos': resultados_productos,
        'resultados_servicios': resultados_servicios,
        'resultados_empresas': resultados_empresas,
        'resultados_usuarios': resultados_usuarios,
        'user_info': user_info
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
                
                resultado = {
                    'id': ps.id_producto_sucursal,
                    'nombre': ps.id_producto_fk.nombre_producto_empresa,
                    'descripcion': ps.id_producto_fk.descripcion_producto_empresa,
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
                primera_imagen = imagen_servicio_empresa.objects.filter(id_servicio_fk=ss.id_servicio_fk).first()
                imagen_url = primera_imagen.ruta_imagen_servicio_empresa.url if primera_imagen and primera_imagen.ruta_imagen_servicio_empresa else None
                
                resultado = {
                    'id': ss.id_servicio_sucursal,
                    'nombre': ss.id_servicio_fk.nombre_servicio_empresa,
                    'descripcion': ss.id_servicio_fk.descripcion_servicio_empresa,
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
                        'id': producto.id_producto_empresa,
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
        'pedidos_pendientes': pedidos_pendientes
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
                        'estatus': producto_sucursal_obj.estatus_producto_sucursal
                    }
                    
                    item_data = {
                        'id': producto.id_producto_empresa,
                        'nombre': producto.nombre_producto_empresa,
                        'descripcion': producto.descripcion_producto_empresa,
                        'marca': producto.marca_producto_empresa,
                        'modelo': producto.modelo_producto_empresa,
                        'caracteristicas': producto.caracteristicas_generales_empresa,
                        'tipo': 'producto',
                        'tipo_propietario': 'empresa',
                        'empresa': producto.id_empresa_fk.nombre_empresa,
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
                                'estatus': producto_sucursal_obj.estatus_producto_sucursal
                            }
                        
                        item_data = {
                            'id': producto.id_producto_empresa,
                            'nombre': producto.nombre_producto_empresa,
                            'descripcion': producto.descripcion_producto_empresa,
                            'tipo_propietario': 'empresa',
                            'marca': producto.marca_producto_empresa,
                            'modelo': producto.modelo_producto_empresa,
                            'caracteristicas': producto.caracteristicas_generales_empresa,
                            'tipo': 'producto',
                            'empresa': producto.id_empresa_fk.nombre_empresa,
                            'sucursal': sucursal_info
                        }
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
                        'estatus': producto.estatus_producto_usuario
                    }
                    
                    item_data = {
                        'id': producto.id_producto_usuario,
                        'nombre': producto.nombre_producto_usuario,
                        'descripcion': producto.descripcion_producto_usuario,
                        'marca': producto.marca_producto_usuario,
                        'modelo': producto.modelo_producto_usuario,
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
                        'estatus': servicio_sucursal_obj.estatus_servicio_sucursal
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
        
        context = {
            'item': item_data,
            'imagenes': imagenes,
            'user_info': user_info
        }
        
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



def perfil_usuario(request):
    # Obtener información del usuario si está autenticado
    user_info = None
    usuario_obj = None
    
    # Verificar si se está solicitando un perfil específico por ID
    usuario_id = request.GET.get('id')
    if usuario_id:
        try:
            usuario_obj = usuario.objects.get(id_usuario=usuario_id)
            # Para perfiles públicos, no necesitamos user_info completo
            user_info = {
                'is_authenticated': False,
                'is_public_profile': True
            }
        except usuario.DoesNotExist:
            # Si no existe el usuario, redirigir o mostrar error
            return render(request, 'ecommerce_app/perfil_usuario.html', {
                'error': 'Usuario no encontrado',
                'user_info': {'is_authenticated': False}
            })
    else:
        # Verificar si hay usuario autenticado
        current_user = None
        if is_user_authenticated(request):
            current_user = get_current_user(request)
        
        account_type = request.session.get('account_type', 'usuario')
        
        if current_user and account_type == 'usuario':
            # Para usuarios autenticados, current_user ya es el usuario
            usuario_obj = current_user
            user_info = {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre_usuario,
                'email': current_user.correo_usuario,
                'tipo': current_user.rol_usuario,
                'is_authenticated': True
            }
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
    
    return render(request, 'ecommerce_app/perfil_usuario.html', {
        'user_info': user_info,
        'usuario': usuario_obj
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
            productos_query = producto_empresa.objects.filter(id_empresa_fk=empresa_obj).select_related('id_categoria_prod_fk')
            productos_con_imagenes = []
            productos_por_categoria = defaultdict(list)
            
            for prod in productos_query:
                primera_imagen = imagen_producto_empresa.objects.filter(id_producto_fk=prod).first()
                prod.primera_imagen = primera_imagen
                productos_con_imagenes.append(prod)
                
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
                    'empresa_nombre': current_user.nombre_empresa
                })
            elif current_user:
                user_info.update({
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'id': current_user.id_usuario
                })
            
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
                    'id': current_user.id_usuario
                })
            
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
                    'empresa_nombre': current_user.nombre_empresa
                })
            elif current_user:
                user_info.update({
                    'nombre': current_user.nombre_usuario,
                    'email': current_user.correo_usuario,
                    'id': current_user.id_usuario
                })
            
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
                    'id': current_user.id_usuario
                })
            
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


@csrf_exempt
@require_POST
def agregar_al_carrito(request):
    """Vista para agregar productos al carrito"""
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
        
        # Obtener datos del request
        producto_id = request.POST.get('producto_id')
        tipo_producto = request.POST.get('tipo_propietario')  # 'empresa' o 'usuario'
        cantidad = int(request.POST.get('cantidad', 1))
        
        if not producto_id or not tipo_producto:
            return JsonResponse({
                'success': False,
                'message': 'Datos incompletos'
            }, status=400)
        
        account_type = request.session.get('account_type', 'usuario')
        
        # Lógica para empresas
        if account_type == 'empresa':
            # Buscar carrito existente (activo o pendiente)
            carrito = carrito_compra_producto_empresa.objects.filter(
                id_empresa_fk=current_user,
                estatuscarrito_prod_empresa__in=['activo', 'pendiente']
            ).first()
            
            created = False
            if not carrito:
                # Si no existe carrito, crear uno nuevo con estatus activo
                carrito = carrito_compra_producto_empresa.objects.create(
                    id_empresa_fk=current_user,
                    estatuscarrito_prod_empresa='activo',
                    total_carrito_prod_empresa=0
                )
                created = True
            
            # Obtener el producto y su precio
            if tipo_producto == 'empresa':
                try:
                    producto_sucursal_obj = producto_sucursal.objects.get(id_producto_sucursal=producto_id)
                    precio = producto_sucursal_obj.precio_producto_sucursal
                    stock_disponible = producto_sucursal_obj.stock_producto_sucursal
                    
                    # Validar stock disponible
                    if cantidad > stock_disponible:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad solicitada ({cantidad}) excede el stock disponible ({stock_disponible} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Verificar si ya existe en el carrito
                    detalle_existente = detalle_compra_producto_empresa.objects.filter(
                        id_fk_carritocompra_empresa=carrito,
                        id_fk_producto_sucursal_empresa=producto_sucursal_obj
                    ).first()
                    
                    if detalle_existente:
                        # Validar stock con cantidad existente en carrito
                        nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_empresa + cantidad
                        if nueva_cantidad_total > stock_disponible:
                            return JsonResponse({
                                'success': False,
                                'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({stock_disponible} unidades)',
                                'stock_insuficiente': True
                            }, status=400)
                        
                        # Actualizar cantidad
                        detalle_existente.cantidad_deta_carrito_prod_empresa += cantidad
                        detalle_existente.subtotal_deta_carrito_prod_empresa = (
                            detalle_existente.cantidad_deta_carrito_prod_empresa * precio
                        )
                        detalle_existente.save()
                    else:
                        # Crear nuevo detalle
                        detalle_compra_producto_empresa.objects.create(
                            id_fk_carritocompra_empresa=carrito,
                            id_fk_producto_sucursal_empresa=producto_sucursal_obj,
                            cantidad_deta_carrito_prod_empresa=cantidad,
                            precio_unit_deta_carrito_prod_empresa=precio,
                            subtotal_deta_carrito_prod_empresa=cantidad * precio
                        )
                        
                except producto_sucursal.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto de empresa no encontrado'
                    }, status=404)
                    
            elif tipo_producto == 'usuario':
                try:
                    producto_usuario_obj = producto_usuario.objects.get(id_producto_usuario=producto_id)
                    precio = producto_usuario_obj.precio_producto_usuario
                    stock_disponible = producto_usuario_obj.stock_producto_usuario
                    
                    # Validar stock disponible
                    if cantidad > stock_disponible:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad solicitada ({cantidad}) excede el stock disponible ({stock_disponible} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Verificar si ya existe en el carrito
                    detalle_existente = detalle_compra_producto_empresa.objects.filter(
                        id_fk_carritocompra_empresa=carrito,
                        idproducto_fk_usuario=producto_usuario_obj
                    ).first()
                    
                    if detalle_existente:
                        # Validar stock con cantidad existente en carrito
                        nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_empresa + cantidad
                        if nueva_cantidad_total > stock_disponible:
                            return JsonResponse({
                                'success': False,
                                'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({stock_disponible} unidades)',
                                'stock_insuficiente': True
                            }, status=400)
                        
                        # Actualizar cantidad
                        detalle_existente.cantidad_deta_carrito_prod_empresa += cantidad
                        detalle_existente.subtotal_deta_carrito_prod_empresa = (
                            detalle_existente.cantidad_deta_carrito_prod_empresa * precio
                        )
                        detalle_existente.save()
                    else:
                        # Crear nuevo detalle
                        detalle_compra_producto_empresa.objects.create(
                            id_fk_carritocompra_empresa=carrito,
                            idproducto_fk_usuario=producto_usuario_obj,
                            cantidad_deta_carrito_prod_empresa=cantidad,
                            precio_unit_deta_carrito_prod_empresa=precio,
                            subtotal_deta_carrito_prod_empresa=cantidad * precio
                        )
                        
                except producto_usuario.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto de usuario no encontrado'
                    }, status=404)
        
        # Lógica para usuarios
        else:
            # Buscar carrito existente (activo o pendiente)
            carrito = carrito_compra_producto_usuario.objects.filter(
                id_usuario_fk=current_user,
                estatuscarrito_prod_usuario__in=['activo', 'pendiente']
            ).first()
            
            created = False
            if not carrito:
                # Si no existe carrito, crear uno nuevo con estatus activo
                carrito = carrito_compra_producto_usuario.objects.create(
                    id_usuario_fk=current_user,
                    estatuscarrito_prod_usuario='activo',
                    total_carrito_prod_usuario=0
                )
                created = True
            
            # Obtener el producto y su precio
            if tipo_producto == 'empresa':
                try:
                    producto_sucursal_obj = producto_sucursal.objects.get(id_producto_sucursal=producto_id)
                    precio = producto_sucursal_obj.precio_producto_sucursal
                    stock_disponible = producto_sucursal_obj.stock_producto_sucursal
                    
                    # Validar stock disponible
                    if cantidad > stock_disponible:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad solicitada ({cantidad}) excede el stock disponible ({stock_disponible} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Verificar si ya existe en el carrito
                    detalle_existente = detalle_compra_producto_usuario.objects.filter(
                        id_fk_carritocompra_usuario=carrito,
                        id_fk_producto_sucursal_empresa=producto_sucursal_obj
                    ).first()
                    
                    if detalle_existente:
                        # Validar stock con cantidad existente en carrito
                        nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_usuario + cantidad
                        if nueva_cantidad_total > stock_disponible:
                            return JsonResponse({
                                'success': False,
                                'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({stock_disponible} unidades)',
                                'stock_insuficiente': True
                            }, status=400)
                        
                        # Actualizar cantidad
                        detalle_existente.cantidad_deta_carrito_prod_usuario += cantidad
                        detalle_existente.subtotal_deta_carrito_prod_usuario = (
                            detalle_existente.cantidad_deta_carrito_prod_usuario * precio
                        )
                        detalle_existente.save()
                    else:
                        # Crear nuevo detalle
                        detalle_compra_producto_usuario.objects.create(
                            id_fk_carritocompra_usuario=carrito,
                            id_fk_producto_sucursal_empresa=producto_sucursal_obj,
                            cantidad_deta_carrito_prod_usuario=cantidad,
                            precio_unit_deta_carrito_prod_usuario=precio,
                            subtotal_deta_carrito_prod_usuario=cantidad * precio
                        )
                        
                except producto_sucursal.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto de empresa no encontrado'
                    }, status=404)
                    
            elif tipo_producto == 'usuario':
                try:
                    producto_usuario_obj = producto_usuario.objects.get(id_producto_usuario=producto_id)
                    precio = producto_usuario_obj.precio_producto_usuario
                    stock_disponible = producto_usuario_obj.stock_producto_usuario
                    
                    # Validar stock disponible
                    if cantidad > stock_disponible:
                        return JsonResponse({
                            'success': False,
                            'message': f'La cantidad solicitada ({cantidad}) excede el stock disponible ({stock_disponible} unidades)',
                            'stock_insuficiente': True
                        }, status=400)
                    
                    # Verificar si ya existe en el carrito
                    detalle_existente = detalle_compra_producto_usuario.objects.filter(
                        id_fk_carritocompra_usuario=carrito,
                        idproducto_fk_usuario=producto_usuario_obj
                    ).first()
                    
                    if detalle_existente:
                        # Validar stock con cantidad existente en carrito
                        nueva_cantidad_total = detalle_existente.cantidad_deta_carrito_prod_usuario + cantidad
                        if nueva_cantidad_total > stock_disponible:
                            return JsonResponse({
                                'success': False,
                                'message': f'La cantidad total ({nueva_cantidad_total}) excedería el stock disponible ({stock_disponible} unidades)',
                                'stock_insuficiente': True
                            }, status=400)
                        
                        # Actualizar cantidad
                        detalle_existente.cantidad_deta_carrito_prod_usuario += cantidad
                        detalle_existente.subtotal_deta_carrito_prod_usuario = (
                            detalle_existente.cantidad_deta_carrito_prod_usuario * precio
                        )
                        detalle_existente.save()
                    else:
                        # Crear nuevo detalle
                        detalle_compra_producto_usuario.objects.create(
                            id_fk_carritocompra_usuario=carrito,
                            idproducto_fk_usuario=producto_usuario_obj,
                            cantidad_deta_carrito_prod_usuario=cantidad,
                            precio_unit_deta_carrito_prod_usuario=precio,
                            subtotal_deta_carrito_prod_usuario=cantidad * precio
                        )
                        
                except producto_usuario.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto de usuario no encontrado'
                    }, status=404)
        
        # Actualizar total del carrito
        if account_type == 'empresa':
            total = sum(
                detalle.subtotal_deta_carrito_prod_empresa 
                for detalle in carrito.detalles.all()
            )
            carrito.total_carrito_prod_empresa = total
        else:
            total = sum(
                detalle.subtotal_deta_carrito_prod_usuario 
                for detalle in carrito.detalles.all()
            )
            carrito.total_carrito_prod_usuario = total
        
        carrito.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto agregado al carrito exitosamente',
            'carrito_created': created
        })
        
    except Exception as e:
        logger.error(f"Error al agregar producto al carrito: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
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
            
            # Actualizar la cantidad y recalcular subtotal
            detalle.cantidad_deta_carrito_prod_empresa = int(nueva_cantidad)
            detalle.subtotal_deta_carrito_prod_empresa = detalle.cantidad_deta_carrito_prod_empresa * detalle.precio_unit_deta_carrito_prod_empresa
            detalle.save()
            
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
            
            # Actualizar la cantidad y recalcular subtotal
            detalle.cantidad_deta_carrito_prod_usuario = int(nueva_cantidad)
            detalle.subtotal_deta_carrito_prod_usuario = detalle.cantidad_deta_carrito_prod_usuario * detalle.precio_unit_deta_carrito_prod_usuario
            detalle.save()
            
            # Recalcular el total del carrito
            total = sum(
                d.subtotal_deta_carrito_prod_usuario 
                for d in carrito.detalles.all()
            )
            carrito.total_carrito_prod_usuario = total
            carrito.save()
        
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
        producto_id = data.get('producto_id')
        
        if not producto_id:
            return JsonResponse({
                'success': False,
                'message': 'ID del producto es requerido'
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
            try:
                detalle = detalle_compra_producto_empresa.objects.get(
                    id_fk_carritocompra_empresa=carrito,
                    id_fk_producto_sucursal_empresa_id=producto_id
                )
                detalle.delete()
                
                # Recalcular el total del carrito
                total = sum(
                    d.subtotal_deta_carrito_prod_empresa 
                    for d in carrito.detalles.all()
                )
                carrito.total_carrito_prod_empresa = total
                carrito.save()
                
            except detalle_compra_producto_empresa.DoesNotExist:
                # Intentar buscar por producto de usuario
                try:
                    detalle = detalle_compra_producto_empresa.objects.get(
                        id_fk_carritocompra_empresa=carrito,
                        idproducto_fk_usuario_id=producto_id
                    )
                    detalle.delete()
                    
                    # Recalcular el total del carrito
                    total = sum(
                        d.subtotal_deta_carrito_prod_empresa 
                        for d in carrito.detalles.all()
                    )
                    carrito.total_carrito_prod_empresa = total
                    carrito.save()
                    
                except detalle_compra_producto_empresa.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado en el carrito'
                    }, status=404)
        
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
            try:
                detalle = detalle_compra_producto_usuario.objects.get(
                    id_fk_carritocompra_usuario=carrito,
                    idproducto_fk_usuario_id=producto_id
                )
                detalle.delete()
                
                # Recalcular el total del carrito
                total = sum(
                    d.subtotal_deta_carrito_prod_usuario 
                    for d in carrito.detalles.all()
                )
                carrito.total_carrito_prod_usuario = total
                carrito.save()
                
            except detalle_compra_producto_usuario.DoesNotExist:
                # Intentar buscar por producto de sucursal
                try:
                    detalle = detalle_compra_producto_usuario.objects.get(
                        id_fk_carritocompra_usuario=carrito,
                        id_fk_producto_sucursal_empresa_id=producto_id
                    )
                    detalle.delete()
                    
                    # Recalcular el total del carrito
                    total = sum(
                        d.subtotal_deta_carrito_prod_usuario 
                        for d in carrito.detalles.all()
                    )
                    carrito.total_carrito_prod_usuario = total
                    carrito.save()
                    
                except detalle_compra_producto_usuario.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Producto no encontrado en el carrito'
                    }, status=404)
        
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
                        
                        vendedor_id = producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.id_empresa
                        vendedor_nombre = producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.nombre_empresa
                        
                        if vendedor_id not in productos_por_empresa:
                            productos_por_empresa[vendedor_id] = []
                        
                        productos_por_empresa[vendedor_id].append({
                            'id': producto.id_producto_empresa,
                            'nombre': producto.nombre_producto_empresa,
                            'descripcion': producto.descripcion_producto_empresa,
                            'cantidad': detalle.cantidad_deta_carrito_prod_empresa,
                            'precio_unitario': detalle.precio_unit_deta_carrito_prod_empresa,
                            'subtotal': detalle.subtotal_deta_carrito_prod_empresa,
                            'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                            'vendedor_id': vendedor_id,
                            'vendedor_nombre': vendedor_nombre
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
                
                # Agregar cada empresa como un vendedor separado
                for empresa_id, productos in productos_por_empresa.items():
                    productos_por_vendedor[f'empresa_{empresa_id}'] = productos
                
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
                        
                        vendedor_id = producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.id_empresa
                        vendedor_nombre = producto_sucursal_obj.id_sucursal_fk.id_empresa_fk.nombre_empresa
                        
                        if vendedor_id not in productos_por_empresa:
                            productos_por_empresa[vendedor_id] = []
                        
                        productos_por_empresa[vendedor_id].append({
                            'id': producto.id_producto_empresa,
                            'nombre': producto.nombre_producto_empresa,
                            'descripcion': producto.descripcion_producto_empresa,
                            'cantidad': detalle.cantidad_deta_carrito_prod_usuario,
                            'precio_unitario': detalle.precio_unit_deta_carrito_prod_usuario,
                            'subtotal': detalle.subtotal_deta_carrito_prod_usuario,
                            'imagen': imagen.ruta_imagen_producto_empresa.url if imagen else None,
                            'vendedor_id': vendedor_id,
                            'vendedor_nombre': vendedor_nombre
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
                
                # Agregar cada empresa como un vendedor separado
                for empresa_id, productos in productos_por_empresa.items():
                    productos_por_vendedor[f'empresa_{empresa_id}'] = productos
                
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
        
        # Separar productos por vendedor (empresa/usuario) para crear pedidos agrupados
        print(f"Separando productos por vendedor...")
        print(f"Total productos en carrito antes del filtrado: {len(productos_carrito)}")
        for i, prod in enumerate(productos_carrito[:3]):  # Solo mostrar los primeros 3
            print(f"Producto {i+1}: tipo={prod.get('tipo')}, id={prod.get('id')}, nombre={prod.get('nombre')}")
            if prod['tipo'] == 'empresa' and 'producto_sucursal_obj' in prod:
                empresa_id = prod['producto_sucursal_obj'].id_sucursal_fk.id_empresa_fk.id_empresa
                print(f"  -> Empresa ID: {empresa_id}, vendedor_key: empresa_{empresa_id}")
            elif prod['tipo'] == 'usuario' and 'producto_usuario_obj' in prod:
                usuario_id = prod['producto_usuario_obj'].id_usuario_fk.id_usuario
                print(f"  -> Usuario ID: {usuario_id}, vendedor_key: usuario_{usuario_id}")
        productos_por_empresa = {}
        productos_por_usuario = {}
        
        for producto in productos_carrito:
            if producto['tipo'] == 'empresa':
                # Agrupar por sucursal/empresa
                if 'producto_sucursal_obj' in producto:
                    sucursal_id = producto['producto_sucursal_obj'].id_sucursal_fk.id_sucursal
                    empresa_id = producto['producto_sucursal_obj'].id_sucursal_fk.id_empresa_fk.id_empresa
                    
                    # Filtrar por vendedores seleccionados si no es "finalizar todos"
                    if vendedores_a_procesar is not None:
                        vendedor_key = f"empresa_{empresa_id}"
                        if vendedor_key not in vendedores_a_procesar:
                            continue  # Saltar este producto si el vendedor no está seleccionado
                    
                    if empresa_id not in productos_por_empresa:
                        productos_por_empresa[empresa_id] = {
                            'empresa_obj': producto['producto_sucursal_obj'].id_sucursal_fk.id_empresa_fk,
                            'productos': [],
                            'total': 0
                        }
                    
                    productos_por_empresa[empresa_id]['productos'].append(producto)
                    productos_por_empresa[empresa_id]['total'] += producto['subtotal']
            
            elif producto['tipo'] == 'usuario':
                # Agrupar por usuario vendedor
                if 'producto_usuario_obj' in producto:
                    usuario_id = producto['producto_usuario_obj'].id_usuario_fk.id_usuario
                    
                    # Filtrar por vendedores seleccionados si no es "finalizar todos"
                    if vendedores_a_procesar is not None:
                        vendedor_key = f"usuario_{usuario_id}"
                        if vendedor_key not in vendedores_a_procesar:
                            continue  # Saltar este producto si el vendedor no está seleccionado
                    
                    if usuario_id not in productos_por_usuario:
                        productos_por_usuario[usuario_id] = {
                            'usuario_obj': producto['producto_usuario_obj'].id_usuario_fk,
                            'productos': [],
                            'total': 0
                        }
                    
                    productos_por_usuario[usuario_id]['productos'].append(producto)
                    productos_por_usuario[usuario_id]['total'] += producto['subtotal']
        
        print(f"Productos agrupados (filtrados) - Empresas: {len(productos_por_empresa)}, Usuarios: {len(productos_por_usuario)}")
        
        # Verificar que hay productos para procesar
        if not productos_por_empresa and not productos_por_usuario:
            return JsonResponse({'success': False, 'error': 'No hay productos seleccionados para procesar'})
        
        # Crear pedidos según el tipo de cuenta del comprador
        pedidos_creados = []
        
        with transaction.atomic():
            if account_type == 'empresa':
                print("Creando pedidos para empresa compradora...")
                
                # Crear pedidos de empresa para productos de empresas
                for empresa_id, grupo in productos_por_empresa.items():
                    nuevo_pedido = pedido_empresa.objects.create(
                        id_carrito_fk=carrito_empresa,
                        numero_pedido=f"{numero_pedido}-EMP{empresa_id}",
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
                    
                    pedidos_creados.append({
                        'tipo': 'empresa',
                        'id': nuevo_pedido.id_pedido_empresa,
                        'vendedor': grupo['empresa_obj'].nombre_empresa,
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
                    
                    pedidos_creados.append({
                        'tipo': 'empresa',
                        'id': nuevo_pedido.id_pedido_empresa,
                        'vendedor': grupo['usuario_obj'].nombre_usuario,
                        'total': float(grupo['total'])
                    })
            
            else:  # account_type == 'usuario'
                print("Creando pedidos para usuario comprador...")
                
                # Crear pedidos de usuario para productos de empresas
                for empresa_id, grupo in productos_por_empresa.items():
                    nuevo_pedido = pedido_usuario.objects.create(
                        id_carrito_fk=carrito_usuario,
                        numero_pedido=f"{numero_pedido}-EMP{empresa_id}",
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
                    
                    pedidos_creados.append({
                        'tipo': 'usuario',
                        'id': nuevo_pedido.id_pedido_usuario,
                        'vendedor': grupo['empresa_obj'].nombre_empresa,
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
            productos_procesados = sum(len(grupo['productos']) for grupo in productos_por_empresa.values()) + \
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
            
            # Eliminar productos de empresas procesados
            for empresa_id, grupo in productos_por_empresa.items():
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
def mis_ventas(request):
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
        
        return render(request, 'ecommerce_app/mis_ventas.html', context)
        
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
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                    else:
                        nombre_producto = "Producto no disponible"
                        imagen_url = None
                    
                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url
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
                    'tipo_pedido': 'empresa'
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
                        imagen = imagen_producto_empresa.objects.filter(
                            id_producto_fk=detalle.id_fk_producto_sucursal_empresa.id_producto_fk
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_empresa.url if imagen else None
                    elif detalle.idproducto_fk_usuario:
                        nombre_producto = detalle.idproducto_fk_usuario.nombre_producto_usuario
                        imagen = imagen_producto_usuario.objects.filter(
                            id_producto_fk=detalle.idproducto_fk_usuario
                        ).first()
                        imagen_url = imagen.ruta_imagen_producto_usuario.url if imagen else None
                    else:
                        nombre_producto = "Producto no disponible"
                        imagen_url = None
                    
                    detalles_list.append({
                        'nombre_producto': nombre_producto,
                        'cantidad': detalle.cantidad_detalle_pedido,
                        'precio_unitario': float(detalle.precio_unitario_pedido),
                        'subtotal': float(detalle.subtotal_detalle_pedido),
                        'imagen': imagen_url
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
                    'tipo_pedido': 'usuario'
                })
        
        context = {
            'user_info': user_info,
            'account_type': account_type,
            'pedidos_historial': pedidos_historial,
            'total_pedidos': len(pedidos_historial)
        }
        
        return render(request, 'ecommerce_app/mis_pedidos.html', context)
        
    except Exception as e:
        logger.error(f"Error en función mis_pedidos: {str(e)}")
        return redirect('/ecommerce/carrito')
        
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
        
        # Cambiar el estado a 'confirmado'
        pedido_encontrado.estado_pedido = 'confirmado'
        pedido_encontrado.save()
        
        logger.info(f"Pedido {numero_pedido} confirmado por {account_type} {current_user}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Venta confirmada exitosamente',
            'nuevo_estado': 'confirmado'
        })
        
    except Exception as e:
        logger.error(f"Error en función confirmar_venta: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'})