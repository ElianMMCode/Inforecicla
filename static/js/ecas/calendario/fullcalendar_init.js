// static/js/PuntoECA/fullcalendar_init.js
// Inicializa FullCalendar en el div #calendar y maneja eventos mock + creación desde modal.

// ==== Mover lógica de edición/modal acá para evitar contextos disjuntos ====
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
// Delegado click para botón "Editar Evento" centralizado en el mismo archivo
// Garantiza mismo contexto y acceso global real

document.addEventListener("DOMContentLoaded", function () {
  document.addEventListener("click", function (event) {
    // Handler Eliminar Evento - solo si no es tipo venta/compra
    if (event.target && event.target.id === "btnEliminarEvento") {
      if (!globalThis.eventoActual) return;
      const tipo =
        globalThis.eventoActual.tipoRepeticion ||
        globalThis.eventoActual.tipo ||
        "";
      const isVenta =
        globalThis.eventoActual && globalThis.eventoActual.tipo === "venta";
      const isCompra =
        globalThis.eventoActual && globalThis.eventoActual.tipo === "compra";
      if (isVenta || isCompra) {
        alert(
          "No se puede eliminar eventos de tipo Venta o Compra desde aquí.",
        );
        return;
      }
      const eventoId = globalThis.eventoActual.id;
      const esRepetido = eventoId && eventoId.startsWith("evinst-");
      const esSerie =
        globalThis.eventoActual.tipoRepeticion &&
        globalThis.eventoActual.tipoRepeticion !== "NINGUNA";
      if (esRepetido || esSerie) {
        // Abrir modal custom para opciones de eliminación
        const modalEliminar = new bootstrap.Modal(
          document.getElementById("modalEliminarEvento"),
        );
        modalEliminar.show();
        // Desvincular handlers previos para evitar múltiple binding
        const btnSolo = document.getElementById("btnEliminarSoloRepeticion");
        const btnSerie = document.getElementById("btnEliminarSerieCompleta");
        // Importante: remover event listener previos (en apps con single page, relevante)
        btnSolo.onclick = null;
        btnSerie.onclick = null;
        btnSolo.onclick = function () {
          eliminarEvento("instancia");
        };
        btnSerie.onclick = function () {
          eliminarEvento("serie");
        };
        // Ocultar el modal de detalle cuando abrís el de eliminación
        let modalDetalle = bootstrap.Modal.getInstance(
          document.getElementById("modalDetalleEvento"),
        );
        if (modalDetalle) modalDetalle.hide();
        return;
      } else {
        // Evento normal/sin repeticiones - confirm para borrar
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

    // Nueva función dedicada para eliminar
    function eliminarEvento(deleteMode) {
      const eventoId = globalThis.eventoActual.id;
      fetch("/punto-eca/calendario/evento/eliminar/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": (document.cookie.match(/csrftoken=([^;]+)/) || [
            null,
            "",
          ])[1],
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
        .catch(() => {
          alert("Error de red al intentar eliminar.");
        });
      // Cerrar modal de eliminar si existe
      let modalEliminar = bootstrap.Modal.getInstance(
        document.getElementById("modalEliminarEvento"),
      );
      if (modalEliminar) modalEliminar.hide();
    }
    if (event.target && event.target.id === "btnEditarEvento") {
      console.log(
        "DEBUG boton editar: eventoActual =",
        globalThis.eventoActual,
      );
      // Antes de abrir modal, poblar selects de edición desde los de creación (garantiza opciones)
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
      // También copiar los tipos de repetición
      copiarOpcionesSelect(
        "selectTipoRepeticion",
        "editarSelectTipoRepeticion",
      );
      // Llenar los datos del evento a editar
      if (typeof llenarModalEdicion === "function" && globalThis.eventoActual) {
        llenarModalEdicion(globalThis.eventoActual);
      } else {
        console.warn(
          "llenarModalEdicion no se ejecutó o eventoActual no seteado",
        );
      }
      // Buscamos los modales
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

  // --- MOCK de eventos iniciales (luego pueden venir desde backend) ---
  let eventosMock = [
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
  let calendar = new FullCalendar.Calendar(calendarEl, {
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
    events: EVENTOS, // <-- now uses events from backend, not the mock
    eventContent: function (arg) {
      // Custom rendering para visualizar más info en la celda, no solo en tooltip
      const e = arg.event;
      const tipo = e.extendedProps.type || e.type || "";
      let innerHtml = "";
      if (tipo === "venta") {
        let material = e.extendedProps.nombreMaterial || e.title || "-";
        let cantidad =
          e.extendedProps.cantidad !== undefined
            ? parseFloat(e.extendedProps.cantidad)
            : "";
        let precio =
          e.extendedProps.precioUnitario !== undefined
            ? parseFloat(e.extendedProps.precioUnitario)
            : "";
        let total = cantidad !== "" && precio !== "" ? cantidad * precio : "";
        innerHtml =
          `<b>Venta:</b> ${material}` +
          (cantidad !== "" ? ` (${cantidad})` : "") +
          (total !== "" ? ` - $${total}` : "");
      } else if (tipo === "compra") {
        let material = e.extendedProps.nombreMaterial || e.title || "-";
        let cantidad =
          e.extendedProps.cantidad !== undefined
            ? parseFloat(e.extendedProps.cantidad)
            : "";
        let precio =
          e.extendedProps.precioUnitario !== undefined
            ? parseFloat(e.extendedProps.precioUnitario)
            : "";
        let total = cantidad !== "" && precio !== "" ? cantidad * precio : "";
        innerHtml =
          `<b>Compra:</b> ${material}` +
          (cantidad !== "" ? ` (${cantidad})` : "") +
          (total !== "" ? ` - $${total}` : "");
      } else {
        // Mostramos título, descripción corta, material y centro si existen
        let desc =
          e.extendedProps.descripcion || e.extendedProps.description || "";
        let material =
          e.extendedProps.material || e.extendedProps.nombreMaterial || "";
        let centro =
          e.extendedProps.centro || e.extendedProps.nombreCentroAcopio || "";
        innerHtml = `<b>${e.title}</b>`;
        if (desc)
          innerHtml += `<br><span style='font-size:0.90em;'>${desc}</span>`;
        if (material)
          innerHtml += `<br><span style='font-size:0.88em;color:#555;'>${material}</span>`;
        if (centro)
          innerHtml += `<br><span style='font-size:0.88em;color:#555;'>${centro}</span>`;
      }
      return {
        html: `<span style="font-size:0.95em;white-space:normal;word-break:break-word;">${innerHtml}</span>`,
      };
    },
    eventDidMount: function (info) {
      // Forzar el color definido en cada evento
      if (info.event.backgroundColor) {
        info.el.style.backgroundColor = info.event.backgroundColor;
        info.el.style.borderColor = info.event.backgroundColor;
        info.el.style.color = "#fff"; // texto blanco para contraste
      }
      // Armamos el contenido para el tooltip según el tipo
      let e = info.event;
      let tipo = e.extendedProps.type || e.type || "";
      let contenido = "";
      if (tipo === "venta") {
        let cantidad =
          e.extendedProps.cantidad !== undefined
            ? parseFloat(e.extendedProps.cantidad)
            : null;
        let precio =
          e.extendedProps.precioUnitario !== undefined
            ? parseFloat(e.extendedProps.precioUnitario)
            : null;
        let total = cantidad && precio ? cantidad * precio : null;
        contenido =
          `<b>Venta</b><br>Material: ${e.extendedProps.nombreMaterial || e.title || "-"}<br>` +
          (cantidad !== null ? `Cantidad: ${cantidad}<br>` : "") +
          (precio !== null ? `Precio unitario: $${precio}<br>` : "") +
          (total !== null ? `Total: $${total}<br>` : "") +
          `Centro: ${e.extendedProps.nombreCentroAcopio || e.extendedProps.centro || "-"}<br>` +
          `${e.extendedProps.descripcion || e.extendedProps.description || ""}`;
      } else if (tipo === "compra") {
        let cantidad =
          e.extendedProps.cantidad !== undefined
            ? parseFloat(e.extendedProps.cantidad)
            : null;
        let precio =
          e.extendedProps.precioUnitario !== undefined
            ? parseFloat(e.extendedProps.precioUnitario)
            : null;
        let total = cantidad && precio ? cantidad * precio : null;
        contenido =
          `<b>Compra</b><br>Material: ${e.extendedProps.nombreMaterial || e.title || "-"}<br>` +
          (cantidad !== null ? `Cantidad: ${cantidad}<br>` : "") +
          (precio !== null ? `Precio unitario: $${precio}<br>` : "") +
          (total !== null ? `Total: $${total}<br>` : "") +
          `Centro: ${e.extendedProps.nombreCentroAcopio || e.extendedProps.centro || "-"}<br>` +
          `${e.extendedProps.descripcion || e.extendedProps.description || ""}`;
      } else {
        contenido =
          `<b>${e.title}</b><br>` +
          (e.extendedProps.descripcion || e.extendedProps.description || "");
      }
      // Setear el atributo y actilet el tooltip de Bootstrap
      info.el.setAttribute("data-bs-toggle", "tooltip");
      info.el.setAttribute("data-bs-html", "true");
      info.el.setAttribute("title", contenido);
      // Ahora inicializamos el tooltip de Bootstrap 5
      if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
        new bootstrap.Tooltip(info.el);
      }
    },
    eventClick: function (info) {
      // Siempre setea globalThis.eventoActual ANTES de mostrar detalles
      let e = info.event;
      globalThis.eventoActual = {
        id: e.id,
        title: e.title,
        descripcion:
          e.extendedProps.descripcion || e.extendedProps.description || "",
        start: e.start
          ? typeof e.start === "string"
            ? e.start
            : e.start.toISOString()
          : "",
        end: e.end
          ? typeof e.end === "string"
            ? e.end
            : e.end.toISOString()
          : "",
        backgroundColor: e.backgroundColor || e.color || "#28a745",
        materialId:
          e.extendedProps.materialId || e.extendedProps.material_id || "",
        centroAcopioId:
          e.extendedProps.centroAcopioId ||
          e.extendedProps.centro_acopio_id ||
          "",
        tipoRepeticion:
          e.extendedProps.tipoRepeticion ||
          e.extendedProps.tipo_repeticion ||
          "",
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
      if (!globalThis.eventoActual || !globalThis.eventoActual.id) {
        console.warn(
          "DEBUG: eventoActual quedó incompleto",
          globalThis.eventoActual,
          e.extendedProps,
        );
      } else {
        console.log("eventoActual seteado:", globalThis.eventoActual);
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
  globalThis._calendarioEca = calendar;

  // --- Captura submit del formulario para crear evento ---
  let form = document.getElementById("formCrearEvento");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      agregarEventoDesdeFormulario();
    });
  }
  // También por si usan el botón explícito
  let btnGuardar = document.getElementById("btnGuardarEvento");
  if (btnGuardar) {
    btnGuardar.addEventListener("click", function (e) {
      agregarEventoDesdeFormulario();
    });
  }

  // Forzar recarga al cerrar el modal de crear evento (vía cualquier método)
  let modalCrear = document.getElementById("modalCrearEvento");
  if (modalCrear) {
    modalCrear.addEventListener("hidden.bs.modal", function () {
      globalThis.location.reload();
    });
  }

  function agregarEventoDesdeFormulario() {
    // Obtener valores de los campos
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

    // Construir dates ISO
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
    // Cerrar el modal, limpiar el form y recargar la página
    setTimeout(function () {
      let modal = bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modalCrearEvento"),
      );
      modal.hide();
      form.reset();
      ocultarAlertas();
      globalThis.location.reload(); // Recarga la página al guardar un evento nuevo
    }, 800);
  }
  // ==============================================
  // Lógica para editar evento desde el modal edición
  // ==============================================
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
      // Validación mínima
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
          for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
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
            // Refrescar el calendario podría implicar reload de eventos, según estructura
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
        document.getElementById("alertEditarErrorText").innerText =
          "Error de red o servidor";
        document.getElementById("alertEditarError").classList.remove("d-none");
      }
    });
  }
});

// Modal para DETALLES DE VENTA (con IDs nuevos de section-calendario.html)
function mostrarDetallesVenta(evento) {
  document.getElementById("detallesVentaTitulo").textContent =
    evento.extendedProps.nombreMaterial || evento.title || "-";
  document.getElementById("detallesVentaFecha").textContent = evento.start
    ? evento.start.toLocaleString
      ? typeof evento.start === "object"
        ? evento.start.toLocaleString("es-CO")
        : evento.start
      : evento.start
    : "-";
  // Cantidad
  let cantidad =
    evento.extendedProps.cantidad !== undefined
      ? parseFloat(evento.extendedProps.cantidad)
      : "";
  document.getElementById("detallesVentaCantidad").textContent =
    cantidad !== ""
      ? cantidad.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "-";
  // Precio unitario
  let precio =
    evento.extendedProps.precioUnitario !== undefined
      ? parseFloat(evento.extendedProps.precioUnitario)
      : "";
  document.getElementById("detallesVentaPrecio").textContent =
    precio !== ""
      ? "$" +
        precio.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "-";
  // Total
  let total = cantidad !== "" && precio !== "" ? cantidad * precio : "";
  document.getElementById("detallesVentaTotal").textContent =
    total !== ""
      ? "$" +
        total.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "-";
  // Centro de Acopio
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
  // Mostrar el modal usando el nuevo ID
  let modalVenta = new bootstrap.Modal(
    document.getElementById("modalDetallesVenta"),
  );
  modalVenta.show();
}

// Modal para DETALLE GENÉRICO DE EVENTO
globalThis.mostrarDetalleEvento = function mostrarDetalleEvento(evento) {
  // Refuerzo: setea global el evento actual mostrado
  globalThis.eventoActual = globalThis.eventoActual = {
    id: evento.id,
    title: evento.title || evento.extendedProps.titulo || "",
    descripcion:
      evento.extendedProps.descripcion ||
      evento.extendedProps.description ||
      "",
    start: evento.start
      ? typeof evento.start === "string"
        ? evento.start
        : evento.start.toISOString()
      : "",
    end: evento.end
      ? typeof evento.end === "string"
        ? evento.end
        : evento.end.toISOString()
      : "",
    backgroundColor: evento.backgroundColor || evento.color || "#28a745",
    materialId:
      evento.extendedProps.materialId || evento.extendedProps.material_id || "",
    centroAcopioId:
      evento.extendedProps.centroAcopioId ||
      evento.extendedProps.centro_acopio_id ||
      "",
    tipoRepeticion:
      evento.extendedProps.tipoRepeticion ||
      evento.extendedProps.tipo_repeticion ||
      "",
    fechaFinRepeticion:
      evento.extendedProps.fechaFinRepeticion ||
      evento.extendedProps.fecha_fin_repeticion ||
      "",
    observaciones: evento.extendedProps.observaciones || "",
    puntoEcaId:
      evento.extendedProps.puntoEcaId ||
      evento.extendedProps.punto_eca_id ||
      "",
    usuarioId:
      evento.extendedProps.usuarioId || evento.extendedProps.usuario_id || "",
  };
  console.log("Refuerzo eventoActual modal:", globalThis.eventoActual);
  // Mostrar en consola para debug
  console.log("Evento para detalle:", evento, evento.extendedProps);
  document.getElementById("eventoDetalleTitulo").textContent =
    evento.title || evento.extendedProps.titulo || "-";
  // Fecha y hora (simple)
  let fechaStr = "-";
  if (evento.start) {
    if (typeof evento.start === "object" && evento.start.toLocaleString) {
      fechaStr = evento.start.toLocaleString("es-CO");
    } else {
      fechaStr = evento.start;
    }
    if (evento.end) {
      let finStr =
        typeof evento.end === "object" && evento.end.toLocaleString
          ? evento.end.toLocaleString("es-CO")
          : evento.end;
      fechaStr += " a " + finStr;
    }
  }
  document.getElementById("eventoDetalleFecha").textContent = fechaStr;
  // Buscar distintos posibles nombres para material
  document.getElementById("eventoDetalleMaterial").textContent =
    evento.extendedProps.material ||
    evento.extendedProps.nombreMaterial ||
    evento.extendedProps.material_nombre ||
    evento.extendedProps.tipo_material ||
    "-";
  // Buscar distintos posibles nombres para centro
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
  // Mostrar el modal
  let modal = new bootstrap.Modal(
    document.getElementById("modalDetalleEvento"),
  );
  modal.show();
};

function mostrarDetallesCompra(evento) {
  document.getElementById("detCompraMaterial").textContent =
    evento.extendedProps.nombreMaterial || evento.title || "-";
  document.getElementById("detCompraFecha").textContent = evento.start
    ? evento.start.toLocaleString
      ? typeof evento.start === "object"
        ? evento.start.toLocaleString("es-CO")
        : evento.start
      : evento.start
    : "-";
  // Para compras, los campos de cantidad/precio/unitario/total pueden venir en extendedProps
  let cantidad =
    evento.extendedProps.cantidad !== undefined
      ? parseFloat(evento.extendedProps.cantidad)
      : "";
  document.getElementById("detCompraCantidad").textContent =
    cantidad !== ""
      ? cantidad.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "-";
  let precio =
    evento.extendedProps.precioUnitario !== undefined
      ? parseFloat(evento.extendedProps.precioUnitario)
      : "";
  document.getElementById("detCompraPrecio").textContent =
    precio !== ""
      ? "$" +
        precio.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "-";
  let total = cantidad !== "" && precio !== "" ? cantidad * precio : "";
  document.getElementById("detCompraTotal").textContent =
    total !== ""
      ? "$" +
        total.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "-";
  document.getElementById("detCompraObservaciones").textContent =
    evento.extendedProps.observaciones ||
    evento.extendedProps.descripcion ||
    evento.extendedProps.description ||
    "Sin observaciones";
  // Mostrar el modal usando el nuevo ID
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
