// =============================
// LISTENERS ELIMINAR DESDE TABLA HISTORIAL
// =============================

// Parsear datos JSON inyectados por Django (mover desde plantilla)
(function parseTemplateInjectedData() {
  try {
    globalThis.CENTROS = parseJsonInyectado("centros-data");
    globalThis.ENTRADAS_INICIALES = parseJsonInyectado("entradas-data");
    globalThis.SALIDAS_INICIALES = parseJsonInyectado("salidas-data");
    globalThis.HISTORIAL_COMPRAS = parseJsonInyectado("historial-compras-data");
    globalThis.HISTORIAL_VENTAS = parseJsonInyectado("historial-ventas-data");

    // Paginación: respetar si ya fueron definidas en otro lado
    globalThis.PAGINA_ACTUAL_ENTRADAS = globalThis.PAGINA_ACTUAL_ENTRADAS || 1;
    globalThis.PAGINA_ACTUAL_SALIDAS = globalThis.PAGINA_ACTUAL_SALIDAS || 1;
    globalThis.REGISTROS_POR_PAGINA = globalThis.REGISTROS_POR_PAGINA || 5;
    globalThis.PAGINA_ACTUAL_HISTORIAL = globalThis.PAGINA_ACTUAL_HISTORIAL || 1;
    globalThis.REGISTROS_POR_PAGINA_HISTORIAL = globalThis.REGISTROS_POR_PAGINA_HISTORIAL || 10;
  } catch (err) {
    console.error("Error parsing injected template data:", err);
  }
})();

function parseJsonInyectado(id) {
  const elemento = document.getElementById(id);
  if (!elemento) return [];
  try {
    return JSON.parse(elemento.textContent || elemento.innerText || "null") || [];
  } catch (error) {
    console.warn("No se pudo parsear", id, error);
    return [];
  }
}

// Funciones de apoyo extraídas (SonarQube)
function toISO(fecha) {
  if (!fecha) return 0;
  return new Date(fecha.replace(" ", "T")).getTime();
}

