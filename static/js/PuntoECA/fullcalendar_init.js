// static/js/PuntoECA/fullcalendar_init.js
// Inicializa FullCalendar en el div #calendar y maneja eventos mock + creación desde modal.

// ==== Mover lógica de edición/modal acá para evitar contextos disjuntos ====
function llenarModalEdicion(evento) {
  console.log('llenarModalEdicion, recibí:', evento);
  if (!evento) {
    console.warn('No hay evento!');
    return;
  }
  function setSelectValue(selId, value, labelFallback) {
    var sel = document.getElementById(selId);
    if (!sel) return;
    if (value && !Array.from(sel.options).some(opt => opt.value == value)) {
      var opt = document.createElement('option');
      opt.value = value;
      opt.text = labelFallback || value;
      sel.appendChild(opt);
    }
    sel.value = value || '';
  }
  document.getElementById('editarEventoId').value = evento.id || '';
  document.getElementById('inputEditarTitulo').value = evento.title || '';
  document.getElementById('inputEditarDescripcion').value = evento.descripcion || '';
  document.getElementById('inputEditarFechaInicio').value = (evento.start||'').split('T')[0] || '';
  document.getElementById('inputEditarHoraInicio').value = (evento.start||'').split('T')[1] ? (evento.start||'').split('T')[1].substring(0,5) : '';
  document.getElementById('inputEditarHoraFin').value = (evento.end||'').split('T')[1] ? (evento.end||'').split('T')[1].substring(0,5) : '';
  document.getElementById('inputEditarColor').value = evento.backgroundColor || '#28a745';
  setSelectValue('editarSelectMaterial', evento.materialId, '(Material no disponible)');
  setSelectValue('editarSelectCentroAcopio', evento.centroAcopioId, '(Centro no disponible)');
  setSelectValue('editarSelectTipoRepeticion', evento.tipoRepeticion || 'NINGUNA');
  document.getElementById('inputEditarFechaFinRepeticion').value = (evento.fechaFinRepeticion || '').split('T')[0] || '';
  document.getElementById('inputEditarObservaciones').value = evento.observaciones || '';
  document.getElementById('editarPuntoEcaId').value = evento.puntoEcaId || '';
  document.getElementById('editarUsuarioId').value = evento.usuarioId || '';
}
// Delegado click para botón "Editar Evento" centralizado en el mismo archivo
// Garantiza mismo contexto y acceso global real

