/* global bootstrap, EVENTOS */
// static/js/PuntoECA/fullcalendar_init.js
// Inicializa FullCalendar en el div #calendar y maneja eventos mock + creación desde modal.

function llenarModalEdicion(evento) {
  console.log("llenarModalEdicion, recibí:", evento);
  if (!evento) {
    console.warn("No hay evento!");
    return;
  }
  function setSelectValue(selId, value, labelFallback) {
    let sel = document.getElementById(selId);
    if (!sel) return;
    if (value && !Array.from(sel.options).some((opt) => opt.value == value)) {
      let opt = document.createElement("option");
      opt.value = value;
      opt.text = labelFallback || value;
      sel.appendChild(opt);
    }
    sel.value = value || "";
  }
  document.getElementById("editarEventoId").value = evento.id || "";
  document.getElementById("inputEditarTitulo").value = evento.title || "";
  document.getElementById("inputEditarDescripcion").value =
    evento.descripcion || "";
  document.getElementById("inputEditarFechaInicio").value =
    (evento.start || "").split("T")[0] || "";
  document.getElementById("inputEditarHoraInicio").value = (
    evento.start || ""
  ).split("T")[1]
    ? (evento.start || "").split("T")[1].substring(0, 5)
    : "";
  document.getElementById("inputEditarHoraFin").value = (
    evento.end || ""
  ).split("T")[1]
    ? (evento.end || "").split("T")[1].substring(0, 5)
    : "";
  document.getElementById("inputEditarColor").value =
    evento.backgroundColor || "#28a745";
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
  document.getElementById("inputEditarFechaFinRepeticion").value =
    (evento.fechaFinRepeticion || "").split("T")[0] || "";
  document.getElementById("inputEditarObservaciones").value =
    evento.observaciones || "";
  document.getElementById("editarPuntoEcaId").value = evento.puntoEcaId || "";
  document.getElementById("editarUsuarioId").value = evento.usuarioId || "";
}

function eliminarEvento(deleteMode) {
  const eventoId = globalThis.eventoActual?.id;
  const tokenMatch = /csrftoken=([^;]+)/.exec(document.cookie);
  const csrfToken = tokenMatch ? tokenMatch[1] : "";

  fetch("/punto-eca/calendario/evento/eliminar/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({ eventoId, deleteMode }),
  })
    .then((res) => res.json())
    .then((result) => {
      if (result.success) {
        globalThis.location.reload();
      } else {
        alert(result.error || "Error eliminando el evento");
      }
    })
    .catch((e) => {
      console.error("Excepción en eliminarEvento:", e);
      alert("Error de red al intentar eliminar.");
    });

  let modalEliminar = bootstrap.Modal.getInstance(
    document.getElementById("modalEliminarEvento"),
  );
  if (modalEliminar) modalEliminar.hide();
}

function calcularTotalYFormato(cantidadVal, precioVal) {
  const cantidad =
    cantidadVal === undefined ? "" : Number.parseFloat(cantidadVal);
  const precio = precioVal === undefined ? "" : Number.parseFloat(precioVal);
  const total = cantidad === "" || precio === "" ? "" : cantidad * precio;
  return { cantidad, precio, total };
}

function renderHtmlVentaCompra(e, tipo) {
  let material = e.extendedProps.nombreMaterial || e.title || "-";
  const { cantidad, total } = calcularTotalYFormato(
    e.extendedProps.cantidad,
    e.extendedProps.precioUnitario,
  );

  const etiqueta = tipo.charAt(0).toUpperCase() + tipo.slice(1);
  let innerHtml = `<b>${etiqueta}:</b> ${material}`;
  innerHtml += cantidad === "" ? "" : ` (${cantidad})`;
  innerHtml += total === "" ? "" : ` - $${total}`;
  return innerHtml;
}

function renderHtmlGenerico(e) {
  let desc = e.extendedProps.descripcion || e.extendedProps.description || "";
  let material =
    e.extendedProps.material || e.extendedProps.nombreMaterial || "";
  let centro =
    e.extendedProps.centro || e.extendedProps.nombreCentroAcopio || "";
  let innerHtml = `<b>${e.title}</b>`;
  if (desc) innerHtml += `<br><span style='font-size:0.90em;'>${desc}</span>`;
  if (material)
    innerHtml += `<br><span style='font-size:0.88em;color:#555;'>${material}</span>`;
  if (centro)
    innerHtml += `<br><span style='font-size:0.88em;color:#555;'>${centro}</span>`;
  return innerHtml;
}