function escaparHtml(valor) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  return String(valor ?? "").replaceAll(/[&<>"']/g, (m) => map[m]);
}

function formatearMoneda(valor) {
  const numero = Number(valor || 0);
  return numero.toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatearFechaHora(valor) {
  if (!valor) return "-";
  const fecha = new Date(valor);
  if (Number.isNaN(fecha.getTime())) return String(valor);
  return fecha.toLocaleString("es-CO", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function obtenerFechaHoraActual() {
  const ahora = new Date();
  const ahoraLocal = new Date(
    ahora.getTime() - ahora.getTimezoneOffset() * 60000,
  );
  return ahoraLocal.toISOString().slice(0, 16);
}

function obtenerUnidadMedida(material, fallback = "") {
  const unidadMedida = material?.unidadMedida;
  if (unidadMedida && typeof unidadMedida === "object") {
    return unidadMedida.nombre || unidadMedida.clave || fallback;
  }
  if (typeof unidadMedida === "string") {
    return unidadMedida;
  }
  return material?.unidad ?? fallback;
}

function normalizarNumero(valor, fallback = null) {
  if (valor === undefined || valor === null || valor === "") {
    return fallback;
  }
  const numero = Number.parseFloat(valor);
  return Number.isNaN(numero) ? fallback : numero;
}

function formatearNumeroCampo(valor) {
  return valor !== null && !Number.isNaN(valor) ? valor.toFixed(2) : "";
}

function establecerValorCampo(elemento, valor, opciones = {}) {
  if (!elemento) return;
  elemento.value = valor ?? "";

  const jquery = globalThis.$;
  if (opciones.dispararChange && jquery) {
    jquery(elemento).val(elemento.value).trigger("change");
  }

  if (opciones.dispararInput) {
    elemento.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

function triggerEventsCampo(elemento) {
  if (!elemento) return;
  elemento.dispatchEvent(new Event("input", { bubbles: true }));
  elemento.dispatchEvent(new Event("change", { bubbles: true }));
}

function obtenerBotonSubmitFormulario(form) {
  return form?.querySelector('button[type="submit"]') || null;
}

function establecerEstadoBotonSubmit(submitBtn, esProcesando, textoNormal) {
  if (!submitBtn) return;
  submitBtn.disabled = esProcesando;
  submitBtn.innerHTML = esProcesando
    ? '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...'
    : textoNormal;
}

function restablecerSubmitMovimiento(
  submitBtn,
  textoNormal,
  form = null,
  marcarEnviando = null,
) {
  if (typeof marcarEnviando === "function") {
    marcarEnviando("0");
  } else if (form) {
    form.dataset.enviando = "0";
  }
  establecerEstadoBotonSubmit(submitBtn, false, textoNormal);
}

function prepararCamposMaterial(material) {
  return {
    materialId:
      material.materialId || material.id || material.material?.materialId || "",
    nombre: material.nmbMaterial || material.nombre || material.text || "",
    tipo: material.nmbTipo || material.tipo || "",
    categoria: material.nmbCategoria || material.categoria || "",
    descripcion: material.dscMaterial || material.descripcion || "",
    unidad: obtenerUnidadMedida(material),
    stockActual: normalizarNumero(material.stockActual),
    capacidadMaxima: normalizarNumero(material.capacidadMaxima),
    precioCompra: normalizarNumero(material.precioCompra),
    precioVenta: normalizarNumero(material.precioVenta),
    inventarioId:
      material.inventarioId ||
      material.inventario_id ||
      material.inventarioID ||
      material.inventario ||
      "",
  };
}

function numeroComoTexto(valor) {
  if (valor === undefined || valor === null || valor === "") return "";
  const numero = Number(valor);
  return Number.isNaN(numero) ? "" : String(numero);
}

function esMaterialCoincidente(material, campos) {
  return (
    material.materialId === campos.materialId ||
    (material.nmbMaterial && material.nmbMaterial === campos.nombre)
  );
}

function manejarErrorBusquedaMateriales(estadoBusquedaEl, error) {
  console.error("Error en la búsqueda de materiales:", error);
  if (estadoBusquedaEl) {
    estadoBusquedaEl.innerHTML =
      '<div class="alert alert-danger mb-0" role="alert"><i class="bi bi-exclamation-octagon me-2"></i>Error de conexión</div>';
  }
}

function buscarMaterialEnInventario(data, campos) {
  return data.find((item) => esMaterialCoincidente(item, campos));
}

function recargarPagina() {
  location.reload();
}

function establecerValoresEnCampos(valoresPorId) {
  Object.entries(valoresPorId).forEach(([id, valor]) => {
    const elemento = document.getElementById(id);
    if (elemento) elemento.value = valor ?? "";
  });
}

function abrirModalBootstrap(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  new bootstrap.Modal(modal).show();
}

function poblarEdicionCompra(entrada) {
  const fechaCompra = entrada.fechaCompra
    ? new Date(entrada.fechaCompra).toISOString().slice(0, 16)
    : "";
  establecerValoresEnCampos({
    editCompraId: entrada.compraId,
    editInventarioId: entrada.inventarioId,
    editCompraMaterialId: entrada.materialId,
    editCompraMaterial: entrada.nombreMaterial,
    editCompraFecha: fechaCompra,
    editCompraCantidad: entrada.cantidad,
    editCompraPrecio: entrada.precioCompra,
    editCompraObservaciones: entrada.observaciones,
  });
  abrirModalBootstrap("editarCompraModal");
}

function poblarEdicionVenta(venta) {
  const fechaVenta = venta.fechaVenta
    ? new Date(venta.fechaVenta).toISOString().slice(0, 16)
    : "";
  establecerValoresEnCampos({
    editVentaId: venta.ventaId,
    editInventarioIdVenta: venta.inventarioId,
    editVentaMaterialId: venta.materialId,
    editVentaMaterial: venta.nombreMaterial,
    editVentaFecha: fechaVenta,
    editVentaCantidad: venta.cantidad,
    editVentaPrecio: venta.precioVenta,
    editVentaCentro: venta.centroAcopioId,
    editVentaObservaciones: venta.observaciones,
  });
  abrirModalBootstrap("editarVentaModal");
}

function cerrarModalRelacionado(modalId) {
  const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
  if (modal) modal.hide();
}

function generarHtmlPaginacion(totalPaginas, paginaActual) {
  let html =
    '<li class="page-item ' +
    (paginaActual <= 1 ? "disabled" : "") +
    '"><button class="page-link" type="button" data-page="' +
    (paginaActual - 1) +
    '" ' +
    (paginaActual <= 1 ? 'disabled' : '') +
    '>Anterior</button></li>';

  for (let i = 1; i <= totalPaginas; i++) {
    html +=
      '<li class="page-item ' +
      (i === paginaActual ? "active" : "") +
      '"><button class="page-link" type="button" data-page="' +
      i +
      '">' +
      i +
      "</button></li>";
  }

  html +=
    '<li class="page-item ' +
    (paginaActual >= totalPaginas ? "disabled" : "") +
    '"><button class="page-link" type="button" data-page="' +
    (paginaActual + 1) +
    '" ' +
    (paginaActual >= totalPaginas ? 'disabled' : '') +
    '>Siguiente</button></li>';

  return html;
}

function actualizarPaginacionGenerica(paginacionId, totalPaginas, paginaActual) {
  const paginacion = document.getElementById(paginacionId);
  if (!paginacion) return;
  if (totalPaginas <= 0) {
    paginacion.innerHTML = "";
    return;
  }
  paginacion.innerHTML = generarHtmlPaginacion(totalPaginas, paginaActual);
}

function construirBotonesMovimientoTabla({
  detalleClase,
  detalleAttr,
  detalleId,
  detalleTitle,
  eliminarClase,
  eliminarAttr,
  eliminarId,
  eliminarTitle,
}) {
  return `
    <div class="d-flex gap-2 justify-content-center">
      <button type="button" class="btn btn-sm ${detalleClase} text-white" ${detalleAttr}="${escaparHtml(detalleId)}" title="${detalleTitle}">
        <i class="bi bi-eye-fill"></i>
      </button>
      <button type="button" class="btn btn-sm ${eliminarClase}" ${eliminarAttr}="${escaparHtml(eliminarId)}" title="${eliminarTitle}">
        <i class="bi bi-trash3-fill"></i>
      </button>
    </div>
  `;
}

function construirFilaMovimientoTabla({
  fecha,
  material,
  cantidad,
  precio,
  total,
  categoria,
  tipo,
  totalClase,
  detalleClase,
  detalleAttr,
  detalleId,
  detalleTitle,
  eliminarClase,
  eliminarAttr,
  eliminarId,
  eliminarTitle,
  centro = null,
}) {
  const cantidadTxt = escaparHtml(formatearMoneda(cantidad));
  const precioTxt = escaparHtml(formatearMoneda(precio));
  const totalTxt = escaparHtml(formatearMoneda(total));
  const centroHtml = centro === null ? "" : `<td class="small">${escaparHtml(centro || "-")}</td>`;

  return `
    <tr data-categoria="${escaparHtml(categoria)}" data-tipo="${escaparHtml(tipo)}">
      <td class="small">${escaparHtml(fecha)}</td>
      <td class="small">${material}</td>
      <td class="text-end small">${cantidadTxt}</td>
      <td class="text-end small">$${precioTxt}</td>
      <td class="text-end small fw-semibold ${totalClase}">$${totalTxt}</td>
      ${centroHtml}
      <td class="text-center">
        ${construirBotonesMovimientoTabla({
          detalleClase,
          detalleAttr,
          detalleId,
          detalleTitle,
          eliminarClase,
          eliminarAttr,
          eliminarId,
          eliminarTitle,
        })}
      </td>
    </tr>
  `;
}

function esRespuestaExitosaMovimiento(data) {
  return Boolean(
    data &&
      (data.error === false ||
        data.ok ||
        data.success ||
        data.status === 200 ||
        data.status === 201),
  );
}

function enviarActualizacionMovimiento({
  url,
  datosActualizacion,
  tituloExito,
  textoExito,
  tituloError,
  textoError,
}) {
  fetch(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": obtenerCsrfTokenMovimiento(),
    },
    body: JSON.stringify(datosActualizacion),
  })
    .then((res) => res.json())
    .then((data) => {
      if (esRespuestaExitosaMovimiento(data)) {
        mostrarSwalMensajeMovimiento({
          icon: "success",
          title: tituloExito,
          text: data.mensaje || data.message || textoExito,
          onClose: recargarPagina,
        });
      } else {
        mostrarSwalMensajeMovimiento({
          icon: "error",
          title: tituloError || "Error al actualizar",
          text: data.mensaje || data.message || textoError || "Error al actualizar",
        });
      }
    });
}

function poblarDetalleMovimiento({
  prefijo,
  material,
  fecha,
  cantidad,
  precio,
  total,
  observaciones,
  centroAcopio = null,
  botonIds = [],
  botonAtributo = null,
  botonValor = null,
}) {
  document.getElementById(`det${prefijo}Material`).textContent = material || "-";
  document.getElementById(`det${prefijo}Fecha`).textContent = fecha;
  document.getElementById(`det${prefijo}Cantidad`).textContent =
    cantidad.toLocaleString("es-CO", { minimumFractionDigits: 2 });
  document.getElementById(`det${prefijo}Precio`).textContent =
    "$" + precio.toLocaleString("es-CO", { minimumFractionDigits: 2 });
  document.getElementById(`det${prefijo}Total`).textContent =
    "$" + total.toLocaleString("es-CO", { minimumFractionDigits: 2 });
  document.getElementById(`det${prefijo}Observaciones`).textContent =
    observaciones || "Sin observaciones";

  if (centroAcopio !== null) {
    const centroEl = document.getElementById(`det${prefijo}Centro`);
    if (centroEl) {
      centroEl.textContent = centroAcopio || "-";
    }
  }

  if (botonIds.length && botonAtributo) {
    asignarDataEnBotones(botonIds, botonAtributo, botonValor);
  }
}

function obtenerHistorialMovimiento(movimientoId, esCompra) {
  const listado = esCompra ? globalThis.HISTORIAL_COMPRAS : globalThis.HISTORIAL_VENTAS;
  const campoId = esCompra ? "compraId" : "ventaId";
  return (listado || []).find((item) => item[campoId] === movimientoId);
}

function obtenerMovimientoInicial(movimientoId, esCompra) {
  const listado = esCompra ? globalThis.ENTRADAS_INICIALES : globalThis.SALIDAS_INICIALES;
  const campoId = esCompra ? "compraId" : "ventaId";
  return (listado || []).find((item) => item[campoId] === movimientoId);
}

function mostrarDetallesSalidaPorId(ventaId) {
  const salida = (globalThis.SALIDAS_INICIALES || []).find((item) => item.ventaId === ventaId);
  if (!salida) {
    mostrarSwalMensajeMovimiento({
      icon: "info",
      title: "Sin detalles",
      text: "No se encontraron los detalles de esta venta",
    });
    return;
  }

  const fecha = salida.fechaVenta
    ? new Date(salida.fechaVenta).toLocaleDateString("es-CO")
    : "-";
  const cantidad = Number.parseFloat(salida.cantidad || 0);
  const precio = Number.parseFloat(salida.precioVenta || 0);
  const total = cantidad * precio;

  poblarDetalleMovimiento({
    prefijo: "Salida",
    material: salida.nombreMaterial,
    fecha,
    cantidad,
    precio,
    total,
    observaciones: salida.observaciones,
    centroAcopio: salida.nombreCentroAcopio,
    botonIds: ["btnEliminarSalida", "btnEditarSalida"],
    botonAtributo: "ventaId",
    botonValor: ventaId,
  });

  const modal = new bootstrap.Modal(
    document.getElementById("detallesSalidaModal"),
  );
  modal.show();
}

function asignarDataEnBotones(ids, atributo, valor) {
  ids.forEach((id) => {
    const boton = document.getElementById(id);
    if (boton) boton.dataset[atributo] = valor;
  });
}

function poblarDetallesHistorialCompra(movimiento, fecha, cantidad, precio, total, movimientoId) {
  poblarDetalleMovimiento({
    prefijo: "Entrada",
    material: movimiento.nombreMaterial,
    fecha,
    cantidad,
    precio,
    total,
    observaciones: movimiento.observaciones,
    botonIds: ["btnEditarEntrada", "btnEliminarEntrada"],
    botonAtributo: "compraId",
    botonValor: movimientoId,
  });
}

function poblarDetallesHistorialVenta(movimiento, fecha, cantidad, precio, total, movimientoId) {
  poblarDetalleMovimiento({
    prefijo: "Salida",
    material: movimiento.nombreMaterial,
    fecha,
    cantidad,
    precio,
    total,
    observaciones: movimiento.observaciones,
    centroAcopio: movimiento.nombreCentroAcopio,
    botonIds: ["btnEditarSalida", "btnEliminarSalida"],
    botonAtributo: "ventaId",
    botonValor: movimientoId,
  });
}

function mostrarDetallesHistorialPorBoton(btn) {
  const esCompra = btn.classList.contains("btn-editar-historial-compra");
  const movimientoId = esCompra ? btn.dataset.compraId : btn.dataset.ventaId;
  const tipoMovimiento = esCompra ? "Compra" : "Venta";
  const movimiento = obtenerHistorialMovimiento(movimientoId, esCompra);

  if (!movimiento) {
    mostrarSwalMensajeMovimiento({
      icon: "info",
      title: "Sin detalles",
      text: "No se encontraron los detalles de este movimiento",
    });
    return;
  }

  const fecha = movimiento.fecha
    ? new Date(movimiento.fecha).toLocaleDateString("es-CO")
    : "-";
  const cantidad = Number.parseFloat(movimiento.cantidad || 0);
  const precio = Number.parseFloat(movimiento.precio || 0);
  const total = cantidad * precio;

  const poblarDetalles = esCompra
    ? poblarDetallesHistorialCompra
    : poblarDetallesHistorialVenta;
  poblarDetalles(movimiento, fecha, cantidad, precio, total, movimientoId);

  const modalId = esCompra ? "detallesEntradaModal" : "detallesSalidaModal";
  const modal = new bootstrap.Modal(document.getElementById(modalId));
  document.getElementById(modalId).dataset.isHistoryItem = "true";
  document.getElementById(modalId).dataset.historyItemType =
    tipoMovimiento.toLowerCase();

  modal.show();
}

function manejarClickEdicionMovimiento(btn) {
  const esCompra = btn.id === "btnEditarEntrada";
  const movimientoId = esCompra ? btn.dataset.compraId : btn.dataset.ventaId;
  const esHistorial = Boolean(
    document.querySelector(
      esCompra
        ? `.btn-editar-historial-compra[data-compra-id="${movimientoId}"]`
        : `.btn-editar-historial-venta[data-venta-id="${movimientoId}"]`,
    ),
  );

  if (!movimientoId) return;

  cerrarModalRelacionado(esCompra ? "detallesEntradaModal" : "detallesSalidaModal");

  const movimiento = esHistorial
    ? obtenerHistorialMovimiento(movimientoId, esCompra)
    : obtenerMovimientoInicial(movimientoId, esCompra);

  if (!movimiento) return;

  if (esCompra) {
    poblarEdicionCompra(movimiento);
  } else {
    poblarEdicionVenta(movimiento);
  }
}

function generarFilaEntrada(entrada) {
  const fecha = entrada.fechaCompra
    ? new Date(entrada.fechaCompra).toLocaleString("es-CO", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "-";
  const cantidad = Number.parseFloat(entrada.cantidad || 0);
  const precio = Number.parseFloat(entrada.precioCompra || 0);
  const total = cantidad * precio;
  return construirFilaMovimientoTabla({
    fecha,
    material: escaparHtml(entrada.nombreMaterial || "-"),
    cantidad,
    precio,
    total,
    categoria: entrada.nombreCategoria || "",
    tipo: entrada.nombreTipo || "",
    totalClase: "text-danger",
    detalleClase: "btn-danger btn-detalles-entrada",
    detalleAttr: "data-compra-id",
    detalleId: entrada.compraId,
    detalleTitle: "Ver detalles",
    eliminarClase: "btn-outline-danger btn-eliminar-entrada",
    eliminarAttr: "data-compra-id",
    eliminarId: entrada.compraId,
    eliminarTitle: "Eliminar",
  });
}

function generarFilaSalida(salida) {
  const fecha = salida.fechaVenta
    ? new Date(salida.fechaVenta).toLocaleString("es-CO", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "-";
  const cantidad = Number.parseFloat(salida.cantidad || 0);
  const precio = Number.parseFloat(salida.precioVenta || 0);
  const total = cantidad * precio;
  return construirFilaMovimientoTabla({
    fecha,
    material: escaparHtml(salida.nombreMaterial || "-"),
    cantidad,
    precio,
    total,
    categoria: salida.nombreCategoria || "",
    tipo: salida.nombreTipo || "",
    totalClase: "text-success",
    detalleClase: "btn-success btn-detalles-salida",
    detalleAttr: "data-venta-id",
    detalleId: salida.ventaId,
    detalleTitle: "Ver detalles",
    eliminarClase: "btn-outline-success btn-eliminar-salida",
    eliminarAttr: "data-venta-id",
    eliminarId: salida.ventaId,
    eliminarTitle: "Eliminar",
    centro: salida.nombreCentroAcopio || "-",
  });
}

function generarFilaHistorial(mov) {
  const fecha = formatearFechaHora(mov.fecha);
  const cantidadNumber = Number.parseFloat(mov.cantidad || 0);
  const cantidad = escaparHtml(formatearMoneda(cantidadNumber));
  const precioNumber = Number.parseFloat(mov.precio || 0);
  const precio = escaparHtml(formatearMoneda(precioNumber));
  const tipoBadge =
    mov.tipo === "Compra"
      ? '<span class="badge bg-danger">Compra</span>'
      : '<span class="badge bg-success">Venta</span>';
  const total = escaparHtml(formatearMoneda(cantidadNumber * precioNumber));
  const esCompra = mov.tipo === "Compra";
  const botonId = esCompra ? mov.compraId : mov.ventaId;
  const acciones = construirBotonesMovimientoTabla({
    detalleClase: esCompra
      ? "btn-danger btn-editar-historial-compra"
      : "btn-success btn-editar-historial-venta",
    detalleAttr: esCompra ? "data-compra-id" : "data-venta-id",
    detalleId: botonId,
    detalleTitle: "Ver detalles",
    eliminarClase: esCompra
      ? "btn-outline-danger btn-eliminar-historial-compra"
      : "btn-outline-success btn-eliminar-historial-venta",
    eliminarAttr: esCompra ? "data-compra-id" : "data-venta-id",
    eliminarId: botonId,
    eliminarTitle: esCompra ? "Eliminar compra" : "Eliminar venta",
  });
  const materialEsc = escaparHtml(mov.nombreMaterial || "-");
  return `
            <tr>
                <td class="small">${escaparHtml(fecha)}</td>
                <td class="small">${tipoBadge}</td>
                <td class="small fw-bold">${materialEsc}</td>
                <td class="text-end small">${cantidad}</td>
                <td class="text-end small">$${precio}</td>
                <td class="text-end small fw-semibold">$${total}</td>
                <td class="text-center">${acciones}</td>
            </tr>
        `;
}

function obtenerPuntoEcaIdActual() {
  return (
    document.querySelector("section[data-punto-eca-id]")?.dataset.puntoEcaId ||
    ""
  );
}

function obtenerCsrfTokenMovimiento() {
  return (
    document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content") || ""
  );
}

function obtenerValorFiltroExport(id) {
  return document.getElementById(id)?.value?.trim() || "";
}

function construirUrlExport(baseUrl, params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([clave, valor]) => {
    if (valor !== undefined && valor !== null && String(valor).trim() !== "") {
      searchParams.set(clave, String(valor).trim());
    }
  });
  const query = searchParams.toString();
  return query ? `${baseUrl}?${query}` : baseUrl;
}

function obtenerValoresUnicos(items, selector) {
  const valores = new Set();
  (items || []).forEach((item) => {
    const valor = selector(item);
    if (valor) valores.add(valor);
  });
  return Array.from(valores).sort((a, b) => a.localeCompare(b));
}

function poblarSelectConValores($select, valores, placeholder, opciones = {}) {
  if (!$select?.length) return;

  $select.find('option:not([value=""])').remove();
  valores.forEach((valor) => {
    $select.append($("<option>").val(valor).text(valor));
  });

  $select.select2({
    theme: "bootstrap4",
    width: "100%",
    allowClear: true,
    placeholder,
    minimumInputLength: opciones.minimumInputLength ?? 0,
  });
}

async function descargarArchivoExportacion(url, filename) {
  const response = await fetch(url, {
    method: "GET",
    credentials: "same-origin",
    headers: {
      Accept: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const contentType = (response.headers.get("content-type") || "").toLowerCase();
  if (!contentType.includes("spreadsheetml.sheet")) {
    const text = await response.text();
    throw new Error(
      `Respuesta inesperada: ${contentType || "sin content-type"}. ${text.slice(0, 120)}`,
    );
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = objectUrl;
  enlace.download = filename;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(objectUrl);
}

function obtenerParamsExportCompras() {
  return {
    punto_eca_id: obtenerPuntoEcaIdActual(),
    material: obtenerValorFiltroExport("filtroCompraMaterial"),
    categoria: obtenerValorFiltroExport("filtroCompraCategoria"),
    tipo: obtenerValorFiltroExport("filtroCompraTipo"),
    fecha_desde: obtenerValorFiltroExport("filtroCompraFechaDesde"),
    fecha_hasta: obtenerValorFiltroExport("filtroCompraFechaHasta"),
  };
}

function obtenerParamsExportVentas() {
  return {
    punto_eca_id: obtenerPuntoEcaIdActual(),
    material: obtenerValorFiltroExport("filtroVentaMaterial"),
    categoria: obtenerValorFiltroExport("filtroVentaCategoria"),
    tipo: obtenerValorFiltroExport("filtroVentaTipo"),
    centro_acopio: obtenerValorFiltroExport("filtroVentaCentro"),
    fecha_desde: obtenerValorFiltroExport("filtroVentaFechaDesde"),
    fecha_hasta: obtenerValorFiltroExport("filtroVentaFechaHasta"),
  };
}

function obtenerFiltrosHistorial() {
  return {
    material: obtenerValorFiltroExport("filtroHistorialMaterial"),
    categoria: obtenerValorFiltroExport("filtroHistorialCategoria"),
    tipoMaterial: obtenerValorFiltroExport("filtroHistorialTipo"),
    centroAcopio: obtenerValorFiltroExport("filtroHistorialCentroAcopio"),
    tipoMovimiento: obtenerValorFiltroExport("filtroHistorialTipoMovimiento"),
    fechaDesde: obtenerValorFiltroExport("filtroHistorialDesde"),
    fechaHasta: obtenerValorFiltroExport("filtroHistorialHasta"),
  };
}

function obtenerParamsExportHistorial() {
  const filtros = obtenerFiltrosHistorial();
  return {
    punto_eca_id: obtenerPuntoEcaIdActual(),
    material: filtros.material,
    categoria: filtros.categoria,
    tipo: filtros.tipoMaterial,
    centro_acopio: filtros.centroAcopio,
    tipo_movimiento: filtros.tipoMovimiento,
    fecha_desde: filtros.fechaDesde,
    fecha_hasta: filtros.fechaHasta,
  };
}

function sincronizarEnlacesExportacion() {
  const exportaciones = [
    [
      "btnExportComprasExcel",
      "/punto-eca/movimientos/exportar-compras-excel/",
      obtenerParamsExportCompras,
      "compras.xlsx",
    ],
    ["btnExportComprasPdf", "/punto-eca/movimientos/exportar-compras-pdf/", obtenerParamsExportCompras],
    [
      "btnExportVentasExcel",
      "/punto-eca/movimientos/exportar-ventas-excel/",
      obtenerParamsExportVentas,
      "ventas.xlsx",
    ],
    ["btnExportVentasPdf", "/punto-eca/movimientos/exportar-ventas-pdf/", obtenerParamsExportVentas],
    [
      "btnExportHistorialExcel",
      "/punto-eca/movimientos/exportar-historial-excel/",
      obtenerParamsExportHistorial,
      "historial_movimientos.xlsx",
    ],
    ["btnExportHistorialPdf", "/punto-eca/movimientos/exportar-historial-pdf/", obtenerParamsExportHistorial],
  ];

  exportaciones.forEach(([botonId, baseUrl, obtenerParams, filename]) => {
    const boton = document.getElementById(botonId);
    if (!boton) return;
    if (boton.dataset.exportBound === "1") return;
    boton.dataset.exportBound = "1";
    const actualizarHref = () => {
      boton.href = construirUrlExport(baseUrl, obtenerParams());
    };
    actualizarHref();
    if (filename) {
      boton.addEventListener("click", async (event) => {
        event.preventDefault();
        try {
          actualizarHref();
          await descargarArchivoExportacion(boton.href, filename);
        } catch (error) {
          console.error("Error descargando exportación:", error);
          if (typeof globalThis.mostrarSwalMensajeMovimiento === "function") {
            globalThis.mostrarSwalMensajeMovimiento({
              icon: "error",
              title: "No se pudo descargar el archivo",
              text: "El servidor no devolvió un Excel válido.",
            });
          } else {
            alert("No se pudo descargar el archivo. Revisa la sesión o intenta de nuevo.");
          }
        }
      });
      return;
    }

    boton.addEventListener("click", actualizarHref);
  });
}

document.addEventListener("DOMContentLoaded", sincronizarEnlacesExportacion);
sincronizarEnlacesExportacion();

function eliminarMovimientoPorId(tipo, id, opciones = {}) {
  const esCompra = tipo === "compra";
  const {
    confirmTitle = esCompra ? "Eliminar compra" : "Eliminar venta",
    confirmText = esCompra
      ? "¿Estás seguro de que deseas eliminar esta compra?"
      : "¿Estás seguro de que deseas eliminar esta venta?",
    successTitle = esCompra ? "Compra eliminada" : "Venta eliminada",
    successText = esCompra
      ? "Compra eliminada correctamente"
      : "Venta eliminada correctamente",
    sinDatosTitle = "Sin datos",
    sinDatosText = esCompra
      ? "No se encontraron los datos de esta compra"
      : "No se encontraron los datos de esta venta",
  } = opciones;

  globalThis
    .confirmarSwalMovimiento({
      title: confirmTitle,
      text: confirmText,
    })
    .then((confirmado) => {
      if (!confirmado) return;

      const listado = esCompra
        ? [...(globalThis.HISTORIAL_COMPRAS || []), ...(globalThis.ENTRADAS_INICIALES || [])]
        : [...(globalThis.HISTORIAL_VENTAS || []), ...(globalThis.SALIDAS_INICIALES || [])];
      const campoId = esCompra ? "compraId" : "ventaId";
      const entrada = listado.find((item) => String(item[campoId]) === String(id));

      if (!entrada) {
        globalThis.mostrarSwalMensajeMovimiento({
          icon: "info",
          title: sinDatosTitle,
          text: sinDatosText,
        });
        return;
      }

      const datosEliminar = {
        [campoId]: id,
        inventarioId: entrada.inventarioId || "",
        puntoId: obtenerPuntoEcaIdActual(),
        materialId: entrada.materialId || "",
      };

      fetch(`/punto-eca/movimientos/borrar-${esCompra ? "compra" : "venta"}/${id}/`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": obtenerCsrfTokenMovimiento(),
        },
        body: JSON.stringify(datosEliminar),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success || data.ok || !data.error) {
            globalThis.mostrarSwalMensajeMovimiento({
              icon: "success",
              title: successTitle,
              text: successText,
              onClose: recargarPagina,
            });
          } else {
            globalThis.mostrarSwalMensajeMovimiento({
              icon: "error",
              title: "Error al eliminar",
              text:
                "Error al eliminar: " +
                (data.mensaje || data.message || "Error desconocido"),
            });
          }
        })
        .catch((error) => {
          globalThis.mostrarSwalMensajeMovimiento({
            icon: "error",
            title: "Error de red",
            text:
              "Error al procesar la solicitud: " +
              (error?.message ?? error),
          });
        });
    });
}

function eliminarCompraPorId(compraId, opciones = {}) {
  return eliminarMovimientoPorId("compra", compraId, opciones);
}

function eliminarVentaPorId(ventaId, opciones = {}) {
  return eliminarMovimientoPorId("venta", ventaId, opciones);
}

const eliminacionesMovimientos = [
  {
    selector: ".btn-eliminar-historial-compra",
    obtenerId: (btn) => btn.dataset.compraId,
    ejecutar: (id) =>
      eliminarCompraPorId(id, {
        confirmTitle: "Eliminar compra",
        confirmText: "¿Estás seguro de que deseas eliminar esta compra?",
        successTitle: "Compra eliminada",
        successText: "Compra eliminada correctamente",
        sinDatosText: "No se encontraron los datos de esta compra",
      }),
  },
  {
    selector: ".btn-eliminar-entrada",
    obtenerId: (btn) => btn.dataset.compraId,
    ejecutar: (id) =>
      eliminarCompraPorId(id, {
        confirmTitle: "Eliminar entrada",
        confirmText: "¿Estás seguro de que deseas eliminar esta entrada?",
        successTitle: "Entrada eliminada",
        successText: "Entrada eliminada correctamente",
        sinDatosText: "No se encontraron los datos de esta entrada",
      }),
  },
  {
    selector: ".btn-eliminar-historial-venta",
    obtenerId: (btn) => btn.dataset.ventaId,
    ejecutar: (id) =>
      eliminarVentaPorId(id, {
        confirmTitle: "Eliminar venta",
        confirmText: "¿Estás seguro de que deseas eliminar esta venta?",
        successTitle: "Venta eliminada",
        successText: "Venta eliminada correctamente",
        sinDatosText: "No se encontraron los datos de esta venta",
      }),
  },
  {
    selector: ".btn-eliminar-salida",
    obtenerId: (btn) => btn.dataset.ventaId,
    ejecutar: (id) =>
      eliminarVentaPorId(id, {
        confirmTitle: "Eliminar salida",
        confirmText: "¿Estás seguro de que deseas eliminar esta salida?",
        successTitle: "Salida eliminada",
        successText: "Salida eliminada correctamente",
        sinDatosText: "No se encontraron los datos de esta salida",
      }),
  },
];

document.addEventListener("click", function (e) {
  const accion = eliminacionesMovimientos.find((item) => e.target.closest(item.selector));
  if (!accion) return;
  const btn = e.target.closest(accion.selector);
  const id = accion.obtenerId(btn);
  if (!id) return;
  accion.ejecutar(id);
});

// Captura clicks en elementos con data-action (migración de handlers inline)
document.addEventListener("click", function (e) {
  const btn = e.target.closest('[data-action="cambiar-material"]');
  if (!btn) return;
  e.preventDefault();
  if (typeof globalThis.cambiarMaterial === "function") {
    try {
      globalThis.cambiarMaterial();
    } catch (err) {
      console.error("Error ejecutando cambiarMaterial:", err);
    }
  }
});

(function () {
  console.log("Script inline de movimientos ejecutándose...");

  function mostrarEstadoBusquedaMov(state) {
    let estadoEl = document.getElementById("estadoBusquedaMov");
    if (!estadoEl) return;
    if (state === "idle") {
      estadoEl.innerHTML =
        '<i class="bi bi-search display-6 d-block mb-2"></i><p class="mb-0">Buscando materiales...</p>';
      estadoEl.style.display = "";
    } else if (state === "loading") {
      estadoEl.innerHTML =
        '<div class="d-flex flex-column align-items-center"><div class="spinner-border text-primary mb-3" role="status"></div><p class="mb-0">Buscando materiales...</p></div>';
      estadoEl.style.display = "";
    } else if (state === "error") {
      estadoEl.innerHTML =
        '<div class="alert alert-danger mb-0" role="alert"><i class="bi bi-exclamation-octagon me-2"></i>Error de búsqueda</div>';
      estadoEl.style.display = "";
    } else if (state === "hidden") {
      estadoEl.style.display = "none";
    }
  }

  function construirHtmlExitoMovimiento(titulo, campos) {
    const filas = campos
      .map(
        (campo) => `
          <tr>
            <td class="text-muted fw-semibold text-start py-2">${escaparHtml(campo.etiqueta)}</td>
            <td class="text-dark text-end py-2">${escaparHtml(campo.valor)}</td>
          </tr>`,
      )
      .join("");

    return `
      <div class="text-start">
        <p class="mb-3">${escaparHtml(titulo)}</p>
        <div class="table-responsive">
          <table class="table table-sm align-middle mb-0">
            <tbody>${filas}</tbody>
          </table>
        </div>
      </div>`;
  }

  globalThis.mostrarSwalMensajeMovimiento =
    function mostrarSwalMensajeMovimiento({
      icon = "info",
      title = "Aviso",
      text = "",
      html = "",
      confirmButtonText = "Cerrar",
      onClose,
    } = {}) {
      if (typeof Swal === "undefined") {
        alert(text ? `${title}\n\n${text}` : title);
        if (typeof onClose === "function") onClose();
        return;
      }

      Swal.fire({
        icon,
        title,
        text: html ? undefined : text,
        html: html || undefined,
        confirmButtonText,
        allowOutsideClick: false,
        allowEscapeKey: false,
      }).then(() => {
        if (typeof onClose === "function") onClose();
      });
    };

  globalThis.confirmarSwalMovimiento = function confirmarSwalMovimiento({
    title = "Confirmar acción",
    text = "",
    confirmButtonText = "Sí, continuar",
    cancelButtonText = "Cancelar",
  } = {}) {
    if (typeof Swal === "undefined") {
      return Promise.resolve(confirm(text || title));
    }

    return Swal.fire({
      icon: "question",
      title,
      text,
      showCancelButton: true,
      confirmButtonText,
      cancelButtonText,
      reverseButtons: true,
      allowOutsideClick: false,
      allowEscapeKey: false,
    }).then((result) => result.isConfirmed);
  };

  globalThis.mostrarSwalExitoMovimiento = function mostrarSwalExitoMovimiento(
    tipo,
    data,
    onClose,
  ) {
    if (typeof Swal === "undefined") {
      const resumen = [
        `${tipo} registrada correctamente`,
        `Material: ${data.material || "-"}`,
        `Cantidad: ${data.cantidad || "-"}`,
        `Fecha: ${formatearFechaHora(data.fecha)}`,
        `${tipo === "Compra" ? "Precio compra" : "Precio venta"}: $${formatearMoneda(data.precio)}`,
        `Total: $${formatearMoneda(data.total)}`,
        `Observaciones: ${data.observaciones || "-"}`,
        ...(tipo === "Compra"
          ? []
          : [`Centro de acopio: ${data.centroAcopio || "-"}`]),
        `ID registro: ${data.idRegistro || "-"}`,
      ].join("\n");

      alert(resumen);
      if (typeof onClose === "function") onClose();
      return;
    }

    const esCompra = tipo === "Compra";
    const titulo = esCompra
      ? "Compra registrada correctamente"
      : "Venta registrada correctamente";
    const html = construirHtmlExitoMovimiento(titulo, [
      { etiqueta: "Material", valor: data.material || "-" },
      { etiqueta: "Cantidad", valor: data.cantidad || "-" },
      { etiqueta: "Fecha", valor: formatearFechaHora(data.fecha) },
      {
        etiqueta: esCompra ? "Precio compra" : "Precio venta",
        valor: "$" + formatearMoneda(data.precio),
      },
      { etiqueta: "Total", valor: "$" + formatearMoneda(data.total) },
      { etiqueta: "Observaciones", valor: data.observaciones || "-" },
      ...(esCompra
        ? []
        : [{ etiqueta: "Centro de acopio", valor: data.centroAcopio || "-" }]),
      { etiqueta: "ID registro", valor: data.idRegistro || "-" },
    ]);

    Swal.fire({
      icon: "success",
      title: titulo,
      html,
      confirmButtonText: "Cerrar",
      allowOutsideClick: false,
      allowEscapeKey: false,
      customClass: {
        popup: "swal2-movimientos-success",
      },
    }).then(() => {
      if (typeof onClose === "function") onClose();
    });
  };

  // Esperar a que jQuery y Select2 estén listos
  function inicializarSelect2() {
    let btnLimpiarBusqueda = document.getElementById("btnLimpiarBusquedaMov");
    if (btnLimpiarBusqueda) {
      btnLimpiarBusqueda.addEventListener("click", function () {
        let inputBusqueda = document.getElementById(
          "buscarMaterialMovimientos",
        );
        if (inputBusqueda) {
          $(inputBusqueda).val(null).trigger("change");
        }
        $("#selectCategoriaMov").val("").trigger("change");
        $("#selectTipoMov").val("").trigger("change");
        let resultadosDiv = document.getElementById("resultadosBusquedaMov");
        if (resultadosDiv) resultadosDiv.innerHTML = "";
        let seccionBusquedaMaterial = document.getElementById(
          "seccionBusquedaMaterial",
        );
        if (seccionBusquedaMaterial) seccionBusquedaMaterial.classList.remove("d-none");
        let formEntradaContainer = document.getElementById(
          "formEntradaContainer",
        );
        let formSalidaContainer = document.getElementById(
          "formSalidaContainer",
        );
        if (formEntradaContainer) formEntradaContainer.classList.add("d-none");
        if (formSalidaContainer) formSalidaContainer.classList.add("d-none");
        let collapseEntradas = document.getElementById("collapseEntradas");
        let collapseSalidas = document.getElementById("collapseSalidas");
        if (collapseEntradas) {
          collapseEntradas.classList.remove("show");
          collapseEntradas.setAttribute("aria-expanded", "false");
          let buttonEntradas = document.querySelector(
            '[data-bs-target="#collapseEntradas"]',
          );
          if (buttonEntradas) buttonEntradas.classList.add("collapsed");
        }
        if (collapseSalidas) {
          collapseSalidas.classList.remove("show");
          collapseSalidas.setAttribute("aria-expanded", "false");
          let buttonSalidas = document.querySelector(
            '[data-bs-target="#collapseSalidas"]',
          );
          if (buttonSalidas) buttonSalidas.classList.add("collapsed");
        }
        mostrarEstadoBusquedaMov("idle");
      });
    }
    if ($ === undefined || $.fn?.select2 === undefined) {
      setTimeout(inicializarSelect2, 100);
      return;
    }

    const puntoEcaSection = document.querySelector("section[data-usuario-id]");
    const puntoEcaId = puntoEcaSection?.dataset.puntoEcaId;

    const inputBusqueda = document.getElementById("buscarMaterialMovimientos");

    function aplicarCamposMaterial(prefijo, campos) {
      [
        ["MaterialSeleccionado", campos.nombre, { dispararChange: true }],
        ["MaterialId", campos.materialId, { dispararChange: true }],
        ["InventarioId", campos.inventarioId, { dispararChange: true }],
        ["MaterialTipo", campos.tipo, { dispararChange: true }],
        ["MaterialCategoria", campos.categoria, { dispararChange: true }],
        ["MaterialDescripcion", campos.descripcion, { dispararChange: true }],
        ["MaterialUnidad", campos.unidad, { dispararChange: true }],
        ["StockActual", formatearNumeroCampo(campos.stockActual), { dispararChange: true }],
        ["CapacidadMaxima", formatearNumeroCampo(campos.capacidadMaxima), { dispararChange: true }],
        ["PrecioCompra", formatearNumeroCampo(campos.precioCompra), { dispararChange: true, dispararInput: true }],
        ["PrecioVenta", formatearNumeroCampo(campos.precioVenta), { dispararChange: true, dispararInput: true }],
      ].forEach(([sufijo, valor, opciones]) => {
        establecerValorCampo(
          document.getElementById(prefijo + sufijo),
          valor,
          opciones,
        );
      });
    }

    function aplicarMaterialEnFormulario(material, omitirFetch = false) {
      if (!material) return;

      globalThis.lastMaterialSeleccionado = material;

      const campos = prepararCamposMaterial(material);

      establecerValorCampo(
        document.getElementById("entradaFecha"),
        obtenerFechaHoraActual(),
      );
      establecerValorCampo(
        document.getElementById("salidaFecha"),
        obtenerFechaHoraActual(),
      );

      aplicarCamposMaterial("entrada", campos);
      aplicarCamposMaterial("salida", campos);

      const tieneInventario = Boolean(campos.inventarioId);
      const tieneDatosInventario = [
        campos.stockActual,
        campos.capacidadMaxima,
        campos.precioCompra,
        campos.precioVenta,
      ].some((valor) => valor !== null && valor !== undefined);

      if (
        omitirFetch ||
        tieneInventario ||
        tieneDatosInventario ||
        !puntoEcaId
      ) {
        return;
      }

      const params = new URLSearchParams({
        puntoId: puntoEcaId,
        texto: campos.nombre,
      });
      const url =
        "/punto-eca/materiales/inventario/" +
        (params.toString() ? "?" + params.toString() : "");

      fetch(url, {
        method: "GET",
        headers: { Accept: "application/json" },
      })
        .then((res) => res.json())
        .then((data) => {
          if (!Array.isArray(data) || data.length === 0) {
            return;
          }

          const encontrado = buscarMaterialEnInventario(data, campos);

          aplicarMaterialEnFormulario(
            { ...material, ...(encontrado || data[0]) },
            true,
          );
        })
        .catch((error) => {
          console.error("Error al cargar inventario del material:", error);
        });
    }

    function construirDtoMaterialSeleccionado(dataset) {
      return {
        materialId: dataset.materialId || "",
        inventarioId:
          dataset.inventarioId ||
          dataset.inventario_id ||
          dataset.inventarioID ||
          dataset.inventario ||
          "",
        nmbMaterial: dataset.nombre || "",
        nmbTipo: dataset.tipo || "",
        nmbCategoria: dataset.categoria || "",
        dscMaterial: dataset.descripcion || "",
        unidadMedida: dataset.unidad || null,
        stockActual:
          dataset.stockActual !== undefined && dataset.stockActual !== ""
            ? Number.parseFloat(dataset.stockActual)
            : null,
        capacidadMaxima:
          dataset.capacidadMaxima !== undefined && dataset.capacidadMaxima !== ""
            ? Number.parseFloat(dataset.capacidadMaxima)
            : null,
        precioCompra:
          dataset.precioCompra !== undefined && dataset.precioCompra !== ""
            ? Number.parseFloat(dataset.precioCompra)
            : null,
        precioVenta:
          dataset.precioVenta !== undefined && dataset.precioVenta !== ""
            ? Number.parseFloat(dataset.precioVenta)
            : null,
      };
    }

      function mostrarPanelMaterialSeleccionado() {
        let formEntradaContainer = document.getElementById("formEntradaContainer");
        let formSalidaContainer = document.getElementById("formSalidaContainer");
        if (formEntradaContainer) formEntradaContainer.classList.remove("d-none");
        if (formSalidaContainer) formSalidaContainer.classList.remove("d-none");

        let seccionBusquedaMaterial = document.getElementById(
          "seccionBusquedaMaterial",
        );
        if (seccionBusquedaMaterial) seccionBusquedaMaterial.classList.add("d-none");

        let collapseEntradas = document.getElementById("collapseEntradas");
        let collapseSalidas = document.getElementById("collapseSalidas");
        if (collapseEntradas) {
          collapseEntradas.classList.add("show");
          collapseEntradas.setAttribute("aria-expanded", "true");
          let buttonEntradas = document.querySelector(
            '[data-bs-target="#collapseEntradas"]',
          );
          if (buttonEntradas) buttonEntradas.classList.remove("collapsed");
        }
        if (collapseSalidas) {
          collapseSalidas.classList.add("show");
          collapseSalidas.setAttribute("aria-expanded", "true");
          let buttonSalidas = document.querySelector(
            '[data-bs-target="#collapseSalidas"]',
          );
          if (buttonSalidas) buttonSalidas.classList.remove("collapsed");
        }

        triggerEventsCampo(document.getElementById("entradaMaterialSeleccionado"));
        triggerEventsCampo(document.getElementById("entradaMaterialId"));
        triggerEventsCampo(document.getElementById("salidaMaterialSeleccionado"));
        triggerEventsCampo(document.getElementById("salidaMaterialId"));
      }

    function manejarSeleccionResultadoMaterial(e) {
      e.preventDefault();

      const item = e.currentTarget;
      const dto = construirDtoMaterialSeleccionado(item.dataset);
      aplicarMaterialEnFormulario(dto);

      const modalInstance = bootstrap.Modal.getInstance(
        document.getElementById("buscarMaterialMovimientosModal"),
      );
      if (modalInstance) modalInstance.hide();

      const formEntradaContainer = document.getElementById("formEntradaContainer");
      mostrarPanelMaterialSeleccionado();

      if (
        formEntradaContainer &&
        typeof formEntradaContainer.scrollIntoView === "function"
      ) {
        formEntradaContainer.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }

    // INICIALIZAR SELECT2 EN BUSCAR MATERIAL (AJAX)
    let $buscarMaterial = $(inputBusqueda);
    if ($buscarMaterial.length) {
      let endpoint = "/punto-eca/materiales/inventario";

      $buscarMaterial.select2({
        theme: "bootstrap4",
        width: "100%",
        placeholder: "Nombre, código, categoría...",
        minimumInputLength: 0,
        allowClear: true,
        ajax: {
          url: endpoint,
          dataType: "json",
          delay: 300,
          data: function (params) {
            let searchTerm = params.term || "";
            let categoria = $("#selectCategoriaMov").val() || "";
            let tipo = $("#selectTipoMov").val() || "";
            let requestData = { texto: searchTerm, puntoId: puntoEcaId };
            if (categoria) requestData.categoria = categoria;
            if (tipo) requestData.tipo = tipo;
            return requestData;
          },
          processResults: function (data) {
            if (data.error) return { results: [] };
            if (!Array.isArray(data)) data = [];
            data = data.slice().reverse();
            let results = data.map(function (m) {
              return {
                id: m.materialId || m.id || "",
                text: m.nmbMaterial || m.nombre || "Material sin nombre",
                imagenUrl: m.imagenUrl || "/imagenes/materiales.png",
                nmbTipo: m.nmbTipo || "",
                nmbCategoria: m.nmbCategoria || "",
                data: m,
              };
            });
            return { results: results };
          },
          error: function (xhr, status, error) {
            console.error("Error AJAX:", error);
          },
          cache: false,
        },
        templateResult: function (data) {
          if (data.loading) return data.text;
          if (!data.id) return data.text;
          let imagenUrl = data.imagenUrl || "/imagenes/materiales.png";
          let nmbTipo = data.nmbTipo || "";
          let nmbCategoria = data.nmbCategoria || "";
          let $state = $(
            '<span class="select2-state"><img alt="imagen material" class="img-material-select2" style="width: 24px; height: 24px; margin-right: 8px; border-radius: 4px; object-fit: cover;" /> ' +
              '<span class="state-text"></span><small class="state-meta" style="margin-left: 4px; color: #999; font-size: 0.85em;"></small></span>',
          );
          $state.find(".state-text").text(data.text || "Material sin nombre");
          $state.find("img").attr("src", imagenUrl);
          if (nmbTipo || nmbCategoria) {
            let metaText = [];
            if (nmbTipo) metaText.push(nmbTipo);
            if (nmbCategoria) metaText.push(nmbCategoria);
            $state.find(".state-meta").text("(" + metaText.join(" • ") + ")");
          }
          return $state;
        },
        templateSelection: function (data) {
          if (!data.id) return data.text;
          return data.text;
        },
      });
      function applyMaterialToForms(m) {
        aplicarMaterialEnFormulario(m);
      }

      $buscarMaterial.on("select2:opening", function () {
        setTimeout(function () {
          let searchInput = $(".select2-search__field");
          if (searchInput && searchInput.length > 0) {
            searchInput.trigger("input");
          }
        }, 100);
      });

      $buscarMaterial.on("select2:select", function (e) {
        try {
          let data = e.params.data || {};
          let dto = data.data || data;
          applyMaterialToForms(dto);
          mostrarPanelMaterialSeleccionado();

          const formEntradaContainer = document.getElementById(
            "formEntradaContainer",
          );
          if (formEntradaContainer && typeof formEntradaContainer.scrollIntoView === "function") {
            formEntradaContainer.scrollIntoView({
              behavior: "smooth",
              block: "center",
            });
          }
        } catch (err) {
          console.error("Error al procesar selección de material:", err);
        }
      });
    }

    // INICIALIZAR SELECT2 EN CATEGORÍA
    let $selectCategoria = $("#selectCategoriaMov");
    if ($selectCategoria.length) {
      $selectCategoria.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona una categoría...",
        minimumInputLength: 0,
      });
      $selectCategoria.on("select2:select", function () {
        buscarMateriales();
      });
    }

    // INICIALIZAR SELECT2 EN TIPO
    let $selectTipo = $("#selectTipoMov");
    if ($selectTipo.length) {
      $selectTipo.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona un tipo...",
        minimumInputLength: 0,
      });
      $selectTipo.on("select2:select", function () {
        buscarMateriales();
      });
    }

    // INICIALIZAR SELECT2 EN CENTRO DE ACOPIO
    let $selectCentroAcopio = $("#salidaCentroAcopio");
    if ($selectCentroAcopio.length) {
      $selectCentroAcopio.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona un centro...",
        minimumInputLength: 0,
      });
    }

    async function buscarMateriales() {
      const texto = $buscarMaterial?.val() || "";
      const categoria = $("#selectCategoriaMov").val() || "";
      const tipo = $("#selectTipoMov").val() || "";

      let modalBuscarMaterial = document.getElementById(
        "buscarMaterialMovimientosModal",
      );
      if (!modalBuscarMaterial) return;

      let estadoBusquedaEl = document.getElementById("estadoBusquedaMov");
      if (estadoBusquedaEl) {
        estadoBusquedaEl.innerHTML =
          '<div class="d-flex flex-column align-items-center"><div class="spinner-border text-primary mb-3" role="status"></div><p class="mb-0">Buscando materiales...</p></div>';
      }

      let listaResultadosEl = document.getElementById("resultadosBusquedaMov");
      if (listaResultadosEl) listaResultadosEl.innerHTML = "";

      let modal = new bootstrap.Modal(modalBuscarMaterial);
      modal.show();

      let endpoint = "/punto-eca/materiales/inventario/";
      let params = new URLSearchParams();

      if (texto) params.append("texto", texto);
      if (categoria) params.append("categoria", categoria);
      if (tipo) params.append("tipo", tipo);
      if (puntoEcaId) params.append("puntoId", puntoEcaId);

      let url = endpoint + (params.toString() ? "?" + params.toString() : "");

      try {
        const res = await fetch(url, {
          method: "GET",
          headers: { Accept: "application/json" },
        });
        const data = await res.json();

        if (!res.ok) {
          let mensajeError = data?.mensaje || data?.message || "Error desconocido";
          if (estadoBusquedaEl) {
            estadoBusquedaEl.innerHTML =
              '<div class="alert alert-warning mb-0" role="alert"><i class="bi bi-exclamation-triangle me-2"></i>' +
              mensajeError +
              "</div>";
          }
          return;
        }

        renderResultadosBusquedaMov(Array.isArray(data) ? data : []);
      } catch (error) {
        manejarErrorBusquedaMateriales(estadoBusquedaEl, error);
      }
    }

    function renderResultadosBusquedaMov(materiales) {
      let listaResultadosEl = document.getElementById("resultadosBusquedaMov");
      let estadoBusquedaEl = document.getElementById("estadoBusquedaMov");

      if (!listaResultadosEl) return;
      listaResultadosEl.innerHTML = "";

      if (!materiales || materiales.length === 0) {
        listaResultadosEl.innerHTML =
          '<div class="list-group-item text-muted text-center py-4">Sin resultados disponibles</div>';
        if (estadoBusquedaEl) {
          estadoBusquedaEl.innerHTML =
            '<i class="bi bi-search display-6 d-block mb-2"></i><p class="mb-0">No se encontraron materiales con estos filtros</p>';
        }
        return;
      }

      materiales.forEach((material) => {
        let item = document.createElement("button");
        item.type = "button";
        item.className =
          "list-group-item list-group-item-action resultado-material-item d-flex align-items-start gap-3";

        let unidadVal = "";
        if (
          material.unidadMedida !== undefined &&
          material.unidadMedida !== null
        ) {
          if (typeof material.unidadMedida === "string") {
            unidadVal = material.unidadMedida;
          } else if (typeof material.unidadMedida === "object") {
            unidadVal =
              material.unidadMedida.nombre || material.unidadMedida.clave || "";
          } else {
            unidadVal = String(material.unidadMedida || "");
          }
        }

        item.dataset.materialId = material.materialId || "";
        item.dataset.inventarioId =
          material.inventarioId || material.inventario_id || material.inventarioID || "";
        item.dataset.nombre = material.nmbMaterial || "";
        item.dataset.descripcion = material.dscMaterial || "";
        item.dataset.tipo = material.nmbTipo || "";
        item.dataset.categoria = material.nmbCategoria || "";
        item.dataset.unidad = unidadVal;
        item.dataset.stockActual = numeroComoTexto(material.stockActual);
        item.dataset.capacidadMaxima = numeroComoTexto(material.capacidadMaxima);
        item.dataset.precioCompra = numeroComoTexto(material.precioCompra);
        item.dataset.precioVenta = numeroComoTexto(material.precioVenta);

        let img = document.createElement("img");
        img.src = material.imagenUrl || "/imagenes/materiales.png";
        img.alt = material.nmbMaterial || "Material";
        img.className = "rounded";
        img.style.width = "64px";
        img.style.height = "64px";
        img.style.objectFit = "cover";
        img.style.flexShrink = "0";

        let content = document.createElement("div");
        content.className = "flex-grow-1 text-start";

        let title = document.createElement("div");
        title.className = "fw-semibold";
        title.textContent = material.nmbMaterial || "Material sin nombre";

        let desc = document.createElement("small");
        desc.className = "text-muted d-block mb-2";
        desc.textContent = material.dscMaterial || "Sin descripción";

        let badges = document.createElement("div");
        let tipoBadge = document.createElement("span");
        tipoBadge.className = "badge bg-primary me-1";
        tipoBadge.textContent = material.nmbTipo || "Tipo";
        let catBadge = document.createElement("span");
        catBadge.className = "badge bg-secondary";
        catBadge.textContent = material.nmbCategoria || "Categoría";

        badges.appendChild(tipoBadge);
        badges.appendChild(catBadge);
        content.appendChild(title);
        content.appendChild(desc);
        content.appendChild(badges);

        let actionBadge = document.createElement("span");
        actionBadge.className =
          "badge bg-primary rounded-pill align-self-start";
        actionBadge.textContent = "Seleccionar";

        item.appendChild(img);
        item.appendChild(content);
        item.appendChild(actionBadge);
        listaResultadosEl.appendChild(item);
      });

      if (estadoBusquedaEl) {
        estadoBusquedaEl.style.display = "none";
      }

      document.querySelectorAll(".resultado-material-item").forEach((item) => {
        item.addEventListener("click", manejarSeleccionResultadoMaterial);
      });
    }

    mostrarEstadoBusquedaMov("idle");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSelect2);
  } else {
    inicializarSelect2();
  }
})();

