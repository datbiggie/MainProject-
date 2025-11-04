from django.db.models import Sum

# Context processor para exponer el número de items en el carrito
def cart_count(request):
	"""Devuelve {'cart_count': <int>} con la suma de cantidades del carrito activo del usuario.

	Usa la función get_current_user(request) definida en views.py para resolver el usuario
	desde la sesión personalizada del proyecto.
	"""
	try:
		# Importar aquí para evitar problemas de importación circular en tiempo de carga
		from .views import get_current_user
		from .models import (
			carrito_compra_producto_usuario,
			detalle_compra_producto_usuario,
			carrito_compra_producto_empresa,
			detalle_compra_producto_empresa,
		)

		count = 0
		current_user = get_current_user(request)
		if not current_user:
			return {'cart_count': 0}

		account_type = request.session.get('account_type', 'usuario')

		if account_type == 'empresa':
			carrito = carrito_compra_producto_empresa.objects.filter(
				id_empresa_fk=current_user,
				estatuscarrito_prod_empresa__in=['activo', 'pendiente']
			).first()
			if carrito:
				total = detalle_compra_producto_empresa.objects.filter(
					id_fk_carritocompra_empresa=carrito
				).aggregate(total=Sum('cantidad_deta_carrito_prod_empresa'))['total'] or 0
				count = int(total)
		else:
			carrito = carrito_compra_producto_usuario.objects.filter(
				id_usuario_fk=current_user,
				estatuscarrito_prod_usuario__in=['activo', 'pendiente']
			).first()
			if carrito:
				total = detalle_compra_producto_usuario.objects.filter(
					id_fk_carritocompra_usuario=carrito
				).aggregate(total=Sum('cantidad_deta_carrito_prod_usuario'))['total'] or 0
				count = int(total)

		return {'cart_count': count}
	except Exception:
		# No queremos romper renderizados por errores aquí; devolver 0 y loguear si es necesario
		return {'cart_count': 0}