document.addEventListener("DOMContentLoaded", function () {
  document.addEventListener('click', function(event) {
    if (event.target && event.target.id === 'btnEditarEvento') {
      console.log('DEBUG boton editar: eventoActual =', window.eventoActual);
      // Antes de abrir modal, poblar selects de edición desde los de creación (garantiza opciones)
      function copiarOpcionesSelect(srcId, destId) {
        var src = document.getElementById(srcId);
        var dest = document.getElementById(destId);
        if (!src || !dest) return;
        dest.innerHTML = '';
        Array.from(src.options).forEach(function(opt) {
          var copia = opt.cloneNode(true);
          dest.appendChild(copia);
        });
      }
      copiarOpcionesSelect('selectMaterial', 'editarSelectMaterial');
      copiarOpcionesSelect('selectCentroAcopio', 'editarSelectCentroAcopio');
      // También copiar los tipos de repetición
      copiarOpcionesSelect('selectTipoRepeticion', 'editarSelectTipoRepeticion');
      // Llenar los datos del evento a editar
      if (typeof llenarModalEdicion === 'function' && window.eventoActual) {
        llenarModalEdicion(window.eventoActual);
      } else {
        console.warn('llenarModalEdicion no se ejecutó o eventoActual no seteado');
      }
      // Buscamos los modales
      var detalleModal = document.getElementById('modalDetalleEvento');
      var editarModal = document.getElementById('modalEditarEvento');
      if (detalleModal && editarModal) {
        var bootstrapModalDetalle = bootstrap.Modal.getInstance(detalleModal) || new bootstrap.Modal(detalleModal);
        var bootstrapModalEditar = bootstrap.Modal.getInstance(editarModal) || new bootstrap.Modal(editarModal);
        bootstrapModalDetalle.hide();
        setTimeout(function () { bootstrapModalEditar.show(); }, 400);
      }
    }
  });
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  // --- MOCK de eventos iniciales (luego pueden venir desde backend) ---
  var eventosMock = [
    {
      id: "1",
      title: "Venta Semanal de Plástico",
      start: "2024-03-18T10:00:00",
      end: "2024-03-18T11:00:00",
      color: "#28a745",
      description: "Evento demo: venta de plástico",
      material: "Plástico",
      centro: "Centro 1",
    },
  ];

  // --- Inicializa FullCalendar ---
  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    events: EVENTOS, // <-- now uses events from backend, not the mock
    eventClick: function (info) {
      // Siempre setea window.eventoActual ANTES de mostrar detalles
      var e = info.event;
      window.eventoActual = {
        id: e.id,
        title: e.title,
        descripcion: e.extendedProps.descripcion || e.extendedProps.description || '',
        start: e.start ? (typeof e.start === 'string' ? e.start : e.start.toISOString()) : '',
        end: e.end ? (typeof e.end === 'string' ? e.end : e.end.toISOString()) : '',
        backgroundColor: e.backgroundColor || e.color || '#28a745',
        materialId: e.extendedProps.materialId || e.extendedProps.material_id || '',
        centroAcopioId: e.extendedProps.centroAcopioId || e.extendedProps.centro_acopio_id || '',
        tipoRepeticion: e.extendedProps.tipoRepeticion || e.extendedProps.tipo_repeticion || '',
        fechaFinRepeticion: e.extendedProps.fechaFinRepeticion || e.extendedProps.fecha_fin_repeticion || '',
        observaciones: e.extendedProps.observaciones || '',
        puntoEcaId: e.extendedProps.puntoEcaId || e.extendedProps.punto_eca_id || window._PUNTO_ECA_ID || '',
        usuarioId: e.extendedProps.usuarioId || e.extendedProps.usuario_id || window._USUARIO_ID || ''
      };
      if (!window.eventoActual || !window.eventoActual.id) {
        console.warn('DEBUG: eventoActual quedó incompleto', window.eventoActual, e.extendedProps);
      } else {
        console.log('eventoActual seteado:', window.eventoActual);
      }
      const tipo = e.extendedProps.type || e.type || "";
      if (tipo === "venta") {
        mostrarDetallesVenta(e);
      } else if (tipo === "compra") {
        mostrarDetallesCompra(e);
      } else {
        mostrarDetalleEvento(e);
      }
    },
  });

  calendar.render();
  // Exponer el calendar globalmente para usarlo desde otros scripts
  window._calendarioEca = calendar;

  // --- Captura submit del formulario para crear evento ---
  var form = document.getElementById("formCrearEvento");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      agregarEventoDesdeFormulario();
    });
  }
  // También por si usan el botón explícito
  var btnGuardar = document.getElementById("btnGuardarEvento");
  if (btnGuardar) {
    btnGuardar.addEventListener("click", function (e) {
      agregarEventoDesdeFormulario();
    });
  }

  function agregarEventoDesdeFormulario() {
    // Obtener valores de los campos
    var titulo = document.getElementById("inputTitulo").value;
    var descripcion = document.getElementById("inputDescripcion").value;
    var material =
      document.getElementById("selectMaterial").options[
        document.getElementById("selectMaterial").selectedIndex
      ]?.text;
    var centro =
      document.getElementById("selectCentroAcopio").options[
        document.getElementById("selectCentroAcopio").selectedIndex
      ]?.text;
    var fecha = document.getElementById("inputFechaInicio").value;
    var horaInicio = document.getElementById("inputHoraInicio").value;
    var horaFin = document.getElementById("inputHoraFin").value;
    var color = document.getElementById("inputColor").value;
    var observaciones = document.getElementById("inputObservaciones").value;

    if (!titulo || !fecha || !horaInicio || !horaFin) {
      mostrarError("Faltan datos obligatorios");
      return;
    }

    // Construir dates ISO
    var start = fecha + "T" + horaInicio;
    var end = fecha + "T" + horaFin;
    var nuevoEvento = {
      id: String(Date.now()),
      title: titulo,
      start: start,
      end: end,
      color: color || "#28a745",
      description: descripcion || "",
      material: material || "",
      centro: centro || "",
      observaciones: observaciones || "",
    };
    calendar.addEvent(nuevoEvento);
    mostrarExito();
    // Cerrar el modal y limpiar el form
    setTimeout(function () {
      var modal = bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modalCrearEvento"),
      );
      modal.hide();
      form.reset();
      ocultarAlertas();
    }, 800);
  }
  // ==============================================
  // Lógica para editar evento desde el modal edición
  // ==============================================
  var btnGuardarEditar = document.getElementById('btnGuardarEditarEvento');
  if (btnGuardarEditar) {
    btnGuardarEditar.addEventListener('click', async function () {
      const data = {
        eventoId: document.getElementById('editarEventoId').value,
        materialId: document.getElementById('editarSelectMaterial').value,
        centroAcopioId: document.getElementById('editarSelectCentroAcopio').value,
        puntoEcaId: document.getElementById('editarPuntoEcaId').value,
        usuarioId: document.getElementById('editarUsuarioId').value,
        titulo: document.getElementById('inputEditarTitulo').value,
        descripcion: document.getElementById('inputEditarDescripcion').value,
        fechaInicio: document.getElementById('inputEditarFechaInicio').value,
        horaInicio: document.getElementById('inputEditarHoraInicio').value,
        horaFin: document.getElementById('inputEditarHoraFin').value,
        color: document.getElementById('inputEditarColor').value,
        tipoRepeticion: document.getElementById('editarSelectTipoRepeticion').value,
        fechaFinRepeticion: document.getElementById('inputEditarFechaFinRepeticion').value,
        observaciones: document.getElementById('inputEditarObservaciones').value
      };
      // Validación mínima
      const faltan = [];
      if(!data.materialId) faltan.push('Material');
      if(!data.puntoEcaId) faltan.push('Punto ECA');
      if(!data.usuarioId) faltan.push('Usuario');
      if(!data.titulo) faltan.push('Título');
      if(!data.fechaInicio) faltan.push('Fecha Inicio');
      if(!data.horaInicio) faltan.push('Hora Inicio');
      if(!data.horaFin) faltan.push('Hora Fin');
      if (faltan.length > 0) {
        document.getElementById('alertEditarErrorText').innerText = 'Faltan campos obligatorios: ' + faltan.join(', ');
        document.getElementById('alertEditarError').classList.remove('d-none');
        return;
      }
      function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      }
      try {
        const response = await fetch('/punto-eca/calendario/evento/editar/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
          document.getElementById('alertEditarError').classList.add('d-none');
          document.getElementById('alertEditarSuccess').classList.remove('d-none');
          setTimeout(function () {
            var modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modalEditarEvento'));
            modal.hide();
            document.getElementById('alertEditarSuccess').classList.add('d-none');
            // Refrescar el calendario podría implicar reload de eventos, según estructura
            window.location.reload();
          }, 1200);
        } else {
          document.getElementById('alertEditarErrorText').innerText = result.error || 'Error al actualizar el evento';
          document.getElementById('alertEditarError').classList.remove('d-none');
        }
      } catch (e) {
        document.getElementById('alertEditarErrorText').innerText = 'Error de red o servidor';
        document.getElementById('alertEditarError').classList.remove('d-none');
      }
    });
  }

});