// ========================================================
// INICIALIZAR SELECT2 EN FILTROS DE COMPRA Y VENTA
// ========================================================
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(function () {
    const $filtroMaterialCompra = $("#filtroCompraMaterial");
    const $filtroCategoriaCompra = $("#filtroCompraCategoria");
    const $filtroTipoCompra = $("#filtroCompraTipo");

    if ($filtroMaterialCompra.length) {
      poblarSelectConValores(
        $filtroMaterialCompra,
        obtenerValoresUnicos(globalThis.ENTRADAS_INICIALES, (entrada) =>
          entrada.nombreMaterial,
        ),
        "Selecciona material...",
        { minimumInputLength: 0 },
      );
    }

    if ($filtroCategoriaCompra.length) {
      poblarSelectConValores(
        $filtroCategoriaCompra,
        obtenerValoresUnicos(globalThis.ENTRADAS_INICIALES, (entrada) =>
          entrada.nombreCategoria,
        ),
        "Selecciona categoría...",
      );
    }

    if ($filtroTipoCompra.length) {
      poblarSelectConValores(
        $filtroTipoCompra,
        obtenerValoresUnicos(globalThis.ENTRADAS_INICIALES, (entrada) =>
          entrada.nombreTipo,
        ),
        "Selecciona tipo...",
      );
    }
  }, 300);

  setTimeout(function () {
    const $filtroMaterialVenta = $("#filtroVentaMaterial");
    const $filtroCategoriaVenta = $("#filtroVentaCategoria");
    const $filtroTipoVenta = $("#filtroVentaTipo");
    const $filtroCentroVenta = $("#filtroVentaCentro");

    if ($filtroMaterialVenta.length) {
      poblarSelectConValores(
        $filtroMaterialVenta,
        obtenerValoresUnicos(globalThis.SALIDAS_INICIALES, (salida) =>
          salida.nombreMaterial,
        ),
        "Selecciona material...",
      );
    }

    if ($filtroCategoriaVenta.length) {
      poblarSelectConValores(
        $filtroCategoriaVenta,
        obtenerValoresUnicos(globalThis.SALIDAS_INICIALES, (salida) =>
          salida.nombreCategoria,
        ),
        "Selecciona categoría...",
      );
    }

    if ($filtroTipoVenta.length) {
      poblarSelectConValores(
        $filtroTipoVenta,
        obtenerValoresUnicos(globalThis.SALIDAS_INICIALES, (salida) =>
          salida.nombreTipo,
        ),
        "Selecciona tipo...",
      );
    }

    if ($filtroCentroVenta.length) {
      const centros = Array.isArray(globalThis.CENTROS)
        ? globalThis.CENTROS
        : Object.values(globalThis.CENTROS || {});
      poblarSelectConValores(
        $filtroCentroVenta,
        obtenerValoresUnicos(centros, (centro) =>
          centro.nombre || centro.nmbCentro || centro.nmbCentroAcopio || "",
        ),
        "Selecciona centro de acopio...",
      );
    }
  }, 300);

  setTimeout(function () {
    const $filtroHistorialMaterial = $("#filtroHistorialMaterial");
    const $filtroHistorialCategoria = $("#filtroHistorialCategoria");
    const $filtroHistorialTipo = $("#filtroHistorialTipo");
    const $filtroHistorialCentroAcopio = $("#filtroHistorialCentroAcopio");

    if ($filtroHistorialMaterial.length) {
      poblarSelectConValores(
        $filtroHistorialMaterial,
        obtenerValoresUnicos(
          [...(globalThis.HISTORIAL_COMPRAS || []), ...(globalThis.HISTORIAL_VENTAS || [])],
          (mov) => mov.nombreMaterial,
        ),
        "Selecciona material...",
        { minimumInputLength: 0 },
      );
    }

    if ($filtroHistorialCategoria.length) {
      poblarSelectConValores(
        $filtroHistorialCategoria,
        obtenerValoresUnicos(
          [...(globalThis.HISTORIAL_COMPRAS || []), ...(globalThis.HISTORIAL_VENTAS || [])],
          (mov) => mov.nombreCategoria,
        ),
        "Selecciona categoría...",
      );
    }

    if ($filtroHistorialTipo.length) {
      poblarSelectConValores(
        $filtroHistorialTipo,
        obtenerValoresUnicos(
          [...(globalThis.HISTORIAL_COMPRAS || []), ...(globalThis.HISTORIAL_VENTAS || [])],
          (mov) => mov.nombreTipo,
        ),
        "Selecciona tipo...",
      );
    }

    if ($filtroHistorialCentroAcopio.length) {
      const centros = Array.isArray(globalThis.CENTROS)
        ? globalThis.CENTROS
        : Object.values(globalThis.CENTROS || {});
      poblarSelectConValores(
        $filtroHistorialCentroAcopio,
        obtenerValoresUnicos(centros, (c) =>
          c.nombre || c.nmbCentro || c.nmbCentroAcopio || "",
        ),
        "Selecciona centro de acopio...",
      );
    }
  }, 300);

  const btnFiltrarCompra = document.getElementById("btnFiltrarCompra");
  const btnLimpiarCompra = document.getElementById("btnLimpiarCompra");
  const btnFiltrarVenta = document.getElementById("btnFiltrarVenta");
  const btnLimpiarVenta = document.getElementById("btnLimpiarVenta");

  if (btnFiltrarCompra) {
    btnFiltrarCompra.addEventListener("click", function () {
      const material = $("#filtroCompraMaterial").val() || "";
      const categoria = $("#filtroCompraCategoria").val() || "";
      const tipo = $("#filtroCompraTipo").val() || "";
      const fechaDesde =
        document.getElementById("filtroCompraFechaDesde")?.value || "";
      const fechaHasta =
        document.getElementById("filtroCompraFechaHasta")?.value || "";

      const entradasData = globalThis.ENTRADAS_INICIALES || [];
      const entradasFiltradas = entradasData.filter((entrada) => {
        const cumpleMaterial =
          !material ||
          (entrada.nombreMaterial || "")
            .toLowerCase()
            .includes(material.toLowerCase());
        const cumpleCategoria =
          !categoria || (entrada.nombreCategoria || "") === categoria;
        const cumpleTipo = !tipo || (entrada.nombreTipo || "") === tipo;
        const cumpleFechaDesde =
          !fechaDesde ||
          new Date(entrada.fechaCompra).toISOString().split("T")[0] >=
            fechaDesde;
        const cumpleFechaHasta =
          !fechaHasta ||
          new Date(entrada.fechaCompra).toISOString().split("T")[0] <=
            fechaHasta;
        return (
          cumpleMaterial &&
          cumpleCategoria &&
          cumpleTipo &&
          cumpleFechaDesde &&
          cumpleFechaHasta
        );
      });
      globalThis.ENTRADAS_INICIALES = entradasFiltradas;
      renderizarEntradas();
    });
  }

  if (btnLimpiarCompra) {
    btnLimpiarCompra.addEventListener("click", function () {
      location.reload();
    });
  }

  if (btnFiltrarVenta) {
    btnFiltrarVenta.addEventListener("click", function () {
      const material = $("#filtroVentaMaterial").val() || "";
      const categoria = $("#filtroVentaCategoria").val() || "";
      const tipo = $("#filtroVentaTipo").val() || "";
      const centroAcopio = $("#filtroVentaCentro").val() || "";
      const fechaDesde =
        document.getElementById("filtroVentaFechaDesde")?.value || "";
      const fechaHasta =
        document.getElementById("filtroVentaFechaHasta")?.value || "";

      const salidasData = globalThis.SALIDAS_INICIALES || [];
      const salidasFiltradas = salidasData.filter((salida) => {
        const cumpleMaterial =
          !material ||
          (salida.nombreMaterial || "")
            .toLowerCase()
            .includes(material.toLowerCase());
        const cumpleCategoria =
          !categoria || (salida.nombreCategoria || "") === categoria;
        const cumpleTipo = !tipo || (salida.nombreTipo || "") === tipo;
        const cumpleCentro =
          !centroAcopio || (salida.nombreCentroAcopio || "") === centroAcopio;
        const cumpleFechaDesde =
          !fechaDesde ||
          new Date(salida.fechaVenta).toISOString().split("T")[0] >= fechaDesde;
        const cumpleFechaHasta =
          !fechaHasta ||
          new Date(salida.fechaVenta).toISOString().split("T")[0] <= fechaHasta;
        return (
          cumpleMaterial &&
          cumpleCategoria &&
          cumpleTipo &&
          cumpleCentro &&
          cumpleFechaDesde &&
          cumpleFechaHasta
        );
      });
      globalThis.SALIDAS_INICIALES = salidasFiltradas;
      renderizarSalidas();
    });
  }

  if (btnLimpiarVenta) {
    btnLimpiarVenta.addEventListener("click", function () {
      location.reload();
    });
  }

  // CARGA INICIAL DE DATOS
  renderizarEntradas();
  renderizarSalidas();
  renderizarHistorial();

  const btnFiltrarHist = document.getElementById("btnFiltrarHistorial");
  const btnLimpiarHist = document.getElementById("btnLimpiarHistorial");
  const inputMaterial = document.getElementById("filtroHistorialMaterial");

  function resetearPaginaHistorialYRender() {
    globalThis.PAGINA_ACTUAL_HISTORIAL = 1;
    renderizarHistorial();
  }

  function limpiarFiltrosHistorial() {
    [
      "#filtroHistorialMaterial",
      "#filtroHistorialCategoria",
      "#filtroHistorialTipo",
    ].forEach((selector) => {
      $(selector).val("").trigger("change");
    });
    document.getElementById("filtroHistorialTipoMovimiento").value = "";
    document.getElementById("filtroHistorialDesde").value = "";
    document.getElementById("filtroHistorialHasta").value = "";
  }

  if (btnFiltrarHist) {
    btnFiltrarHist.addEventListener("click", resetearPaginaHistorialYRender);
  }
  $(
    "#filtroHistorialMaterial, #filtroHistorialCategoria, #filtroHistorialTipo",
  ).on("change", resetearPaginaHistorialYRender);

  if (btnLimpiarHist) {
    btnLimpiarHist.addEventListener("click", function () {
      limpiarFiltrosHistorial();
      renderizarHistorial();
    });
  }
  if (inputMaterial) {
    inputMaterial.addEventListener("change", renderizarHistorial);
  }

  // Función para renderizar entradas
  function renderizarEntradas() {
    const tbody = document.getElementById("tablasEntradasBody");
    if (!tbody) return;
    let entradasData = globalThis.ENTRADAS_INICIALES;
    if (
      typeof entradasData === "object" &&
      !Array.isArray(entradasData) &&
      entradasData !== null
    ) {
      entradasData = Object.values(entradasData);
    }
    if (!Array.isArray(entradasData) || !entradasData) entradasData = [];
    entradasData = entradasData
      .slice()
      .sort((a, b) => toISO(b.fechaCompra) - toISO(a.fechaCompra));

    if (entradasData.length === 0) {
      tbody.innerHTML =
        '<tr class="text-muted text-center"><td colspan="6" class="py-3"><small>Sin registros</small></td></tr>';
      const badge = document.getElementById("badgeEntradasCount");
      if (badge) badge.textContent = "0 registros";
      actualizarPaginacionEntradas(0);
      return;
    }

    const registrosPorPagina = globalThis.REGISTROS_POR_PAGINA || 5;
    const totalPaginas = Math.ceil(entradasData.length / registrosPorPagina);

    if (globalThis.PAGINA_ACTUAL_ENTRADAS > totalPaginas)
      globalThis.PAGINA_ACTUAL_ENTRADAS = totalPaginas;
    if (globalThis.PAGINA_ACTUAL_ENTRADAS < 1)
      globalThis.PAGINA_ACTUAL_ENTRADAS = 1;

    const inicio = (globalThis.PAGINA_ACTUAL_ENTRADAS - 1) * registrosPorPagina;
    const fin = inicio + registrosPorPagina;
    const registrosPagina = entradasData.slice(inicio, fin);

    tbody.innerHTML = registrosPagina.map(generarFilaEntrada).join("");

    const badge = document.getElementById("badgeEntradasCount");
    if (badge) badge.textContent = entradasData.length + " registros";
    actualizarPaginacionEntradas(totalPaginas);
  }

  function actualizarPaginacionEntradas(totalPaginas) {
    actualizarPaginacionGenerica(
      "paginacionEntradas",
      totalPaginas,
      globalThis.PAGINA_ACTUAL_ENTRADAS || 1,
    );
  }
  globalThis.cambiarPaginaEntradas = function (pagina) {
    globalThis.PAGINA_ACTUAL_ENTRADAS = pagina;
    renderizarEntradas();
  };

  // Función para renderizar salidas
  function renderizarSalidas() {
    const tbody = document.getElementById("tablasSalidasBody");
    if (!tbody) return;
    let salidasData = globalThis.SALIDAS_INICIALES || [];
    salidasData = salidasData.sort(
      (a, b) =>
        new Date(b.fechaVenta || 0).getTime() -
        new Date(a.fechaVenta || 0).getTime(),
    );

    if (!salidasData || salidasData.length === 0) {
      tbody.innerHTML =
        '<tr class="text-muted text-center"><td colspan="7" class="py-3"><small>Sin registros</small></td></tr>';
      const badge = document.getElementById("badgeSalidasCount");
      if (badge) badge.textContent = "0 registros";
      actualizarPaginacionSalidas(0);
      return;
    }

    const registrosPorPagina = globalThis.REGISTROS_POR_PAGINA || 5;
    const totalPaginas = Math.ceil(salidasData.length / registrosPorPagina);
    if (globalThis.PAGINA_ACTUAL_SALIDAS > totalPaginas)
      globalThis.PAGINA_ACTUAL_SALIDAS = totalPaginas;
    if (globalThis.PAGINA_ACTUAL_SALIDAS < 1)
      globalThis.PAGINA_ACTUAL_SALIDAS = 1;

    const inicio = (globalThis.PAGINA_ACTUAL_SALIDAS - 1) * registrosPorPagina;
    const fin = inicio + registrosPorPagina;
    const registrosPagina = salidasData.slice(inicio, fin);

    tbody.innerHTML = registrosPagina.map(generarFilaSalida).join("");

    const badge = document.getElementById("badgeSalidasCount");
    if (badge) badge.textContent = salidasData.length + " registros";
    actualizarPaginacionSalidas(totalPaginas);
  }

  function actualizarPaginacionSalidas(totalPaginas) {
    actualizarPaginacionGenerica(
      "paginacionSalidas",
      totalPaginas,
      globalThis.PAGINA_ACTUAL_SALIDAS || 1,
    );
  }
  globalThis.cambiarPaginaSalidas = function (pagina) {
    globalThis.PAGINA_ACTUAL_SALIDAS = pagina;
    renderizarSalidas();
  };

  function renderizarHistorial() {
    const tbody = document.getElementById("tablasHistorialBody");
    if (!tbody) return;

    const compras = (globalThis.HISTORIAL_COMPRAS || []).map((c) => ({
      ...c,
      tipo: "Compra",
      fecha: c.fechaCompra,
      precio: c.precioCompra,
    }));
    const ventas = (globalThis.HISTORIAL_VENTAS || []).map((v) => ({
      ...v,
      tipo: "Venta",
      fecha: v.fechaVenta,
      precio: v.precioVenta,
    }));

    const movimientos = [...compras, ...ventas].sort(
      (a, b) =>
        new Date(b.fecha || 0).getTime() - new Date(a.fecha || 0).getTime(),
    );

    const {
      material,
      categoria,
      tipoMaterial,
      centroAcopio,
      tipoMovimiento,
      fechaDesde,
      fechaHasta,
    } = obtenerFiltrosHistorial();

    const movimientosFiltrados = movimientos.filter((mov) => {
      const cumpleMaterial =
        !material || (mov.nombreMaterial || "") === material;
      const cumpleCategoria =
        !categoria || (mov.nombreCategoria || "") === categoria;
      const cumpleTipo =
        !tipoMaterial || (mov.nombreTipo || "") === tipoMaterial;
      const cumpleCentro =
        !centroAcopio ||
        (mov.tipo === "Venta"
          ? (mov.nombreCentroAcopio || "") === centroAcopio
          : true);
      const cumpleTipoMovimiento =
        !tipoMovimiento ||
        (tipoMovimiento === "compra" && mov.tipo === "Compra") ||
        (tipoMovimiento === "venta" && mov.tipo === "Venta");
      const cumpleFechaDesde =
        !fechaDesde ||
        new Date(mov.fecha).toISOString().split("T")[0] >= fechaDesde;
      const cumpleFechaHasta =
        !fechaHasta ||
        new Date(mov.fecha).toISOString().split("T")[0] <= fechaHasta;
      return (
        cumpleMaterial &&
        cumpleCategoria &&
        cumpleTipo &&
        cumpleCentro &&
        cumpleTipoMovimiento &&
        cumpleFechaDesde &&
        cumpleFechaHasta
      );
    });

    const registrosPorPagina = globalThis.REGISTROS_POR_PAGINA_HISTORIAL || 10;
    const totalPaginas = Math.ceil(
      movimientosFiltrados.length / registrosPorPagina,
    );
    if (globalThis.PAGINA_ACTUAL_HISTORIAL > totalPaginas)
      globalThis.PAGINA_ACTUAL_HISTORIAL = totalPaginas;
    if (globalThis.PAGINA_ACTUAL_HISTORIAL < 1)
      globalThis.PAGINA_ACTUAL_HISTORIAL = 1;

    const inicio =
      (globalThis.PAGINA_ACTUAL_HISTORIAL - 1) * registrosPorPagina;
    const fin = inicio + registrosPorPagina;
    const paginaMovimientos = movimientosFiltrados.slice(inicio, fin);

    if (movimientosFiltrados.length === 0) {
      tbody.innerHTML =
        '<tr class="text-muted text-center"><td colspan="6" class="py-4"><i class="bi bi-inbox"></i><p class="mb-0 mt-2">Sin movimientos registrados</p></td></tr>';
      const badge = document.getElementById("badgeHistorialCount");
      if (badge) badge.textContent = "0 registros";
      actualizarPaginacionHistorial(0);
      return;
    }

    tbody.innerHTML = paginaMovimientos.map(generarFilaHistorial).join("");

    const badge = document.getElementById("badgeHistorialCount");
    if (badge) badge.textContent = movimientosFiltrados.length + " registros";
    actualizarPaginacionHistorial(totalPaginas);
  }

  function actualizarPaginacionHistorial(totalPaginas) {
    actualizarPaginacionGenerica(
      "paginacionHistorial",
      totalPaginas,
      globalThis.PAGINA_ACTUAL_HISTORIAL || 1,
    );
  }
  globalThis.cambiarPaginaHistorial = function (pagina) {
    globalThis.PAGINA_ACTUAL_HISTORIAL = pagina;
    renderizarHistorial();
  };

  globalThis.cambiarMaterial = function () {
    ["entrada", "salida"].forEach((prefix) => {
      [
        "MaterialSeleccionado",
        "MaterialId",
        "InventarioId",
        "MaterialTipo",
        "MaterialCategoria",
        "MaterialDescripcion",
      ].forEach((field) => {
        const el = document.getElementById(prefix + field);
        if (el) el.value = "";
      });
    });
    document
      .querySelectorAll(".alert-success")
      .forEach((alerta) => alerta.remove());
    const formEntradaContainer = document.getElementById(
      "formEntradaContainer",
    );
    const formSalidaContainer = document.getElementById("formSalidaContainer");
    if (formEntradaContainer) formEntradaContainer.classList.add("d-none");
    if (formSalidaContainer) formSalidaContainer.classList.add("d-none");
    const seccionBusquedaMaterial = document.getElementById(
      "seccionBusquedaMaterial",
    );
    if (seccionBusquedaMaterial) seccionBusquedaMaterial.classList.remove("d-none");
  };

  // Actualizar stocks
  function actualizarStock(prefix, op) {
    const stock = Number.parseFloat(
      document.getElementById(prefix + "StockActual")?.value || 0,
    );
    const cantidad = Number.parseFloat(
      document.getElementById(prefix + "Cantidad")?.value || 0,
    );
    const resultante = op === "+" ? stock + cantidad : stock - cantidad;
    const resEl = document.getElementById(
      prefix + (op === "+" ? "StockResultante" : "StockRestante"),
    );
    if (resEl)
      resEl.textContent = Number.isNaN(resultante)
        ? "-"
        : resultante.toFixed(2);
  }
  const entCant = document.getElementById("entradaCantidad"),
    entPrecio = document.getElementById("entradaPrecioCompra"),
    entTotal = document.getElementById("entradaTotalCompra"),
    entStock = document.getElementById("entradaStockActual");

  function actualizarTotalEntrada() {
    const cantidad = Number.parseFloat(entCant?.value || 0);
    const precio = Number.parseFloat(entPrecio?.value || 0);
    const total = cantidad * precio;
    if (entTotal) entTotal.value = Number.isNaN(total) ? "" : total.toFixed(2);
  }

  if (entCant) {
    entCant.addEventListener("input", () => {
      actualizarStock("entrada", "+");
      actualizarTotalEntrada();
    });
  }

  if (entPrecio) {
    entPrecio.addEventListener("input", actualizarTotalEntrada);
  }

  if (entStock) {
    entStock.addEventListener("change", () => actualizarStock("entrada", "+"));
  }

  const salCant = document.getElementById("salidaCantidad"),
    salPrecio = document.getElementById("salidaPrecioVenta"),
    salTotal = document.getElementById("salidaTotalVenta"),
    salStock = document.getElementById("salidaStockActual");

  function actualizarTotalSalida() {
    const cantidad = Number.parseFloat(salCant?.value || 0);
    const precio = Number.parseFloat(salPrecio?.value || 0);
    const total = cantidad * precio;
    if (salTotal) salTotal.value = Number.isNaN(total) ? "" : total.toFixed(2);
  }

  if (salCant) {
    salCant.addEventListener("input", () => {
      actualizarStock("salida", "-");
      actualizarTotalSalida();
    });
  }

  if (salPrecio) {
    salPrecio.addEventListener("input", actualizarTotalSalida);
  }

  if (salStock) {
    salStock.addEventListener("change", () => actualizarStock("salida", "-"));
  }

  globalThis.mostrarFeedbackMovimientos = function (msg, tipo = "success") {
    const div = document.getElementById("movimientosFeedback");
    if (!div) return;
    div.innerHTML = `<div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
            ${msg}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button></div>`;
  };

  globalThis.mostrarErrorMovimientos = function (
    mensaje,
    onClose,
    titulo = "Error",
  ) {
    if (typeof globalThis.mostrarSwalMensajeMovimiento === "function") {
      globalThis.mostrarSwalMensajeMovimiento({
        icon: "error",
        title: titulo,
        text: mensaje,
        onClose,
      });
      return;
    }

    globalThis.mostrarFeedbackMovimientos(mensaje, "danger");
    if (typeof onClose === "function") onClose();
  };

  globalThis.mostrarErrorCampo = function (input, mensaje) {
    limpiarErrorCampo(input);
    input.classList.add("is-invalid");
    const feedbackDiv = document.createElement("div");
    feedbackDiv.className = "invalid-feedback";
    feedbackDiv.textContent = mensaje;
    input.parentNode.insertBefore(feedbackDiv, input.nextSibling);
  };

  globalThis.limpiarErrorCampo = function (input) {
    input.classList.remove("is-invalid");
    const feedbackDiv = input.parentNode.querySelector(".invalid-feedback");
    if (feedbackDiv) {
      feedbackDiv.remove();
    }
  };

  globalThis.validarCampoRequerido = function (
    input,
    mensajeError = "Este campo es requerido",
  ) {
    limpiarErrorCampo(input);

    let esValido = true;
    const valor = input.value.trim();

    if (input.type === "number") {
      if (valor === "" || Number.parseFloat(valor) <= 0) {
        esValido = false;
      }
    } else if (input.type === "select-one" || input.tagName === "SELECT") {
      if (valor === "") {
        esValido = false;
      }
    }

    if (!esValido) {
      mostrarErrorCampo(input, mensajeError);
      return false;
    }

    return true;
  };

  globalThis.validarCantidad = function (input) {
    limpiarErrorCampo(input);

    const valor = input.value.trim();

    if (valor === "") {
      mostrarErrorCampo(input, "Ingrese la cantidad");
      return false;
    }

    const cantidad = Number.parseFloat(valor);

    if (cantidad < 0) {
      mostrarErrorCampo(input, "No se permiten valores negativos");
      return false;
    }

    if (cantidad === 0) {
      mostrarErrorCampo(input, "La cantidad debe ser mayor a 0");
      return false;
    }

    if (Number.isNaN(cantidad)) {
      mostrarErrorCampo(input, "Ingrese una cantidad válida");
      return false;
    }

    return true;
  };

  globalThis.validarCampoFecha = function (
    input,
    mensajeError = "Fecha requerida",
  ) {
    limpiarErrorCampo(input);

    let esValido = true;
    const valor = input.value.trim();

    if (valor === "") {
      esValido = false;
    }

    if (!esValido) {
      mostrarErrorCampo(input, mensajeError);
      return false;
    }

    return true;
  };

  function obtenerDatosFormularioMovimiento(prefijo) {
    return {
      materialSeleccionado: document.getElementById(`${prefijo}MaterialSeleccionado`),
      cantidad: document.getElementById(`${prefijo}Cantidad`),
      fecha: document.getElementById(`${prefijo}Fecha`),
      precio: document.getElementById(
        prefijo === "entrada" ? "entradaPrecioCompra" : "salidaPrecioVenta",
      ),
      inventarioId:
        document.getElementById(`${prefijo}InventarioId`)?.value ||
        globalThis.lastMaterialSeleccionado?.inventarioId ||
        globalThis.lastMaterialSeleccionado?.inventario_id ||
        "",
      materialId: document.getElementById(`${prefijo}MaterialId`)?.value || "",
      observaciones: document.getElementById(`${prefijo}Observaciones`)?.value || "",
      centroAcopio: document.getElementById("salidaCentroAcopio")?.value || "",
      puntoEcaId: document.querySelector("section[data-punto-eca-id]")?.dataset
        .puntoEcaId,
      csrfToken:
        document
          .querySelector('meta[name="csrf-token"]')
          ?.getAttribute("content") || "",
    };
  }

  function construirResumenExitoMovimiento(prefijo, extras = {}) {
    const cantidad = document.getElementById(`${prefijo}Cantidad`)?.value || 0;
    const precio = document.getElementById(
      prefijo === "entrada" ? "entradaPrecioCompra" : "salidaPrecioVenta",
    )?.value || 0;

    return {
      material: document.getElementById(`${prefijo}MaterialSeleccionado`)?.value,
      cantidad,
      fecha: document.getElementById(`${prefijo}Fecha`)?.value,
      precio,
      total: (Number.parseFloat(cantidad) || 0) * (Number.parseFloat(precio) || 0),
      observaciones: document.getElementById(`${prefijo}Observaciones`)?.value,
      ...extras,
    };
  }

  function procesarSubmitEntrada(ev) {
    ev.preventDefault();
    const form = ev.currentTarget;
    const submitBtn = obtenerBotonSubmitFormulario(form);
    establecerEstadoBotonSubmit(submitBtn, true, '<i class="bi bi-check-circle me-2"></i>Guardar Entrada');

    const datosFormulario = obtenerDatosFormularioMovimiento("entrada");
    const { materialSeleccionado, cantidad, fecha, precio, csrfToken } = datosFormulario;

    let esValido = true;

    if (materialSeleccionado?.value.trim() === "") {
      mostrarErrorCampo(materialSeleccionado, "Seleccione un material");
      esValido = false;
    }

    if (!validarCantidad(cantidad)) esValido = false;
    if (!validarCampoFecha(fecha, "Seleccione una fecha")) esValido = false;
    if (!validarCampoRequerido(precio, "Ingrese un precio de compra"))
      esValido = false;

    if (!esValido) {
      establecerEstadoBotonSubmit(
        submitBtn,
        false,
        '<i class="bi bi-check-circle me-2"></i>Guardar Entrada',
      );
      return;
    }

    const data = {
      inventarioId: datosFormulario.inventarioId,
      materialId: datosFormulario.materialId,
      cantidad: cantidad?.value,
      fechaCompra: fecha?.value,
      precioCompra: precio?.value,
      observaciones: datosFormulario.observaciones,
      puntoEcaId: datosFormulario.puntoEcaId,
    };

    fetch(`/punto-eca/movimientos/registrar-compra/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    })
      .then((res) => res.json())
      .then((resp) => {
        if (resp.error) {
          globalThis.mostrarErrorMovimientos(
            resp.mensaje || "Error: operación no realizada",
            () => {
              restablecerSubmitMovimiento(
                submitBtn,
                '<i class="bi bi-check-circle me-2"></i>Guardar Entrada',
              );
            },
            "No se pudo registrar la compra",
          );
        } else {
          globalThis.mostrarSwalExitoMovimiento(
            "Compra",
            construirResumenExitoMovimiento("entrada", {
              idRegistro:
                resp.compra_id ||
                resp.compraId ||
                resp.id ||
                resp.registroId ||
                "-",
            }),
            () => globalThis.location.reload(),
          );
        }
      })
      .catch((err) => {
        globalThis.mostrarErrorMovimientos(
          "Error al conectar con el backend: " + err,
          () => {
            restablecerSubmitMovimiento(
              submitBtn,
              '<i class="bi bi-check-circle me-2"></i>Guardar Entrada',
            );
          },
          "Error de conexión",
        );
      })
      .finally(() => {
        if (document.querySelectorAll(".swal2-container").length === 0) {
          establecerEstadoBotonSubmit(
            submitBtn,
            false,
            '<i class="bi bi-check-circle me-2"></i>Guardar Entrada',
          );
        }
      });
  }

  const formEntrada = document.getElementById("formEntrada");
  if (formEntrada) {
    formEntrada.addEventListener("submit", procesarSubmitEntrada);
  }

  function procesarSubmitSalida(ev) {
    ev.preventDefault();
    const form = ev.currentTarget;
    if (form.dataset.enviando === "1") return;
    form.dataset.enviando = "1";

    const submitBtn = obtenerBotonSubmitFormulario(form);
    establecerEstadoBotonSubmit(submitBtn, true, '<i class="bi bi-check-circle me-2"></i>Guardar Salida');

    const datosFormulario = obtenerDatosFormularioMovimiento("salida");
    const { materialSeleccionado, cantidad, fecha, precio, csrfToken, centroAcopio } = datosFormulario;

    let esValido = true;

    if (materialSeleccionado?.value.trim() === "") {
      mostrarErrorCampo(materialSeleccionado, "Seleccione un material");
      esValido = false;
    }

    if (!validarCantidad(cantidad)) esValido = false;
    if (!validarCampoFecha(fecha, "Seleccione una fecha")) esValido = false;
    if (!validarCampoRequerido(precio, "Ingrese un precio de venta"))
      esValido = false;

    if (!esValido) {
      restablecerSubmitMovimiento(
        submitBtn,
        '<i class="bi bi-check-circle me-2"></i>Guardar Salida',
        form,
      );
      return;
    }

    const data = {
      inventarioId: datosFormulario.inventarioId,
      materialId: datosFormulario.materialId,
      cantidad: cantidad?.value,
      fechaVenta: fecha?.value,
      precioVenta: precio?.value,
      observaciones: datosFormulario.observaciones,
      centroAcopioId: centroAcopio,
      puntoEcaId: datosFormulario.puntoEcaId,
    };

    fetch(`/punto-eca/movimientos/registrar-venta/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    })
      .then((res) => res.json())
      .then((resp) => {
        if (resp.error) {
          globalThis.mostrarErrorMovimientos(
            resp.mensaje || "Error: operación no realizada",
            () => {
              restablecerSubmitMovimiento(
                submitBtn,
                '<i class="bi bi-check-circle me-2"></i>Guardar Salida',
                form,
              );
            },
            "No se pudo registrar la venta",
          );
        } else {
          const datosExitoVenta = construirResumenExitoMovimiento("salida", {
            centroAcopio:
              document.getElementById("salidaCentroAcopio")?.selectedOptions?.[0]
                ?.textContent || centroAcopio || "-",
            idRegistro:
              resp.venta_id ||
              resp.ventaId ||
              resp.id ||
              resp.registroId ||
              "-",
          });

          try {
            if (typeof globalThis.mostrarSwalExitoMovimiento === "function") {
              globalThis.mostrarSwalExitoMovimiento(
                "Venta",
                datosExitoVenta,
                () => globalThis.location.reload(),
              );
              return;
            }
          } catch (error_) {
            console.error("Error mostrando Swal de venta:", error_);
          }

          mostrarFeedbackMovimientos(
            "Venta registrada correctamente",
            "success",
          );
          globalThis.setTimeout(() => {
            globalThis.location.reload();
          }, 100);
        }
      })
      .catch((err) => {
        globalThis.mostrarErrorMovimientos(
          "Error al conectar con el backend: " + err,
          () => {
            restablecerSubmitMovimiento(
              submitBtn,
              '<i class="bi bi-check-circle me-2"></i>Guardar Salida',
              form,
            );
          },
          "Error de conexión",
        );
      })
      .finally(() => {
        if (form.dataset.enviando !== "1" && document.querySelectorAll(".swal2-container").length === 0) {
          establecerEstadoBotonSubmit(
            submitBtn,
            false,
            '<i class="bi bi-check-circle me-2"></i>Guardar Salida',
          );
        }
      });
  }

  const formSalida = document.getElementById("formSalida");
  if (formSalida) {
    formSalida.addEventListener("submit", procesarSubmitSalida);
  }
});