function buildTooltipVentaCompra(e, tipo) {
  const { cantidad, precio, total } = calcularTotalYFormato(
    e.extendedProps.cantidad,
    e.extendedProps.precioUnitario,
  );
  const tipoLabel = tipo.charAt(0).toUpperCase() + tipo.slice(1);

  let contenido = `<b>${tipoLabel}</b><br>Material: ${e.extendedProps.nombreMaterial || e.title || "-"}<br>`;
  contenido += cantidad === "" ? "" : `Cantidad: ${cantidad}<br>`;
  contenido += precio === "" ? "" : `Precio unitario: $${precio}<br>`;
  contenido += total === "" ? "" : `Total: $${total}<br>`;
  contenido += `Centro: ${e.extendedProps.nombreCentroAcopio || e.extendedProps.centro || "-"}<br>`;
  contenido += `${e.extendedProps.descripcion || e.extendedProps.description || ""}`;
  return contenido;
}

function formatearFechaISO(fecha) {
  if (!fecha) return "";
  if (typeof fecha === "string") return fecha;
  return fecha.toISOString();
}

function formatearRangoFechasLocal(inicio, fin) {
  if (!inicio) return "-";
  let fechaStr =
    typeof inicio === "object" && inicio.toLocaleString
      ? inicio.toLocaleString("es-CO")
      : inicio;
  if (fin) {
    let finStr =
      typeof fin === "object" && fin.toLocaleString
        ? fin.toLocaleString("es-CO")
        : fin;
    fechaStr += " a " + finStr;
  }
  return fechaStr;
}

// Extracción de lógica para S3776
function extraerDatosEvento(e) {
  return {
    id: e.id,
    title: e.title,
    descripcion:
      e.extendedProps.descripcion || e.extendedProps.description || "",
    start: formatearFechaISO(e.start),
    end: formatearFechaISO(e.end),
    backgroundColor: e.backgroundColor || e.color || "#28a745",
    materialId: e.extendedProps.materialId || e.extendedProps.material_id || "",
    centroAcopioId:
      e.extendedProps.centroAcopioId || e.extendedProps.centro_acopio_id || "",
    tipoRepeticion:
      e.extendedProps.tipoRepeticion || e.extendedProps.tipo_repeticion || "",
    fechaFinRepeticion:
      e.extendedProps.fechaFinRepeticion ||
      e.extendedProps.fecha_fin_repeticion ||
      "",
    observaciones: e.extendedProps.observaciones || "",
    puntoEcaId:
      e.extendedProps.puntoEcaId ||
      e.extendedProps.punto_eca_id ||
      globalThis._PUNTO_ECA_ID ||
      "",
    usuarioId:
      e.extendedProps.usuarioId ||
      e.extendedProps.usuario_id ||
      globalThis._USUARIO_ID ||
      "",
  };
}

