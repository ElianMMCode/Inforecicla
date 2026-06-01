/* global bootstrap, EVENTOS */
// static/js/PuntoECA/fullcalendar_init.js

/** * ==========================================
 * UTILS & HELPERS (DRY Patterns)
 * ==========================================
 */
const $el = (id) => document.getElementById(id);
const getVal = (id) => $el(id)?.value || "";
const validarRangoFechas = (fechaInicio, horaInicio, fechaFin, horaFin) => {
  const inicio = `${fechaInicio}T${horaInicio}`;
  const fin = `${fechaFin || fechaInicio}T${horaFin}`;

  if (fin <= inicio) {
    return "La fecha de fin debe ser posterior a la de inicio.";
  }

  return "";
};
const setVal = (id, val) => {
  if ($el(id)) $el(id).value = val || "";
};
const setText = (id, text) => {
  if ($el(id)) $el(id).textContent = text || "-";
};
const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (character) => {
    switch (character) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      case "'":
        return "&#39;";
      default:
        return character;
    }
  });

const getInitialEvents = () => {
  const eventsScript = document.getElementById("eventos-data");

  if (eventsScript?.textContent) {
    try {
      return JSON.parse(eventsScript.textContent);
    } catch (error) {
      console.error("No fue posible leer los eventos iniciales:", error);
    }
  }

  if (Array.isArray(globalThis.EVENTOS)) {
    return globalThis.EVENTOS;
  }

  return [];
};

// Instancia única y cacheada para mejor rendimiento (Intl API)
const copFormatter = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const formatMoney = (val) =>
  val === "" ? "-" : "$" + copFormatter.format(val);
const formatQty = (val) => (val === "" ? "-" : copFormatter.format(val));

function getCsrfToken() {
  // Corrección SonarQube S6594: Uso de RegExp.exec() en lugar de String.match()
  const match = /csrftoken=([^;]+)/.exec(document.cookie);
  return match ? match[1] : "";
}

async function showSwal(options) {
  const swal = globalThis.Swal;
  const config = {
    confirmButtonColor: "#198754",
    confirmButtonText: "Entendido",
    ...options,
  };

  if (swal?.fire) {
    return swal.fire(config);
  }

  if (globalThis.console?.warn) {
    console.warn("SweetAlert2 no está disponible:", config.title, config.text);
  }
  return Promise.resolve({ isConfirmed: true });
}

async function showValidationSwal(message) {
  return showSwal({
    icon: "warning",
    title: "Campos obligatorios pendientes",
    text: message,
  });
}

async function showResultSwal(icon, title, text) {
  return showSwal({
    icon,
    title,
    text,
  });
}

/** * ==========================================
 * LÓGICA DE NEGOCIO Y CÁLCULOS
 * ==========================================
 */
function calcularTotalYFormato(cantidadVal, precioVal) {
  const cantidad =
    cantidadVal === undefined ? "" : Number.parseFloat(cantidadVal);
  const precio = precioVal === undefined ? "" : Number.parseFloat(precioVal);
  return {
    cantidad,
    precio,
    total: cantidad === "" || precio === "" ? "" : cantidad * precio,
  };
}

function extraerDatosEvento(e) {
  const props = e.extendedProps;
  return {
    id: e.id,
    title: e.title,
    descripcion: props.descripcion || props.description || "",
    start: typeof e.start === "string" ? e.start : e.start?.toISOString() || "",
    end: typeof e.end === "string" ? e.end : e.end?.toISOString() || "",
    backgroundColor: e.backgroundColor || e.color || "#28a745",
    materialId: props.materialId || props.material_id || "",
    centroAcopioId: props.centroAcopioId || props.centro_acopio_id || "",
    tipoRepeticion: props.tipoRepeticion || props.tipo_repeticion || "",
    fechaFinRepeticion:
      props.fechaFinRepeticion || props.fecha_fin_repeticion || "",
    observaciones: props.observaciones || "",
    puntoEcaId:
      props.puntoEcaId || props.punto_eca_id || globalThis._PUNTO_ECA_ID || "",
    usuarioId:
      props.usuarioId || props.usuario_id || globalThis._USUARIO_ID || "",
    tipo: props.type || e.type || "",
  };
}