// Carga Masiva (IIFE)
(function () {
  let modoCargaMasiva = null;

  function limpiarEstadoCargaMasiva() {
    const inputArchivo = document.getElementById("inputArchivoCargaMasiva");
    if (inputArchivo) inputArchivo.value = "";
    const feedback = document.getElementById("feedbackCargaMasiva");
    if (feedback) feedback.innerHTML = "";
  }

  function actualizarEtiquetaCargaMasiva(modo) {
    const spanTipo = document.getElementById("spanTipoCargaMasiva");
    if (spanTipo) {
      spanTipo.textContent = modo === "compras" ? "Compra" : "Venta";
      spanTipo.className =
        modo === "compras"
          ? "badge bg-info fw-normal"
          : "badge bg-success fw-normal";
    }

    const tipoOperacion = document.getElementById("tipoOperacionRequerido");
    if (tipoOperacion) {
      tipoOperacion.textContent = modo === "compras" ? "compra" : "venta";
    }
  }

  function actualizarCamposModoCargaMasiva(modo) {
    const esCompras = modo === "compras";
    [
      ["campoPrecioCompra", esCompras],
      ["campoFechaCompra", esCompras],
      ["campoPrecioVenta", !esCompras],
      ["campoFechaVenta", !esCompras],
    ].forEach(([id, visible]) => {
      const campo = document.getElementById(id);
      if (campo) campo.style.display = visible ? "" : "none";
    });
  }

  function actualizarPlantillaCargaMasiva(modo) {
    const descargarPlantilla = document.getElementById(
      "descargarPlantillaCargaMasiva",
    );
    if (!descargarPlantilla) return;

    const esCompras = modo === "compras";
      const url = esCompras
        ? "/static/plantilla_carga_compras.csv"
        : "/static/plantilla_carga_ventas.csv";
      const text = esCompras
        ? "Descargar plantilla de ejemplo para compras"
        : "Descargar plantilla de ejemplo para ventas";

      if (descargarPlantilla.tagName === "A") {
        descargarPlantilla.href = url;
        descargarPlantilla.textContent = text;
        descargarPlantilla.setAttribute("target", "_blank");
        descargarPlantilla.setAttribute("rel", "noopener noreferrer");
      } else {
        descargarPlantilla.dataset.href = url;
        descargarPlantilla.textContent = text;
      }
  }

  function generarDetalleCargaMasiva(detalle) {
    const isOk = detalle.status === "success";
    const rowClass = isOk
      ? "list-group-item list-group-item-success"
      : "list-group-item list-group-item-danger";
    return `<li class='${rowClass} d-flex justify-content-between align-items-center'>
        <span><b>Fila ${detalle.fila}:</b> ${detalle.mensaje || detalle.status}</span>
        <span>${isOk ? "✅" : "❌"}</span>
    </li>`;
  }

  function setModoCargaMasiva(mode) {
    modoCargaMasiva = mode || "compras";
    limpiarEstadoCargaMasiva();
    actualizarEtiquetaCargaMasiva(modoCargaMasiva);
    actualizarCamposModoCargaMasiva(modoCargaMasiva);
    actualizarPlantillaCargaMasiva(modoCargaMasiva);
  }

  function abrirModalCargaMasiva(e) {
    if (e?.preventDefault) e.preventDefault();
    let mode = e?.target?.id === "btnBulkImportVentas" ? "ventas" : "compras";
    setModoCargaMasiva(mode);
    const modal = new bootstrap.Modal(
      document.getElementById("modalCargaMasiva"),
    );
    modal.show();
  }

  document.addEventListener("DOMContentLoaded", function () {
    ["btnBulkImportCompras", "btnBulkImportVentas"].forEach((botonId) => {
      const boton = document.getElementById(botonId);
      if (boton) boton.addEventListener("click", abrirModalCargaMasiva);
    });

    let form = document.getElementById("formCargaMasiva");
    if (form) {
      form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        let feedback = document.getElementById("feedbackCargaMasiva");
        feedback.innerHTML =
          '<span class="text-info">Subiendo archivo, por favor espera...</span>';
        let archivoInput = document.getElementById("inputArchivoCargaMasiva");
        let archivo = archivoInput?.files?.[0];
        if (!archivo) {
          feedback.innerHTML =
            '<span class="text-danger">Debe seleccionar un archivo</span>';
          return;
        }
        let endpoint =
          modoCargaMasiva === "compras"
            ? "/punto-eca/movimientos/compras/bulk_import/"
            : "/punto-eca/movimientos/ventas/bulk_import/";
        let formData = new FormData();
        formData.append("file", archivo);
        let csrfToken =
          document
            .querySelector('meta[name="csrf-token"]')
            ?.getAttribute("content") || "";
        fetch(endpoint, {
          method: "POST",
          body: formData,
          headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
        })
          .then((res) => res.json())
          .then((data) => {
            let html = "";
            if (data.status === "success") {
              const resumen = data.resumen || {};
              const total =
                resumen.total_filas ??
                (Array.isArray(data.detalles) ? data.detalles.length : 0);
              const exitosas = resumen.exitosas ?? 0;
              const conErrores = resumen.con_errores ?? 0;
              html += `<div class="alert alert-success py-2 fw-semibold">${data.mensaje || "Archivo procesado correctamente."}<br><span class='small'><b>Total filas:</b> ${total} &bullet; <span class='text-success'><b>Éxito:</b> ${exitosas}</span> &bullet; <span class='text-danger'><b>Error:</b> ${conErrores}</span></span></div>`;

              if (Array.isArray(data.detalles) && data.detalles.length > 0) {
                html += `<div style="max-height:300px;overflow-y:auto"><ul class="list-group">
                                ${data.detalles.map(generarDetalleCargaMasiva).join("")}</ul></div>`;
              }
            } else {
              html += `<div class="alert alert-danger py-2">${data.mensaje || "Ocurrió un error."}</div>`;
            }
            feedback.innerHTML = html;
          })
          .catch((err) => {
            feedback.innerHTML = `<div class="alert alert-danger py-2">Error al subir archivo: ${err}</div>`;
          });
      });
    }
    // Manejar descarga de plantilla cuando es botón
    document.addEventListener("click", function (ev) {
      const el = ev.target.closest("#descargarPlantillaCargaMasiva");
      if (!el) return;
      ev.preventDefault();
      const href = el.tagName === "A" ? el.href : el.dataset.href;
      if (!href) return;
      const a = document.createElement("a");
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      document.body.appendChild(a);
      a.click();
      a.remove();
    });
  });
})();

