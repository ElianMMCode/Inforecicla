// =============================
// LISTENERS ELIMINAR DESDE TABLA HISTORIAL
// =============================

// Eliminar compra desde historial
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-eliminar-historial-compra");
  if (!btn) return;
  const compraId = btn.dataset.compraId;
  if (!confirm("¿Estás seguro de que deseas eliminar esta compra?")) return;
  // Buscar en HISTORIAL_COMPRAS o ENTRADAS_INICIALES
  const entrada =
    (globalThis.HISTORIAL_COMPRAS || []).find(
      (e) => String(e.compraId) === String(compraId),
    ) ||
    (globalThis.ENTRADAS_INICIALES || []).find(
      (e) => String(e.compraId) === String(compraId),
    );
  if (!entrada) {
    alert("No se encontraron los datos de esta compra");
    return;
  }
  const puntoId = document.querySelector("section[data-punto-eca-id]")?.dataset
    .puntoEcaId;
  const inventarioId = entrada.inventarioId || "";
  const materialId = entrada.materialId || "";
  const datosEliminar = { compraId, inventarioId, puntoId, materialId };
  let csrfToken =
    document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content") || "";
  fetch(`/punto-eca/movimientos/borrar-compra/${compraId}/`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(datosEliminar),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success || data.ok || !data.error) {
        alert("Compra eliminada correctamente");
        location.reload();
      } else {
        alert(
          "Error al eliminar: " +
            (data.mensaje || data.message || "Error desconocido"),
        );
      }
    })
    .catch((error) => {
      alert(
        "Error al procesar la solicitud: " +
          (error && error.message ? error.message : error),
      );
    });
});

// Eliminar venta desde historial
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-eliminar-historial-venta");
  if (!btn) return;
  const ventaId = btn.dataset.ventaId;
  if (!confirm("¿Estás seguro de que deseas eliminar esta venta?")) return;
  // Buscar en HISTORIAL_VENTAS o SALIDAS_INICIALES
  const salida =
    (globalThis.HISTORIAL_VENTAS || []).find(
      (s) => String(s.ventaId) === String(ventaId),
    ) ||
    (globalThis.SALIDAS_INICIALES || []).find(
      (s) => String(s.ventaId) === String(ventaId),
    );
  if (!salida) {
    alert("No se encontraron los datos de esta venta");
    return;
  }
  const puntoId = document.querySelector("section[data-punto-eca-id]")?.dataset
    .puntoEcaId;
  const inventarioId = salida.inventarioId || "";
  const materialId = salida.materialId || "";
  const datosEliminar = { ventaId, inventarioId, puntoId, materialId };
  let csrfToken =
    document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content") || "";
  fetch(`/punto-eca/movimientos/borrar-venta/${ventaId}/`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(datosEliminar),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success || data.ok || !data.error) {
        alert("Venta eliminada correctamente");
        location.reload();
      } else {
        alert(
          "Error al eliminar: " +
            (data.mensaje || data.message || "Error desconocido"),
        );
      }
    })
    .catch((error) => {
      alert(
        "Error al procesar la solicitud: " +
          (error && error.message ? error.message : error),
      );
    });
});