/** * ==========================================
 * GESTIÓN DE UI Y MODALES
 * ==========================================
 */
function setSelectValue(selId, value, labelFallback) {
  const sel = $el(selId);
  if (!sel) return;
  if (value && !Array.from(sel.options).some((opt) => opt.value == value)) {
    sel.add(new Option(labelFallback || value, value));
  }
  sel.value = value || "";
}

function llenarModalEdicion(evento) {
  if (!evento) return console.warn("¡No hay evento!");

  const [fechaInicio, tiempoInicio] = (evento.start || "").split("T");
  const [, tiempoFin] = (evento.end || "").split("T");

  setVal("editarEventoId", evento.id);
  setVal("inputEditarTitulo", evento.title);
  setVal("inputEditarDescripcion", evento.descripcion);
  setVal("inputEditarFechaInicio", fechaInicio);
  setVal("inputEditarHoraInicio", tiempoInicio?.substring(0, 5));
  setVal("inputEditarHoraFin", tiempoFin?.substring(0, 5));
  setVal("inputEditarColor", evento.backgroundColor);
  setVal(
    "inputEditarFechaFinRepeticion",
    (evento.fechaFinRepeticion || "").split("T")[0],
  );
  setVal("inputEditarObservaciones", evento.observaciones);
  setVal("editarPuntoEcaId", evento.puntoEcaId);
  setVal("editarUsuarioId", evento.usuarioId);

  setSelectValue(
    "editarSelectMaterial",
    evento.materialId,
    "(Material no disponible)",
  );
  setSelectValue(
    "editarSelectCentroAcopio",
    evento.centroAcopioId,
    "(Centro no disponible)",
  );
  setSelectValue(
    "editarSelectTipoRepeticion",
    evento.tipoRepeticion || "NINGUNA",
  );
}

// Consolidación de Detalles Venta y Compra en una sola función
function mostrarDetallesTransaccion(evento, prefijoDOM) {
  const props = evento.extendedProps;

  // Corrección SonarQube S6582: Uso de Optional Chaining
  const fechaFormat =
    evento.start?.toLocaleString?.("es-CO") || evento.start || "-";

  const { cantidad, precio, total } = calcularTotalYFormato(
    props.cantidad,
    props.precioUnitario,
  );

  setText(`${prefijoDOM}Titulo`, props.nombreMaterial || evento.title);
  setText(`${prefijoDOM}Material`, props.nombreMaterial || evento.title); // Fallback para ID de compra
  setText(`${prefijoDOM}Fecha`, fechaFormat);
  setText(`${prefijoDOM}Cantidad`, formatQty(cantidad));
  setText(`${prefijoDOM}Precio`, formatMoney(precio));
  setText(`${prefijoDOM}Total`, formatMoney(total));
  setText(
    `${prefijoDOM}Observaciones`,
    props.observaciones ||
      props.descripcion ||
      props.description ||
      "Sin observaciones",
  );

  // Elementos exclusivos de Venta
  if (prefijoDOM === "detallesVenta") {
    setText("detallesVentaCentro", props.nombreCentroAcopio || props.centro);
    setText(
      "detallesVentaDescripcion",
      props.descripcion || props.description || "Sin descripción",
    );
  }

  const modalId =
    prefijoDOM === "detallesVenta"
      ? "modalDetallesVenta"
      : "modalDetallesCompra";
  new bootstrap.Modal($el(modalId)).show();
}

