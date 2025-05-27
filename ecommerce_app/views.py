from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from .models import *
import logging

# Configurar el logger
logger = logging.getLogger(__name__)

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
                        return JsonResponse({'success': True, 'message': 'Inicio de sesión exitoso'})
                    else:
                        return JsonResponse({'success': False, 'message': 'Contraseña incorrecta'})
                else:
                    # Si está hasheada, usar check_password
                    if check_password(password, user.password_usuario):
                        return JsonResponse({'success': True, 'message': 'Inicio de sesión exitoso'})
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

        nuevo_usuario = usuario(
            nombre_usuario=nombre_usuario + ' ' + apellido,
            correo_usuario=email,
            telefono_usuario=telefono,
            password_usuario=password,
            autenticacion_usuario='local',  
            tipo_usuario='persona',          
            fecha_nacimiento=fecha_nacimiento,
            pais=pais,
            estado=estado
        )
        nuevo_usuario.save()
        return redirect('/ecommerce/registrar_persona/?success=true')

    return render(request, 'ecommerce_app/registrar_persona.html')

def registrar_empresa(request):
    usuario_obj = usuario.objects.get(id_usuario=6)
    if request.method=='POST':
        logger.info(f"Datos recibidos: {request.POST}")
        nombre_empresa=request.POST.get('nombre_empresa')
        descripcion_empresa=request.POST.get('descripcion_empresa')
        logo_empresa=request.FILES.get('logo_empresa')
        pais_empresa=request.POST.get('pais_empresa')
        estado_empresa=request.POST.get('estado_empresa')
        tipo_empresa=request.POST.get('tipo_empresa')
        direccion_empresa=request.POST.getlist('direccion_empresa')[0]  # Tomar el primer valor de la lista
        latitud=request.POST.get('latitud')
        longitud=request.POST.get('longitud')
        id_usuario_fk=request.POST.get('id_usuario_fk')

        # Logging para verificar los datos
        logger.info(f"Dirección recibida: {direccion_empresa}")
        logger.info(f"Tipo de dirección: {type(direccion_empresa)}")

        try:
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
                id_usuario_fk=usuario_obj
            )
            nueva_empresa.save()
            logger.info(f"Empresa guardada exitosamente: {nueva_empresa.nombre_empresa}")
            logger.info(f"Dirección guardada: {nueva_empresa.direccion_empresa}")
            return redirect('/ecommerce/registrar_empresa/?success=true')
        except Exception as e:
            logger.error(f"Error al guardar la empresa: {str(e)}")
            return render(request, 'ecommerce_app/registrar_empresa.html', {'error': str(e)})
    return render(request, 'ecommerce_app/registrar_empresa.html')