// Listeners Modales de Edición (Envuelto en DOMContentLoaded para proteger funciones)
document.addEventListener("DOMContentLoaded", function () {
  function limpiarEstadoModales() {
    if (document.querySelectorAll(".modal.show").length > 0) return;
    document
      .querySelectorAll(".modal-backdrop")
      .forEach((backdrop) => backdrop.remove());
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("overflow");
    document.body.style.removeProperty("padding-right");
  }

  [
    "detallesEntradaModal",
    "detallesSalidaModal",
    "editarCompraModal",
    "editarVentaModal",
  ].forEach((modalId) => {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;
    modalElement.addEventListener("hidden.bs.modal", limpiarEstadoModales);
  });

  // Ver Detalles de Entrada
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-detalles-entrada");
    if (!btn) return;
    const compraId = btn.dataset.compraId;
    const entrada = globalThis.ENTRADAS_INICIALES.find(
      (e) => e.compraId === compraId,
    );
    if (!entrada) {
      mostrarSwalMensajeMovimiento({
        icon: "info",
        title: "Sin detalles",
        text: "No se encontraron los detalles de esta entrada",
      });
      return;
    }

    const fecha = entrada.fechaCompra
      ? new Date(entrada.fechaCompra).toLocaleDateString("es-CO")
      : "-";
    const cantidad = Number.parseFloat(entrada.cantidad || 0);
    const precio = Number.parseFloat(entrada.precioCompra || 0);
    const total = cantidad * precio;

    document.getElementById("detEntradaMaterial").textContent =
      entrada.nombreMaterial || "-";
    document.getElementById("detEntradaFecha").textContent = fecha;
    document.getElementById("detEntradaCantidad").textContent =
      cantidad.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detEntradaPrecio").textContent =
      "$" + precio.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detEntradaTotal").textContent =
      "$" + total.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detEntradaObservaciones").textContent =
      entrada.observaciones || "Sin observaciones";

    const btnEdit = document.getElementById("btnEditarEntrada");
    const btnDel = document.getElementById("btnEliminarEntrada");
    if (btnEdit) btnEdit.dataset.compraId = compraId;
    if (btnDel) btnDel.dataset.compraId = compraId;

    const modal = new bootstrap.Modal(
      document.getElementById("detallesEntradaModal"),
    );
    modal.show();
  });

  // Eliminar entrada desde modal
  const btnEliminarEntradaModal = document.getElementById("btnEliminarEntrada");
  if (btnEliminarEntradaModal) {
    btnEliminarEntradaModal.addEventListener("click", function () {
      eliminarCompraPorId(this.dataset.compraId, {
        confirmTitle: "Eliminar entrada",
        confirmText: "¿Estás seguro de que deseas eliminar esta entrada?",
        successTitle: "Entrada eliminada",
        successText: "Entrada eliminada correctamente",
        sinDatosText: "No se encontraron los datos de esta entrada",
      });
    });
  }

    // Eliminar salida desde modal
    const btnEliminarSalidaModal = document.getElementById("btnEliminarSalida");
    if (btnEliminarSalidaModal) {
      btnEliminarSalidaModal.addEventListener("click", function () {
        eliminarVentaPorId(this.dataset.ventaId, {
          confirmTitle: "Eliminar salida",
          confirmText: "¿Estás seguro de que deseas eliminar esta salida?",
          successTitle: "Salida eliminada",
          successText: "Salida eliminada correctamente",
          sinDatosText: "No se encontraron los datos de esta salida",
        });
      });
    }

  // Guardar Edición Compra
  const btnGuardarCompra = document.getElementById("btnGuardarCompra");
  if (btnGuardarCompra) {
    btnGuardarCompra.addEventListener("click", function () {
      const datosActualizacion = {
        puntoId: document.querySelector("section[data-punto-eca-id]")?.dataset
          .puntoEcaId,
        materialId: document.getElementById("editCompraMaterialId").value,
        compraId: document.getElementById("editCompraId").value,
        inventarioId: document.getElementById("editInventarioId").value,
        cantidad: Number.parseFloat(
          document.getElementById("editCompraCantidad").value,
        ),
        fechaCompra: document.getElementById("editCompraFecha").value,
        precioCompra: Number.parseFloat(
          document.getElementById("editCompraPrecio").value,
        ),
        observaciones: document.getElementById("editCompraObservaciones").value,
      };
      enviarActualizacionMovimiento({
        url: `/punto-eca/movimientos/editar-compra/${datosActualizacion.compraId}/`,
        datosActualizacion,
        tituloExito: "Compra actualizada",
        textoExito: "Compra actualizada",
      });
    });
  }

  // Guardar Edición Venta
  const btnGuardarVenta = document.getElementById("btnGuardarVenta");
  if (btnGuardarVenta) {
    btnGuardarVenta.addEventListener("click", function () {
      const datosActualizacion = {
        puntoId: document.querySelector("section[data-punto-eca-id]")?.dataset
          .puntoEcaId,
        ventaId: document.getElementById("editVentaId").value,
        materialId: document.getElementById("editVentaMaterialId").value,
        inventarioId: document.getElementById("editInventarioIdVenta").value,
        cantidad: Number.parseFloat(
          document.getElementById("editVentaCantidad").value,
        ),
        fechaVenta: document.getElementById("editVentaFecha").value,
        precioVenta: Number.parseFloat(
          document.getElementById("editVentaPrecio").value,
        ),
        centroAcopioId: document.getElementById("editVentaCentro").value,
        observaciones: document.getElementById("editVentaObservaciones").value,
      };
      enviarActualizacionMovimiento({
        url: `/punto-eca/movimientos/editar-venta/${datosActualizacion.ventaId}/`,
        datosActualizacion,
        tituloExito: "Venta actualizada",
        textoExito: "Venta actualizada",
      });
    });
  }

  // Editar desde modal de detalles (entradas y salidas regulares e historial)
  document.addEventListener("click", function (e) {
    const btn = e.target.closest("#btnEditarEntrada, #btnEditarSalida");
    if (!btn) return;
    manejarClickEdicionMovimiento(btn);
  });
});