globalThis.mostrarDetalleEvento = function (evento) {
  globalThis.eventoActual = extraerDatosEvento(evento);
  const props = evento.extendedProps;

  // Corrección SonarQube S3358: Extracción de operación ternaria anidada
  let textoFecha = evento.start || "-";
  if (typeof evento.start?.toLocaleString === "function") {
    const inicioFormateado = evento.start.toLocaleString("es-CO");
    const finFormateado =
      typeof evento.end?.toLocaleString === "function"
        ? ` a ${evento.end.toLocaleString("es-CO")}`
        : "";
    textoFecha = `${inicioFormateado}${finFormateado}`;
  }

  setText("eventoDetalleTitulo", evento.title || props.titulo);
  setText("eventoDetalleFecha", textoFecha);
  setText(
    "eventoDetalleMaterial",
    props.material ||
      props.nombreMaterial ||
      props.material_nombre ||
      props.tipo_material,
  );
  setText(
    "eventoDetalleCentro",
    props.centro ||
      props.nombreCentroAcopio ||
      props.centro_acopio_nombre ||
      props.centroAcopio,
  );
  setText(
    "eventoDetalleDescripcion",
    props.descripcion || props.description || "Sin descripción",
  );
  setText(
    "eventoDetalleObservaciones",
    props.observaciones || "Sin observaciones",
  );

  new bootstrap.Modal($el("modalDetalleEvento")).show();
};

/** * ==========================================
 * PETICIONES HTTP (API)
 * ==========================================
 */
async function eliminarEvento(deleteMode) {
  const eventoId = globalThis.eventoActual?.id;
  try {
    const res = await fetch("/punto-eca/calendario/evento/eliminar/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ eventoId, deleteMode }),
    });
    const result = await res.json();

    if (result.success) {
      await showResultSwal(
        "success",
        "Evento eliminado",
        "El evento se eliminó correctamente.",
      );
      globalThis.location.reload();
      return;
    }

    await showResultSwal(
      "error",
      "Error",
      result.error || "Error eliminando el evento",
    );
  } catch (e) {
    console.error("Excepción en eliminarEvento:", e);
    await showResultSwal(
      "error",
      "Error de red",
      "Error de red al intentar eliminar.",
    );
  } finally {
    bootstrap.Modal.getInstance($el("modalEliminarEvento"))?.hide();
  }
}

/** * ==========================================
 * INICIALIZACIÓN DE FULLCALENDAR Y EVENTOS
 * ==========================================
 */
