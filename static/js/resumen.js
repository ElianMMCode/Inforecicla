function formatearFecha(fecha) {
    if (!fecha || fecha === 'N/A') return 'N/A';

    const date = new Date(fecha);
    const hoy = new Date();
    const ayer = new Date(hoy);
    ayer.setDate(ayer.getDate() - 1);

    if (date.toDateString() === hoy.toDateString()) {
        return 'Hoy';
    } else if (date.toDateString() === ayer.toDateString()) {
        return 'Ayer';
    } else {
        return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Script de resumen Bootstrap cargado');

    // Intentar obtener datos del atributo data del HTML (datos del servidor)
    const elementoResumen = document.querySelector('[data-resumen-datos]');
    let datosResumen = null;

    if (elementoResumen?.dataset.resumenDatos) {
        try {
            const datosString = elementoResumen.dataset.resumenDatos;
            console.log('📦 String de datos recibido:', datosString.substring(0, 100) + '...');

            // Parsear JSON
            datosResumen = JSON.parse(datosString);
            console.log('✅ Datos del resumen obtenidos desde el servidor:', datosResumen);

            // Validar que los datos esenciales estén presentes
            if (!datosResumen.inventarioTotal || !datosResumen.entradasMes) {
                console.warn('⚠️ Datos incompletos, usando datos de ejemplo');
                datosResumen = null;
            }
        } catch (e) {
            console.error('❌ Error parsing datos del servidor:', e);
            console.log('📝 String recibido:', elementoResumen.dataset.resumenDatos);
            datosResumen = null;
        }
    }

    // Si no hay datos válidos, mostrar datos de ejemplo
    if (!datosResumen) {
        console.warn('⚠️ No hay datos válidos del servidor, usando datos de ejemplo');
        datosResumen = {
            inventarioTotal: "1250.50",
            entradasMes: "450.75",
            salidasMes: "350.00",
            capacidadPorcentaje: 65,
            proximoDespacho: "Programado",
            proximaFecha: "2025-12-15",
            alertas: [{
                titulo: "Capacidad moderada",
                descripcion: "El inventario está en nivel moderado",
                tipo: "info"
            }],
            alertaCount: 1,
            movimientos: [
                {
                    fecha: "2025-12-10",
                    tipo: "Entrada",
                    cantidad: "150.00",
                    descripcion: "Plástico PET",
                    usuario: "Punto ECA",
                    icono: "arrow-down-circle-fill",
                    color: "text-info"
                },
                {
                    fecha: "2025-12-09",
                    tipo: "Salida",
                    cantidad: "80.00",
                    descripcion: "Aluminio",
                    usuario: "Sistema",
                    icono: "arrow-up-circle-fill",
                    color: "text-warning"
                }
            ]
        };
    }

    // Actualizar la UI con los datos
    actualizarUI(datosResumen);

    // Botón actualizar (recargar la página para obtener datos frescos)
    const btnActualizar = document.getElementById('btnActualizarResumen');
    if (btnActualizar) {
        btnActualizar.addEventListener('click', function() {
            console.log('🔄 Actualizando resumen...');
            this.disabled = true;
            const icon = this.querySelector('i');
            icon.style.animation = 'spin 0.6s linear';

            // Recargar la página después de 1 segundo
            setTimeout(() => {
                location.reload();
            }, 1000);
        });
    }

    function _actualizarTarjetaInventario(tarjeta, datos) {
        const heading = tarjeta.querySelector('h3, h6');
        if (heading) {
            heading.textContent = datos.inventarioTotal + ' kg';
        }
        const progreso = tarjeta.querySelector('.progress-bar');
        if (progreso) {
            progreso.style.width = datos.capacidadPorcentaje + '%';
        }
        const capacidad = tarjeta.querySelector('[class*="text-muted"]');
        if (capacidad) {
            capacidad.textContent = datos.capacidadPorcentaje + '% de capacidad';
        }
    }

    function _actualizarTarjetaEntradas(tarjeta, datos) {
        const heading = tarjeta.querySelector('h3, h6');
        if (heading) {
            heading.textContent = datos.entradasMes + ' kg';
        }
    }

    function _actualizarTarjetaSalidas(tarjeta, datos) {
        const heading = tarjeta.querySelector('h3, h6');
        if (heading) {
            heading.textContent = datos.salidasMes + ' kg';
        }
    }

    function _actualizarTarjetaProximo(tarjeta, datos) {
        const heading = tarjeta.querySelector('h3, h6');
        if (heading) {
            heading.textContent = datos.proximoDespacho;
        }
        const subtext = tarjeta.querySelector('[class*="text-muted"]');
        if (subtext) {
            subtext.textContent = datos.proximaFecha;
        }
    }

    function actualizarUI(datos) {
        console.log('🎨 Actualizando UI con datos');

        const tarjetas = document.querySelectorAll('.card');

        tarjetas.forEach(tarjeta => {
            const texto = tarjeta.textContent;

            if (texto.includes('Inventario')) {
                _actualizarTarjetaInventario(tarjeta, datos);
            } else if (texto.includes('Entradas')) {
                _actualizarTarjetaEntradas(tarjeta, datos);
            } else if (texto.includes('Salidas')) {
                _actualizarTarjetaSalidas(tarjeta, datos);
            } else if (texto.includes('Próximo') || texto.includes('Próx')) {
                _actualizarTarjetaProximo(tarjeta, datos);
            }
        });

        actualizarAlertas(datos.alertas, datos.alertaCount);
        cargarMovimientos(datos.movimientos);

        console.log('✅ UI actualizada correctamente');
    }

    // Función para actualizar alertas
    function actualizarAlertas(alertas, count) {
        const alertasContainer = document.getElementById('alertasContainer');
        const alertaCount = document.getElementById('alertaCount');

        if (alertaCount) {
            alertaCount.textContent = count;
        }

        if (alertasContainer) {
            if (!alertas || alertas.length === 0) {
                alertasContainer.innerHTML = `
                    <div class="text-center py-5">
                        <i class="bi bi-check-circle text-success" style="font-size: 2.5rem;"></i>
                        <p class="text-muted mt-3 mb-0">Sin alertas. Todo funciona correctamente.</p>
                    </div>
                `;
            } else {
                let html = '<div class="list-group list-group-flush">';
                alertas.forEach(alerta => {
                    let severidad;
                    if (alerta.tipo === 'warning') {
                        severidad = 'warning';
                    } else if (alerta.tipo === 'critico') {
                        severidad = 'danger';
                    } else {
                        severidad = 'info';
                    }
                    html += `
                        <div class="alert alert-${severidad} alert-dismissible fade show" role="alert">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            <strong>${alerta.titulo}</strong><br/>
                            <small>${alerta.descripcion}</small>
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                });
                html += '</div>';
                alertasContainer.innerHTML = html;
            }
        }
    }

    // Función para cargar movimientos
    function cargarMovimientos(movimientos) {
        const container = document.getElementById('ultimosMovimientos');

        if (!container) {
            console.warn('⚠️ Contenedor de movimientos no encontrado');
            return;
        }

        if (!movimientos || movimientos.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-inbox text-muted" style="font-size: 2rem;"></i>
                    <p class="text-muted mt-2">Sin movimientos registrados</p>
                </div>
            `;
            return;
        }

        let html = '<div class="list-group list-group-flush">';

        movimientos.forEach((mov) => {
            html += `
                <div class="list-group-item border-start border-success border-2 px-4">
                    <div class="row align-items-center py-3">
                        <div class="col-auto">
                            <i class="bi bi-${mov.icono} ${mov.color}" style="font-size: 1.5rem;"></i>
                        </div>
                        <div class="col">
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <strong class="text-dark">${mov.tipo}</strong>
                                <span class="badge bg-success bg-opacity-25 text-success">${mov.cantidad} kg</span>
                            </div>
                            <small class="text-muted">
                                <i class="bi bi-box me-1"></i>${mov.descripcion}
                                <span class="mx-2">•</span>
                                <i class="bi bi-person me-1"></i>${mov.usuario}
                            </small>
                        </div>
                        <div class="col-auto text-end">
                            <small class="text-muted d-block">${formatearFecha(mov.fecha)}</small>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    // Agregar estilos de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
        
        .list-group-item {
            transition: background-color 0.2s ease;
        }
        
        .list-group-item:hover {
            background-color: rgba(25, 135, 84, 0.05);
        }

        .card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1) !important;
        }
    `;
    document.head.appendChild(style);

    console.log('✅ Resumen inicializado correctamente');
});