// Eliminar venta desde tabla de salidas
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-eliminar-salida");
  if (!btn) return;
  eliminarVentaPorId(btn.dataset.ventaId, {
    confirmTitle: "Eliminar salida",
    confirmText: "¿Estás seguro de que deseas eliminar esta salida?",
    successTitle: "Salida eliminada",
    successText: "Salida eliminada correctamente",
    sinDatosText: "No se encontraron los datos de esta salida",
  });
});

// Ver Detalles de Salida
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-detalles-salida");
  if (!btn) return;
  mostrarDetallesSalidaPorId(btn.dataset.ventaId);
});

// Delegated pagination handler for buttons with data-page
document.addEventListener("click", function (e) {
  const pageBtn = e.target.closest("[data-page]");
  if (!pageBtn) return;
  const page = Number(pageBtn.dataset.page);
  if (Number.isNaN(page)) return;
  if (pageBtn.closest("#paginacionEntradas")) {
    if (typeof globalThis.cambiarPaginaEntradas === "function")
      globalThis.cambiarPaginaEntradas(page);
  } else if (pageBtn.closest("#paginacionSalidas")) {
    if (typeof globalThis.cambiarPaginaSalidas === "function")
      globalThis.cambiarPaginaSalidas(page);
  } else if (pageBtn.closest("#paginacionHistorial")) {
    if (typeof globalThis.cambiarPaginaHistorial === "function")
      globalThis.cambiarPaginaHistorial(page);
  }
});