document.addEventListener("DOMContentLoaded", function () {
  document.addEventListener("click", function (event) {
    if (event.target?.id === "btnEliminarEvento") {
      if (!globalThis.eventoActual) return;

      const isVenta = globalThis.eventoActual?.tipo === "venta";
      const isCompra = globalThis.eventoActual?.tipo === "compra";

      if (isVenta || isCompra) {
        alert(
          "No se puede eliminar eventos de tipo Venta o Compra desde aquí.",
        );
        return;
      }

      const eventoId = globalThis.eventoActual.id;
      const esRepetido = eventoId?.startsWith("evinst-");
      const esSerie =
        globalThis.eventoActual.tipoRepeticion &&
        globalThis.eventoActual.tipoRepeticion !== "NINGUNA";

      if (esRepetido || esSerie) {
        const modalEliminar = new bootstrap.Modal(
          document.getElementById("modalEliminarEvento"),
        );
        modalEliminar.show();

        const btnSolo = document.getElementById("btnEliminarSoloRepeticion");
        const btnSerie = document.getElementById("btnEliminarSerieCompleta");
        btnSolo.onclick = null;
        btnSerie.onclick = null;

        btnSolo.onclick = function () {
          eliminarEvento("instancia");
        };
        btnSerie.onclick = function () {
          eliminarEvento("serie");
        };

        let modalDetalle = bootstrap.Modal.getInstance(
          document.getElementById("modalDetalleEvento"),
        );
        if (modalDetalle) modalDetalle.hide();
        return;
      } else {
        if (
          !globalThis.confirm(
            "¿Estás seguro de que querés eliminar este evento?",
          )
        )
          return;
        eliminarEvento("serie");
        return;
      }
    }

    if (event.target?.id === "btnEditarEvento") {
      function copiarOpcionesSelect(srcId, destId) {
        let src = document.getElementById(srcId);
        let dest = document.getElementById(destId);
        if (!src || !dest) return;
        dest.innerHTML = "";
        Array.from(src.options).forEach(function (opt) {
          let copia = opt.cloneNode(true);
          dest.appendChild(copia);
        });
      }
      copiarOpcionesSelect("selectMaterial", "editarSelectMaterial");
      copiarOpcionesSelect("selectCentroAcopio", "editarSelectCentroAcopio");
      copiarOpcionesSelect(
        "selectTipoRepeticion",
        "editarSelectTipoRepeticion",
      );

      if (typeof llenarModalEdicion === "function" && globalThis.eventoActual) {
        llenarModalEdicion(globalThis.eventoActual);
      } else {
        console.warn(
          "llenarModalEdicion no se ejecutó o eventoActual no seteado",
        );
      }

      let detalleModal = document.getElementById("modalDetalleEvento");
      let editarModal = document.getElementById("modalEditarEvento");
      if (detalleModal && editarModal) {
        let bootstrapModalDetalle =
          bootstrap.Modal.getInstance(detalleModal) ||
          new bootstrap.Modal(detalleModal);
        let bootstrapModalEditar =
          bootstrap.Modal.getInstance(editarModal) ||
          new bootstrap.Modal(editarModal);
        bootstrapModalDetalle.hide();
        setTimeout(function () {
          bootstrapModalEditar.show();
        }, 400);
      }
    }
  });

  let calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  // Solución TS(2570): Usando globalThis para referenciar FullCalendar sin alertar al linter TS
  let calendar = new globalThis.FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    eventTimeFormat: {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    },
    events: typeof EVENTOS === "undefined" ? [] : EVENTOS,
    eventContent: function (arg) {
      const e = arg.event;
      const tipo = e.extendedProps.type || e.type || "";
      let innerHtml = "";

      if (tipo === "venta" || tipo === "compra") {
        innerHtml = renderHtmlVentaCompra(e, tipo);
      } else {
        innerHtml = renderHtmlGenerico(e);
      }
      return {
        html: `<span style="font-size:0.95em;white-space:normal;word-break:break-word;">${innerHtml}</span>`,
      };
    },
    eventDidMount: function (info) {
      if (info.event.backgroundColor) {
        info.el.style.backgroundColor = info.event.backgroundColor;
        info.el.style.borderColor = info.event.backgroundColor;
        info.el.style.color = "#fff";
      }

      let e = info.event;
      let tipo = e.extendedProps.type || e.type || "";
      let contenido = "";

      if (tipo === "venta" || tipo === "compra") {
        contenido = buildTooltipVentaCompra(e, tipo);
      } else {
        contenido =
          `<b>${e.title}</b><br>` +
          (e.extendedProps.descripcion || e.extendedProps.description || "");
      }

      info.el.dataset.bsToggle = "tooltip";
      info.el.dataset.bsHtml = "true";
      info.el.setAttribute("title", contenido);

      if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
        bootstrap.Tooltip.getOrCreateInstance(info.el);
      }
    },
    eventClick: function (info) {
      let e = info.event;

      globalThis.eventoActual = extraerDatosEvento(e);

      // S7735: Camino positivo primero para evitar condición negada confusa
      if (globalThis.eventoActual?.id) {
        console.log("eventoActual seteado:", globalThis.eventoActual);
      } else {
        console.warn(
          "DEBUG: eventoActual quedó incompleto",
          globalThis.eventoActual,
          e.extendedProps,
        );
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
  globalThis._calendarioEca = calendar;

  let form = document.getElementById("formCrearEvento");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      agregarEventoDesdeFormulario();
    });
  }

  let btnGuardar = document.getElementById("btnGuardarEvento");
  if (btnGuardar) {
    btnGuardar.addEventListener("click", function () {
      agregarEventoDesdeFormulario();
    });
  }

  let modalCrear = document.getElementById("modalCrearEvento");
  if (modalCrear) {
    modalCrear.addEventListener("hidden.bs.modal", function () {
      globalThis.location.reload();
    });
  }

  function agregarEventoDesdeFormulario() {
    let titulo = document.getElementById("inputTitulo").value;
    let descripcion = document.getElementById("inputDescripcion").value;
    let material =
      document.getElementById("selectMaterial").options[
        document.getElementById("selectMaterial").selectedIndex
      ]?.text;
    let centro =
      document.getElementById("selectCentroAcopio").options[
        document.getElementById("selectCentroAcopio").selectedIndex
      ]?.text;
    let fecha = document.getElementById("inputFechaInicio").value;
    let horaInicio = document.getElementById("inputHoraInicio").value;
    let horaFin = document.getElementById("inputHoraFin").value;
    let color = document.getElementById("inputColor").value;
    let observaciones = document.getElementById("inputObservaciones").value;

    if (!titulo || !fecha || !horaInicio || !horaFin) {
      mostrarError("Faltan datos obligatorios");
      return;
    }

    let start = fecha + "T" + horaInicio;
    let end = fecha + "T" + horaFin;
    let nuevoEvento = {
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

    setTimeout(function () {
      let modal = bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modalCrearEvento"),
      );
      modal.hide();
      form.reset();
      ocultarAlertas();
      globalThis.location.reload();
    }, 800);
  }

  let btnGuardarEditar = document.getElementById("btnGuardarEditarEvento");
  if (btnGuardarEditar) {
    btnGuardarEditar.addEventListener("click", async function () {
      const data = {
        eventoId: document.getElementById("editarEventoId").value,
        materialId: document.getElementById("editarSelectMaterial").value,
        centroAcopioId: document.getElementById("editarSelectCentroAcopio")
          .value,
        puntoEcaId: document.getElementById("editarPuntoEcaId").value,
        usuarioId: document.getElementById("editarUsuarioId").value,
        titulo: document.getElementById("inputEditarTitulo").value,
        descripcion: document.getElementById("inputEditarDescripcion").value,
        fechaInicio: document.getElementById("inputEditarFechaInicio").value,
        horaInicio: document.getElementById("inputEditarHoraInicio").value,
        horaFin: document.getElementById("inputEditarHoraFin").value,
        color: document.getElementById("inputEditarColor").value,
        tipoRepeticion: document.getElementById("editarSelectTipoRepeticion")
          .value,
        fechaFinRepeticion: document.getElementById(
          "inputEditarFechaFinRepeticion",
        ).value,
        observaciones: document.getElementById("inputEditarObservaciones")
          .value,
      };

      const faltan = [];
      if (!data.materialId) faltan.push("Material");
      if (!data.puntoEcaId) faltan.push("Punto ECA");
      if (!data.usuarioId) faltan.push("Usuario");
      if (!data.titulo) faltan.push("Título");
      if (!data.fechaInicio) faltan.push("Fecha Inicio");
      if (!data.horaInicio) faltan.push("Hora Inicio");
      if (!data.horaFin) faltan.push("Hora Fin");

      if (faltan.length > 0) {
        document.getElementById("alertEditarErrorText").innerText =
          "Faltan campos obligatorios: " + faltan.join(", ");
        document.getElementById("alertEditarError").classList.remove("d-none");
        return;
      }

      function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
          const cookies = document.cookie.split(";");
          // S4138: Cambiado a for-of loop
          for (const cookieItem of cookies) {
            const cookie = cookieItem.trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
              cookieValue = decodeURIComponent(
                cookie.substring(name.length + 1),
              );
              break;
            }
          }
        }
        return cookieValue;
      }

      try {
        const response = await fetch("/punto-eca/calendario/evento/editar/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify(data),
        });
        const result = await response.json();

        if (result.success) {
          document.getElementById("alertEditarError").classList.add("d-none");
          document
            .getElementById("alertEditarSuccess")
            .classList.remove("d-none");
          setTimeout(function () {
            let modal = bootstrap.Modal.getOrCreateInstance(
              document.getElementById("modalEditarEvento"),
            );
            modal.hide();
            document
              .getElementById("alertEditarSuccess")
              .classList.add("d-none");
            globalThis.location.reload();
          }, 1200);
        } else {
          document.getElementById("alertEditarErrorText").innerText =
            result.error || "Error al actualizar el evento";
          document
            .getElementById("alertEditarError")
            .classList.remove("d-none");
        }
      } catch (e) {
        // S2486: Se captura la excepción y se maneja (imprimiendo en consola)
        console.error("Excepción en edición de evento:", e);
        document.getElementById("alertEditarErrorText").innerText =
          "Error de red o servidor";
        document.getElementById("alertEditarError").classList.remove("d-none");
      }
    });
  }
});

