// ==================== REPORTE DE PRODUCTOS JS ====================

// Variables globales
let chartMasVendidos = null;
let chartDistribucionIngresos = null;
let chartRentabilidad = null;
let datosReporte = null;

// Inicialización
$(document).ready(function() {
    inicializarFechas();
    configurarEventos();
    
    // Cargar reporte inicial (último mes)
    generarReporte();
});

// Inicializar fechas por defecto
function inicializarFechas() {
    const hoy = new Date();
    const hace30Dias = new Date();
    hace30Dias.setDate(hoy.getDate() - 30);
    
    $('#fechaFin').val(formatearFecha(hoy));
    $('#fechaInicio').val(formatearFecha(hace30Dias));
}

// Formatear fecha a YYYY-MM-DD
function formatearFecha(fecha) {
    const year = fecha.getFullYear();
    const month = String(fecha.getMonth() + 1).padStart(2, '0');
    const day = String(fecha.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Configurar eventos
function configurarEventos() {
    // Cambio en tipo de reporte
    $('#tipoReporte').on('change', function() {
        const tipo = $(this).val();
        if (tipo === 'personalizado') {
            $('#divFechaInicio, #divFechaFin').show();
        } else {
            $('#divFechaInicio, #divFechaFin').hide();
        }
    });
    
    // Submit del formulario
    $('#formFiltros').on('submit', function(e) {
        e.preventDefault();
        generarReporte();
    });
    
    // Exportar Excel
    $('#btnExportarExcel').on('click', function() {
        exportarExcel();
    });
}

// Generar reporte
function generarReporte() {
    // Mostrar loading
    $('#loadingSpinner').show();
    $('#reporteResultados, #sinDatos').hide();
    
    // Obtener datos del formulario
    const formData = {
        tipo_reporte: $('#tipoReporte').val(),
        fecha_inicio: $('#fechaInicio').val(),
        fecha_fin: $('#fechaFin').val(),
        sucursal_id: $('#sucursalFiltro').val() || '',
        categoria_id: $('#categoriaFiltro').val() || ''
    };
    
    // Hacer petición AJAX
    $.ajax({
        url: '/ecommerce/api/obtener_datos_reporte_productos/',
        method: 'GET',
        data: formData,
        success: function(response) {
            $('#loadingSpinner').hide();
            
            if (response.success) {
                datosReporte = response.data;
                
                if (datosReporte.todos_productos.length > 0 || datosReporte.productos_sin_movimiento.length > 0) {
                    mostrarReporte(datosReporte);
                    $('#reporteResultados').show().addClass('fade-in');
                } else {
                    $('#sinDatos').show().addClass('fade-in');
                }
            } else {
                mostrarError(response.error || 'Error al obtener datos del reporte');
            }
        },
        error: function(xhr, status, error) {
            $('#loadingSpinner').hide();
            console.error('Error:', error);
            mostrarError('Error al conectar con el servidor');
        }
    });
}

// Mostrar reporte
function mostrarReporte(data) {
    // Actualizar sucursales en el select
    if (accountType === 'empresa' && data.sucursales.length > 0) {
        const selectSucursal = $('#sucursalFiltro');
        const valorActual = selectSucursal.val();
        selectSucursal.empty();
        selectSucursal.append('<option value="">Todas las sucursales</option>');
        data.sucursales.forEach(function(sucursal) {
            selectSucursal.append(`<option value="${sucursal.id}">${sucursal.nombre}</option>`);
        });
        selectSucursal.val(valorActual);
    }
    
    // Actualizar categorías en el select
    if (data.categorias && data.categorias.length > 0) {
        const selectCategoria = $('#categoriaFiltro');
        const valorActual = selectCategoria.val();
        selectCategoria.empty();
        selectCategoria.append('<option value="">Todas las categorías</option>');
        data.categorias.forEach(function(categoria) {
            selectCategoria.append(`<option value="${categoria.id}">${categoria.nombre}</option>`);
        });
        selectCategoria.val(valorActual);
    }
    
    // Generar gráficos y tablas
    generarGraficoMasVendidos(data.productos_mas_vendidos);
    generarListaMasVendidos(data.productos_mas_vendidos);
    llenarTablaMasVendidos(data.productos_mas_vendidos);
    llenarTablaMenosVendidos(data.productos_menos_vendidos);
    llenarTablaSinMovimiento(data.productos_sin_movimiento);
    generarGraficoDistribucionIngresos(data.productos_mas_vendidos);
    generarGraficoRentabilidad(data.todos_productos);
    llenarTablaRentabilidad(data.todos_productos);
}

// Generar gráfico de productos más vendidos
function generarGraficoMasVendidos(productos) {
    const ctx = document.getElementById('chartMasVendidos');
    
    if (chartMasVendidos) {
        chartMasVendidos.destroy();
    }
    
    const nombres = productos.map(p => p.nombre.length > 20 ? p.nombre.substring(0, 20) + '...' : p.nombre);
    const cantidades = productos.map(p => p.cantidad);
    
    chartMasVendidos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: nombres,
            datasets: [{
                label: 'Cantidad Vendida',
                data: cantidades,
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgb(13, 110, 253)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const producto = productos[context.dataIndex];
                            return [
                                `Cantidad: ${producto.cantidad}`,
                                `Ingresos: $${formatearNumero(producto.ingresos)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Generar lista de productos más vendidos
function generarListaMasVendidos(productos) {
    const lista = $('#listaMasVendidos');
    lista.empty();
    
    productos.forEach(function(producto, index) {
        const medalla = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
        
        lista.append(`
            <div class="d-flex justify-content-between align-items-center mb-3 p-2 border-bottom">
                <div>
                    <h6 class="mb-0">${medalla} ${producto.nombre}</h6>
                    <small class="text-muted">${producto.cantidad} unidades</small>
                </div>
                <div class="text-end">
                    <strong class="text-success">$${formatearNumero(producto.ingresos)}</strong>
                </div>
            </div>
        `);
    });
}

// Llenar tabla de productos más vendidos
function llenarTablaMasVendidos(productos) {
    const tbody = $('#tablaMasVendidos');
    tbody.empty();
    
    productos.forEach(function(producto, index) {
        tbody.append(`
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${producto.nombre}</td>
                <td class="text-center"><span class="badge bg-primary">${producto.cantidad}</span></td>
                <td><strong class="text-success">$${formatearNumero(producto.ingresos)}</strong></td>
                <td>$${formatearNumero(producto.precio_promedio)}</td>
                <td class="text-center">${producto.num_ventas}</td>
            </tr>
        `);
    });
}

// Llenar tabla de productos menos vendidos
function llenarTablaMenosVendidos(productos) {
    const tbody = $('#tablaMenosVendidos');
    tbody.empty();
    
    if (productos.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="6" class="text-center text-muted">No hay datos disponibles</td>
            </tr>
        `);
        return;
    }
    
    productos.forEach(function(producto, index) {
        tbody.append(`
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${producto.nombre}</td>
                <td class="text-center"><span class="badge bg-warning">${producto.cantidad}</span></td>
                <td>$${formatearNumero(producto.ingresos)}</td>
                <td>$${formatearNumero(producto.precio_promedio)}</td>
                <td class="text-center">${producto.num_ventas}</td>
            </tr>
        `);
    });
}

// Llenar tabla de productos sin movimiento
function llenarTablaSinMovimiento(productos) {
    const tbody = $('#tablaSinMovimiento');
    tbody.empty();
    
    if (productos.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="5" class="text-center text-success">
                    <i class="fas fa-check-circle me-2"></i>
                    ¡Excelente! Todos tus productos tienen movimiento
                </td>
            </tr>
        `);
        return;
    }
    
    productos.forEach(function(producto, index) {
        tbody.append(`
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${producto.nombre}</td>
                <td class="text-center">${producto.stock}</td>
                <td>$${formatearNumero(producto.precio)}</td>
                <td>
                    <span class="badge bg-danger">Promocionar</span>
                    <span class="badge bg-warning">Revisar Precio</span>
                </td>
            </tr>
        `);
    });
}

// Generar gráfico de distribución de ingresos
function generarGraficoDistribucionIngresos(productos) {
    const ctx = document.getElementById('chartDistribucionIngresos');
    
    if (chartDistribucionIngresos) {
        chartDistribucionIngresos.destroy();
    }
    
    const top5 = productos.slice(0, 5);
    const nombres = top5.map(p => p.nombre.length > 15 ? p.nombre.substring(0, 15) + '...' : p.nombre);
    const ingresos = top5.map(p => p.ingresos);
    
    const colores = [
        'rgba(13, 110, 253, 0.8)',
        'rgba(10, 88, 202, 0.8)',
        'rgba(110, 168, 254, 0.8)',
        'rgba(25, 135, 84, 0.8)',
        'rgba(13, 202, 240, 0.8)'
    ];
    
    chartDistribucionIngresos = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: nombres,
            datasets: [{
                data: ingresos,
                backgroundColor: colores,
                borderColor: '#fff',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const total = ingresos.reduce((a, b) => a + b, 0);
                            const porcentaje = ((context.parsed / total) * 100).toFixed(1);
                            return [
                                `Ingresos: $${formatearNumero(context.parsed)}`,
                                `Porcentaje: ${porcentaje}%`
                            ];
                        }
                    }
                }
            }
        }
    });
}

// Generar gráfico de rentabilidad
function generarGraficoRentabilidad(productos) {
    const ctx = document.getElementById('chartRentabilidad');
    
    if (chartRentabilidad) {
        chartRentabilidad.destroy();
    }
    
    const top10 = productos.sort((a, b) => b.rentabilidad - a.rentabilidad).slice(0, 10);
    const nombres = top10.map(p => p.nombre.length > 20 ? p.nombre.substring(0, 20) + '...' : p.nombre);
    const rentabilidad = top10.map(p => p.rentabilidad);
    
    chartRentabilidad = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: nombres,
            datasets: [{
                label: 'Rentabilidad por Venta',
                data: rentabilidad,
                backgroundColor: 'rgba(25, 135, 84, 0.7)',
                borderColor: 'rgb(25, 135, 84)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return `Rentabilidad: $${formatearNumero(context.parsed.x)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + formatearNumero(value);
                        }
                    }
                }
            }
        }
    });
}

