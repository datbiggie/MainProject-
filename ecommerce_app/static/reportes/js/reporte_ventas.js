// ==================== REPORTE DE VENTAS JS ====================

// Variables globales
let chartVentasPorDia = null;
let chartTopProductos = null;
let datosReporte = null;

// Inicialización
$(document).ready(function() {
    inicializarFechas();
    cargarSucursales();
    configurarEventos();
    
    // Cargar reporte inicial (último mes)
    $('#tipoReporte').val('mensual');
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

// Cargar sucursales (solo para empresas)
function cargarSucursales() {
    if (accountType === 'empresa') {
        // Las sucursales se cargarán con el reporte
        console.log('Sucursales se cargarán con el reporte');
    }
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
    
    // Exportar PDF
    $('#btnExportarPDF').on('click', function() {
        exportarPDF();
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
        sucursal_id: $('#sucursalFiltro').val() || ''
    };
    
    // Hacer petición AJAX
    $.ajax({
        url: '/ecommerce/api/obtener_datos_reporte/',
        method: 'GET',
        data: formData,
        success: function(response) {
            $('#loadingSpinner').hide();
            
            if (response.success) {
                datosReporte = response.data;
                
                if (datosReporte.ventas.length > 0) {
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
    // Actualizar KPIs
    $('#kpiTotalVentas').text('$' + formatearNumero(data.total_ventas));
    $('#kpiTotalPedidos').text(data.total_pedidos);
    $('#kpiTicketPromedio').text('$' + formatearNumero(data.ticket_promedio));
    $('#kpiPeriodo').text(formatearFechaLegible(data.fecha_inicio) + ' - ' + formatearFechaLegible(data.fecha_fin));
    
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
    
    // Generar gráficos
    generarGraficoVentasPorDia(data.ventas_por_dia);
    generarGraficoTopProductos(data.productos_vendidos);
    
    // Llenar tabla
    llenarTablaVentas(data.ventas);
}

// Generar gráfico de ventas por día
function generarGraficoVentasPorDia(ventasPorDia) {
    const ctx = document.getElementById('chartVentasPorDia');
    
    // Destruir gráfico anterior si existe
    if (chartVentasPorDia) {
        chartVentasPorDia.destroy();
    }
    
    const fechas = ventasPorDia.map(v => formatearFechaLegible(v.fecha));
    const totales = ventasPorDia.map(v => v.total);
    
    chartVentasPorDia = new Chart(ctx, {
        type: 'line',
        data: {
            labels: fechas,
            datasets: [{
                label: 'Ventas Diarias',
                data: totales,
                borderColor: 'rgb(13, 110, 253)',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: 'rgb(13, 110, 253)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return 'Ventas: $' + formatearNumero(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + formatearNumero(value);
                        },
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        },
                        maxRotation: 45,
                        minRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Generar gráfico de top productos
function generarGraficoTopProductos(productos) {
    const ctx = document.getElementById('chartTopProductos');
    
    // Destruir gráfico anterior si existe
    if (chartTopProductos) {
        chartTopProductos.destroy();
    }
    
    const nombres = productos.map(p => p.nombre.length > 20 ? p.nombre.substring(0, 20) + '...' : p.nombre);
    const cantidades = productos.map(p => p.cantidad);
    
    const colores = [
        'rgba(13, 110, 253, 0.8)',
        'rgba(10, 88, 202, 0.8)',
        'rgba(110, 168, 254, 0.8)',
        'rgba(25, 135, 84, 0.8)',
        'rgba(13, 202, 240, 0.8)'
    ];
    
    chartTopProductos = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: nombres,
            datasets: [{
                data: cantidades,
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
                    display: true,
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 11
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    return {
                                        text: `${label} (${value})`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
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
            }
        }
    });
}

// Llenar tabla de ventas
function llenarTablaVentas(ventas) {
    const tbody = $('#tablaVentasBody');
    tbody.empty();
    
    ventas.forEach(function(venta) {
        let badgeClass = '';
        switch(venta.estado) {
            case 'confirmado':
                badgeClass = 'badge-confirmado';
                break;
            case 'enviado':
                badgeClass = 'badge-enviado';
                break;
            case 'entregado':
                badgeClass = 'badge-entregado';
                break;
        }
        
        let row = `
            <tr>
                <td><strong>${venta.numero_pedido}</strong></td>
                <td>${venta.fecha}</td>
                <td>${venta.producto}</td>
                <td class="text-center">${venta.cantidad}</td>
                <td>$${formatearNumero(venta.precio_unitario)}</td>
                <td><strong>$${formatearNumero(venta.subtotal)}</strong></td>
                <td><span class="badge ${badgeClass}">${venta.estado}</span></td>
        `;
        
        if (accountType === 'empresa') {
            row += `<td>${venta.sucursal || '-'}</td>`;
        }
        
        row += `
                <td>${venta.tipo_comprador}</td>
            </tr>
        `;
        
        tbody.append(row);
    });
}

// Formatear número con separadores de miles
function formatearNumero(numero) {
    return parseFloat(numero).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Formatear fecha legible
function formatearFechaLegible(fecha) {
    const partes = fecha.split('-');
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    return `${partes[2]} ${meses[parseInt(partes[1]) - 1]} ${partes[0]}`;
}

// Mostrar error
function mostrarError(mensaje) {
    alert('Error: ' + mensaje);
}

// Exportar a PDF
function exportarPDF() {
    if (!datosReporte) {
        alert('No hay datos para exportar');
        return;
    }
    
    // Usar window.print() para generar PDF
    window.print();
}

// Exportar a Excel
function exportarExcel() {
    if (!datosReporte || !datosReporte.ventas || datosReporte.ventas.length === 0) {
        alert('No hay datos para exportar');
        return;
    }
    
    // Crear contenido CSV
    let csv = 'N° Pedido,Fecha,Producto,Cantidad,Precio Unitario,Subtotal,Estado';
    
    if (accountType === 'empresa') {
        csv += ',Sucursal';
    }
    
    csv += ',Tipo Comprador\n';
    
    datosReporte.ventas.forEach(function(venta) {
        csv += `"${venta.numero_pedido}",`;
        csv += `"${venta.fecha}",`;
        csv += `"${venta.producto}",`;
        csv += `${venta.cantidad},`;
        csv += `${venta.precio_unitario},`;
        csv += `${venta.subtotal},`;
        csv += `"${venta.estado}"`;
        
        if (accountType === 'empresa') {
            csv += `,"${venta.sucursal || '-'}"`;
        }
        
        csv += `,"${venta.tipo_comprador}"\n`;
    });
    
    // Agregar resumen
    csv += '\n\nRESUMEN\n';
    csv += `Total Ventas,$${formatearNumero(datosReporte.total_ventas)}\n`;
    csv += `Total Pedidos,${datosReporte.total_pedidos}\n`;
    csv += `Ticket Promedio,$${formatearNumero(datosReporte.ticket_promedio)}\n`;
    
    // Crear blob y descargar
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `reporte_ventas_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