function mostrarDetallesVenta(evento) {
  document.getElementById("detallesVentaTitulo").textContent =
    evento.extendedProps.nombreMaterial || evento.title || "-";

  let fechaFormat = evento.start;
  if (
    fechaFormat &&
    typeof fechaFormat === "object" &&
    fechaFormat.toLocaleString
  ) {
    fechaFormat = fechaFormat.toLocaleString("es-CO");
  }
  document.getElementById("detallesVentaFecha").textContent =
    fechaFormat || "-";

  const { cantidad, precio, total } = calcularTotalYFormato(
    evento.extendedProps.cantidad,
    evento.extendedProps.precioUnitario,
  );

  document.getElementById("detallesVentaCantidad").textContent =
    cantidad === ""
      ? "-"
      : cantidad.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
  document.getElementById("detallesVentaPrecio").textContent =
    precio === ""
      ? "-"
      : "$" +
        precio.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
  document.getElementById("detallesVentaTotal").textContent =
    total === ""
      ? "-"
      : "$" +
        total.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });

  document.getElementById("detallesVentaCentro").textContent =
    evento.extendedProps.nombreCentroAcopio ||
    evento.extendedProps.centro ||
    "-";
  document.getElementById("detallesVentaDescripcion").textContent =
    evento.extendedProps.descripcion ||
    evento.extendedProps.description ||
    "Sin descripción";
  document.getElementById("detallesVentaObservaciones").textContent =
    evento.extendedProps.observaciones || "Sin observaciones";

  let modalVenta = new bootstrap.Modal(
    document.getElementById("modalDetallesVenta"),
  );
  modalVenta.show();
}