// Modal para DETALLES DE VENTA (con IDs nuevos de section-calendario.html)
function mostrarDetallesVenta(evento) {
  document.getElementById("detallesVentaTitulo").textContent = evento.extendedProps.nombreMaterial || evento.title || "-";
  document.getElementById("detallesVentaFecha").textContent = evento.start ? (evento.start.toLocaleString ? (typeof evento.start === 'object' ? evento.start.toLocaleString('es-CO') : evento.start) : evento.start) : "-";
  // Cantidad
  var cantidad = (evento.extendedProps.cantidad !== undefined ? parseFloat(evento.extendedProps.cantidad) : '');
  document.getElementById("detallesVentaCantidad").textContent = cantidad !== '' ? cantidad.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-';
  // Precio unitario
  var precio = (evento.extendedProps.precioUnitario !== undefined ? parseFloat(evento.extendedProps.precioUnitario) : '');
  document.getElementById("detallesVentaPrecio").textContent = precio !== '' ? ('$' + precio.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})) : '-';
  // Total
  var total = (cantidad !== '' && precio !== '') ? (cantidad * precio) : '';
  document.getElementById("detallesVentaTotal").textContent = (total !== '' ? ('$' + total.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})) : '-');
  // Centro de Acopio
  document.getElementById("detallesVentaCentro").textContent = evento.extendedProps.nombreCentroAcopio || evento.extendedProps.centro || "-";
  document.getElementById("detallesVentaDescripcion").textContent = evento.extendedProps.descripcion || evento.extendedProps.description || "Sin descripción";
  document.getElementById("detallesVentaObservaciones").textContent = evento.extendedProps.observaciones || "Sin observaciones";
  // Mostrar el modal usando el nuevo ID
  var modalVenta = new bootstrap.Modal(document.getElementById("modalDetallesVenta"));
  modalVenta.show();
}

