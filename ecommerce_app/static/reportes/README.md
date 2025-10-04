# Sistema de Reportes de Ventas

## 📊 Descripción

Sistema completo de reportes de ventas con filtros personalizables, gráficos interactivos y exportación de datos. Diseñado para usuarios individuales y empresas con múltiples sucursales.

## ✨ Características Principales

### 1. **Filtros Avanzados**
- **Tipo de Reporte**: Diario, Semanal, Mensual o Personalizado
- **Rango de Fechas**: Selección personalizada de fecha inicio y fin
- **Filtro por Sucursal**: Solo para empresas, permite filtrar ventas por sucursal específica

### 2. **KPIs (Indicadores Clave)**
- **Total de Ventas**: Suma total de ingresos en el período
- **Total de Pedidos**: Cantidad de pedidos confirmados
- **Ticket Promedio**: Valor promedio por pedido
- **Período**: Rango de fechas del reporte

### 3. **Visualizaciones**
- **Gráfico de Evolución**: Línea temporal mostrando ventas diarias
- **Top 5 Productos**: Gráfico de dona con los productos más vendidos
- **Tabla Detallada**: Lista completa de todas las ventas con información detallada

### 4. **Exportación**
- **PDF**: Impresión directa del reporte
- **Excel/CSV**: Descarga de datos en formato CSV para análisis posterior

## 🚀 Uso

### Acceso al Reporte
```
URL: /ecommerce/reporte_ventas/
```

### Generar Reporte

1. **Seleccionar Tipo de Reporte**:
   - Últimas 24 horas
   - Última semana
   - Último mes
   - Personalizado (con fechas específicas)

2. **Aplicar Filtros** (opcional):
   - Seleccionar sucursal (solo empresas)
   - Definir rango de fechas personalizado

3. **Generar**: Click en "Generar Reporte"

### Exportar Datos

- **PDF**: Click en "Exportar PDF" → Se abrirá el diálogo de impresión
- **Excel**: Click en "Exportar Excel" → Se descargará archivo CSV

## 📁 Estructura de Archivos

```
ecommerce_app/
├── views.py                           # Vistas del reporte
│   ├── reporte_ventas()              # Vista principal
│   └── api_obtener_datos_reporte()   # API de datos
│
├── urls.py                            # Rutas
│   ├── reporte_ventas/
│   └── api/obtener_datos_reporte/
│
├── templates/ecommerce_app/
│   └── reporte_ventas.html           # Template HTML
│
└── static/reportes/
    ├── css/
    │   └── reporte_ventas.css        # Estilos
    └── js/
        └── reporte_ventas.js         # Lógica JavaScript
```

## 🔧 Tecnologías Utilizadas

- **Backend**: Django (Python)
- **Frontend**: 
  - HTML5
  - CSS3 (Bootstrap 5)
  - JavaScript (jQuery)
- **Gráficos**: Chart.js 4.4.0
- **Iconos**: Font Awesome 6.4.0

## 📊 Datos del Reporte

### Para Empresas
El reporte incluye:
- Ventas de productos de todas las sucursales
- Filtrado por sucursal específica
- Información del comprador (Usuario o Empresa)
- Nombre de la sucursal en cada venta

### Para Usuarios Individuales
El reporte incluye:
- Ventas de productos propios
- Información del comprador (Usuario o Empresa)
- Sin filtro de sucursal

### Estados de Pedidos Incluidos
- ✅ Confirmado
- 📦 Enviado
- ✔️ Entregado

**Nota**: Los pedidos pendientes y cancelados NO se incluyen en el reporte.

## 🎨 Diseño

### Paleta de Colores
- **Primary**: Gradiente púrpura (#667eea → #764ba2)
- **Success**: Gradiente verde (#11998e → #38ef7d)
- **Info**: Azul claro (#0dcaf0)
- **Warning**: Amarillo (#ffc107)

### Características de UI/UX
- Diseño responsive (móvil, tablet, desktop)
- Animaciones suaves
- Cards con efecto hover
- Gráficos interactivos
- Tabla con scroll horizontal
- Loading spinner durante carga

## 📱 Responsive

El reporte está completamente optimizado para:
- 📱 Móviles (< 768px)
- 📱 Tablets (768px - 1024px)
- 💻 Desktop (> 1024px)

## 🔐 Seguridad

- Requiere autenticación (@require_login)
- Los datos se filtran por usuario/empresa logueado
- Validación de permisos en el backend
- Protección contra inyección SQL (Django ORM)

## 📈 Métricas Calculadas

### Total de Ventas
```python
SUM(subtotal_detalle_pedido) WHERE estado IN ['confirmado', 'enviado', 'entregado']
```

### Ticket Promedio
```python
Total de Ventas / Número de Pedidos Únicos
```

### Productos Más Vendidos
```python
GROUP BY producto
ORDER BY SUM(cantidad) DESC
LIMIT 5
```

## 🐛 Troubleshooting

### El reporte no carga
- Verificar que el usuario esté autenticado
- Revisar que existan ventas en el período seleccionado
- Comprobar la consola del navegador para errores JavaScript

### Los gráficos no se muestran
- Verificar que Chart.js esté cargado correctamente
- Revisar la consola para errores de Canvas
- Asegurar que existan datos para graficar

### La exportación no funciona
- Para PDF: Verificar que el navegador permita impresión
- Para Excel: Verificar que el navegador permita descargas

## 🔄 Actualizaciones Futuras

Posibles mejoras:
- [ ] Exportación a PDF nativo (sin impresión)
- [ ] Filtro por categoría de producto
- [ ] Comparación entre períodos
- [ ] Gráficos adicionales (barras, áreas)
- [ ] Reporte de servicios
- [ ] Dashboard con múltiples reportes
- [ ] Programación de reportes automáticos
- [ ] Envío por email

## 📞 Soporte

Para problemas o sugerencias, contactar al equipo de desarrollo.

---

**Versión**: 1.0.0  
**Fecha**: Octubre 2025  
**Desarrollado para**: MainProject E-commerce Platform
