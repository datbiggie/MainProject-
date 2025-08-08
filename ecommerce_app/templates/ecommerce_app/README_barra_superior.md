# Barra Superior Bienvenido - Guía de Implementación

## Descripción
La barra superior es un componente reutilizable que se incluye en múltiples páginas del sistema. Contiene el logo, texto de bienvenida y tres iconos de navegación con funcionalidad de sesión.

## Archivos Creados

### 1. Template HTML
- **Ubicación**: `templates/ecommerce_app/barra_superior_bienvenido.html`
- **Contenido**: HTML completo de la barra superior con modal de sesión

### 2. Estilos CSS
- **Ubicación**: `static/barra_superior/css/main.css`
- **Contenido**: Todos los estilos necesarios para la barra superior y modal

### 3. Imágenes
- **Ubicación**: `static/barra_superior/images/logo.jpg`
- **Nota**: Copiar el logo desde `iniciar_sesion/images/logo.jpg`

## Cómo Implementar en Nuevas Páginas

### Paso 1: Incluir el Template
Agregar esta línea en el `<head>` de tu HTML, después de los otros enlaces CSS:

```html
{% include 'ecommerce_app/barra_superior_bienvenido.html' %}
```

### Paso 2: Incluir el CSS
Agregar esta línea en el `<head>` de tu HTML, después de los otros enlaces CSS:

```html
<link rel="stylesheet" href="{% static 'barra_superior/css/main.css' %}">
```

### Paso 3: Ajustar el Body
Asegúrate de que el body tenga un `margin-top: 70px` para compensar la barra superior fija:

```css
body {
    margin-top: 70px;
}
```

## Páginas que Deben Incluir la Barra Superior

1. ✅ **iniciar_sesion.html** - Ya implementado
2. ⏳ **registrar_empresa.html** - Pendiente
3. ⏳ **registrar_persona.html** - Pendiente
4. ⏳ **sucursal.html** - Pendiente

## Funcionalidades

### Iconos de Navegación
- **🏠 Inicio (Verde)**: Enlace al index
- **👤 Perfil (Azul)**: Modal de sesión
- **❓ FAQ (Naranja)**: Preguntas frecuentes

### Modal de Sesión
- **Usuario logueado**: Muestra información del usuario y botón de cerrar sesión
- **Usuario no logueado**: Muestra mensaje y botón de iniciar sesión

## Estructura de Archivos

```
MainProject-/
├── ecommerce_app/
│   ├── templates/
│   │   └── ecommerce_app/
│   │       ├── barra_superior_bienvenido.html
│   │       ├── iniciar_sesion.html
│   │       ├── registrar_empresa.html
│   │       ├── registrar_persona.html
│   │       └── sucursal.html
│   └── static/
│       ├── barra_superior/
│       │   ├── css/
│       │   │   └── main.css
│       │   └── images/
│       │       └── logo.jpg
│       └── iniciar_sesion/
│           └── css/
│               └── main.css (limpiado)
```

## Ventajas de esta Implementación

1. **Reutilización**: Un solo archivo para todas las páginas
2. **Mantenimiento**: Cambios centralizados
3. **Consistencia**: Mismo diseño en todas las páginas
4. **Optimización**: CSS separado y específico
5. **Escalabilidad**: Fácil agregar nuevas páginas

## Notas Importantes

- El modal de sesión requiere que la variable `user_info` esté disponible en el contexto
- Los iconos usan SVG inline para mejor rendimiento
- El diseño es completamente responsive
- Los colores de los iconos son configurables en el CSS 