// Ver Detalles de Historial
document.addEventListener("click", function (e) {
  const btn = e.target.closest(
    ".btn-editar-historial-compra, .btn-editar-historial-venta",
  );
  if (!btn) return;
  mostrarDetallesHistorialPorBoton(btn);
});

function bloquearTeclasNoNumericas(e) {
  if (["e", "E", "-", "+"].includes(e.key)) e.preventDefault();
}

function bloquearTeclasNoNumericasVenta(e) {
  bloquearTeclasNoNumericas(e);
}

function inicializarCalculoMovimiento({
  precioInputId,
  cantidadInputId,
  totalInputId,
  stockInputId,
  stockResultadoId,
  esCompra,
  bloquearTeclas,
}) {
  const precioInput = document.getElementById(precioInputId);
  const cantidadInput = document.getElementById(cantidadInputId);
  const totalInput = document.getElementById(totalInputId);
  const stockInput = document.getElementById(stockInputId);
  const stockResultado = document.getElementById(stockResultadoId);

  const calcularTotal = () => {
    const precio = Number.parseFloat(precioInput?.value) || 0;
    const cantidad = Number.parseFloat(cantidadInput?.value) || 0;
    const total = precio * cantidad;
    if (totalInput) totalInput.value = Number.isFinite(total) ? total.toFixed(2) : "";

    const stockActual = Number.parseFloat(stockInput?.value) || 0;
    const stockCalculado = esCompra ? stockActual + cantidad : stockActual - cantidad;
    if (stockResultado) {
      stockResultado.textContent = Number.isFinite(stockCalculado)
        ? stockCalculado.toFixed(2)
        : "-";
    }
  };

  if (precioInput) {
    precioInput.addEventListener("input", calcularTotal);
    precioInput.addEventListener("keydown", bloquearTeclas);
    precioInput.addEventListener("input", function () {
      if (this.value && this.value.length > 12) this.value = this.value.slice(0, 12);
      calcularTotal();
    });
  }

  if (cantidadInput) {
    cantidadInput.addEventListener("input", calcularTotal);
    cantidadInput.addEventListener("keydown", bloquearTeclas);
    cantidadInput.addEventListener("input", function () {
      if (this.value && this.value.length > 10) this.value = this.value.slice(0, 10);
      calcularTotal();
    });
  }

  calcularTotal();
}