def sucursalfuncion(request):
    # Obtener todas las sucursales
    sqlsucursal = sucursal.objects.all()
    
    # Obtener la empresa actual (por ahora hardcodeada)
    empresa_obj = empresa.objects.get(id_empresa=8)
   
    if request.method == 'POST':
        logger.info(f"Datos POST recibidos: {request.POST}")
        logger.info(f"Archivos recibidos: {request.FILES}")
        
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
            logger.info(f"Sucursal guardada exitosamente: {nueva_sucursal.nombre_sucursal}")
            
           
            

            
            return redirect('/ecommerce/sucursal/?success=true')
        except Exception as e:
            logger.error(f"Error al guardar la sucursal: {str(e)}")
            logger.error(f"Traceback completo: {e.__traceback__}")
            return render(request, 'ecommerce_app/sucursal.html', {
                'error': str(e),
            })

    # Pasar las sucursales al template
    return render(request, 'ecommerce_app/sucursal.html', {
        'sqlsucursal': sqlsucursal,
        
        'success': request.GET.get('success')
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
            logger.info(f"Sucursal actualizada exitosamente: {sucursal_obj.nombre_sucursal}")
            return redirect('/ecommerce/sucursal/?updated=true')
        except Exception as e:
            logger.error(f"Error al actualizar la sucursal: {str(e)}")
            return redirect('/ecommerce/sucursal/?error=true')
    
    return redirect('/ecommerce/sucursal/')



def eliminar_sucursal(request):
    if request.method == 'POST':
        try:
            id_sucursal = request.POST.get('id_sucursal')
            sucursal_obj = sucursal.objects.get(id_sucursal=id_sucursal)
            nombre_sucursal = sucursal_obj.nombre_sucursal
            sucursal_obj.delete()
            logger.info(f"Sucursal eliminada exitosamente: {nombre_sucursal}")
            return redirect('/ecommerce/sucursal/?deleted=true')
        except Exception as e:
            logger.error(f"Error al eliminar la sucursal: {str(e)}")
            return redirect('/ecommerce/sucursal/?error=true')
    
    return redirect('/ecommerce/sucursal/')





def producto_funcion(request):
    empresa_obj = empresa.objects.get(id_empresa=8)
    categoria_producto_all = categoria_producto.objects.all()

    
    if request.method == 'POST':
        logger.info(f"Datos recibidos: {request.POST}")
        nombre_producto = request.POST.get('nombre_producto')
        descripcion_producto = request.POST.get('descripcion_producto')
        marca_producto = request.POST.get('marca_producto')
        modelo_producto = request.POST.get('modelo_producto')
        imagen_producto = request.FILES.get('imagen_producto')
        caracteristicas_generales = request.POST.get('caracteristicas_generales')
        estatus_producto = request.POST.get('estatus_producto')
        categoria_id = request.POST.get('categoria_producto')
        categoria_producto_consul=categoria_producto.objects.get(id_categoria_prod=categoria_id)

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
        return redirect('/ecommerce/producto/?success=true')
    
    return render(request, 'ecommerce_app/producto.html', {'categoria_producto_all': categoria_producto_all})

def servicio_funcion(request):
    categoria_servicio_all = categoria_servicio.objects.all()
    empresa_obj = empresa.objects.get(id_empresa=8)
    if request.method == 'POST':
        logger.info(f"Datos recibidos: {request.POST}")
        nombre_servicio = request.POST.get('nombre_servicio')
        descripcion_servicio = request.POST.get('descripcion_servicio')
        estatus_servicio = request.POST.get('estatus_servicio')
        categoria_id = request.POST.get('categoria_servicio')
        categoria_servicio_consul=categoria_servicio.objects.get(id_categoria_serv=categoria_id)
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
        return redirect('/ecommerce/servicio/?success=true')
    
        
        
    return render(request, 'ecommerce_app/servicio.html', {'categoria_servicio_all': categoria_servicio_all})



def eliminar_todas_sucursales(request):
    if request.method == 'POST':
        try:
            # Obtener el número de sucursales antes de eliminarlas
            total_sucursales = sucursal.objects.count()
            
            # Eliminar todas las sucursales
            sucursal.objects.all().delete()
            
            logger.info(f"Se eliminaron {total_sucursales} sucursales")
            
            # Mostrar mensaje de éxito
            return redirect('/ecommerce/sucursal/?deleted=true')
        except Exception as e:
            logger.error(f"Error al eliminar las sucursales: {str(e)}")
            return redirect('/ecommerce/sucursal/?error=true')
    
    return redirect('/ecommerce/sucursal/')






def categoria_producto_funcion(request):
    if request.method == 'POST':
        logger.info(f"Datos recibidos: {request.POST}")
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
        logger.info(f"Categoria guardada exitosamente: {nueva_categoria.nombre_categoria_prod}")
        return redirect('/ecommerce/categoria_producto/?success=true')

    return render(request, 'ecommerce_app/categoria_producto.html')

def categoria_servicio_funcion(request):
    if request.method == 'POST':
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
        return redirect('/ecommerce/categoria_servicio/?success=true')

    return render(request, 'ecommerce_app/categoria_servicio.html')




def categ_producto_config_funcion(request):
    categ_producto_all= categoria_producto.objects.all().order_by('-fecha_creacion_prod')


    return render(request, 'ecommerce_app/categ_producto_config.html', {'categoria_producto':categ_producto_all})



def eliminar_categoria_funcion(request):
    if request.method == 'POST':
        try:
            id_categoria = request.POST.get('id_categoria')
            logger.info(f"Intentando eliminar categoría con ID: {id_categoria}")
            
            if not id_categoria:
                logger.error("No se proporcionó ID de categoría")
                return redirect('/ecommerce/categ_producto_config/?error=true')
                
            categoria_obj = categoria_producto.objects.get(id_categoria_prod=id_categoria)
            nombre_categoria = categoria_obj.nombre_categoria_prod
            
            # Verificar si hay productos asociados
            productos_asociados = producto.objects.filter(id_categoria_prod_fk=categoria_obj).exists()
            if productos_asociados:
                logger.error(f"No se puede eliminar la categoría {nombre_categoria} porque tiene productos asociados")
                return redirect('/ecommerce/categ_producto_config/?error=true')
            
            categoria_obj.delete()
            logger.info(f"Categoría eliminada exitosamente: {nombre_categoria}")
            return redirect('/ecommerce/categ_producto_config/?deleted=true')
            
        except categoria_producto.DoesNotExist:
            logger.error(f"Error al eliminar la categoría: Categoría no encontrada con ID {id_categoria}")
            return redirect('/ecommerce/categ_producto_config/?error=true')
        except Exception as e:
            logger.error(f"Error al eliminar la categoría: {str(e)}")
            return redirect('/ecommerce/categ_producto_config/?error=true')
    
    return redirect('/ecommerce/categ_producto_config/')



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
