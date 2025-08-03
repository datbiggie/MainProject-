# Guía de Sesiones Personalizadas en Django

## Resumen

Este proyecto utiliza un sistema de sesiones personalizado con el modelo `usuario` en lugar del sistema de autenticación estándar de Django. Esto permite mayor flexibilidad y control sobre el manejo de usuarios.

## Funciones Principales

### 1. Funciones de Sesión

#### `get_current_user(request)`
Obtiene el usuario actual desde la sesión.
```python
current_user = get_current_user(request)
if current_user:
    print(f"Usuario: {current_user.nombre_usuario}")
```

#### `is_user_authenticated(request)`
Verifica si el usuario está autenticado.
```python
if is_user_authenticated(request):
    # Usuario está logueado
    pass
```

#### `logout_user(request)`
Cierra la sesión del usuario.
```python
logout_user(request)
```

### 2. Decorador de Protección

#### `@require_login`
Protege vistas que requieren autenticación.
```python
@require_login
def mi_vista_protegida(request):
    # Solo usuarios autenticados pueden acceder
    pass
```

## Variables de Sesión

El sistema almacena las siguientes variables en la sesión:

- `user_id`: ID del usuario
- `user_email`: Email del usuario
- `user_name`: Nombre del usuario
- `user_type`: Tipo de usuario (persona/empresa)
- `is_authenticated`: Estado de autenticación

## Ejemplos de Uso

### 1. Obtener Usuario Actual en una Vista

```python
def mi_vista(request):
    current_user = get_current_user(request)
    if current_user:
        # Usar información del usuario
        empresa_usuario = empresa.objects.filter(id_usuario_fk=current_user).first()
        return render(request, 'template.html', {'empresa': empresa_usuario})
    else:
        return redirect('/ecommerce/iniciar_sesion')
```

### 2. Proteger una Vista Completa

```python
@require_login
def vista_protegida(request):
    # Esta vista solo es accesible para usuarios autenticados
    current_user = get_current_user(request)
    return render(request, 'template.html', {'user': current_user})
```

### 3. Verificar Autenticación en Templates

```html
{% if user_info %}
    <p>Bienvenido: {{ user_info.nombre }}</p>
    <a href="{% url 'cerrar_sesion' %}">Cerrar Sesión</a>
{% else %}
    <a href="{% url 'iniciar_sesion' %}">Iniciar Sesión</a>
{% endif %}
```

## URLs Disponibles

- `/ecommerce/iniciar_sesion/`: Página de login
- `/ecommerce/cerrar_sesion/`: Cerrar sesión
- `/ecommerce/registrar_persona/`: Registro de personas
- `/ecommerce/registrar_empresa/`: Registro de empresas (requiere login)

## Flujo de Autenticación

1. **Registro**: Usuario se registra como persona
2. **Login**: Usuario inicia sesión con email y contraseña
3. **Sesión**: Se crea una sesión con los datos del usuario
4. **Acceso**: Usuario puede acceder a vistas protegidas
5. **Logout**: Usuario cierra sesión

## Seguridad

- Las contraseñas se hashean usando `make_password()`
- Las sesiones se validan en cada request
- Las vistas protegidas redirigen a login si no hay sesión
- Las sesiones se limpian automáticamente si el usuario no existe

## Troubleshooting

### Problema: Usuario no puede acceder a vistas protegidas
**Solución**: Verificar que la sesión se creó correctamente en el login.

### Problema: Sesión se pierde
**Solución**: Verificar que `django.contrib.sessions` está en `INSTALLED_APPS`.

### Problema: Error al obtener usuario actual
**Solución**: Verificar que el usuario existe en la base de datos.

## Migración desde el Sistema Anterior

Si tienes vistas que usaban IDs hardcodeados:

**Antes:**
```python
empresa_obj = empresa.objects.get(id_empresa=9)
```

**Después:**
```python
current_user = get_current_user(request)
empresa_obj = empresa.objects.get(id_usuario_fk=current_user)
```

## Notas Importantes

1. Todas las vistas que requieren autenticación deben usar el decorador `@require_login`
2. Siempre verificar que el usuario existe antes de usar sus datos
3. Las sesiones se almacenan en la base de datos por defecto
4. El sistema es compatible con el middleware de sesiones de Django 