function inicializarCalculoCompra() {
  inicializarCalculoMovimiento({
    precioInputId: "entradaPrecioCompra",
    cantidadInputId: "entradaCantidad",
    totalInputId: "entradaTotalCompra",
    stockInputId: "entradaStockActual",
    stockResultadoId: "entradaStockResultante",
    esCompra: true,
    bloquearTeclas: bloquearTeclasNoNumericas,
  });
}

function inicializarCalculoVenta() {
  inicializarCalculoMovimiento({
    precioInputId: "salidaPrecioVenta",
    cantidadInputId: "salidaCantidad",
    totalInputId: "salidaTotalVenta",
    stockInputId: "salidaStockActual",
    stockResultadoId: "salidaStockRestante",
    esCompra: false,
    bloquearTeclas: bloquearTeclasNoNumericasVenta,
  });
}

// Inicializar cálculos y fechas
document.addEventListener("DOMContentLoaded", function () {
  inicializarCalculoCompra();
  inicializarCalculoVenta();

  try {
    const editVentaSelect = document.getElementById("editVentaCentro");
    if (editVentaSelect) {
      let centros = globalThis.CENTROS || [];
      if (!Array.isArray(centros) && typeof centros === "object") {
        centros = Object.values(centros || {});
      }
      editVentaSelect.innerHTML =
        "<option value=''>Selecciona un centro...</option>";
      centros.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id || c.id === 0 ? String(c.id) : "";
        opt.textContent = c.nombre || c.nmbCentro || c.nmbCentroAcopio || "";
        editVentaSelect.appendChild(opt);
      });
    }
  } catch (e) {
    console.error("Error populating editVentaCentro on DOMContentLoaded", e);
  }

  const fechaHoraExacta = obtenerFechaHoraActual();
  const limitePasado = "2025-01-01T00:00";
  const inputFechaCompra = document.getElementById("entradaFecha");
  const inputFechaVenta = document.getElementById("salidaFecha");

  if (inputFechaCompra) {
    inputFechaCompra.value = fechaHoraExacta;
    inputFechaCompra.max = fechaHoraExacta;
    inputFechaCompra.min = limitePasado;
  }

  if (inputFechaVenta) {
    inputFechaVenta.value = fechaHoraExacta;
    inputFechaVenta.max = fechaHoraExacta;
    inputFechaVenta.min = limitePasado;
  }
});