// Modal para DETALLE GENÉRICO DE EVENTO
globalThis.mostrarDetalleEvento = function mostrarDetalleEvento(evento) {
  // Refuerzo: setea global el evento actual mostrado
  window.eventoActual = window.eventoActual = {
    id: evento.id,
    title: evento.title || evento.extendedProps.titulo || '',
    descripcion: evento.extendedProps.descripcion || evento.extendedProps.description || '',
    start: evento.start ? (typeof evento.start === 'string' ? evento.start : evento.start.toISOString()) : '',
    end: evento.end ? (typeof evento.end === 'string' ? evento.end : evento.end.toISOString()) : '',
    backgroundColor: evento.backgroundColor || evento.color || '#28a745',
    materialId: evento.extendedProps.materialId || evento.extendedProps.material_id || '',
    centroAcopioId: evento.extendedProps.centroAcopioId || evento.extendedProps.centro_acopio_id || '',
    tipoRepeticion: evento.extendedProps.tipoRepeticion || evento.extendedProps.tipo_repeticion || '',
    fechaFinRepeticion: evento.extendedProps.fechaFinRepeticion || evento.extendedProps.fecha_fin_repeticion || '',
    observaciones: evento.extendedProps.observaciones || '',
    puntoEcaId: evento.extendedProps.puntoEcaId || evento.extendedProps.punto_eca_id || '',
    usuarioId: evento.extendedProps.usuarioId || evento.extendedProps.usuario_id || ''
  };
  console.log('Refuerzo eventoActual modal:', window.eventoActual);
  // Mostrar en consola para debug
  console.log('Evento para detalle:', evento, evento.extendedProps);
  document.getElementById("eventoDetalleTitulo").textContent = evento.title || evento.extendedProps.titulo || "-";
  // Fecha y hora (simple)
  let fechaStr = "-";
  if (evento.start) {
    if (typeof evento.start === "object" && evento.start.toLocaleString) {
      fechaStr = evento.start.toLocaleString("es-CO");
    } else {
      fechaStr = evento.start;
    }
    if (evento.end) {
      let finStr = typeof evento.end === "object" && evento.end.toLocaleString ? evento.end.toLocaleString("es-CO") : evento.end;
      fechaStr += " a " + finStr;
    }
  }
  document.getElementById("eventoDetalleFecha").textContent = fechaStr;
  // Buscar distintos posibles nombres para material
  document.getElementById("eventoDetalleMaterial").textContent =
    evento.extendedProps.material || evento.extendedProps.nombreMaterial || evento.extendedProps.material_nombre || evento.extendedProps.tipo_material || "-";
  // Buscar distintos posibles nombres para centro
  document.getElementById("eventoDetalleCentro").textContent =
    evento.extendedProps.centro || evento.extendedProps.nombreCentroAcopio || evento.extendedProps.centro_acopio_nombre || evento.extendedProps.centroAcopio || "-";
  document.getElementById("eventoDetalleDescripcion").textContent = evento.extendedProps.descripcion || evento.extendedProps.description || "Sin descripción";
  document.getElementById("eventoDetalleObservaciones").textContent = evento.extendedProps.observaciones || "Sin observaciones";
  // Mostrar el modal
  var modal = new bootstrap.Modal(document.getElementById("modalDetalleEvento"));
  modal.show();
}

function mostrarDetallesCompra(evento) {
  document.getElementById("detCompraMaterial").textContent = evento.extendedProps.nombreMaterial || evento.title || "-";
  document.getElementById("detCompraFecha").textContent = evento.start ? (evento.start.toLocaleString ? (typeof evento.start === 'object' ? evento.start.toLocaleString('es-CO') : evento.start) : evento.start) : "-";
  // Para compras, los campos de cantidad/precio/unitario/total pueden venir en extendedProps
  var cantidad = (evento.extendedProps.cantidad !== undefined ? parseFloat(evento.extendedProps.cantidad) : '');
  document.getElementById("detCompraCantidad").textContent = cantidad !== '' ? cantidad.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-';
  var precio = (evento.extendedProps.precioUnitario !== undefined ? parseFloat(evento.extendedProps.precioUnitario) : '');
  document.getElementById("detCompraPrecio").textContent = precio !== '' ? ('$' + precio.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})) : '-';
  var total = (cantidad !== '' && precio !== '') ? (cantidad * precio) : '';
  document.getElementById("detCompraTotal").textContent = (total !== '' ? ('$' + total.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})) : '-');
  document.getElementById("detCompraObservaciones").textContent = evento.extendedProps.observaciones || evento.extendedProps.descripcion || evento.extendedProps.description || 'Sin observaciones';
  // Mostrar el modal usando el nuevo ID
  var modalCompra = new bootstrap.Modal(document.getElementById("modalDetallesCompra"));
  modalCompra.show();
}

function mostrarError(msg) {
  var alert = document.getElementById("alertError");
  var text = document.getElementById("alertErrorText");
  if (alert && text) {
    text.textContent = msg;
    alert.classList.remove("d-none");
  }
}
function mostrarExito() {
  var alert = document.getElementById("alertSuccess");
  if (alert) alert.classList.remove("d-none");
}
function ocultarAlertas() {
  var error = document.getElementById("alertError");
  var ok = document.getElementById("alertSuccess");
  if (error) error.classList.add("d-none");
  if (ok) ok.classList.add("d-none");
}
