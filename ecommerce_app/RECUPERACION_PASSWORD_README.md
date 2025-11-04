# Sistema de Recuperación de Contraseña - Guía de Pruebas

## Problemas Solucionados ✅

### 1. **Archivo JavaScript Faltante**
- **Problema**: El template `confirmar_recuperacion.html` referenciaba `confirm.js` que no existía
- **Solución**: Creado `static/recuperacion/confirm.js` con funcionalidad completa

### 2. **Diseño Mejorado**
- **Problema**: La página de confirmación tenía un diseño básico
- **Solución**: Actualizado `confirmar_recuperacion.html` con:
  - Bootstrap 5 y FontAwesome
  - Validación de formularios en tiempo real
  - Botones para mostrar/ocultar contraseña
  - Diseño consistente con `recuperar_clave.html`
  - Mejor UX y mensajes informativos

### 3. **Mejoras en el Backend**
- **Problema**: Posibles errores silenciosos en la actualización de contraseña
- **Solución**: Mejorada la función `confirmar_recuperacion` con:
  - Logging detallado para debugging
  - Manejo de errores específicos
  - Validaciones más robustas
  - Mejor manejo de CSRF
  - Mensajes de error más descriptivos

## Cómo Probar el Sistema 🧪

### Opción 1: Prueba Automática
```bash
# Ejecutar el script de pruebas
python manage.py shell < ecommerce_app/test_password_reset.py
```

### Opción 2: Prueba Manual

#### Paso 1: Solicitar Recuperación
1. Ir a `/ecommerce/recuperar_clave/`
2. Ingresar un email válido de usuario o empresa
3. Verificar que se muestre el mensaje de confirmación
4. Revisar el email recibido

#### Paso 2: Confirmar Recuperación
1. Hacer clic en el enlace del email
2. Verificar que se abra `/ecommerce/confirmar_recuperacion/`
3. Ingresar nueva contraseña (mínimo 6 caracteres)
4. Confirmar la contraseña
5. Hacer clic en "Actualizar contraseña"

#### Paso 3: Verificar Actualización
1. Intentar iniciar sesión con la nueva contraseña
2. Verificar que el acceso sea exitoso

## Archivos Modificados/Creados 📁

### Nuevos Archivos:
- `static/recuperacion/confirm.js` - JavaScript para confirmación
- `test_password_reset.py` - Script de pruebas
- `RECUPERACION_PASSWORD_README.md` - Esta documentación

### Archivos Modificados:
- `templates/ecommerce_app/confirmar_recuperacion.html` - Diseño mejorado
- `views.py` - Función `confirmar_recuperacion` mejorada

## Funcionalidades Implementadas ⚡

### Frontend (confirm.js):
- ✅ Validación en tiempo real de contraseñas
- ✅ Verificación de coincidencia de contraseñas
- ✅ Manejo de errores con SweetAlert2
- ✅ Loading states en botones
- ✅ Redirección automática tras éxito

### Backend (views.py):
- ✅ Logging detallado para debugging
- ✅ Validación de longitud mínima de contraseña
- ✅ Manejo específico de errores de usuario/empresa
- ✅ Verificación de existencia de usuarios
- ✅ Hash seguro de contraseñas con Django

### Template (confirmar_recuperacion.html):
- ✅ Diseño responsive con Bootstrap 5
- ✅ Iconos con FontAwesome
- ✅ Botones para mostrar/ocultar contraseña
- ✅ Validación HTML5
- ✅ Feedback visual de validación

## Debugging 🔍

### Ver Logs del Sistema:
```python
# En Django shell
import logging
logging.basicConfig(level=logging.INFO)

# Los logs aparecerán con formato:
# INFO:ecommerce_app.views:Token válido para payload: {'type': 'usuario', 'id': 123}
# INFO:ecommerce_app.views:Usuario encontrado: Juan Pérez (juan@email.com)
# INFO:ecommerce_app.views:Contraseña actualizada para usuario Juan Pérez
```

### Verificar Token Manualmente:
```python
from django.core import signing

# Generar token
payload = {'type': 'usuario', 'id': 1}
token = signing.dumps(payload, salt='password-reset')

# Validar token
try:
    decoded = signing.loads(token, salt='password-reset', max_age=60*60*2)
    print("Token válido:", decoded)
except signing.BadSignature:
    print("Token inválido")
```

## Configuración Requerida ⚙️

### Settings.py:
```python
# Para envío de emails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # o tu servidor SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-password'
DEFAULT_FROM_EMAIL = 'tu-email@gmail.com'

# URL base para enlaces
SITE_BASE_URL = 'http://localhost:8000'  # Cambiar en producción
```

### URLs.py:
```python
# Verificar que estas rutas estén presentes:
path('recuperar_clave/', views.recuperar_clave, name='recuperar_clave'),
path('api/request_password_reset/', views.request_password_reset, name='request_password_reset'),
path('confirmar_recuperacion/', views.confirmar_recuperacion, name='confirmar_recuperacion'),
```

## Seguridad 🔒

### Medidas Implementadas:
- ✅ Tokens firmados con salt específico
- ✅ Expiración de tokens (2 horas)
- ✅ Hash seguro de contraseñas con Django
- ✅ No exposición de existencia de cuentas
- ✅ Validación de entrada robusta
- ✅ Logging de intentos sospechosos

### Recomendaciones Adicionales:
- 🔄 Implementar rate limiting para prevenir spam
- 🔄 Añadir CAPTCHA en formularios públicos
- 🔄 Configurar HTTPS en producción
- 🔄 Monitorear logs de seguridad

## Solución de Problemas Comunes 🛠️

### "Token inválido o expirado":
- Verificar que el enlace no tenga más de 2 horas
- Comprobar que el token no esté truncado
- Revisar configuración de `SECRET_KEY` en settings

### "Usuario no encontrado":
- Verificar que el email existe en la base de datos
- Comprobar que el ID en el payload sea correcto
- Revisar logs para más detalles

### "Error interno":
- Revisar logs del servidor
- Verificar conexión a base de datos
- Comprobar permisos de escritura

### Emails no llegan:
- Verificar configuración SMTP en settings
- Revisar carpeta de spam
- Comprobar logs de envío de email

---

**Nota**: Este sistema ha sido probado y mejorado para manejar tanto usuarios como empresas de forma segura y eficiente.