(function () {
  console.log("Script inline de movimientos ejecutándose...");

  // Función helper para mostrar estado de búsqueda
  function mostrarEstadoBusquedaMov(state) {
    try {
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
    } catch (e) {}
  }

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
        if (seccionBusquedaMaterial)
          seccionBusquedaMaterial.style.display = "block";
        let formEntradaContainer = document.getElementById(
          "formEntradaContainer",
        );
        let formSalidaContainer = document.getElementById(
          "formSalidaContainer",
        );
        if (formEntradaContainer) formEntradaContainer.style.display = "none";
        if (formSalidaContainer) formSalidaContainer.style.display = "none";
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
    if (typeof $ === "undefined" || typeof $.fn.select2 === "undefined") {
      console.warn("Select2 o jQuery no disponibles, reintentando...");
      setTimeout(inicializarSelect2, 100);
      return;
    }

    console.log("jQuery y Select2 disponibles");

    const puntoEcaSection = document.querySelector("section[data-usuario-id]");
    const usuarioId = puntoEcaSection?.dataset.usuarioId;
    const puntoEcaId = puntoEcaSection?.dataset.puntoEcaId;
    const gestor = puntoEcaSection?.dataset.gestor;

    const inputBusqueda = document.getElementById("buscarMaterialMovimientos");
    const btnLimpiar = document.getElementById("btnLimpiarBusquedaMov");
    const modalBusqueda = document.getElementById(
      "buscarMaterialMovimientosModal",
    );
    const resultadosDiv = document.getElementById("resultadosBusquedaMov");
    const estadoDiv = document.getElementById("estadoBusquedaMov");

    // INICIALIZAR SELECT2 EN BUSCAR MATERIAL (AJAX)
    let $buscarMaterial = $(inputBusqueda);
    if ($buscarMaterial.length) {
      let endpoint = "/punto-eca/materiales/inventario";
      let puntoId = puntoEcaId;

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
            let requestData = { texto: searchTerm, puntoId: puntoId };
            if (categoria) requestData.categoria = categoria;
            if (tipo) requestData.tipo = tipo;
            return requestData;
          },
          processResults: function (data, params) {
            if (data.error) return { results: [] };
            if (!Array.isArray(data)) data = [];
            data = data.slice().reverse();
            let results = data.map(function (m) {
              return {
                id: m.materialId || m.id || "",
                text: m.nmbMaterial || m.nombre || "Material sin nombre",
                element: $("<option>")
                  .attr(
                    "data-imagen",
                    m.imagenUrl || "/imagenes/materiales.png",
                  )
                  .attr("data-tipo", m.nmbTipo || "")
                  .attr("data-categoria", m.nmbCategoria || "")[0],
                data: m,
              };

              // Inicializar validación en tiempo real cuando el DOM esté listo
              document.addEventListener("DOMContentLoaded", function () {
                agregarValidacionEnTiempoRealEntrada();
                agregarValidacionEnTiempoRealSalida();
              });
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
          let imagenUrl =
            data.element?.getAttribute("data-imagen") ||
            "/imagenes/materiales.png";
          let nmbTipo = data.element?.getAttribute("data-tipo") || "";
          let nmbCategoria = data.element?.getAttribute("data-categoria") || "";
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

      function obtenerFechaHoraActual() {
        const ahora = new Date();
        // Ajustamos por la zona horaria local de Colombia (o del cliente)
        const ahoraLocal = new Date(
          ahora.getTime() - ahora.getTimezoneOffset() * 60000,
        );
        // Cortamos la cadena para que coincida exactamente con lo que pide el input HTML
        return ahoraLocal.toISOString().slice(0, 16);
      }

      function applyMaterialToForms(m) {
        try {
          globalThis.lastMaterialSeleccionado = m;
        } catch (e) {}
        if (!m) return;
        let materialId =
          m.materialId || m.id || (m.material && m.material.materialId) || "";
        let materialNombre = m.nmbMaterial || m.nombre || m.text || "";
        let materialTipo = m.nmbTipo || m.tipo || "";
        let materialCategoria = m.nmbCategoria || m.categoria || "";
        let materialDescripcion = m.dscMaterial || m.descripcion || "";
        // Ejemplo dentro de la función donde preparas el formulario:
        let inputFechaCompra = document.getElementById("entradaFecha");
        if (inputFechaCompra) {
          inputFechaCompra.value = obtenerFechaHoraActual();
        }
        let inputFechaVenta = document.getElementById("salidaFecha");
        if (inputFechaVenta) {
          inputFechaVenta.value = obtenerFechaHoraActual();
        }
        let unidad = "";
        if (m.unidadMedida !== undefined && m.unidadMedida !== null) {
          if (typeof m.unidadMedida === "string") {
            unidad = m.unidadMedida;
          } else if (typeof m.unidadMedida === "object") {
            unidad = m.unidadMedida.nombre || m.unidadMedida.clave || "";
          } else {
            unidad = String(m.unidadMedida || "");
          }
        } else if (m.unidad !== undefined && m.unidad !== null) {
          unidad = m.unidad;
        }
        let stockActual =
          m.stockActual !== undefined &&
          m.stockActual !== null &&
          m.stockActual !== ""
            ? parseFloat(m.stockActual)
            : null;
        let capacidadMax =
          m.capacidadMaxima !== undefined &&
          m.capacidadMaxima !== null &&
          m.capacidadMaxima !== ""
            ? parseFloat(m.capacidadMaxima)
            : null;
        let precioCompra =
          m.precioCompra !== undefined &&
          m.precioCompra !== null &&
          m.precioCompra !== ""
            ? parseFloat(m.precioCompra)
            : null;
        let precioVenta =
          m.precioVenta !== undefined &&
          m.precioVenta !== null &&
          m.precioVenta !== ""
            ? parseFloat(m.precioVenta)
            : null;

        function setFields(res) {
          try {
            try {
              globalThis.lastMaterialAplicado = res;
            } catch (e) {}
            let inventarioId =
              (res && res.inventarioId) || (m && m.inventarioId) || "";
            let appliedMaterialNombre =
              (res && (res.nmbMaterial || res.nombre || res.text)) ||
              materialNombre ||
              "";
            let appliedMaterialTipo =
              (res && (res.nmbTipo || res.tipo)) || materialTipo || "";
            let appliedMaterialCategoria =
              (res && (res.nmbCategoria || res.categoria)) ||
              materialCategoria ||
              "";
            let appliedMaterialDescripcion =
              (res && (res.dscMaterial || res.descripcion)) ||
              materialDescripcion ||
              "";
            let appliedUnidad = unidad || "";
            if (
              res &&
              res.unidadMedida !== undefined &&
              res.unidadMedida !== null
            ) {
              if (typeof res.unidadMedida === "string") {
                appliedUnidad = res.unidadMedida;
              } else if (typeof res.unidadMedida === "object") {
                appliedUnidad =
                  res.unidadMedida.nombre ||
                  res.unidadMedida.clave ||
                  unidad ||
                  "";
              } else {
                appliedUnidad = String(res.unidadMedida || unidad || "");
              }
            }

            let inputEntrada = document.getElementById(
              "entradaMaterialSeleccionado",
            );
            let idEntrada = document.getElementById("entradaMaterialId");
            let tipoEntrada = document.getElementById("entradaMaterialTipo");
            let categoriaEntrada = document.getElementById(
              "entradaMaterialCategoria",
            );
            let descripcionEntrada = document.getElementById(
              "entradaMaterialDescripcion",
            );
            let unidadEntrada = document.getElementById(
              "entradaMaterialUnidad",
            );
            let stockActualEntrada =
              document.getElementById("entradaStockActual");
            let capacidadMaxEntrada = document.getElementById(
              "entradaCapacidadMaxima",
            );
            let precioCompraEntrada = document.getElementById(
              "entradaPrecioCompra",
            );

            let inputSalida = document.getElementById(
              "salidaMaterialSeleccionado",
            );
            let idSalida = document.getElementById("salidaMaterialId");
            let tipoSalida = document.getElementById("salidaMaterialTipo");
            let categoriaSalida = document.getElementById(
              "salidaMaterialCategoria",
            );
            let descripcionSalida = document.getElementById(
              "salidaMaterialDescripcion",
            );
            let unidadSalida = document.getElementById("salidaMaterialUnidad");
            let stockActualSalida =
              document.getElementById("salidaStockActual");
            let capacidadMaxSalida = document.getElementById(
              "salidaCapacidadMaxima",
            );
            let precioVentaSalida =
              document.getElementById("salidaPrecioVenta");

            let finalUnidad = appliedUnidad || "";
            if (
              res &&
              res.unidadMedida !== undefined &&
              res.unidadMedida !== null
            ) {
              if (typeof res.unidadMedida === "string") {
                finalUnidad = res.unidadMedida;
              } else if (typeof res.unidadMedida === "object") {
                finalUnidad =
                  res.unidadMedida.nombre ||
                  res.unidadMedida.clave ||
                  appliedUnidad ||
                  "";
              } else {
                finalUnidad = String(res.unidadMedida || appliedUnidad || "");
              }
            }
            let finalStock =
              res && res.stockActual !== undefined && res.stockActual !== null
                ? parseFloat(res.stockActual)
                : stockActual !== null
                  ? stockActual
                  : null;
            let finalCapacidad =
              res &&
              res.capacidadMaxima !== undefined &&
              res.capacidadMaxima !== null
                ? parseFloat(res.capacidadMaxima)
                : capacidadMax !== null
                  ? capacidadMax
                  : null;
            let finalPrecioCompra =
              res &&
              res.precioCompra !== undefined &&
              res.precioCompra !== null &&
              res.precioCompra !== ""
                ? parseFloat(res.precioCompra)
                : precioCompra !== null
                  ? precioCompra
                  : null;
            let finalPrecioVenta =
              res &&
              res.precioVenta !== undefined &&
              res.precioVenta !== null &&
              res.precioVenta !== ""
                ? parseFloat(res.precioVenta)
                : precioVenta !== null
                  ? precioVenta
                  : null;

            if (inputEntrada) {
              inputEntrada.value = appliedMaterialNombre;
              try {
                $(inputEntrada).val(appliedMaterialNombre).trigger("change");
              } catch (e) {}
            }
            if (idEntrada) {
              idEntrada.value = materialId;
              try {
                $(idEntrada).val(materialId).trigger("change");
              } catch (e) {}
            }
            let entradaInventarioIdInput = document.getElementById(
              "entradaInventarioId",
            );
            if (entradaInventarioIdInput) {
              entradaInventarioIdInput.value = inventarioId;
            }
            if (tipoEntrada) {
              tipoEntrada.value = appliedMaterialTipo;
              try {
                $(tipoEntrada).val(appliedMaterialTipo).trigger("change");
              } catch (e) {}
            }
            if (categoriaEntrada) {
              categoriaEntrada.value = appliedMaterialCategoria;
              try {
                $(categoriaEntrada)
                  .val(appliedMaterialCategoria)
                  .trigger("change");
              } catch (e) {}
            }
            if (descripcionEntrada) {
              descripcionEntrada.value = appliedMaterialDescripcion;
              try {
                $(descripcionEntrada)
                  .val(appliedMaterialDescripcion)
                  .trigger("change");
              } catch (e) {}
            }
            if (unidadEntrada) {
              unidadEntrada.value = finalUnidad;
              try {
                $(unidadEntrada).val(finalUnidad).trigger("change");
              } catch (e) {}
            }
            if (stockActualEntrada) {
              stockActualEntrada.value =
                finalStock !== null && !isNaN(finalStock)
                  ? finalStock.toFixed(2)
                  : "";
              try {
                $(stockActualEntrada)
                  .val(
                    finalStock !== null && !isNaN(finalStock)
                      ? finalStock.toFixed(2)
                      : "",
                  )
                  .trigger("change");
              } catch (e) {}
            }
            if (capacidadMaxEntrada) {
              capacidadMaxEntrada.value =
                finalCapacidad !== null && !isNaN(finalCapacidad)
                  ? finalCapacidad.toFixed(2)
                  : "";
              try {
                $(capacidadMaxEntrada)
                  .val(
                    finalCapacidad !== null && !isNaN(finalCapacidad)
                      ? finalCapacidad.toFixed(2)
                      : "",
                  )
                  .trigger("change");
              } catch (e) {}
            }
            if (precioCompraEntrada) {
              precioCompraEntrada.value =
                finalPrecioCompra !== null && !isNaN(finalPrecioCompra)
                  ? finalPrecioCompra.toFixed(2)
                  : "";
              try {
                // 1. Actualiza para frameworks como Select2 o jQuery si lo tienes
                $(precioCompraEntrada)
                  .val(precioCompraEntrada.value)
                  .trigger("change");

                // 2. CORRECCIÓN CRÍTICA: Despacha el evento nativo en lugar de llamar a triggerEvents
                precioCompraEntrada.dispatchEvent(
                  new Event("input", { bubbles: true }),
                );
              } catch (e) {}
            }
            if (inputSalida) {
              inputSalida.value = appliedMaterialNombre;
              try {
                $(inputSalida).val(appliedMaterialNombre).trigger("change");
              } catch (e) {}
            }
            if (idSalida) {
              idSalida.value = materialId;
              try {
                $(idSalida).val(materialId).trigger("change");
              } catch (e) {}
            }
            let salidaInventarioIdInput =
              document.getElementById("salidaInventarioId");
            if (salidaInventarioIdInput) {
              salidaInventarioIdInput.value = inventarioId;
            }
            if (tipoSalida) {
              tipoSalida.value = appliedMaterialTipo;
              try {
                $(tipoSalida).val(appliedMaterialTipo).trigger("change");
              } catch (e) {}
            }
            if (categoriaSalida) {
              categoriaSalida.value = appliedMaterialCategoria;
              try {
                $(categoriaSalida)
                  .val(appliedMaterialCategoria)
                  .trigger("change");
              } catch (e) {}
            }
            if (descripcionSalida) {
              descripcionSalida.value = appliedMaterialDescripcion;
              try {
                $(descripcionSalida)
                  .val(appliedMaterialDescripcion)
                  .trigger("change");
              } catch (e) {}
            }
            if (unidadSalida) {
              unidadSalida.value = finalUnidad;
              try {
                $(unidadSalida).val(finalUnidad).trigger("change");
              } catch (e) {}
            }
            if (stockActualSalida) {
              stockActualSalida.value =
                finalStock !== null && !isNaN(finalStock)
                  ? finalStock.toFixed(2)
                  : "";
              try {
                $(stockActualSalida)
                  .val(
                    finalStock !== null && !isNaN(finalStock)
                      ? finalStock.toFixed(2)
                      : "",
                  )
                  .trigger("change");
              } catch (e) {}
            }
            if (capacidadMaxSalida) {
              capacidadMaxSalida.value =
                finalCapacidad !== null && !isNaN(finalCapacidad)
                  ? finalCapacidad.toFixed(2)
                  : "";
              try {
                $(capacidadMaxSalida)
                  .val(
                    finalCapacidad !== null && !isNaN(finalCapacidad)
                      ? finalCapacidad.toFixed(2)
                      : "",
                  )
                  .trigger("change");
              } catch (e) {}
            }
            if (precioVentaSalida) {
              precioVentaSalida.value =
                finalPrecioVenta !== null && !isNaN(finalPrecioVenta)
                  ? finalPrecioVenta.toFixed(2)
                  : "";
              try {
                // 1. Actualiza para frameworks si es necesario
                $(precioVentaSalida)
                  .val(precioVentaSalida.value)
                  .trigger("change");

                // 2. CORRECCIÓN CRÍTICA: Despacha el evento nativo para activar el cálculo del "Total"
                precioVentaSalida.dispatchEvent(
                  new Event("input", { bubbles: true }),
                );
              } catch (e) {}
            }
          } catch (e) {
            console.error("Error en setFields:", e);
          }
        }

        let hasInventarioId = m && m.inventarioId && m.inventarioId !== "";
        let hasInventoryInfo =
          (stockActual !== null && stockActual !== undefined) ||
          (capacidadMax !== null && capacidadMax !== undefined) ||
          (precioCompra !== null && precioCompra !== undefined) ||
          (precioVenta !== null && precioVenta !== undefined);

        if (
          !hasInventoryInfo &&
          !hasInventarioId &&
          typeof puntoEcaId !== "undefined" &&
          puntoEcaId
        ) {
          try {
            let params = new URLSearchParams();
            params.append("puntoId", puntoEcaId);
            params.append("texto", materialNombre || "");
            let url =
              "/punto-eca/materiales/inventario/" +
              (params.toString() ? "?" + params.toString() : "");

            fetch(url, {
              method: "GET",
              headers: { Accept: "application/json" },
            })
              .then((res) => res.json())
              .then((data) => {
                try {
                  if (Array.isArray(data) && data.length > 0) {
                    let foundById = data.find(function (it) {
                      return it.materialId === materialId;
                    });
                    let foundByName = data.find(function (it) {
                      return (
                        it.nmbMaterial && it.nmbMaterial === materialNombre
                      );
                    });
                    let found = foundById || foundByName || data[0];
                    let merged = Object.assign({}, m, found || {});
                    try {
                      if (
                        merged.stockActual !== undefined &&
                        merged.stockActual !== null
                      )
                        merged.stockActual = parseFloat(merged.stockActual);
                      if (
                        merged.capacidadMaxima !== undefined &&
                        merged.capacidadMaxima !== null
                      )
                        merged.capacidadMaxima = parseFloat(
                          merged.capacidadMaxima,
                        );
                      if (
                        merged.precioCompra !== undefined &&
                        merged.precioCompra !== null
                      )
                        merged.precioCompra = parseFloat(merged.precioCompra);
                      if (
                        merged.precioVenta !== undefined &&
                        merged.precioVenta !== null
                      )
                        merged.precioVenta = parseFloat(merged.precioVenta);
                    } catch (e) {}
                    setFields(merged);
                  } else {
                    setFields(m);
                  }
                } catch (e) {
                  setFields(m);
                }
              })
              .catch((err) => {
                setFields(m);
              });
          } catch (err) {
            setFields(m);
          }
        } else {
          setFields(m);
        }
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

          let formEntradaContainer = document.getElementById(
            "formEntradaContainer",
          );
          let formSalidaContainer = document.getElementById(
            "formSalidaContainer",
          );
          if (formEntradaContainer)
            formEntradaContainer.style.display = "block";
          if (formSalidaContainer) formSalidaContainer.style.display = "block";
          let seccionBusquedaMaterial = document.getElementById(
            "seccionBusquedaMaterial",
          );
          if (seccionBusquedaMaterial)
            seccionBusquedaMaterial.style.display = "none";

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

          function triggerEvents(el) {
            if (!el) return;
            try {
              el.dispatchEvent(new Event("input", { bubbles: true }));
            } catch (e) {}
            try {
              el.dispatchEvent(new Event("change", { bubbles: true }));
            } catch (e) {}
          }
          triggerEvents(document.getElementById("entradaMaterialSeleccionado"));
          triggerEvents(document.getElementById("entradaMaterialId"));
          triggerEvents(document.getElementById("salidaMaterialSeleccionado"));
          triggerEvents(document.getElementById("salidaMaterialId"));

          if (
            formEntradaContainer &&
            typeof formEntradaContainer.scrollIntoView === "function"
          ) {
            formEntradaContainer.scrollIntoView({
              behavior: "smooth",
              block: "center",
            });
          }
        } catch (err) {}
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
      $selectCategoria.on("select2:select", function (e) {
        buscarMateriales();
      });
      $selectCategoria.on("select2:unselect", function (e) {});
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
      $selectTipo.on("select2:select", function (e) {
        buscarMateriales();
      });
      $selectTipo.on("select2:unselect", function (e) {});
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

    function buscarMateriales() {
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

      fetch(url, { method: "GET", headers: { Accept: "application/json" } })
        .then((res) =>
          res
            .json()
            .then((data) => ({ status: res.status, ok: res.ok, data: data })),
        )
        .then(({ status, ok, data }) => {
          if (!ok) {
            let mensajeError =
              data?.mensaje || data?.message || "Error desconocido";
            if (estadoBusquedaEl) {
              estadoBusquedaEl.innerHTML =
                '<div class="alert alert-warning mb-0" role="alert"><i class="bi bi-exclamation-triangle me-2"></i>' +
                mensajeError +
                "</div>";
            }
            return;
          }
          if (!Array.isArray(data)) data = [];
          renderResultadosBusquedaMov(data);
        })
        .catch((error) => {
          if (estadoBusquedaEl) {
            estadoBusquedaEl.innerHTML =
              '<div class="alert alert-danger mb-0" role="alert"><i class="bi bi-exclamation-octagon me-2"></i>Error de conexión</div>';
          }
        });
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

        function numToString(v) {
          if (v === undefined || v === null || v === "") return "";
          let n = Number(v);
          return isNaN(n) ? "" : String(n);
        }

        item.dataset.materialId = material.materialId || "";
        item.dataset.nombre = material.nmbMaterial || "";
        item.dataset.descripcion = material.dscMaterial || "";
        item.dataset.tipo = material.nmbTipo || "";
        item.dataset.categoria = material.nmbCategoria || "";
        item.dataset.unidad = unidadVal;
        item.dataset.stockActual = numToString(material.stockActual);
        item.dataset.capacidadMaxima = numToString(material.capacidadMaxima);
        item.dataset.precioCompra = numToString(material.precioCompra);
        item.dataset.precioVenta = numToString(material.precioVenta);

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
        item.addEventListener("click", function (e) {
          e.preventDefault();
          let dto = {
            materialId: this.dataset.materialId,
            nmbMaterial: this.dataset.nombre,
            nmbTipo: this.dataset.tipo,
            nmbCategoria: this.dataset.categoria,
            dscMaterial: this.dataset.descripcion,
            unidadMedida: this.dataset.unidad || null,
            stockActual:
              this.dataset.stockActual !== undefined &&
              this.dataset.stockActual !== ""
                ? parseFloat(this.dataset.stockActual)
                : null,
            capacidadMaxima:
              this.dataset.capacidadMaxima !== undefined &&
              this.dataset.capacidadMaxima !== ""
                ? parseFloat(this.dataset.capacidadMaxima)
                : null,
            precioCompra:
              this.dataset.precioCompra !== undefined &&
              this.dataset.precioCompra !== ""
                ? parseFloat(this.dataset.precioCompra)
                : null,
            precioVenta:
              this.dataset.precioVenta !== undefined &&
              this.dataset.precioVenta !== ""
                ? parseFloat(this.dataset.precioVenta)
                : null,
          };

          applyMaterialToForms(dto);

          const modalInstance = bootstrap.Modal.getInstance(
            document.getElementById("buscarMaterialMovimientosModal"),
          );
          if (modalInstance) modalInstance.hide();

          let formEntradaContainer = document.getElementById(
            "formEntradaContainer",
          );
          let formSalidaContainer = document.getElementById(
            "formSalidaContainer",
          );
          if (formEntradaContainer)
            formEntradaContainer.style.display = "block";
          if (formSalidaContainer) formSalidaContainer.style.display = "block";
          let seccionBusquedaMaterial = document.getElementById(
            "seccionBusquedaMaterial",
          );
          if (seccionBusquedaMaterial)
            seccionBusquedaMaterial.style.display = "none";

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

          function triggerEvents(el) {
            if (!el) return;
            try {
              el.dispatchEvent(new Event("input", { bubbles: true }));
            } catch (e) {}
            try {
              el.dispatchEvent(new Event("change", { bubbles: true }));
            } catch (e) {}
          }
          triggerEvents(document.getElementById("entradaMaterialSeleccionado"));
          triggerEvents(document.getElementById("entradaMaterialId"));
          triggerEvents(document.getElementById("salidaMaterialSeleccionado"));
          triggerEvents(document.getElementById("salidaMaterialId"));

          if (
            formEntradaContainer &&
            typeof formEntradaContainer.scrollIntoView === "function"
          ) {
            formEntradaContainer.scrollIntoView({
              behavior: "smooth",
              block: "center",
            });
          }
        });
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
      $filtroMaterialCompra.find('option:not([value=""])').remove();
      const materiales = new Set();
      (globalThis.ENTRADAS_INICIALES || []).forEach((entrada) => {
        if (entrada.nombreMaterial) materiales.add(entrada.nombreMaterial);
      });
      Array.from(materiales)
        .sort()
        .forEach((m) => {
          $filtroMaterialCompra.append($("<option>").val(m).text(m));
        });
      $filtroMaterialCompra.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona material...",
        minimumInputLength: 0,
      });
    }

    if ($filtroCategoriaCompra.length) {
      $filtroCategoriaCompra.find('option:not([value=""])').remove();
      const categorias = new Set();
      (globalThis.ENTRADAS_INICIALES || []).forEach((entrada) => {
        if (entrada.nombreCategoria) categorias.add(entrada.nombreCategoria);
      });
      Array.from(categorias)
        .sort()
        .forEach((c) => {
          $filtroCategoriaCompra.append($("<option>").val(c).text(c));
        });
      $filtroCategoriaCompra.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona categoría...",
      });
    }

    if ($filtroTipoCompra.length) {
      $filtroTipoCompra.find('option:not([value=""])').remove();
      const tipos = new Set();
      (globalThis.ENTRADAS_INICIALES || []).forEach((entrada) => {
        if (entrada.nombreTipo) tipos.add(entrada.nombreTipo);
      });
      Array.from(tipos)
        .sort()
        .forEach((t) => {
          $filtroTipoCompra.append($("<option>").val(t).text(t));
        });
      $filtroTipoCompra.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona tipo...",
      });
    }
  }, 300);

  setTimeout(function () {
    const $filtroMaterialVenta = $("#filtroVentaMaterial");
    const $filtroCategoriaVenta = $("#filtroVentaCategoria");
    const $filtroTipoVenta = $("#filtroVentaTipo");
    const $filtroCentroVenta = $("#filtroVentaCentro");

    if ($filtroMaterialVenta.length) {
      $filtroMaterialVenta.find('option:not([value=""])').remove();
      const materiales = new Set();
      (globalThis.SALIDAS_INICIALES || []).forEach((salida) => {
        if (salida.nombreMaterial) materiales.add(salida.nombreMaterial);
      });
      Array.from(materiales)
        .sort()
        .forEach((m) => {
          $filtroMaterialVenta.append($("<option>").val(m).text(m));
        });
      $filtroMaterialVenta.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona material...",
      });
    }

    if ($filtroCategoriaVenta.length) {
      $filtroCategoriaVenta.find('option:not([value=""])').remove();
      const categorias = new Set();
      (globalThis.SALIDAS_INICIALES || []).forEach((salida) => {
        if (salida.nombreCategoria) categorias.add(salida.nombreCategoria);
      });
      Array.from(categorias)
        .sort()
        .forEach((c) => {
          $filtroCategoriaVenta.append($("<option>").val(c).text(c));
        });
      $filtroCategoriaVenta.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona categoría...",
      });
    }

    if ($filtroTipoVenta.length) {
      $filtroTipoVenta.find('option:not([value=""])').remove();
      const tipos = new Set();
      (globalThis.SALIDAS_INICIALES || []).forEach((salida) => {
        if (salida.nombreTipo) tipos.add(salida.nombreTipo);
      });
      Array.from(tipos)
        .sort()
        .forEach((t) => {
          $filtroTipoVenta.append($("<option>").val(t).text(t));
        });
      $filtroTipoVenta.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona tipo...",
      });
    }

    if ($filtroCentroVenta.length) {
      $filtroCentroVenta.find('option:not([value=""])').remove();
      const centros = globalThis.CENTROS || [];
      let centrosArray = Array.isArray(centros)
        ? centros
        : Object.values(centros);
      const nombreCentros = new Set();
      centrosArray.forEach((centro) => {
        const nombre =
          centro.nombre || centro.nmbCentro || centro.nmbCentroAcopio || "";
        if (nombre) nombreCentros.add(nombre);
      });
      Array.from(nombreCentros)
        .sort()
        .forEach((n) => {
          $filtroCentroVenta.append($("<option>").val(n).text(n));
        });
      $filtroCentroVenta.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona centro de acopio...",
      });
    }
  }, 300);

  setTimeout(function () {
    const $filtroHistorialMaterial = $("#filtroHistorialMaterial");
    const $filtroHistorialCategoria = $("#filtroHistorialCategoria");
    const $filtroHistorialTipo = $("#filtroHistorialTipo");
    const $filtroHistorialCentroAcopio = $("#filtroHistorialCentroAcopio");

    if ($filtroHistorialMaterial.length) {
      const materiales = new Set();
      const comprasData = globalThis.HISTORIAL_COMPRAS || [];
      const ventasData = globalThis.HISTORIAL_VENTAS || [];
      [...comprasData, ...ventasData].forEach((mov) => {
        if (mov.nombreMaterial) materiales.add(mov.nombreMaterial);
      });
      Array.from(materiales)
        .sort()
        .forEach((m) => {
          $filtroHistorialMaterial.append($("<option>").val(m).text(m));
        });
      $filtroHistorialMaterial.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona material...",
        minimumInputLength: 0,
      });
    }

    if ($filtroHistorialCategoria.length) {
      const categorias = new Set();
      const comprasData = globalThis.HISTORIAL_COMPRAS || [];
      const ventasData = globalThis.HISTORIAL_VENTAS || [];
      [...comprasData, ...ventasData].forEach((mov) => {
        if (mov.nombreCategoria) categorias.add(mov.nombreCategoria);
      });
      Array.from(categorias)
        .sort()
        .forEach((c) => {
          $filtroHistorialCategoria.append($("<option>").val(c).text(c));
        });
      $filtroHistorialCategoria.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona categoría...",
      });
    }

    if ($filtroHistorialTipo.length) {
      const tipos = new Set();
      const comprasData = globalThis.HISTORIAL_COMPRAS || [];
      const ventasData = globalThis.HISTORIAL_VENTAS || [];
      [...comprasData, ...ventasData].forEach((mov) => {
        if (mov.nombreTipo) tipos.add(mov.nombreTipo);
      });
      Array.from(tipos)
        .sort()
        .forEach((t) => {
          $filtroHistorialTipo.append($("<option>").val(t).text(t));
        });
      $filtroHistorialTipo.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona tipo...",
      });
    }

    if ($filtroHistorialCentroAcopio.length) {
      $filtroHistorialCentroAcopio.find('option:not([value=""])').remove();
      let centros = globalThis.CENTROS || [];
      if (!Array.isArray(centros)) centros = Object.values(centros || {});
      const nombreCentros = new Set();
      centros.forEach((c) => {
        const nombre = c.nombre || c.nmbCentro || c.nmbCentroAcopio || "";
        if (nombre) nombreCentros.add(nombre);
      });
      Array.from(nombreCentros)
        .sort()
        .forEach((n) => {
          $filtroHistorialCentroAcopio.append($("<option>").val(n).text(n));
        });
      $filtroHistorialCentroAcopio.select2({
        theme: "bootstrap4",
        width: "100%",
        allowClear: true,
        placeholder: "Selecciona centro de acopio...",
      });
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

  function obtenerPuntoEcaIdExportacion() {
    return (
      document.querySelector("section[data-punto-eca-id]")?.dataset.puntoEcaId ||
      ""
    );
  }

  function construirUrlExportacion(baseUrl, filtros) {
    const url = new URL(baseUrl, window.location.origin);
    Object.entries(filtros).forEach(([clave, valor]) => {
      if (valor !== undefined && valor !== null && String(valor).trim() !== "") {
        url.searchParams.set(clave, String(valor).trim());
      }
    });
    return url.toString();
  }

  function nombreArchivoDesdeRespuesta(response, fallback) {
    const contentDisposition = response.headers.get("content-disposition") || "";
    const match = contentDisposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)(?:\")?/i);
    if (match && match[1]) {
      return decodeURIComponent(match[1].replace(/\"/g, ""));
    }
    return fallback;
  }

  async function descargarExportacion(url, fallbackNombre) {
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          Accept: "application/octet-stream,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/json",
        },
      });

      const contentType = response.headers.get("content-type") || "";
      if (!response.ok) {
        let mensaje = "No se pudo generar la exportación.";
        if (contentType.includes("application/json")) {
          const data = await response.json();
          mensaje = data.mensaje || data.message || mensaje;
        } else {
          const texto = await response.text();
          if (texto) mensaje = texto;
        }
        alert(mensaje);
        return;
      }

      const blob = await response.blob();
      const nombreArchivo = nombreArchivoDesdeRespuesta(response, fallbackNombre);
      const blobUrl = window.URL.createObjectURL(blob);
      const enlace = document.createElement("a");
      enlace.href = blobUrl;
      enlace.download = nombreArchivo;
      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1000);
    } catch (error) {
      alert(
        "Error al exportar: " +
          (error && error.message ? error.message : String(error)),
      );
    }
  }

  document.querySelectorAll("[data-export-section][data-export-format]").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const puntoEcaId = obtenerPuntoEcaIdExportacion();
      const section = this.dataset.exportSection;
      const format = this.dataset.exportFormat;
      const baseUrl = this.getAttribute("href") || "";
      const filtroBase = { punto_eca_id: puntoEcaId };

      if (section === "compras") {
        Object.assign(filtroBase, {
          material: document.getElementById("filtroCompraMaterial")?.value || "",
          categoria: document.getElementById("filtroCompraCategoria")?.value || "",
          tipo: document.getElementById("filtroCompraTipo")?.value || "",
          fecha_desde: document.getElementById("filtroCompraFechaDesde")?.value || "",
          fecha_hasta: document.getElementById("filtroCompraFechaHasta")?.value || "",
        });
      } else if (section === "ventas") {
        Object.assign(filtroBase, {
          material: document.getElementById("filtroVentaMaterial")?.value || "",
          categoria: document.getElementById("filtroVentaCategoria")?.value || "",
          tipo: document.getElementById("filtroVentaTipo")?.value || "",
          centro_acopio: document.getElementById("filtroVentaCentro")?.value || "",
          fecha_desde: document.getElementById("filtroVentaFechaDesde")?.value || "",
          fecha_hasta: document.getElementById("filtroVentaFechaHasta")?.value || "",
        });
      } else if (section === "historial") {
        Object.assign(filtroBase, {
          material: document.getElementById("filtroHistorialMaterial")?.value || "",
          categoria: document.getElementById("filtroHistorialCategoria")?.value || "",
          tipo: document.getElementById("filtroHistorialTipo")?.value || "",
          centro_acopio: document.getElementById("filtroHistorialCentroAcopio")?.value || "",
          tipo_movimiento: document.getElementById("filtroHistorialTipoMovimiento")?.value || "",
          fecha_desde: document.getElementById("filtroHistorialDesde")?.value || "",
          fecha_hasta: document.getElementById("filtroHistorialHasta")?.value || "",
        });
      }

      const url = construirUrlExportacion(baseUrl, filtroBase);
      const nombreBase =
        section === "historial"
          ? `historial.${format === "pdf" ? "pdf" : "xlsx"}`
          : `${section}.${format === "pdf" ? "pdf" : "xlsx"}`;
      descargarExportacion(url, nombreBase);
    });
  });

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

  if (btnFiltrarHist) {
    btnFiltrarHist.addEventListener("click", resetearPaginaHistorialYRender);
  }
  $(
    "#filtroHistorialMaterial, #filtroHistorialCategoria, #filtroHistorialTipo",
  ).on("change", resetearPaginaHistorialYRender);

  if (btnLimpiarHist) {
    btnLimpiarHist.addEventListener("click", function () {
      $("#filtroHistorialMaterial").val("").trigger("change");
      $("#filtroHistorialCategoria").val("").trigger("change");
      $("#filtroHistorialTipo").val("").trigger("change");
      document.getElementById("filtroHistorialTipoMovimiento").value = "";
      document.getElementById("filtroHistorialDesde").value = "";
      document.getElementById("filtroHistorialHasta").value = "";
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
    entradasData = entradasData.slice().sort((a, b) => {
      function toISO(fecha) {
        if (!fecha) return 0;
        return new Date(fecha.replace(" ", "T")).getTime();
      }
      return toISO(b.fechaCompra) - toISO(a.fechaCompra);
    });

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
    const paginaActual = globalThis.PAGINA_ACTUAL_ENTRADAS || 1;

    if (globalThis.PAGINA_ACTUAL_ENTRADAS > totalPaginas)
      globalThis.PAGINA_ACTUAL_ENTRADAS = totalPaginas;
    if (globalThis.PAGINA_ACTUAL_ENTRADAS < 1)
      window.PAGINA_ACTUAL_ENTRADAS = 1;

    const inicio = (globalThis.PAGINA_ACTUAL_ENTRADAS - 1) * registrosPorPagina;
    const fin = inicio + registrosPorPagina;
    const registrosPagina = entradasData.slice(inicio, fin);

    tbody.innerHTML = registrosPagina
      .map((entrada) => {
        const fecha = entrada.fechaCompra
          ? new Date(entrada.fechaCompra).toLocaleString("es-CO", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })
          : "-";
        const cantidad = parseFloat(entrada.cantidad || 0);
        const precio = parseFloat(entrada.precioCompra || 0);
        const total = cantidad * precio;
        return `
                <tr data-categoria="${entrada.nombreCategoria || ""}" data-tipo="${entrada.nombreTipo || ""}">
                    <td class="small">${fecha}</td>
                    <td class="small">${entrada.nombreMaterial || "-"}</td>
                    <td class="text-end small">${cantidad.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="text-end small">$${precio.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="text-end small fw-semibold text-danger">$${total.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="text-center">
                        <div class="d-flex gap-2 justify-content-center">
                            <button type="button" class="btn btn-sm btn-danger text-white btn-detalles-entrada" data-compra-id="${entrada.compraId}" title="Ver detalles">
                                <i class="bi bi-eye-fill"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger btn-eliminar-entrada" data-compra-id="${entrada.compraId}" title="Eliminar">
                                <i class="bi bi-trash3-fill"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
      })
      .join("");

    const badge = document.getElementById("badgeEntradasCount");
    if (badge) badge.textContent = entradasData.length + " registros";
    actualizarPaginacionEntradas(totalPaginas);
  }

  function actualizarPaginacionEntradas(totalPaginas) {
    const paginacion = document.getElementById("paginacionEntradas");
    if (!paginacion) return;
    if (totalPaginas <= 0) {
      paginacion.innerHTML = "";
      return;
    }
    const paginaActual = globalThis.PAGINA_ACTUAL_ENTRADAS || 1;
    let html =
      '<li class="page-item ' +
      (paginaActual <= 1 ? "disabled" : "") +
      '"><a class="page-link" href="#" onclick="cambiarPaginaEntradas(' +
      (paginaActual - 1) +
      '); return false;">Anterior</a></li>';
    for (let i = 1; i <= totalPaginas; i++) {
      html +=
        '<li class="page-item ' +
        (i === paginaActual ? "active" : "") +
        '"><a class="page-link" href="#" onclick="cambiarPaginaEntradas(' +
        i +
        '); return false;">' +
        i +
        "</a></li>";
    }
    html +=
      '<li class="page-item ' +
      (paginaActual >= totalPaginas ? "disabled" : "") +
      '"><a class="page-link" href="#" onclick="cambiarPaginaEntradas(' +
      (paginaActual + 1) +
      '); return false;">Siguiente</a></li>';
    paginacion.innerHTML = html;
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
    if (globalThis.PAGINA_ACTUAL_SALIDAS < 1) window.PAGINA_ACTUAL_SALIDAS = 1;

    const inicio = (globalThis.PAGINA_ACTUAL_SALIDAS - 1) * registrosPorPagina;
    const fin = inicio + registrosPorPagina;
    const registrosPagina = salidasData.slice(inicio, fin);

    tbody.innerHTML = registrosPagina
      .map((salida) => {
        const fecha = salida.fechaVenta
          ? new Date(salida.fechaVenta).toLocaleString("es-CO", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })
          : "-";
        const cantidad = parseFloat(salida.cantidad || 0);
        const precio = parseFloat(salida.precioVenta || 0);
        const total = cantidad * precio;
        return `
                <tr data-categoria="${salida.nombreCategoria || ""}" data-tipo="${salida.nombreTipo || ""}">
                    <td class="small">${fecha}</td>
                    <td class="small">${salida.nombreMaterial || "-"}</td>
                    <td class="text-end small">${cantidad.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="text-end small">$${precio.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="text-end small fw-semibold text-success">$${total.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="small">${salida.nombreCentroAcopio || "-"}</td>
                    <td class="text-center">
                        <div class="d-flex gap-2 justify-content-center">
                            <button type="button" class="btn btn-sm btn-success text-white btn-detalles-salida" data-venta-id="${salida.ventaId}" title="Ver detalles">
                                <i class="bi bi-eye-fill"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-success btn-eliminar-salida" data-venta-id="${salida.ventaId}" title="Eliminar">
                                <i class="bi bi-trash3-fill"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
      })
      .join("");

    const badge = document.getElementById("badgeSalidasCount");
    if (badge) badge.textContent = salidasData.length + " registros";
    actualizarPaginacionSalidas(totalPaginas);
  }

  function actualizarPaginacionSalidas(totalPaginas) {
    const paginacion = document.getElementById("paginacionSalidas");
    if (!paginacion) return;
    if (totalPaginas <= 0) {
      paginacion.innerHTML = "";
      return;
    }
    const paginaActual = globalThis.PAGINA_ACTUAL_SALIDAS || 1;
    let html =
      '<li class="page-item ' +
      (paginaActual <= 1 ? "disabled" : "") +
      '"><a class="page-link" href="#" onclick="cambiarPaginaSalidas(' +
      (paginaActual - 1) +
      '); return false;">Anterior</a></li>';
    for (let i = 1; i <= totalPaginas; i++) {
      html +=
        '<li class="page-item ' +
        (i === paginaActual ? "active" : "") +
        '"><a class="page-link" href="#" onclick="cambiarPaginaSalidas(' +
        i +
        '); return false;">' +
        i +
        "</a></li>";
    }
    html +=
      '<li class="page-item ' +
      (paginaActual >= totalPaginas ? "disabled" : "") +
      '"><a class="page-link" href="#" onclick="cambiarPaginaSalidas(' +
      (paginaActual + 1) +
      '); return false;">Siguiente</a></li>';
    paginacion.innerHTML = html;
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

    const material =
      document.getElementById("filtroHistorialMaterial")?.value || "";
    const categoria =
      document.getElementById("filtroHistorialCategoria")?.value || "";
    const tipoMaterial =
      document.getElementById("filtroHistorialTipo")?.value || "";
    const centroAcopio =
      document.getElementById("filtroHistorialCentroAcopio")?.value || "";
    const tipoMovimiento =
      document.getElementById("filtroHistorialTipoMovimiento")?.value || "";
    const fechaDesde =
      document.getElementById("filtroHistorialDesde")?.value || "";
    const fechaHasta =
      document.getElementById("filtroHistorialHasta")?.value || "";

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
      window.PAGINA_ACTUAL_HISTORIAL = 1;

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

    tbody.innerHTML = paginaMovimientos
      .map((mov) => {
        const fecha = new Date(mov.fecha).toLocaleString("es-CO", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });
        const cantidadNumber = parseFloat(mov.cantidad || 0);
        const cantidad = cantidadNumber.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
        const precioNumber = parseFloat(mov.precio || 0);
        const precio = precioNumber.toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
        const tipoBadge =
          mov.tipo === "Compra"
            ? '<span class="badge bg-danger">Compra</span>'
            : '<span class="badge bg-success">Venta</span>';
        const total = (cantidadNumber * precioNumber).toLocaleString("es-CO", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });

        const editBtn =
          mov.tipo === "Compra"
            ? `<button type="button" class="btn btn-sm btn-danger text-white btn-editar-historial-compra" data-compra-id="${mov.compraId}" title="Ver detalles"><i class="bi bi-eye"></i></button>`
            : `<button type="button" class="btn btn-sm btn-success text-white btn-editar-historial-venta" data-venta-id="${mov.ventaId}" title="Ver detalles"><i class="bi bi-eye"></i></button>`;
        const delBtn =
          mov.tipo === "Compra"
            ? `<button type="button" class="btn btn-sm btn-outline-danger btn-eliminar-historial-compra" data-compra-id="${mov.compraId}" title="Eliminar compra"><i class="bi bi-trash3-fill"></i></button>`
            : `<button type="button" class="btn btn-sm btn-outline-success btn-eliminar-historial-venta" data-venta-id="${mov.ventaId}" title="Eliminar venta"><i class="bi bi-trash3-fill"></i></button>`;

        return `
                <tr>
                    <td class="small">${fecha}</td>
                    <td class="small">${tipoBadge}</td>
                    <td class="small fw-bold">${mov.nombreMaterial || "-"}</td>
                    <td class="text-end small">${cantidad}</td>
                    <td class="text-end small">$${precio}</td>
                    <td class="text-end small fw-semibold">$${total}</td>
                    <td class="text-center">${editBtn} ${delBtn}</td>
                </tr>
            `;
      })
      .join("");

    const badge = document.getElementById("badgeHistorialCount");
    if (badge) badge.textContent = movimientosFiltrados.length + " registros";
    actualizarPaginacionHistorial(totalPaginas);
  }

  function actualizarPaginacionHistorial(totalPaginas) {
    const paginacion = document.getElementById("paginacionHistorial");
    if (!paginacion) return;
    if (totalPaginas <= 0) {
      paginacion.innerHTML = "";
      return;
    }
    const paginaActual = globalThis.PAGINA_ACTUAL_HISTORIAL || 1;
    let html =
      '<li class="page-item ' +
      (paginaActual <= 1 ? "disabled" : "") +
      '"><a class="page-link" href="#" onclick="cambiarPaginaHistorial(' +
      (paginaActual - 1) +
      '); return false;">Anterior</a></li>';
    for (let i = 1; i <= totalPaginas; i++) {
      html +=
        '<li class="page-item ' +
        (i === paginaActual ? "active" : "") +
        '"><a class="page-link" href="#" onclick="cambiarPaginaHistorial(' +
        i +
        '); return false;">' +
        i +
        "</a></li>";
    }
    html +=
      '<li class="page-item ' +
      (paginaActual >= totalPaginas ? "disabled" : "") +
      '"><a class="page-link" href="#" onclick="cambiarPaginaHistorial(' +
      (paginaActual + 1) +
      '); return false;">Siguiente</a></li>';
    paginacion.innerHTML = html;
  }
  globalThis.cambiarPaginaHistorial = function (pagina) {
    globalThis.PAGINA_ACTUAL_HISTORIAL = pagina;
    renderizarHistorial();
  };

  globalThis.cambiarMaterial = function () {
    // Limpiar campos...
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
    if (formEntradaContainer) formEntradaContainer.style.display = "none";
    if (formSalidaContainer) formSalidaContainer.style.display = "none";
    const seccionBusquedaMaterial = document.getElementById(
      "seccionBusquedaMaterial",
    );
    if (seccionBusquedaMaterial)
      seccionBusquedaMaterial.style.display = "block";
  };

  // Actualizar stocks
  function actualizarStock(prefix, op) {
    const stock = parseFloat(
      document.getElementById(prefix + "StockActual")?.value || 0,
    );
    const cantidad = parseFloat(
      document.getElementById(prefix + "Cantidad")?.value || 0,
    );
    const resultante = op === "+" ? stock + cantidad : stock - cantidad;
    const resEl = document.getElementById(
      prefix + (op === "+" ? "StockResultante" : "StockRestante"),
    );
    if (resEl)
      resEl.textContent = isNaN(resultante) ? "-" : resultante.toFixed(2);
  }
  const entCant = document.getElementById("entradaCantidad"),
    entPrecio = document.getElementById("entradaPrecioCompra"),
    entTotal = document.getElementById("entradaTotalCompra"),
    entStock = document.getElementById("entradaStockActual");

  function actualizarTotalEntrada() {
    const cantidad = parseFloat(entCant?.value || 0);
    const precio = parseFloat(entPrecio?.value || 0);
    const total = cantidad * precio;
    if (entTotal) entTotal.value = !isNaN(total) ? total.toFixed(2) : "";
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
    const cantidad = parseFloat(salCant?.value || 0);
    const precio = parseFloat(salPrecio?.value || 0);
    const total = cantidad * precio;
    if (salTotal) salTotal.value = !isNaN(total) ? total.toFixed(2) : "";
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

  // Función para mostrar error de campo usando Bootstrap validation
  globalThis.mostrarErrorCampo = function (input, mensaje) {
    // Limpiar cualquier error existente
    limpiarErrorCampo(input);

    // Añadir clase is-invalid al input
    input.classList.add("is-invalid");

    // Crear y insertar el div de feedback
    const feedbackDiv = document.createElement("div");
    feedbackDiv.className = "invalid-feedback";
    feedbackDiv.textContent = mensaje;

    // Insertar después del input
    input.parentNode.insertBefore(feedbackDiv, input.nextSibling);
  };

  // Función para limpiar error de campo
  globalThis.limpiarErrorCampo = function (input) {
    // Remover clase is-invalid
    input.classList.remove("is-invalid");

    // Remover div de feedback si existe
    const feedbackDiv = input.parentNode.querySelector(".invalid-feedback");
    if (feedbackDiv) {
      feedbackDiv.remove();
    }
  };

  // Función para validar un campo requerido
  globalThis.validarCampoRequerido = function (
    input,
    mensajeError = "Este campo es requerido",
  ) {
    limpiarErrorCampo(input);

    let esValido = true;
    const valor = input.value.trim();

    // Para inputs tipo number, también verificamos que no esté vacío o sea 0 cuando es requerido
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

  // Función especializada para validar cantidades
  globalThis.validarCantidad = function (input) {
    limpiarErrorCampo(input);

    const valor = input.value.trim();

    // Verificar si está vacío
    if (valor === "") {
      mostrarErrorCampo(input, "Ingrese la cantidad");
      return false;
    }

    // Convertir a número
    const cantidad = Number.parseFloat(valor);

    // Verificar si es negativo
    if (cantidad < 0) {
      mostrarErrorCampo(input, "No se permiten valores negativos");
      return false;
    }

    // Verificar si es cero
    if (cantidad === 0) {
      mostrarErrorCampo(input, "La cantidad debe ser mayor a 0");
      return false;
    }

    // Verificar si es un número válido
    if (Number.isNaN(cantidad)) {
      mostrarErrorCampo(input, "Ingrese una cantidad válida");
      return false;
    }

    return true;
  };

  // Función para validar campos de fecha
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

  // Agregar validación en tiempo real (blur) a los campos de entrada
  function agregarValidacionEnTiempoRealEntrada() {
    const campos = [
      {
        id: "entradaCantidad",
        tipo: "cantidad",
        mensaje: "Ingrese la cantidad",
      },
      { id: "entradaFecha", tipo: "fecha", mensaje: "Seleccione una fecha" },
      {
        id: "entradaPrecioCompra",
        tipo: "requerido",
        mensaje: "Ingrese un precio de compra",
      },
    ];

    campos.forEach((campo) => {
      const input = document.getElementById(campo.id);
      if (input) {
        input.addEventListener("blur", function () {
          if (campo.tipo === "requerido") {
            validarCampoRequerido(input, campo.mensaje);
          } else if (campo.tipo === "fecha") {
            validarCampoFecha(input, campo.mensaje);
          } else if (campo.tipo === "cantidad") {
            validarCantidad(input);
          }
        });

        // También validar al escribir para quitar errores si el usuario corrige
        input.addEventListener("input", function () {
          limpiarErrorCampo(input);
        });
      }
    });
  }

  // Agregar validación en tiempo real (blur) a los campos de salida
  //

  function agregarValidacionEnTiempoRealSalida() {
    const campos = [
      {
        id: "salidaCantidad",
        tipo: "cantidad",
        mensaje: "Ingrese la cantidad",
      },
      { id: "salidaFecha", tipo: "fecha", mensaje: "Seleccione una fecha" },
      {
        id: "salidaPrecioVenta",
        tipo: "requerido",
        mensaje: "Ingrese un precio de venta",
      },
      {
        id: "salidaCentroAcopio",
        tipo: "select",
        mensaje: "Seleccione un centro de acopio",
      },
    ];

    campos.forEach((campo) => {
      const input = document.getElementById(campo.id);
      if (input) {
        input.addEventListener("blur", function () {
          if (campo.tipo === "requerido") {
            validarCampoRequerido(input, campo.mensaje);
          } else if (campo.tipo === "fecha") {
            validarCampoFecha(input, campo.mensaje);
          } else if (campo.tipo === "cantidad") {
            validarCantidad(input);
          } else if (campo.tipo === "select") {
            if (input.value === "") {
              mostrarErrorCampo(input, campo.mensaje);
            } else {
              limpiarErrorCampo(input);
            }
          }
        });

        // También validar al escribir para quitar errores si el usuario corrige
        input.addEventListener("input", function () {
          limpiarErrorCampo(input);
        });
      }
    });
  }

    const formEntrada = document.getElementById("formEntrada");
    if (formEntrada) {
      formEntrada.addEventListener("submit", function (ev) {
        console.log("Validando formulario de entrada");
        ev.preventDefault();
        
        // Disable submit button to prevent duplicate submissions
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';
        }
        
        // Validar campos requeridos
        const materialSeleccionado = document.getElementById(
          "entradaMaterialSeleccionado",
        );
        const cantidad = document.getElementById("entradaCantidad");
        const fecha = document.getElementById("entradaFecha");
        const precioCompra = document.getElementById("entradaPrecioCompra");

      let esValido = true;

      if (materialSeleccionado && materialSeleccionado.value.trim() === "") {
        console.log("Material no seleccionado");
        mostrarErrorCampo(materialSeleccionado, "Seleccione un material");
        esValido = false;
      }

      if (!validarCantidad(cantidad)) {
        console.log("Cantidad inválida");
        esValido = false;
      }

      if (!validarCampoFecha(fecha, "Seleccione una fecha")) {
        console.log("Fecha inválida");
        esValido = false;
      }

      if (!validarCampoRequerido(precioCompra, "Ingrese un precio de compra")) {
        console.log("Precio de compra inválido");
        esValido = false;
      }

      if (!esValido) {
        console.log("Formulario no válido, deteniendo envío");
        return; // Detener el envío si hay errores de validación
      }

      console.log("Formulario válido, enviando...");

      const data = {
        inventarioId: document.getElementById("entradaInventarioId")?.value,
        materialId: document.getElementById("entradaMaterialId")?.value,
        cantidad: document.getElementById("entradaCantidad")?.value,
        fechaCompra: document.getElementById("entradaFecha")?.value,
        precioCompra: document.getElementById("entradaPrecioCompra")?.value,
        observaciones: document.getElementById("entradaObservaciones")?.value,
        puntoEcaId: document.querySelector("section[data-punto-eca-id]")
          ?.dataset.puntoEcaId,
      };
      let csrfToken =
        document
          .querySelector('meta[name="csrf-token"]')
          ?.getAttribute("content") || "";
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
          if (!resp.error) {
            mostrarFeedbackMovimientos(
              resp.mensaje || "¡Compra registrada! 🎉",
              "success",
            );
            // Limpiar alertas de campos
            const inputsEntrada = formEntrada.querySelectorAll(
              "input, select, textarea",
            );
            inputsEntrada.forEach((input) => limpiarErrorCampo(input));
            formEntrada.reset();
            location.reload();
          } else {
            mostrarFeedbackMovimientos(
              resp.mensaje || "Error: operación no realizada",
              "danger",
            );
          }
        })
        .catch((err) => {
          mostrarFeedbackMovimientos(
            "Error al conectar con el backend: " + err,
            "danger",
          );
        });
    });
  }

    const formSalida = document.getElementById("formSalida");
    if (formSalida) {
      formSalida.addEventListener("submit", function (ev) {
        console.log("Validando formulario de salida");
        ev.preventDefault();
        
        // Disable submit button to prevent duplicate submissions
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';
        }
        
        // Validar campos requeridos
      const materialSeleccionado = document.getElementById(
        "salidaMaterialSeleccionado",
      );
      const cantidad = document.getElementById("salidaCantidad");
      const fecha = document.getElementById("salidaFecha");
      const precioVenta = document.getElementById("salidaPrecioVenta");
      const centroAcopio = document.getElementById("salidaCentroAcopio");

      let esValido = true;

      if (materialSeleccionado && materialSeleccionado.value.trim() === "") {
        console.log("Material no seleccionado");
        mostrarErrorCampo(materialSeleccionado, "Seleccione un material");
        esValido = false;
      }

      if (!validarCantidad(cantidad)) {
        console.log("Cantidad inválida");
        esValido = false;
      }

      if (!validarCantidad(cantidad)) {
        console.log("Cantidad inválida");
        esValido = false;
      }

      if (!validarCampoFecha(fecha, "Seleccione una fecha")) {
        console.log("Fecha inválida");
        esValido = false;
      }

      if (!validarCampoRequerido(precioVenta, "Ingrese un precio de venta")) {
        console.log("Precio de venta inválido");
        esValido = false;
      }

      // Validar centro de acopio (select)
      if (centroAcopio && centroAcopio.value === "") {
        console.log("Centro de acopio no seleccionado");
        crearAlertaCampo(
          centroAcopio,
          "Seleccione un centro de acopio",
          "danger",
        );
        esValido = false;
      }

      if (!esValido) {
        console.log("Formulario no válido, deteniendo envío");
        return; // Detener el envío si hay errores de validación
      }

      const data = {
        inventarioId: document.getElementById("salidaInventarioId")?.value,
        materialId: document.getElementById("salidaMaterialId")?.value,
        cantidad: document.getElementById("salidaCantidad")?.value,
        fechaVenta: document.getElementById("salidaFecha")?.value,
        precioVenta: document.getElementById("salidaPrecioVenta")?.value,
        observaciones: document.getElementById("salidaObservaciones")?.value,
        centroAcopioId: document.getElementById("salidaCentroAcopio")?.value,
        puntoEcaId: document.querySelector("section[data-punto-eca-id]")
          ?.dataset.puntoEcaId,
      };
      let csrfToken =
        document
          .querySelector('meta[name="csrf-token"]')
          ?.getAttribute("content") || "";
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
          if (!resp.error) {
            mostrarFeedbackMovimientos(
              resp.mensaje || "¡Venta registrada! 🎉",
              "success",
            );
            // Limpiar alertas de campos
            const inputsSalida = formSalida.querySelectorAll(
              "input, select, textarea",
            );
            inputsSalida.forEach((input) => limpiarErrorCampo(input));
            formSalida.reset();
            setTimeout(renderizarSalidas, 200);
          } else {
            mostrarFeedbackMovimientos(
              resp.mensaje || "Error: operación no realizada",
              "danger",
            );
          }
        })
        .catch((err) => {
          mostrarFeedbackMovimientos(
            "Error al conectar con el backend: " + err,
            "danger",
          );
        });
    });
  }
});