document.addEventListener("DOMContentLoaded", function () {
  // Delegación de eventos globales para clics
  document.addEventListener("click", async function (event) {
    const targetId = event.target?.id;
    if (!targetId || !globalThis.eventoActual) return;

    if (targetId === "btnEliminarEvento") {
      const ev = globalThis.eventoActual;
      if (ev.tipo === "venta" || ev.tipo === "compra") {
        return showResultSwal(
          "warning",
          "Acción no permitida",
          "No se puede eliminar eventos de tipo Venta o Compra desde aquí.",
        );
      }

      const esComplejo =
        ev.id?.startsWith("evinst-") ||
        (ev.tipoRepeticion && ev.tipoRepeticion !== "NINGUNA");

      if (esComplejo) {
        new bootstrap.Modal($el("modalEliminarEvento")).show();
        $el("btnEliminarSoloRepeticion").onclick = () =>
          eliminarEvento("instancia");
        $el("btnEliminarSerieCompleta").onclick = () => eliminarEvento("serie");
        bootstrap.Modal.getInstance($el("modalDetalleEvento"))?.hide();
      } else {
        const confirmation = await showSwal({
          icon: "question",
          title: "Eliminar evento",
          text: "¿Estás seguro de que querés eliminar este evento?",
          showCancelButton: true,
          confirmButtonText: "Sí, eliminar",
          cancelButtonText: "Cancelar",
          confirmButtonColor: "#dc3545",
        });

        if (confirmation.isConfirmed) {
          await eliminarEvento("serie");
        }
      }
    }

    if (targetId === "btnEditarEvento") {
      ["selectMaterial", "selectCentroAcopio", "selectTipoRepeticion"].forEach(
        (id) => {
          const dest = $el(`editar${id.charAt(0).toUpperCase() + id.slice(1)}`);
          if ($el(id) && dest) dest.innerHTML = $el(id).innerHTML; // Clonación rápida de opciones
        },
      );

      llenarModalEdicion(globalThis.eventoActual);

      bootstrap.Modal.getInstance($el("modalDetalleEvento"))?.hide();
      setTimeout(
        () => new bootstrap.Modal($el("modalEditarEvento")).show(),
        400,
      );
    }
  });

  // Init Calendario
  const calendarEl = $el("calendar");
  if (!calendarEl) return;

  const calendar = new globalThis.FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    events: getInitialEvents(),

    eventContent: (arg) => {
      const e = arg.event;
      const tipo = e.extendedProps.type || e.type || "";
      const props = e.extendedProps;
      let html = "";

      if (tipo === "venta" || tipo === "compra") {
        const { cantidad, total } = calcularTotalYFormato(
          props.cantidad,
          props.precioUnitario,
        );
        html = `<b>${escapeHtml(tipo.charAt(0).toUpperCase() + tipo.slice(1))}:</b> ${escapeHtml(props.nombreMaterial || e.title || "-")}`;
        if (cantidad !== "") html += ` (${cantidad})`;
        if (total !== "") html += ` - $${total}`;
      } else {
        html = `<b>${escapeHtml(e.title)}</b>`;
        if (props.descripcion)
          html += `<br><span style='font-size:0.90em;'>${escapeHtml(props.descripcion)}</span>`;
        if (props.material)
          html += `<br><span style='font-size:0.88em;color:#555;'>${escapeHtml(props.material)}</span>`;
      }
      return {
        html: `<span style="font-size:0.95em;white-space:normal;word-break:break-word;">${html}</span>`,
      };
    },

    eventDidMount: (info) => {
      const { event: e, el } = info;
      if (e.backgroundColor) {
        el.style.backgroundColor = el.style.borderColor = e.backgroundColor;
        el.style.color = "#fff";
      }

      const tipo = e.extendedProps.type || e.type || "";
      const props = e.extendedProps;
      let tituloTooltip = "";

      if (tipo === "venta" || tipo === "compra") {
        const { cantidad, precio, total } = calcularTotalYFormato(
          props.cantidad,
          props.precioUnitario,
        );
        tituloTooltip = `<b>${escapeHtml(tipo.charAt(0).toUpperCase() + tipo.slice(1))}</b><br>Material: ${escapeHtml(props.nombreMaterial || e.title || "-")}<br>`;
        if (cantidad !== "") tituloTooltip += `Cantidad: ${cantidad}<br>`;
        if (precio !== "") tituloTooltip += `Precio unitario: $${precio}<br>`;
        if (total !== "") tituloTooltip += `Total: $${total}<br>`;
        tituloTooltip += `Centro: ${escapeHtml(props.nombreCentroAcopio || props.centro || "-")}<br>${escapeHtml(props.descripcion || "")}`;
      } else {
        tituloTooltip = `<b>${escapeHtml(e.title)}</b><br>${escapeHtml(props.descripcion || "")}`;
      }

      el.setAttribute("title", tituloTooltip);
      el.dataset.bsToggle = "tooltip";
      el.dataset.bsHtml = "true";
      if (typeof bootstrap !== "undefined" && bootstrap.Tooltip)
        bootstrap.Tooltip.getOrCreateInstance(el);
    },

    eventClick: (info) => {
      globalThis.eventoActual = extraerDatosEvento(info.event);
      const tipo = globalThis.eventoActual.tipo;

      if (tipo === "venta")
        mostrarDetallesTransaccion(info.event, "detallesVenta");
      else if (tipo === "compra")
        mostrarDetallesTransaccion(info.event, "detCompra");
      else globalThis.mostrarDetalleEvento(info.event);
    },
  });

  calendar.render();
  globalThis._calendarioEca = calendar;

  // Manejo de Formulario Crear
  const formCrear = $el("formCrearEvento");
  const usarFlujoApiCrear = true;
  const agregarEvento = () => {
    const data = {
      title: getVal("inputTitulo"),
      fecha: getVal("inputFechaInicio"),
      horaInicio: getVal("inputHoraInicio"),
      horaFin: getVal("inputHoraFin"),
    };

    if (!data.title || !data.fecha || !data.horaInicio || !data.horaFin) {
      return showValidationSwal("Faltan datos obligatorios.");
    }

    calendar.addEvent({
      id: String(Date.now()),
      title: data.title,
      start: `${data.fecha}T${data.horaInicio}`,
      end: `${data.fecha}T${data.horaFin}`,
      color: getVal("inputColor") || "#28a745",
      description: getVal("inputDescripcion"),
      material:
        $el("selectMaterial")?.options[$el("selectMaterial").selectedIndex]
          ?.text || "",
      centro:
        $el("selectCentroAcopio")?.options[
          $el("selectCentroAcopio").selectedIndex
        ]?.text || "",
      observaciones: getVal("inputObservaciones"),
    });

    showResultSwal(
      "success",
      "Evento creado",
      "El evento se creó correctamente.",
    ).then(() => {
      bootstrap.Modal.getInstance($el("modalCrearEvento"))?.hide();
      formCrear?.reset();
      globalThis.location.reload();
    });
  };

  if (!usarFlujoApiCrear) {
    formCrear?.addEventListener("submit", (e) => {
      e.preventDefault();
      agregarEvento();
    });
    $el("btnGuardarEvento")?.addEventListener("click", agregarEvento);
    $el("modalCrearEvento")?.addEventListener("hidden.bs.modal", () =>
      globalThis.location.reload(),
    );
  }

  // Manejo de Edición API
  $el("btnGuardarEditarEvento")?.addEventListener("click", async () => {
    const reqData = {
      eventoId: getVal("editarEventoId"),
      materialId: getVal("editarSelectMaterial"),
      centroAcopioId: getVal("editarSelectCentroAcopio"),
      puntoEcaId: getVal("editarPuntoEcaId"),
      usuarioId: getVal("editarUsuarioId"),
      titulo: getVal("inputEditarTitulo"),
      descripcion: getVal("inputEditarDescripcion"),
      fechaInicio: getVal("inputEditarFechaInicio"),
      horaInicio: getVal("inputEditarHoraInicio"),
      horaFin: getVal("inputEditarHoraFin"),
      color: getVal("inputEditarColor"),
      tipoRepeticion: getVal("editarSelectTipoRepeticion"),
      fechaFinRepeticion: getVal("inputEditarFechaFinRepeticion"),
      observaciones: getVal("inputEditarObservaciones"),
    };

    const requiredKeys = {
      materialId: "Material",
      puntoEcaId: "Punto ECA",
      usuarioId: "Usuario",
      titulo: "Título",
      fechaInicio: "Fecha Inicio",
      horaInicio: "Hora Inicio",
      horaFin: "Hora Fin",
    };
    const faltan = Object.keys(requiredKeys)
      .filter((key) => !reqData[key])
      .map((key) => requiredKeys[key]);

    if (faltan.length > 0) {
      return showValidationSwal(
        `Faltan campos obligatorios: ${faltan.join(", ")}`,
      );
    }

    const errorRangoEditar = validarRangoFechas(
      reqData.fechaInicio,
      reqData.horaInicio,
      reqData.fechaInicio,
      reqData.horaFin,
    );

    if (errorRangoEditar) {
      return showValidationSwal(errorRangoEditar);
    }

    try {
      const response = await fetch("/punto-eca/calendario/evento/editar/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(reqData),
      });
      const result = await response.json();

      if (result.success) {
        await showResultSwal(
          "success",
          "Evento actualizado",
          "El evento se actualizó correctamente.",
        );
        setTimeout(() => {
          bootstrap.Modal.getInstance($el("modalEditarEvento"))?.hide();
          globalThis.location.reload();
        }, 1200);
      } else {
        await showResultSwal(
          "error",
          "Error",
          result.error || "Error al actualizar",
        );
      }
    } catch (e) {
      console.error("Excepción en edición:", e);
      await showResultSwal(
        "error",
        "Error de red",
        "Error de red o servidor",
      );
    }
  });
});