globalThis.mostrarDetalleEvento = function mostrarDetalleEvento(evento) {
  globalThis.eventoActual = extraerDatosEvento(evento);

  document.getElementById("eventoDetalleTitulo").textContent =
    evento.title || evento.extendedProps.titulo || "-";
  document.getElementById("eventoDetalleFecha").textContent =
    formatearRangoFechasLocal(evento.start, evento.end);
  document.getElementById("eventoDetalleMaterial").textContent =
    evento.extendedProps.material ||
    evento.extendedProps.nombreMaterial ||
    evento.extendedProps.material_nombre ||
    evento.extendedProps.tipo_material ||
    "-";
  document.getElementById("eventoDetalleCentro").textContent =
    evento.extendedProps.centro ||
    evento.extendedProps.nombreCentroAcopio ||
    evento.extendedProps.centro_acopio_nombre ||
    evento.extendedProps.centroAcopio ||
    "-";
  document.getElementById("eventoDetalleDescripcion").textContent =
    evento.extendedProps.descripcion ||
    evento.extendedProps.description ||
    "Sin descripción";
  document.getElementById("eventoDetalleObservaciones").textContent =
    evento.extendedProps.observaciones || "Sin observaciones";

  let modal = new bootstrap.Modal(
    document.getElementById("modalDetalleEvento"),
  );
  modal.show();
};

function mostrarDetallesCompra(evento) {
  document.getElementById("detCompraMaterial").textContent =
    evento.extendedProps.nombreMaterial || evento.title || "-";

  let fechaFormat = evento.start;
  if (
    fechaFormat &&
    typeof fechaFormat === "object" &&
    fechaFormat.toLocaleString
  ) {
    fechaFormat = fechaFormat.toLocaleString("es-CO");
  }
  document.getElementById("detCompraFecha").textContent = fechaFormat || "-";

  const { cantidad, precio, total } = calcularTotalYFormato(
    evento.extendedProps.cantidad,
    evento.extendedProps.precioUnitario,
  );

  document.getElementById("detCompraCantidad").textContent =
    cantidad === ""
      ? "-"
      : cantidad.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
  document.getElementById("detCompraPrecio").textContent =
    precio === ""
      ? "-"
      : "$" +
        precio.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
  document.getElementById("detCompraTotal").textContent =
    total === ""
      ? "-"
      : "$" +
        total.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });

  document.getElementById("detCompraObservaciones").textContent =
    evento.extendedProps.observaciones ||
    evento.extendedProps.descripcion ||
    evento.extendedProps.description ||
    "Sin observaciones";

  let modalCompra = new bootstrap.Modal(
    document.getElementById("modalDetallesCompra"),
  );
  modalCompra.show();
}

function mostrarError(msg) {
  let alert = document.getElementById("alertError");
  let text = document.getElementById("alertErrorText");
  if (alert && text) {
    text.textContent = msg;
    alert.classList.remove("d-none");
  }
}

function mostrarExito() {
  let alert = document.getElementById("alertSuccess");
  if (alert) alert.classList.remove("d-none");
}

function ocultarAlertas() {
  let error = document.getElementById("alertError");
  let ok = document.getElementById("alertSuccess");
  if (error) error.classList.add("d-none");
  if (ok) ok.classList.add("d-none");
}
