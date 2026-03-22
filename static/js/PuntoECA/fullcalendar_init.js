// static/js/PuntoECA/fullcalendar_init.js
// Inicializa FullCalendar en el div #calendar y maneja eventos mock + creación desde modal.

document.addEventListener("DOMContentLoaded", function () {
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
      const tipo = info.event.extendedProps.type || info.event.type || "";
      if (tipo === "venta") {
        mostrarDetallesVenta(info.event);
      } else if (tipo === "compra") {
        mostrarDetallesCompra(info.event);
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

// Modal para DETALLES DE COMPRA (con IDs nuevos de section-calendario.html)
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
