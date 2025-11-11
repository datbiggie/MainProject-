// ==================== REPORTE DE SERVICIOS JS ====================

// Variables globales
let chartMasPrestados = null;
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
        url: '/ecommerce/api/obtener_datos_reporte_servicios/',
        method: 'GET',
        data: formData,
        success: function(response) {
            $('#loadingSpinner').hide();
            
            if (response.success) {
                datosReporte = response.data;
                
                // Suponemos que la API devuelve estructuras similares a productos, pero con prefijo servicios
                if ((datosReporte.servicios_mas_prestados && datosReporte.servicios_mas_prestados.length > 0) || (datosReporte.servicios_sin_prestaciones && datosReporte.servicios_sin_prestaciones.length > 0)) {
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
    if (accountType === 'empresa' && data.sucursales && data.sucursales.length > 0) {
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
    generarGraficoMasPrestados(data.servicios_mas_prestados || []);
    generarListaMasPrestados(data.servicios_mas_prestados || []);
    llenarTablaMasPrestados(data.servicios_mas_prestados || []);
    llenarTablaMenosPrestados(data.servicios_menos_prestados || []);
    llenarTablaSinPrestaciones(data.servicios_sin_prestaciones || []);
    generarGraficoDistribucionIngresos(data.servicios_mas_prestados || []);
    generarGraficoRentabilidad(data.todos_servicios || []);
    llenarTablaRentabilidad(data.todos_servicios || []);
}

// Generar gráfico de servicios más prestados
function generarGraficoMasPrestados(servicios) {
    const ctx = document.getElementById('chartMasPrestados');
    
    if (chartMasPrestados) {
        chartMasPrestados.destroy();
    }
    
    const nombres = servicios.map(p => p.nombre.length > 20 ? p.nombre.substring(0, 20) + '...' : p.nombre);
    const cantidades = servicios.map(p => p.cantidad);
    
    chartMasPrestados = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: nombres,
            datasets: [{
                label: 'Cantidad Prestada',
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
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const servicio = servicios[context.dataIndex];
                            return [
                                `Cantidad: ${servicio.cantidad}`,
                                `Ingresos: $${formatearNumero(servicio.ingresos)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, ticks: { font: { size: 12 } } },
                x: { ticks: { font: { size: 11 }, maxRotation: 45, minRotation: 45 } }
            }
        }
    });
}

// Generar lista de servicios más prestados
function generarListaMasPrestados(servicios) {
    const lista = $('#listaMasPrestados');
    lista.empty();
    
    servicios.forEach(function(servicio, index) {
        const medalla = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
        
        lista.append(`
            <div class="d-flex justify-content-between align-items-center mb-3 p-2 border-bottom">
                <div>
                    <h6 class="mb-0">${medalla} ${servicio.nombre}</h6>
                    <small class="text-muted">${servicio.cantidad} prestaciones</small>
                </div>
                <div class="text-end">
                    <strong class="text-success">$${formatearNumero(servicio.ingresos)}</strong>
                </div>
            </div>
        `);
    });
}

// Llenar tabla de servicios más prestados
function llenarTablaMasPrestados(servicios) {
    const tbody = $('#tablaMasPrestados');
    tbody.empty();
    
    servicios.forEach(function(servicio, index) {
        tbody.append(`
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${servicio.nombre}</td>
                <td class="text-center"><span class="badge bg-primary">${servicio.cantidad}</span></td>
                <td><strong class="text-success">$${formatearNumero(servicio.ingresos)}</strong></td>
                <td>$${formatearNumero(servicio.precio_promedio)}</td>
                <td class="text-center">${servicio.num_prestaciones || servicio.num_ventas || 0}</td>
            </tr>
        `);
    });
}

// Llenar tabla de servicios menos prestados
function llenarTablaMenosPrestados(servicios) {
    const tbody = $('#tablaMenosPrestados');
    tbody.empty();
    
    if (servicios.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="6" class="text-center text-muted">No hay datos disponibles</td>
            </tr>
        `);
        return;
    }
    
    servicios.forEach(function(servicio, index) {
        tbody.append(`
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${servicio.nombre}</td>
                <td class="text-center"><span class="badge bg-warning">${servicio.cantidad}</span></td>
                <td>$${formatearNumero(servicio.ingresos)}</td>
                <td>$${formatearNumero(servicio.precio_promedio)}</td>
                <td class="text-center">${servicio.num_prestaciones || servicio.num_ventas || 0}</td>
            </tr>
        `);
    });
}

// Llenar tabla de servicios sin prestaciones
function llenarTablaSinPrestaciones(servicios) {
    const tbody = $('#tablaSinPrestaciones');
    tbody.empty();
    
    if (servicios.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="5" class="text-center text-success">
                    <i class="fas fa-check-circle me-2"></i>
                    ¡Excelente! Todos tus servicios tienen movimiento
                </td>
            </tr>
        `);
        return;
    }
    
    servicios.forEach(function(servicio, index) {
        tbody.append(`
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${servicio.nombre}</td>
                <td class="text-center">${servicio.estado || ''}</td>
                <td>$${formatearNumero(servicio.precio)}</td>
                <td>
                    <span class="badge bg-danger">Promocionar</span>
                    <span class="badge bg-warning">Revisar Precio</span>
                </td>
            </tr>
        `);
    });
}

// Generar gráfico de distribución de ingresos
function generarGraficoDistribucionIngresos(servicios) {
    const ctx = document.getElementById('chartDistribucionIngresos');
    
    if (chartDistribucionIngresos) {
        chartDistribucionIngresos.destroy();
    }
    
    const top5 = servicios.slice(0, 5);
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
                legend: { position: 'bottom', labels: { padding: 15, font: { size: 11 } } },
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
function generarGraficoRentabilidad(servicios) {
    const ctx = document.getElementById('chartRentabilidad');
    
    if (chartRentabilidad) {
        chartRentabilidad.destroy();
    }
    
    const top10 = (servicios || []).sort((a, b) => (b.rentabilidad || 0) - (a.rentabilidad || 0)).slice(0, 10);
    const nombres = top10.map(p => p.nombre.length > 20 ? p.nombre.substring(0, 20) + '...' : p.nombre);
    const rentabilidad = top10.map(p => p.rentabilidad || 0);
    
    chartRentabilidad = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: nombres,
            datasets: [{
                label: 'Rentabilidad por Prestación',
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
                legend: { display: false },
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
                x: { beginAtZero: true, ticks: { callback: function(value) { return '$' + formatearNumero(value); } } }
            }
        }
    });
}

// Llenar tabla de rentabilidad
function llenarTablaRentabilidad(servicios) {
    const tbody = $('#tablaRentabilidad');
    tbody.empty();
    
    const serviciosOrdenados = (servicios || []).sort((a, b) => (b.rentabilidad || 0) - (a.rentabilidad || 0));
    
    serviciosOrdenados.forEach(function(servicio) {
        const rentabilidadClass = (servicio.rentabilidad || 0) > 100 ? 'text-success' : (servicio.rentabilidad || 0) > 50 ? 'text-warning' : 'text-danger';
        
        tbody.append(`
            <tr>
                <td>${servicio.nombre}</td>
                <td class="text-center">${servicio.cantidad || 0}</td>
                <td><strong class="text-success">$${formatearNumero(servicio.ingresos || 0)}</strong></td>
                <td>$${formatearNumero(servicio.precio_promedio || 0)}</td>
                <td><strong class="${rentabilidadClass}">$${formatearNumero(servicio.rentabilidad || 0)}</strong></td>
            </tr>
        `);
    });
}

// Formatear número con separadores de miles
function formatearNumero(numero) {
    return parseFloat(numero || 0).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Mostrar error
function mostrarError(mensaje) {
    alert('Error: ' + mensaje);
}

// Exportar a Excel
function exportarExcel() {
    if (!datosReporte || !datosReporte.todos_servicios || datosReporte.todos_servicios.length === 0) {
        alert('No hay datos para exportar');
        return;
    }
    
    // Crear contenido CSV
    let csv = 'REPORTE DE SERVICIOS\n\n';
    
    // Servicios más prestados
    csv += 'SERVICIOS MÁS PRESTADOS\n';
    csv += 'Servicio,Cantidad Prestada,Ingresos Totales,Precio Promedio,N° Prestaciones\n';
    (datosReporte.servicios_mas_prestados || []).forEach(function(p) {
        csv += `"${p.nombre}",${p.cantidad},${p.ingresos},${p.precio_promedio},${p.num_prestaciones || p.num_ventas || 0}\n`;
    });
    
    csv += '\n\nSERVICIOS MENOS PRESTADOS\n';
    csv += 'Servicio,Cantidad Prestada,Ingresos Totales,Precio Promedio,N° Prestaciones\n';
    (datosReporte.servicios_menos_prestados || []).forEach(function(p) {
        csv += `"${p.nombre}",${p.cantidad},${p.ingresos},${p.precio_promedio},${p.num_prestaciones || p.num_ventas || 0}\n`;
    });
    
    csv += '\n\nSERVICIOS SIN PRESTACIONES\n';
    csv += 'Servicio,Estado,Precio\n';
    (datosReporte.servicios_sin_prestaciones || []).forEach(function(p) {
        csv += `"${p.nombre}","${p.estado || ''}",${p.precio}\n`;
    });
    
    // Crear blob y descargar
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `reporte_servicios_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