// Carga Masiva (IIFE)
(function () {
  let modoCargaMasiva = null;
  function setModoCargaMasiva(mode) {
    modoCargaMasiva = mode || "compras";
    let inputArchivo = document.getElementById("inputArchivoCargaMasiva");
    if (inputArchivo) inputArchivo.value = "";
    let feedback = document.getElementById("feedbackCargaMasiva");
    if (feedback) feedback.innerHTML = "";
    let spanTipo = document.getElementById("spanTipoCargaMasiva");
    if (spanTipo) {
      spanTipo.textContent = modoCargaMasiva === "compras" ? "Compra" : "Venta";
      spanTipo.className =
        modoCargaMasiva === "compras"
          ? "badge bg-info fw-normal"
          : "badge bg-success fw-normal";
    }
    let tipoOperacion = document.getElementById("tipoOperacionRequerido");
    if (tipoOperacion)
      tipoOperacion.textContent =
        modoCargaMasiva === "compras" ? "compra" : "venta";

    let campoPrecioCompra = document.getElementById("campoPrecioCompra");
    let campoFechaCompra = document.getElementById("campoFechaCompra");
    let campoPrecioVenta = document.getElementById("campoPrecioVenta");
    let campoFechaVenta = document.getElementById("campoFechaVenta");

    if (modoCargaMasiva === "compras") {
      if (campoPrecioCompra) campoPrecioCompra.style.display = "";
      if (campoFechaCompra) campoFechaCompra.style.display = "";
      if (campoPrecioVenta) campoPrecioVenta.style.display = "none";
      if (campoFechaVenta) campoFechaVenta.style.display = "none";
    } else {
      if (campoPrecioCompra) campoPrecioCompra.style.display = "none";
      if (campoFechaCompra) campoFechaCompra.style.display = "none";
      if (campoPrecioVenta) campoPrecioVenta.style.display = "";
      if (campoFechaVenta) campoFechaVenta.style.display = "";
    }

    let descargarPlantilla = document.getElementById(
      "descargarPlantillaCargaMasiva",
    );
    if (descargarPlantilla) {
      if (modoCargaMasiva === "compras") {
        descargarPlantilla.href = "/static/plantilla_carga_compras.csv";
        descargarPlantilla.textContent =
          "Descargar plantilla de ejemplo para compras";
      } else {
        descargarPlantilla.href = "/static/plantilla_carga_ventas.csv";
        descargarPlantilla.textContent =
          "Descargar plantilla de ejemplo para ventas";
      }
    }
  }

  function abrirModalCargaMasiva(e) {
    if (e && e.preventDefault) e.preventDefault();
    let mode = "compras";
    if (e && e.target && e.target.id === "btnBulkImportCompras")
      mode = "compras";
    if (e && e.target && e.target.id === "btnBulkImportVentas") mode = "ventas";
    setModoCargaMasiva(mode);
    const modal = new bootstrap.Modal(
      document.getElementById("modalCargaMasiva"),
    );
    modal.show();
  }

  document.addEventListener("DOMContentLoaded", function () {
    let btnCompras = document.getElementById("btnBulkImportCompras");
    let btnVentas = document.getElementById("btnBulkImportVentas");
    if (btnCompras) btnCompras.addEventListener("click", abrirModalCargaMasiva);
    if (btnVentas) btnVentas.addEventListener("click", abrirModalCargaMasiva);

    let form = document.getElementById("formCargaMasiva");
    if (form) {
      form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        let feedback = document.getElementById("feedbackCargaMasiva");
        feedback.innerHTML =
          '<span class="text-info">Subiendo archivo, por favor espera...</span>';
        let archivoInput = document.getElementById("inputArchivoCargaMasiva");
        let archivo =
          archivoInput && archivoInput.files && archivoInput.files[0];
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
                                ${data.detalles
                                  .map((r) => {
                                    const isOk = r.status === "success";
                                    const rowClass = isOk
                                      ? "list-group-item list-group-item-success"
                                      : "list-group-item list-group-item-danger";
                                    return `<li class='${rowClass} d-flex justify-content-between align-items-center'>
                                        <span><b>Fila ${r.fila}:</b> ${r.mensaje || r.status}</span>
                                        <span>${isOk ? "✅" : "❌"}</span>
                                    </li>`;
                                  })
                                  .join("")}</ul></div>`;
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
  });
})();

// Listeners Modales de Edición (Envuelto en DOMContentLoaded para proteger funciones)
document.addEventListener("DOMContentLoaded", function () {
  function limpiarEstadoModales() {
    if (document.querySelectorAll(".modal.show").length > 0) return;
    document.querySelectorAll(".modal-backdrop").forEach((backdrop) => backdrop.remove());
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("overflow");
    document.body.style.removeProperty("padding-right");
  }

  ["detallesEntradaModal", "detallesSalidaModal", "editarCompraModal", "editarVentaModal"].forEach((modalId) => {
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
      alert("No se encontraron los detalles de esta entrada");
      return;
    }

    const fecha = entrada.fechaCompra
      ? new Date(entrada.fechaCompra).toLocaleDateString("es-CO")
      : "-";
    const cantidad = parseFloat(entrada.cantidad || 0);
    const precio = parseFloat(entrada.precioCompra || 0);
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

  // Eliminar entrada desde tabla (ya está arriba, pero el de modal está aquí)
  const btnEliminarEntradaModal = document.getElementById("btnEliminarEntrada");
  if (btnEliminarEntradaModal) {
    btnEliminarEntradaModal.addEventListener("click", function () {
      const compraId = this.dataset.compraId;
      if (!confirm("¿Estás seguro de que deseas eliminar esta entrada?"))
        return;

      const entrada = globalThis.ENTRADAS_INICIALES.find(
        (e) => e.compraId === compraId,
      );
      if (!entrada) return;

      const puntoId = document.querySelector("section[data-punto-eca-id]")
        ?.dataset.puntoEcaId;
      const datosEliminar = {
        compraId: compraId,
        inventarioId: entrada.inventarioId || "",
        puntoId: puntoId,
        materialId: entrada.materialId || "",
      };

      let csrfToken =
        document
          .querySelector('meta[name="csrf-token"]')
          ?.getAttribute("content") || "";
      fetch(`/punto-eca/movimientos/borrar-compra/${compraId}/`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(datosEliminar),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success || data.ok || !data.error) {
            alert("Entrada eliminada correctamente");
            location.reload();
          } else {
            alert(
              "Error al eliminar: " + (data.mensaje || "Error desconocido"),
            );
          }
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
         cantidad: parseFloat(
           document.getElementById("editCompraCantidad").value,
         ),
         fechaCompra: document.getElementById("editCompraFecha").value,
         precioCompra: parseFloat(
           document.getElementById("editCompraPrecio").value,
         ),
         observaciones: document.getElementById("editCompraObservaciones").value,
       };

       let csrfToken =
         document
           .querySelector('meta[name="csrf-token"]')
           ?.getAttribute("content") || "";
       fetch(
         `/punto-eca/movimientos/editar-compra/${datosActualizacion.compraId}/`,
         {
           method: "PUT",
           headers: {
             "Content-Type": "application/json",
             "X-CSRFToken": csrfToken,
           },
           body: JSON.stringify(datosActualizacion),
         },
       )
         .then((res) => res.json())
        .then((data) => {
          // Back-end returns { error: false, mensaje: '...' } on success
          if (data && (data.error === false || data.ok || data.success || data.status === 200 || data.status === 201)) {
            alert(data.mensaje || data.message || "Compra actualizada");
            location.reload();
          } else {
            alert(data.mensaje || data.message || "Error al actualizar");
          }
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
         cantidad: parseFloat(
           document.getElementById("editVentaCantidad").value,
         ),
         fechaVenta: document.getElementById("editVentaFecha").value,
         precioVenta: parseFloat(
           document.getElementById("editVentaPrecio").value,
         ),
         centroAcopioId: document.getElementById("editVentaCentro").value,
         observaciones: document.getElementById("editVentaObservaciones").value,
       };

       let csrfToken =
         document
           .querySelector('meta[name="csrf-token"]')
           ?.getAttribute("content") || "";
       fetch(
         `/punto-eca/movimientos/editar-venta/${datosActualizacion.ventaId}/`,
         {
           method: "PUT",
           headers: {
             "Content-Type": "application/json",
             "X-CSRFToken": csrfToken,
           },
           body: JSON.stringify(datosActualizacion),
         },
       )
         .then((res) => res.json())
        .then((data) => {
          // Back-end returns { error: false, mensaje: '...' } on success
          if (data && (data.error === false || data.ok || data.success || data.status === 200 || data.status === 201)) {
            alert(data.mensaje || data.message || "Venta actualizada");
            location.reload();
          } else {
            alert(data.mensaje || data.message || "Error al actualizar");
          }
        });
     });
   }

   // Editar desde modal de detalles (entradas y salidas regulares e historial)
   document.addEventListener("click", function (e) {
     const btn = e.target.closest("#btnEditarEntrada, #btnEditarSalida");
     if (!btn) return;

     // Determine which button was clicked and get the appropriate ID
     let movimientoId = null;
     let esCompra = false;
     let esHistorial = false;

     if (btn.id === "btnEditarEntrada") {
       movimientoId = btn.dataset.compraId;
       // Check if this is from historial
       const historialBtn = document.querySelector(`.btn-editar-historial-compra[data-compra-id="${movimientoId}"]`);
       esHistorial = !!historialBtn;
       esCompra = true;
     } else if (btn.id === "btnEditarSalida") {
       movimientoId = btn.dataset.ventaId;
       // Check if this is from historial
       const historialBtn = document.querySelector(`.btn-editar-historial-venta[data-venta-id="${movimientoId}"]`);
       esHistorial = !!historialBtn;
       esCompra = false;
     }

     if (!movimientoId) return;

     // Hide the details modal
     const modalId = esCompra ? "detallesEntradaModal" : "detallesSalidaModal";
     const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
     if (modal) modal.hide();

     if (esHistorial) {
       // Handle history items
       if (esCompra) {
         const entrada = globalThis.HISTORIAL_COMPRAS.find(
           (e) => e.compraId === movimientoId,
         );
         if (!entrada) return;

         document.getElementById("editCompraId").value = entrada.compraId || "";
         document.getElementById("editInventarioId").value =
           entrada.inventarioId || "";
         document.getElementById("editCompraMaterialId").value =
           entrada.materialId || "";
         document.getElementById("editCompraMaterial").value =
           entrada.nombreMaterial || "";
         document.getElementById("editCompraFecha").value = entrada.fechaCompra
           ? new Date(entrada.fechaCompra).toISOString().slice(0, 16)
           : "";
         document.getElementById("editCompraCantidad").value =
           entrada.cantidad || "";
         document.getElementById("editCompraPrecio").value =
           entrada.precioCompra || "";
         document.getElementById("editCompraObservaciones").value =
           entrada.observaciones || "";

         const modalEditar = new bootstrap.Modal(
           document.getElementById("editarCompraModal"),
         );
         modalEditar.show();
       } else {
         const venta = globalThis.HISTORIAL_VENTAS.find(
           (v) => v.ventaId === movimientoId,
         );
         if (!venta) return;

         document.getElementById("editVentaId").value = venta.ventaId || "";
         document.getElementById("editInventarioIdVenta").value =
           venta.inventarioId || "";
         document.getElementById("editVentaMaterialId").value =
           venta.materialId || "";
         document.getElementById("editVentaMaterial").value =
           venta.nombreMaterial || "";
         document.getElementById("editVentaFecha").value = venta.fechaVenta
           ? new Date(venta.fechaVenta).toISOString().slice(0, 16)
           : "";
         document.getElementById("editVentaCantidad").value =
           venta.cantidad || "";
          document.getElementById("editVentaPrecio").value =
            venta.precioVenta || "";
          document.getElementById("editVentaCentro").value =
            venta.centroAcopioId || "";
          document.getElementById("editVentaObservaciones").value =
            venta.observaciones || "";

         const modalEditar = new bootstrap.Modal(
           document.getElementById("editarVentaModal"),
         );
         modalEditar.show();
       }
     } else {
       // Handle regular items (from entradas/salidas tables)
       if (esCompra) {
         const entrada = globalThis.ENTRADAS_INICIALES.find(
           (e) => e.compraId === movimientoId,
         );
         if (!entrada) return;

         document.getElementById("editCompraId").value = entrada.compraId || "";
         document.getElementById("editInventarioId").value =
           entrada.inventarioId || "";
         document.getElementById("editCompraMaterialId").value =
           entrada.materialId || "";
         document.getElementById("editCompraMaterial").value =
           entrada.nombreMaterial || "";
          document.getElementById("editCompraFecha").value = entrada.fechaCompra
            ? new Date(entrada.fechaCompra).toISOString().slice(0, 16)
            : "";
          document.getElementById("editCompraCantidad").value =
            entrada.cantidad || "";
          document.getElementById("editCompraPrecio").value =
            entrada.precioCompra || "";
          document.getElementById("editCompraObservaciones").value =
            entrada.observaciones || "";

         const modalEditar = new bootstrap.Modal(
           document.getElementById("editarCompraModal"),
         );
         modalEditar.show();
       } else {
         const salida = globalThis.SALIDAS_INICIALES.find(
           (s) => s.ventaId === movimientoId,
         );
         if (!salida) return;

          document.getElementById("editVentaId").value = salida.ventaId || "";
          document.getElementById("editInventarioIdVenta").value =
            salida.inventarioId || "";
          document.getElementById("editVentaMaterialId").value =
            salida.materialId || "";
          document.getElementById("editVentaMaterial").value =
            salida.nombreMaterial || "";
          document.getElementById("editVentaFecha").value = salida.fechaVenta
            ? new Date(salida.fechaVenta).toISOString().slice(0, 16)
            : "";
          document.getElementById("editVentaCantidad").value =
            salida.cantidad || "";
          document.getElementById("editVentaPrecio").value =
            salida.precioVenta || "";
          document.getElementById("editVentaCentro").value =
            salida.centroAcopioId || "";
          document.getElementById("editVentaObservaciones").value =
            salida.observaciones || "";

         const modalEditar = new bootstrap.Modal(
           document.getElementById("editarVentaModal"),
         );
         modalEditar.show();
       }
     }
   });
 });

// Manejadores Ligeros Adicionales (Reparación de la función huérfana del final)
(function () {
  function safeParseFloat(v) {
    const n = parseFloat(v);
    return isNaN(n) ? null : n;
  }
  // Tu función original estaba redundante aquí, ya que formSalida y formEntrada ya
  // están manejados correctamente en los bloques superiores dentro de DOMContentLoaded.
  // Lo dejamos como un wrapper seguro para cualquier lógica extra que necesites agregar.
})();

// Ver Detalles de Salida
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-detalles-salida");
  if (!btn) return;
  const ventaId = btn.dataset.ventaId;
  const salida = globalThis.SALIDAS_INICIALES.find(
    (s) => s.ventaId === ventaId,
  );
  if (!salida) {
    alert("No se encontraron los detalles de esta venta");
    return;
  }

  const fecha = salida.fechaVenta
    ? new Date(salida.fechaVenta).toLocaleDateString("es-CO")
    : "-";
  const cantidad = parseFloat(salida.cantidad || 0);
  const precio = parseFloat(salida.precioVenta || 0);
  const total = cantidad * precio;

  document.getElementById("detSalidaMaterial").textContent =
    salida.nombreMaterial || "-";
  document.getElementById("detSalidaFecha").textContent = fecha;
  document.getElementById("detSalidaCantidad").textContent =
    cantidad.toLocaleString("es-CO", { minimumFractionDigits: 2 });
  document.getElementById("detSalidaPrecio").textContent =
    "$" + precio.toLocaleString("es-CO", { minimumFractionDigits: 2 });
  document.getElementById("detSalidaTotal").textContent =
    "$" + total.toLocaleString("es-CO", { minimumFractionDigits: 2 });
  document.getElementById("detSalidaObservaciones").textContent =
    salida.observaciones || "Sin observaciones";
  document.getElementById("detSalidaCentro").textContent =
    salida.nombreCentroAcopio || "-";

  const btnDel = document.getElementById("btnEliminarSalida");
  const btnEdit = document.getElementById("btnEditarSalida");
  if (btnDel) btnDel.dataset.ventaId = ventaId;
  if (btnEdit) btnEdit.dataset.ventaId = ventaId;

  const modal = new bootstrap.Modal(
    document.getElementById("detallesSalidaModal"),
  );
  modal.show();
});

// Ver Detalles de Historial (usa modales existentes)
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-editar-historial-compra, .btn-editar-historial-venta");
  if (!btn) return;
  let movimientoId, tipoMovimiento, modalId;
  
  if (btn.classList.contains("btn-editar-historial-compra")) {
    movimientoId = btn.dataset.compraId;
    tipoMovimiento = "Compra";
    modalId = "detallesEntradaModal"; // Usar modal de entrada para compras
  } else if (btn.classList.contains("btn-editar-historial-venta")) {
    movimientoId = btn.dataset.ventaId;
    tipoMovimiento = "Venta";
    modalId = "detallesSalidaModal"; // Usar modal de salida para ventas
  }
  
  let movimiento;
  if (tipoMovimiento === "Compra") {
    movimiento = globalThis.HISTORIAL_COMPRAS.find(
      (c) => c.compraId === movimientoId,
    );
  } else {
    movimiento = globalThis.HISTORIAL_VENTAS.find(
      (v) => v.ventaId === movimientoId,
    );
  }
  
  if (!movimiento) {
    alert("No se encontraron los detalles de este movimiento");
    return;
  }

  const fecha = movimiento.fecha
    ? new Date(movimiento.fecha).toLocaleDateString("es-CO")
    : "-";
  const cantidad = parseFloat(movimiento.cantidad || 0);
  const precio = parseFloat(movimiento.precio || 0);
  const total = cantidad * precio;

  // Actualizar elementos en el modal apropiado
  if (modalId === "detallesEntradaModal") {
    // Para compras, usar elementos del modal de entrada
    document.getElementById("detEntradaMaterial").textContent =
      movimiento.nombreMaterial || "-";
    document.getElementById("detEntradaFecha").textContent = fecha;
    document.getElementById("detEntradaCantidad").textContent =
      cantidad.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detEntradaPrecio").textContent =
      "$" + precio.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detEntradaTotal").textContent =
      "$" + total.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detEntradaObservaciones").textContent =
      movimiento.observaciones || "Sin observaciones";
  } else if (modalId === "detallesSalidaModal") {
    // Para ventas, usar elementos del modal de salida
    document.getElementById("detSalidaMaterial").textContent =
      movimiento.nombreMaterial || "-";
    document.getElementById("detSalidaFecha").textContent = fecha;
    document.getElementById("detSalidaCantidad").textContent =
      cantidad.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detSalidaPrecio").textContent =
      "$" + precio.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detSalidaTotal").textContent =
      "$" + total.toLocaleString("es-CO", { minimumFractionDigits: 2 });
    document.getElementById("detSalidaObservaciones").textContent =
      movimiento.observaciones || "Sin observaciones";
    document.getElementById("detSalidaCentro").textContent =
      movimiento.nombreCentroAcopio || "-";
  }

   const modal = new bootstrap.Modal(
     document.getElementById(modalId),
   );
   // Mark this as a history item for edit/delete button handlers
   document.getElementById(modalId).dataset.isHistoryItem = "true";
   document.getElementById(modalId).dataset.historyItemType = tipoMovimiento.toLowerCase();
  // Asegurar que los botones internos del modal tienen el dataset correcto
  try {
    if (modalId === "detallesEntradaModal") {
      const btnEditEntrada = document.getElementById("btnEditarEntrada");
      const btnDelEntrada = document.getElementById("btnEliminarEntrada");
      if (btnEditEntrada) btnEditEntrada.dataset.compraId = movimientoId;
      if (btnDelEntrada) btnDelEntrada.dataset.compraId = movimientoId;
    } else if (modalId === "detallesSalidaModal") {
      const btnEditSalida = document.getElementById("btnEditarSalida");
      const btnDelSalida = document.getElementById("btnEliminarSalida");
      if (btnEditSalida) btnEditSalida.dataset.ventaId = movimientoId;
      if (btnDelSalida) btnDelSalida.dataset.ventaId = movimientoId;
    }
  } catch (e) {
    console.error("Error asignando data-* en modal de historial:", e);
  }
   modal.show();
});

// Calcular total de compra cuando cambie precio o cantidad
function inicializarCalculoCompra() {
  const precioCompraInput = document.getElementById("entradaPrecioCompra");
  const cantidadInput = document.getElementById("entradaCantidad");
  const totalCompraInput = document.getElementById("entradaTotalCompra");
  const stockResultanteSpan = document.getElementById("entradaStockResultante");
  const stockActualInput = document.getElementById("entradaStockActual");

  function calcularTotalCompra() {
    const precio = parseFloat(precioCompraInput.value) || 0;
    const cantidad = parseFloat(cantidadInput.value) || 0;
    const total = precio * cantidad;
    totalCompraInput.value = total.toFixed(2);

    // Calcular stock resultante
    const stockActual = parseFloat(stockActualInput.value) || 0;
    const stockResultante = stockActual + cantidad;
    stockResultanteSpan.textContent = stockResultante.toFixed(2);
  }

  // Agregar listeners
  if (precioCompraInput) {
    precioCompraInput.addEventListener("input", calcularTotalCompra);
  }
  if (cantidadInput) {
    cantidadInput.addEventListener("input", calcularTotalCompra);
  }

  // También calcular al inicializar
  calcularTotalCompra();
}

// Calcular total de venta cuando cambie precio o cantidad
function inicializarCalculoVenta() {
  const precioVentaInput = document.getElementById("salidaPrecioVenta");
  const cantidadInput = document.getElementById("salidaCantidad");
  const totalVentaInput = document.getElementById("salidaTotalVenta");
  const stockRestanteSpan = document.getElementById("salidaStockRestante");
  const stockActualInput = document.getElementById("salidaStockActual");

  function calcularTotalVenta() {
    const precio = parseFloat(precioVentaInput.value) || 0;
    const cantidad = parseFloat(cantidadInput.value) || 0;
    const total = precio * cantidad;
    totalVentaInput.value = total.toFixed(2);

    // Calcular stock resultante (para venta es resta)
    const stockActual = parseFloat(stockActualInput.value) || 0;
    const stockRestante = stockActual - cantidad;
    stockRestanteSpan.textContent = stockRestante.toFixed(2);
  }

  // Agregar listeners
  if (precioVentaInput) {
    precioVentaInput.addEventListener("input", calcularTotalVenta);
  }
  if (cantidadInput) {
    cantidadInput.addEventListener("input", calcularTotalVenta);
  }

  // También calcular al inicializar
  calcularTotalVenta();
}

// Inicializar validación en tiempo real cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
  // agregarValidacionEnTiempoRealEntrada();
  // agregarValidacionEnTiempoRealSalida();
  inicializarCalculoCompra();
  inicializarCalculoVenta();
  // Llenar select de edición de venta con centros disponibles
  try {
    const editVentaSelect = document.getElementById("editVentaCentro");
    if (editVentaSelect) {
      let centros = globalThis.CENTROS || window.CENTROS || [];
      if (!Array.isArray(centros) && typeof centros === "object") {
        centros = Object.values(centros || {});
      }
      // Clear and add default
      editVentaSelect.innerHTML = "<option value=''>Selecciona un centro...</option>";
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
});

// --- FUNCIONES AUXILIARES (Pégala al final o junto a otras funciones) ---
function obtenerFechaHoraActual() {
  const ahora = new Date();
  // Ajuste de zona horaria local
  const ahoraLocal = new Date(
    ahora.getTime() - ahora.getTimezoneOffset() * 60000,
  );
  return ahoraLocal.toISOString().slice(0, 16);
}

// --- BLOQUE PRINCIPAL (Actualiza el que ya tienes) ---
document.addEventListener("DOMContentLoaded", function () {
  // Tus inicializaciones actuales
  inicializarCalculoCompra();
  inicializarCalculoVenta();

  // --- NUEVA LÓGICA DE FECHAS ---
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
