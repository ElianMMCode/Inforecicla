/**
 * FullCalendar - Sistema de Creación de Eventos
 * Versión mejorada con Select2
 */

// Bandera para evitar que se ejecute más de una vez
if (window.fullCalendarInitialized) {
    console.warn('⚠️ FullCalendar ya fue inicializado, evitando duplicado');
} else {
    window.fullCalendarInitialized = true;

document.addEventListener('DOMContentLoaded', function() {
    try {
        console.log('🎯 Inicializando sistema de calendario...');

        // ===== VERIFICAR QUE JQUERY Y SELECT2 ESTÉN DISPONIBLES =====
        if (typeof jQuery === 'undefined') {
            console.error('❌ jQuery no está cargado');
            return;
        }
        if (typeof jQuery.fn.select2 === 'undefined') {
            console.error('❌ Select2 no está cargado');
            return;
        }
        console.log('✅ jQuery y Select2 están disponibles');

        // ===== ELEMENTOS DEL DOM =====
        const calendarEl = document.getElementById('calendar');
        const selectMaterial = document.getElementById('selectMaterial');
        const selectCentroAcopio = document.getElementById('selectCentroAcopio');
        const btnGuardarEvento = document.getElementById('btnGuardarEvento');
        const modalCrearEvento = document.getElementById('modalCrearEvento');
        const formCrearEvento = document.getElementById('formCrearEvento');

        if (!calendarEl) {
            console.warn('⚠️ Elemento #calendar no encontrado');
            return;
        }

        // ===== PARÁMETROS =====
        const puntoEcaId = document.querySelector('input[id="inputPuntoEcaId"]')?.value;
        const usuarioId = document.querySelector('input[id="inputUsuarioId"]')?.value;

        console.log('🔍 Buscando inputs...');
        console.log('  input#inputPuntoEcaId existe:', !!document.getElementById('inputPuntoEcaId'));
        console.log('  input#inputUsuarioId existe:', !!document.getElementById('inputUsuarioId'));
        console.log('📋 Parámetros:');
        console.log('  puntoEcaId:', puntoEcaId);
        console.log('  usuarioId:', usuarioId);

        if (!puntoEcaId || !usuarioId) {
            console.error('❌ Parámetros incompletos');
            return;
        }

        let calendar = null;

        // ===== INICIALIZAR CALENDARIO =====
        try {
            calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay'
                },
                locale: 'es',
                height: 'auto',
                selectable: true,
                events: {
                    url: `/api/eventos/punto/${puntoEcaId}/eventos`,
                    method: 'GET',
                    failure: function() {
                        console.warn('⚠️ Error cargando eventos del calendario');
                    }
                },
                select: function(info) {
                    abrirModal(info.start);
                },
                eventClick: function(info) {
                    console.log('📌 Evento clickeado:', info.event.title);
                    mostrarDetallesEvento(info.event);
                }
            });

            calendar.render();
            console.log('✅ Calendario inicializado');
        } catch (e) {
            console.error('❌ Error inicializando calendario:', e);
        }

        // ===== CARGAR MATERIALES =====
        function cargarMateriales() {
            if (!selectMaterial) {
                console.warn('⚠️ selectMaterial no encontrado');
                return;
            }

            console.log('📥 Cargando materiales...');

            fetch(`/punto-eca/catalogo/inventario/materiales/buscar?puntoId=${puntoEcaId}`)
                .then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
                .then(data => {
                    console.log('✅ Materiales recibidos:', data.length);

                    // Limpiar opciones anteriores
                    selectMaterial.innerHTML = '<option value="">-- Seleccionar Material --</option>';

                    if (Array.isArray(data) && data.length > 0) {
                        data.forEach(m => {
                            const opt = document.createElement('option');
                            opt.value = m.materialId;
                            opt.textContent = m.nmbMaterial || m.dscMaterial || 'Material sin nombre';
                            selectMaterial.appendChild(opt);
                        });
                        console.log('✅ ' + data.length + ' materiales agregados');
                    } else {
                        console.warn('⚠️ No hay materiales disponibles');
                        const opt = document.createElement('option');
                        opt.disabled = true;
                        opt.textContent = 'No hay materiales disponibles';
                        selectMaterial.appendChild(opt);
                    }

                    // Reinicializar Select2 después de cargar datos
                    const $ = jQuery;
                    if ($(selectMaterial).data('select2')) {
                        $(selectMaterial).select2('destroy');
                    }
                    $(selectMaterial).select2({
                        dropdownParent: $('#modalCrearEvento'),
                        language: 'es',
                        width: '100%',
                        minimumResultsForSearch: 1,
                        placeholder: 'Seleccionar Material...',
                        allowClear: true,
                        theme: 'bootstrap-5',
                        containerCssClass: 'select2-custom'
                    });
                    console.log('  ✅ Select2 reinicializado en selectMaterial');
                })
                .catch(e => {
                    console.error('❌ Error cargando materiales:', e);
                    selectMaterial.innerHTML = '<option disabled>Error cargando materiales</option>';
                });
        }

        // ===== CARGAR CENTROS =====
        function cargarCentrosAcopio() {
            if (!selectCentroAcopio) {
                console.warn('⚠️ selectCentroAcopio no encontrado');
                return;
            }

            console.log('📥 Cargando centros para puntoEcaId:', puntoEcaId);

            fetch(`/punto-eca/${puntoEcaId}/centros-acopio`)
                .then(response => {
                    console.log('📡 Response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('✅ Centros recibidos - cantidad:', data ? data.length : 0);
                    console.log('📦 Datos completos:', data);

                    // Limpiar opciones anteriores
                    selectCentroAcopio.innerHTML = '<option value="">-- Sin asignar --</option>';

                    if (data && Array.isArray(data) && data.length > 0) {
                        data.forEach((centro, idx) => {
                            console.log(`   Centro ${idx}:`, {
                                cntAcpId: centro.cntAcpId,
                                nombreCntAcp: centro.nombreCntAcp,
                                tienePuntoEca: centro.tienePuntoEca
                            });

                            const opt = document.createElement('option');
                            opt.value = centro.cntAcpId;

                            let nombre = centro.nombreCntAcp || 'Centro sin nombre';

                            if (centro.tienePuntoEca) {
                                nombre += ' (del punto)';
                            } else {
                                nombre += ' (global)';
                            }

                            opt.textContent = nombre;
                            selectCentroAcopio.appendChild(opt);
                        });

                        console.log('✅ ' + data.length + ' centros agregados al select');
                    } else {
                        console.warn('⚠️ No hay centros o data es vacío/null');
                        const opt = document.createElement('option');
                        opt.disabled = true;
                        opt.textContent = 'No hay centros disponibles';
                        selectCentroAcopio.appendChild(opt);
                    }

                    // Reinicializar Select2 después de cargar datos
                    const $ = jQuery;
                    if ($(selectCentroAcopio).data('select2')) {
                        $(selectCentroAcopio).select2('destroy');
                    }
                    $(selectCentroAcopio).select2({
                        dropdownParent: $('#modalCrearEvento'),
                        language: 'es',
                        width: '100%',
                        minimumResultsForSearch: 1,
                        placeholder: 'Seleccionar Centro...',
                        allowClear: true,
                        theme: 'bootstrap-5',
                        containerCssClass: 'select2-custom'
                    });
                    console.log('  ✅ Select2 reinicializado en selectCentroAcopio');
                })
                .catch(error => {
                    console.error('❌ Error cargando centros:', error.message);
                    console.error('Stack:', error.stack);
                    selectCentroAcopio.innerHTML = '<option disabled>Error cargando centros</option>';
                });
        }

        // ===== ABRIR MODAL =====
        function abrirModal(fecha) {
            console.log('📅 Abriendo modal para fecha:', fecha);
            console.log('   Reseteando estado de edición');

            // IMPORTANTE: Resetear el estado de edición ANTES de abrir el modal
            eventoActualEditando = null;
            datosEventoEdicion = null;

            // Esperar un pequeño delay para asegurar que se resetea el estado
            setTimeout(() => {
                const inputFecha = document.getElementById('inputFechaInicio');
                if (inputFecha) {
                    // Convertir la fecha a ISO format (YYYY-MM-DD)
                    const fechaISO = fecha.toISOString().split('T')[0];
                    inputFecha.value = fechaISO;
                    console.log('✅ Fecha pre-cargada:', fechaISO);
                } else {
                    console.warn('⚠️ inputFechaInicio no encontrado');
                }

                if (modalCrearEvento) {
                    const modal = new bootstrap.Modal(modalCrearEvento);
                    modal.show();
                    console.log('✅ Modal abierto');

                    // Cargar datos y mostrar el modal
                    cargarMateriales();
                    cargarCentrosAcopio();

                    // Inicializar Select2 del tipo de repetición después de que el modal sea visible
                    setTimeout(() => {
                        inicializarSelect2();
                    }, 100);
                }
            }, 10);
        }

        // ===== MOSTRAR DETALLES DEL EVENTO =====
        function mostrarDetallesEvento(evento) {
            console.log('📋 Mostrando detalles del evento:', evento.title);
            console.log('   Fecha inicio del evento:', evento.start);
            console.log('   ID del evento:', evento.id);

            const modalDetalles = document.getElementById('modalDetallesEvento');
            if (!modalDetalles) {
                console.warn('⚠️ Modal de detalles no encontrado');
                return;
            }

            // Rellenar datos del evento
            const tituloEl = document.getElementById('detallesTitulo');
            const descripcionEl = document.getElementById('detallesDescripcion');
            const fechaInicioEl = document.getElementById('detallesFechaInicio');
            const fechaFinEl = document.getElementById('detallesFechaFin');
            const materialEl = document.getElementById('detallesMaterial');
            const centroEl = document.getElementById('detallesCentro');
            const btnEditar = document.getElementById('btnEditarEvento');
            const btnBorrar = document.getElementById('btnBorrarEvento');

            if (tituloEl) tituloEl.textContent = evento.title || 'Sin título';
            if (descripcionEl) descripcionEl.textContent = evento.extendedProps?.descripcion || 'Sin descripción';
            if (fechaInicioEl) fechaInicioEl.textContent = new Date(evento.start).toLocaleString('es-ES');
            if (fechaFinEl) fechaFinEl.textContent = new Date(evento.end).toLocaleString('es-ES');
            if (materialEl) materialEl.textContent = evento.extendedProps?.material || 'Sin material';
            if (centroEl) centroEl.textContent = evento.extendedProps?.centro || 'Sin asignar';

            // GUARDAR DATOS DEL EVENTO PARA USO EN BORRADO
            // Esto es importante para poder detectar si es repetido o no
            datosEventoEdicion = {
                eventoId: evento.id,
                fechaInicio: evento.start,
                fechaFin: evento.end,
                tipoRepeticion: evento.extendedProps?.tipoRepeticion || 'SIN_REPETICION',
                esRepeticion: evento.extendedProps?.esRepeticion === true,
                titulo: evento.title
            };
            console.log('📌 Datos guardados para borrado:', datosEventoEdicion);

            // Configurar botones - Pasar OBJETO del evento, no solo ID
            if (btnEditar) {
                btnEditar.onclick = () => editarEvento(evento.id, evento);
            }
            if (btnBorrar) {
                btnBorrar.onclick = () => borrarEvento(evento.id);
            }

            // Mostrar modal
            const modal = new bootstrap.Modal(modalDetalles);
            modal.show();
        }

        // Variables globales para guardar el evento actual y sus datos
        let eventoActualEditando = null;
        let datosEventoEdicion = null;

        // ...existing code...

        // ===== EDITAR EVENTO =====
        function editarEvento(eventoId, eventoClickeado) {
            console.log('✏️ Editando evento:', eventoId);
            console.log('   Evento clickeado:', eventoClickeado);

            // Guardar el evento actual
            eventoActualEditando = eventoId;

            // Si tenemos el evento clickeado, usar su fecha como inicio
            let fechaInicioDelEvento = null;
            if (eventoClickeado && eventoClickeado.start) {
                fechaInicioDelEvento = new Date(eventoClickeado.start);
                console.log('📅 Fecha del evento clickeado:', fechaInicioDelEvento);
            }

            // Obtener los datos del evento desde el servidor
            fetch(`/api/eventos/${eventoId}`)
                .then(response => {
                    if (!response.ok) throw new Error('No se pudo obtener el evento');
                    return response.json();
                })
                .then(evento => {
                    console.log('📋 Evento obtenido:', evento);
                    console.log('   Material ID:', evento.materialId, 'Material Nombre:', evento.materialNombre);
                    console.log('   Centro ID:', evento.centroAcopioId, 'Centro Nombre:', evento.centroAcopioNombre);

                    // Guardar los datos para seleccionar después
                    datosEventoEdicion = evento;

                    // Llenar el formulario de crear evento con los datos actuales
                    document.getElementById('inputTitulo').value = evento.titulo || '';
                    document.getElementById('inputDescripcion').value = evento.descripcion || '';
                    document.getElementById('inputColor').value = evento.color || '#28a745';

                    // Setear las fechas
                    // SI CLICKEÓ UN EVENTO REPETIDO, USAR LA FECHA DEL EVENTO CLICKEADO
                    // SI NO, USAR LA FECHA DEL EVENTO BASE
                    const fechaInicio = fechaInicioDelEvento || new Date(evento.fechaInicio);
                    const fechaFin = new Date(evento.fechaFin);

                    console.log('📅 Fechas a usar:');
                    console.log('   fechaInicio (clickeada):', fechaInicioDelEvento);
                    console.log('   fechaInicio (base):', evento.fechaInicio);
                    console.log('   fechaInicio final:', fechaInicio);

                    // Formatear fechas para los inputs
                    const fechaInicioISO = fechaInicio.toISOString().split('T')[0];
                    const horaInicioStr = String(fechaInicio.getHours()).padStart(2, '0') + ':' +
                                         String(fechaInicio.getMinutes()).padStart(2, '0');
                    const horaFinStr = String(fechaFin.getHours()).padStart(2, '0') + ':' +
                                      String(fechaFin.getMinutes()).padStart(2, '0');

                    document.getElementById('inputFechaInicio').value = fechaInicioISO;
                    document.getElementById('inputHoraInicio').value = horaInicioStr;
                    document.getElementById('inputHoraFin').value = horaFinStr;

                    console.log('✅ Fechas asignadas:');
                    console.log('   inputFechaInicio:', fechaInicioISO);
                    console.log('   inputHoraInicio:', horaInicioStr);
                    console.log('   inputHoraFin:', horaFinStr);

                    // Tipo de repetición
                    document.getElementById('selectTipoRepeticion').value = evento.tipoRepeticion || 'SIN_REPETICION';

                    // Cargar materiales y centros (sin seleccionar aún)
                    console.log('🔄 Cargando materiales y centros...');
                    cargarMateriales();
                    cargarCentrosAcopio();

                    // Cambiar el botón de guardar
                    const btnGuardar = document.getElementById('btnGuardarEvento');
                    btnGuardar.innerHTML = '<i class="bi bi-pencil"></i> Actualizar Evento';
                    btnGuardar.className = 'btn btn-warning btn-sm';

                    // Cerrar modal de detalles
                    const modalDetalles = document.getElementById('modalDetallesEvento');
                    const modalActual = bootstrap.Modal.getInstance(modalDetalles);
                    if (modalActual) modalActual.hide();

                    // Abrir modal de edición
                    setTimeout(() => {
                        const modalCrear = new bootstrap.Modal(document.getElementById('modalCrearEvento'));
                        modalCrear.show();
                    }, 300);
                })
                .catch(error => {
                    console.error('❌ Error obteniendo evento:', error);
                    alert('Error al obtener los datos del evento');
                });
        }

        // ===== BORRAR EVENTO =====
        function borrarEvento(eventoId) {
            console.log('🗑️ Borrando evento:', eventoId);
            console.log('   Datos edición:', datosEventoEdicion);

            // Verificar si es un evento repetido
            // Un evento es repetido si:
            // 1. datosEventoEdicion existe Y tiene tipoRepeticion !== 'SIN_REPETICION'
            // OR
            // 2. Tiene esRepeticion = true (es una instancia)
            const tieneRepeticion = datosEventoEdicion &&
                                   datosEventoEdicion.tipoRepeticion &&
                                   datosEventoEdicion.tipoRepeticion !== 'SIN_REPETICION';
            const esInstanciaRepetida = datosEventoEdicion && datosEventoEdicion.esRepeticion === true;

            console.log('   ¿Tiene repetición?:', tieneRepeticion);
            console.log('   ¿Es instancia repetida?:', esInstanciaRepetida);

            // Si es una instancia repetida O el evento tiene repetición
            if (tieneRepeticion || esInstanciaRepetida) {
                console.log('🔄 Detectado evento repetido');

                // Preguntar qué borrar
                const opcion = confirm('¿Desea borrar SOLO esta ocurrencia?\n\nAceptar = Solo esta ocurrencia\nCancelar = Borrar todo el evento');

                if (!opcion) {
                    // Cancelar = Borrar todo el evento
                    console.log('   Usuario eligió: Borrar TODO el evento');
                    if (confirm('¿Está seguro de que desea borrar TODO el evento repetido?')) {
                        borrarEventoCompleto(eventoId);
                    }
                } else {
                    // Aceptar = Borrar solo esta ocurrencia
                    console.log('   Usuario eligió: Borrar solo ESTA ocurrencia');
                    borrarSoloInstancia(eventoId);
                }
            } else {
                // Si no es repetido, borrar directamente
                console.log('📌 Evento sin repetición, borrando directamente');
                if (confirm('¿Está seguro de que desea borrar este evento?')) {
                    borrarEventoCompleto(eventoId);
                }
            }
        }

        function borrarEventoCompleto(eventoId) {
            console.log('🗑️ Borrando evento completo:', eventoId);

            fetch(`/api/eventos/${eventoId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => {
                console.log('📡 Response status:', response.status);
                if (response.ok) {
                    console.log('✅ Evento borrado completamente');
                    alert('Evento borrado correctamente');

                    // Recargar calendario
                    if (calendar) calendar.refetchEvents();

                    // Cerrar modal
                    const modalDetalles = document.getElementById('modalDetallesEvento');
                    if (modalDetalles) {
                        const modal = bootstrap.Modal.getInstance(modalDetalles);
                        if (modal) modal.hide();
                    }
                } else {
                    return response.json().then(err => {
                        throw new Error(err.error || 'Error desconocido');
                    });
                }
            })
            .catch(error => {
                console.error('❌ Error:', error);
                alert('❌ Error al borrar el evento: ' + error.message);
            });
        }

        function borrarSoloInstancia(eventoId) {
            console.log('🗑️ Borrando solo esta instancia:', eventoId);
            console.log('   Datos edición:', datosEventoEdicion);

            // Construir el payload con fechaInstancia (y opcionalmente instanciaId si está disponible)
            const payload = {
                fechaInstancia: datosEventoEdicion.fechaInicio
            };

            // Si tenemos un instanciaId en los datos, agregarlo también
            if (datosEventoEdicion.instanciaId) {
                payload.instanciaId = datosEventoEdicion.instanciaId;
            }

            console.log('📦 Enviando payload:', payload);

            fetch(`/api/eventos/${eventoId}/instancia`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => {
                console.log('📡 Response status:', response.status);
                if (response.ok) {
                    console.log('✅ Instancia borrada');
                    alert('Ocurrencia borrada correctamente');

                    // Recargar calendario
                    if (calendar) calendar.refetchEvents();

                    // Cerrar modal
                    const modalDetalles = document.getElementById('modalDetallesEvento');
                    if (modalDetalles) {
                        const modal = bootstrap.Modal.getInstance(modalDetalles);
                        if (modal) modal.hide();
                    }
                } else {
                    return response.json().then(err => {
                        throw new Error(err.error || 'Error desconocido');
                    });
                }
            })
            .catch(error => {
                console.error('❌ Error:', error);
                alert('❌ Error al borrar la ocurrencia: ' + error.message);
            });
        }

        // ===== GUARDAR EVENTO =====
        async function guardarEvento() {
            console.log('💾 Guardando evento...');

            // Validar
            if (!selectMaterial?.value) {
                alert('❌ Selecciona un material');
                return;
            }

            const titulo = document.getElementById('inputTitulo')?.value;
            if (!titulo?.trim()) {
                alert('❌ Ingresa un título');
                return;
            }

            try {
                const datos = {
                    materialId: selectMaterial.value,
                    puntoEcaId: puntoEcaId,
                    usuarioId: usuarioId,
                    centroAcopioId: selectCentroAcopio?.value || null,
                    titulo: titulo,
                    descripcion: document.getElementById('inputDescripcion')?.value || '',
                    fechaInicio: (document.getElementById('inputFechaInicio')?.value || '') + 'T' + (document.getElementById('inputHoraInicio')?.value || '10:00') + ':00',
                    fechaFin: (document.getElementById('inputFechaInicio')?.value || '') + 'T' + (document.getElementById('inputHoraFin')?.value || '11:00') + ':00',
                    tipoRepeticion: document.getElementById('selectTipoRepeticion')?.value || 'SIN_REPETICION',
                    fechaFinRepeticion: document.getElementById('inputFechaFinRepeticion')?.value || null,
                    color: document.getElementById('inputColor')?.value || '#28a745'
                };

                console.log('📤 Enviando datos:', datos);

                if (btnGuardarEvento) {
                    btnGuardarEvento.disabled = true;
                    btnGuardarEvento.innerHTML = 'Guardando...';
                }

                // Determinar si es creación o edición
                let url = '/api/eventos/crear-venta';
                let metodo = 'POST';

                if (eventoActualEditando) {
                    url = `/api/eventos/${eventoActualEditando}`;
                    metodo = 'PUT';
                    console.log('✏️ Actualizando evento existente:', eventoActualEditando);
                } else {
                    console.log('➕ Creando nuevo evento');
                }

                const res = await fetch(url, {
                    method: metodo,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datos)
                });

                console.log('📡 Response status:', res.status);

                if (res.ok) {
                    const respuesta = await res.json();
                    console.log('✅ Evento guardado:', respuesta);
                    const mensaje = eventoActualEditando ? 'Evento actualizado correctamente' : 'Evento creado correctamente';
                    alert('✅ ' + mensaje);

                    // Recargar calendario
                    if (calendar) calendar.refetchEvents();

                    // Cerrar modal
                    const modal = bootstrap.Modal.getInstance(modalCrearEvento);
                    if (modal) modal.hide();

                    // Limpiar formulario
                    if (formCrearEvento) formCrearEvento.reset();
                } else {
                    const err = await res.json();
                    console.error('❌ Error:', err);
                    alert('❌ Error: ' + (err.error || 'Error al guardar'));
                }
            } catch (e) {
                console.error('❌ Exception:', e);
                alert('❌ Error: ' + e.message);
            } finally {
                if (btnGuardarEvento) {
                    btnGuardarEvento.disabled = false;
                    btnGuardarEvento.innerHTML = '<i class="bi bi-save"></i> Guardar Evento';
                    btnGuardarEvento.className = 'btn btn-success btn-sm';
                }

                // Resetear estado de edición
                eventoActualEditando = null;
            }
        }

        // ===== EVENT LISTENERS =====
        // Usar una bandera para evitar agregar múltiples listeners
        let guardaEventoListenerAgregado = false;

        function agregarListenerGuardarEvento() {
            if (guardaEventoListenerAgregado) {
                console.log('⚠️ Listener de guardar evento ya fue agregado, evitando duplicado');
                return;
            }

            if (!btnGuardarEvento) {
                console.warn('⚠️ btnGuardarEvento no encontrado');
                return;
            }

            console.log('➕ Agregando listener a btnGuardarEvento');

            // Remover listeners anteriores clonando el elemento
            const btnNuevo = btnGuardarEvento.cloneNode(true);
            btnGuardarEvento.replaceWith(btnNuevo);

            // Actualizar referencia
            window.btnGuardarEvento = document.getElementById('btnGuardarEvento');

            if (window.btnGuardarEvento) {
                window.btnGuardarEvento.addEventListener('click', guardarEvento);
                guardaEventoListenerAgregado = true;
                console.log('✅ Listener agregado correctamente');
            }
        }

        // Agregar listener en la carga inicial
        setTimeout(() => {
            agregarListenerGuardarEvento();
        }, 500);

        if (modalCrearEvento) {
            modalCrearEvento.addEventListener('show.bs.modal', () => {
                console.log('📋 Modal abierto - evento en edición:', eventoActualEditando);

                // GUARDAR LA FECHA SI ESTÁ PRE-CARGADA (crear evento nuevo)
                const fechaGuardada = document.getElementById('inputFechaInicio')?.value;
                console.log('   Fecha pre-cargada antes de resetear:', fechaGuardada);

                // Si NO estamos editando, resetear el formulario
                if (!eventoActualEditando) {
                    console.log('➕ Modo: CREAR nuevo evento');
                    if (formCrearEvento) {
                        formCrearEvento.reset();
                        console.log('   Formulario reseteado');
                    }

                    // RESTAURAR LA FECHA GUARDADA
                    if (fechaGuardada) {
                        document.getElementById('inputFechaInicio').value = fechaGuardada;
                        console.log('   ✅ Fecha restaurada:', fechaGuardada);
                    }

                    // Resetear botón a su estado original
                    if (btnGuardarEvento) {
                        btnGuardarEvento.innerHTML = '<i class="bi bi-save"></i> Guardar Evento';
                        btnGuardarEvento.className = 'btn btn-success btn-sm';
                    }
                } else {
                    console.log('✏️ Modo: EDITAR evento');
                }

                cargarMateriales();
                cargarCentrosAcopio();
            });

            // Escuchar cuando el modal se ha mostrado completamente
            modalCrearEvento.addEventListener('shown.bs.modal', () => {
                console.log('📋 Modal completamente abierto');

                // Si estamos editando, seleccionar el material y centro ahora
                if (eventoActualEditando && datosEventoEdicion) {
                    console.log('⏳ Seleccionando material y centro después de inicializar...');

                    // Esperar a que Select2 esté completamente inicializado
                    const $ = jQuery;

                    // Número máximo de intentos de sincronización
                    let intentos = 0;
                    const maxIntentos = 10;
                    const intervalo = setInterval(() => {
                        intentos++;
                        console.log(`🔄 Intento ${intentos} de sincronizar Select2...`);

                        // Seleccionar Material
                        if (datosEventoEdicion.materialId) {
                            const selectMaterialElement = document.getElementById('selectMaterial');
                            if (selectMaterialElement) {
                                const opcionesMaterial = Array.from(selectMaterialElement.options).map(o => ({value: o.value, text: o.text}));
                                const existeMaterial = opcionesMaterial.find(o => o.value === datosEventoEdicion.materialId);

                                if (existeMaterial) {
                                    console.log('✅ Material encontrado en opciones:', datosEventoEdicion.materialId);
                                    selectMaterialElement.value = datosEventoEdicion.materialId;
                                    $(selectMaterialElement).trigger('change');
                                    console.log('   Material seleccionado:', datosEventoEdicion.materialNombre);
                                } else {
                                    console.warn('⚠️ Material no encontrado en opciones. Disponibles:', opcionesMaterial);
                                    if (intentos < maxIntentos) {
                                        return; // Reintentar
                                    }
                                }
                            }
                        }

                        // Seleccionar Centro
                        if (datosEventoEdicion.centroAcopioId) {
                            const selectCentroElement = document.getElementById('selectCentroAcopio');
                            if (selectCentroElement) {
                                const opcionesCentro = Array.from(selectCentroElement.options).map(o => ({value: o.value, text: o.text}));
                                const existeCentro = opcionesCentro.find(o => o.value === datosEventoEdicion.centroAcopioId);

                                if (existeCentro) {
                                    console.log('✅ Centro encontrado en opciones:', datosEventoEdicion.centroAcopioId);
                                    selectCentroElement.value = datosEventoEdicion.centroAcopioId;
                                    $(selectCentroElement).trigger('change');
                                    console.log('   Centro seleccionado:', datosEventoEdicion.centroAcopioNombre);
                                } else {
                                    console.warn('⚠️ Centro no encontrado en opciones. Disponibles:', opcionesCentro);
                                    if (intentos < maxIntentos) {
                                        return; // Reintentar
                                    }
                                }
                            }
                        }

                        // Ambos encontrados o máximo de intentos
                        clearInterval(intervalo);
                        console.log('✅ Sincronización completada');
                    }, 200); // Reintentar cada 200ms

                    // Limpiar intervalo después de máximo tiempo
                    setTimeout(() => clearInterval(intervalo), maxIntentos * 200 + 100);
                }
            });
        }

        console.log('✅ Sistema completamente inicializado');

        // ===== INICIALIZAR SELECT2 =====
        function inicializarSelect2() {
            console.log('🎨 Inicializando Select2...');

            try {
                // Usar $ de jQuery de forma segura
                const $ = jQuery;

                // Inicializar selectMaterial si existe y aún no está inicializado
                if (selectMaterial) {
                    if ($(selectMaterial).data('select2')) {
                        console.log('  ♻️ Destruyendo Select2 anterior en selectMaterial');
                        $(selectMaterial).select2('destroy');
                    }
                    $(selectMaterial).select2({
                        dropdownParent: $('#modalCrearEvento'),
                        language: 'es',
                        width: '100%',
                        minimumResultsForSearch: 1,
                        placeholder: 'Seleccionar Material...',
                        allowClear: true,
                        theme: 'bootstrap-5',
                        containerCssClass: 'select2-custom'
                    });
                    console.log('  ✅ Select2 inicializado en selectMaterial');
                }

                // Inicializar selectCentroAcopio si existe
                if (selectCentroAcopio) {
                    if ($(selectCentroAcopio).data('select2')) {
                        console.log('  ♻️ Destruyendo Select2 anterior en selectCentroAcopio');
                        $(selectCentroAcopio).select2('destroy');
                    }
                    $(selectCentroAcopio).select2({
                        dropdownParent: $('#modalCrearEvento'),
                        language: 'es',
                        width: '100%',
                        minimumResultsForSearch: 1,
                        placeholder: 'Seleccionar Centro...',
                        allowClear: true,
                        theme: 'bootstrap-5',
                        containerCssClass: 'select2-custom'
                    });
                    console.log('  ✅ Select2 inicializado en selectCentroAcopio');
                }

                // Inicializar selectTipoRepeticion
                const selectTipoRepeticion = document.getElementById('selectTipoRepeticion');
                if (selectTipoRepeticion) {
                    if ($(selectTipoRepeticion).data('select2')) {
                        console.log('  ♻️ Destruyendo Select2 anterior en selectTipoRepeticion');
                        $(selectTipoRepeticion).select2('destroy');
                    }
                    $(selectTipoRepeticion).select2({
                        dropdownParent: $('#modalCrearEvento'),
                        language: 'es',
                        width: '100%',
                        minimumResultsForSearch: 1,
                        placeholder: 'Seleccionar tipo de repetición...',
                        allowClear: false,
                        theme: 'bootstrap-5',
                        containerCssClass: 'select2-custom'
                    });
                    console.log('  ✅ Select2 inicializado en selectTipoRepeticion');
                }

                console.log('✅ Select2 completamente inicializado');
            } catch (e) {
                console.warn('⚠️ Error inicializando Select2:', e.message);
            }
        }

    } catch (error) {
        console.error('❌ Error global:', error);
    }
});

} // Cierre de la bandera fullCalendarInitialized