// Llenar tabla de rentabilidad
function llenarTablaRentabilidad(productos) {
    const tbody = $('#tablaRentabilidad');
    tbody.empty();
    
    const productosOrdenados = productos.sort((a, b) => b.rentabilidad - a.rentabilidad);
    
    productosOrdenados.forEach(function(producto) {
        const rentabilidadClass = producto.rentabilidad > 100 ? 'text-success' : producto.rentabilidad > 50 ? 'text-warning' : 'text-danger';
        
        tbody.append(`
            <tr>
                <td>${producto.nombre}</td>
                <td class="text-center">${producto.cantidad}</td>
                <td><strong class="text-success">$${formatearNumero(producto.ingresos)}</strong></td>
                <td>$${formatearNumero(producto.precio_promedio)}</td>
                <td><strong class="${rentabilidadClass}">$${formatearNumero(producto.rentabilidad)}</strong></td>
            </tr>
        `);
    });
}

// Formatear número con separadores de miles
function formatearNumero(numero) {
    return parseFloat(numero).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Mostrar error
function mostrarError(mensaje) {
    alert('Error: ' + mensaje);
}

// Exportar a Excel
function exportarExcel() {
    if (!datosReporte || !datosReporte.todos_productos || datosReporte.todos_productos.length === 0) {
        alert('No hay datos para exportar');
        return;
    }
    
    // Crear contenido CSV
    let csv = 'REPORTE DE PRODUCTOS\n\n';
    
    // Productos más vendidos
    csv += 'PRODUCTOS MÁS VENDIDOS\n';
    csv += 'Producto,Cantidad Vendida,Ingresos Totales,Precio Promedio,N° Ventas\n';
    datosReporte.productos_mas_vendidos.forEach(function(p) {
        csv += `"${p.nombre}",${p.cantidad},${p.ingresos},${p.precio_promedio},${p.num_ventas}\n`;
    });
    
    csv += '\n\nPRODUCTOS MENOS VENDIDOS\n';
    csv += 'Producto,Cantidad Vendida,Ingresos Totales,Precio Promedio,N° Ventas\n';
    datosReporte.productos_menos_vendidos.forEach(function(p) {
        csv += `"${p.nombre}",${p.cantidad},${p.ingresos},${p.precio_promedio},${p.num_ventas}\n`;
    });
    
    csv += '\n\nPRODUCTOS SIN MOVIMIENTO\n';
    csv += 'Producto,Stock,Precio\n';
    datosReporte.productos_sin_movimiento.forEach(function(p) {
        csv += `"${p.nombre}",${p.stock},${p.precio}\n`;
    });
    
    // Crear blob y descargar
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `reporte_productos_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
