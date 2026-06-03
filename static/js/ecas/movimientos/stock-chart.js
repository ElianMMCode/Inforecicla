/* global Chart */
/**
 * Gráfico temporal de stock (multi-material) para la sección de Movimientos.
 * - Reconstruye la serie histórica de stock por material a partir de
 *   `entradas-data` (+cantidad) y `salidas-data` (-cantidad), anclado en
 *   el stock actual (campo stockActual de cada Inventario).
 * - Renderiza con Chart.js v4. La librería se carga vía CDN en el template.
 * - Datos inyectados por Django con json_script: materiales-stock-data,
 *   entradas-data, salidas-data.
 */

(function initStockChartModule() {
  "use strict";

  /* ============================================================ */
  /* 1. Paleta de colores y estado del módulo                     */
  /* ============================================================ */
  const PALETA_COLORES = [
    "#0d6efd", "#dc3545", "#198754", "#ffc107", "#6f42c1",
    "#fd7e14", "#20c997", "#d63384", "#0dcaf0", "#6c757d",
  ];

  const TZ_BOGOTA = "America/Bogota";
  const MAX_BUCKETS_DIARIO = 120; // 4 meses máx en granularidad día
  const MAX_BUCKETS_SEMANA = 104; // 2 años máx en granularidad semana
  const MAX_BUCKETS_MES = 60; // 5 años máx en granularidad mes

  const state = {
    chart: null,
    materiales: [],
    materialesById: new Map(),
    operacionesByMaterial: new Map(),
    seleccionados: new Set(),
    granularidad: "day",
    mostrarCapacidad: true,
    filtrosAplicados: false,
  };

  /* ============================================================ */
  /* 2. Utilidades                                                 */
  /* ============================================================ */
  function escapeHtml(valor) {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return String(valor ?? "").replaceAll(/[&<>"']/g, (m) => map[m]);
  }

  function leerJsonInyectado(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent || el.innerText || "null");
    } catch (err) {
      console.warn(`No se pudo parsear #${id}`, err);
      return null;
    }
  }

  function parseFecha(isoString) {
    if (!isoString) return null;
    const s = String(isoString).replace(" ", "T");
    const d = new Date(s);
    return Number.isNaN(d.getTime()) ? null : d;
  }

  function toISODate(d) {
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }

  function inicioDelDia(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function inicioDeSemana(d) {
    // Semana ISO: lunes como primer día
    const copia = inicioDelDia(d);
    const dia = copia.getDay(); // 0=domingo, 1=lunes, ...
    const diff = dia === 0 ? -6 : 1 - dia;
    copia.setDate(copia.getDate() + diff);
    return copia;
  }

  function inicioDeMes(d) {
    return new Date(d.getFullYear(), d.getMonth(), 1);
  }

  function bucketDeFecha(fecha, granularidad) {
    if (granularidad === "day") return inicioDelDia(fecha);
    if (granularidad === "week") return inicioDeSemana(fecha);
    return inicioDeMes(fecha);
  }

  function formatearLabelBucket(fecha, granularidad) {
    if (granularidad === "day") {
      return fecha.toLocaleDateString("es-CO", {
        day: "2-digit",
        month: "short",
        timeZone: TZ_BOGOTA,
      });
    }
    if (granularidad === "week") {
      const num = getNumeroSemana(fecha);
      return `Sem ${num}`;
    }
    return fecha.toLocaleDateString("es-CO", {
      month: "short",
      year: "numeric",
      timeZone: TZ_BOGOTA,
    });
  }

  function getNumeroSemana(d) {
    // ISO week number
    const fecha = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    const dia = fecha.getUTCDay() || 7;
    fecha.setUTCDate(fecha.getUTCDate() + 4 - dia);
    const inicioAnio = new Date(Date.UTC(fecha.getUTCFullYear(), 0, 1));
    return Math.ceil(((fecha - inicioAnio) / 86400000 + 1) / 7);
  }

  function generarBuckets(desde, hasta, granularidad) {
    const inicio = bucketDeFecha(desde, granularidad);
    const fin = bucketDeFecha(hasta, granularidad);
    const buckets = [];
    const cursor = new Date(inicio);
    while (cursor <= fin) {
      buckets.push(new Date(cursor));
      if (granularidad === "day") cursor.setDate(cursor.getDate() + 1);
      else if (granularidad === "week") cursor.setDate(cursor.getDate() + 7);
      else cursor.setMonth(cursor.getMonth() + 1);
    }
    return buckets;
  }

  function getMaxBuckets(granularidad) {
    if (granularidad === "day") return MAX_BUCKETS_DIARIO;
    if (granularidad === "week") return MAX_BUCKETS_SEMANA;
    return MAX_BUCKETS_MES;
  }

  /* ============================================================ */
  /* 3. Bootstrap del módulo                                      */
  /* ============================================================ */
  function initStockChart() {
    const wrapper = document.getElementById("collapseStockChart");
    if (!wrapper) return; // sección no presente en esta página

    const materiales = leerJsonInyectado("materiales-stock-data") || [];
    const compras = leerJsonInyectado("entradas-data") || [];
    const ventas = leerJsonInyectado("salidas-data") || [];

    state.materiales = materiales;
    state.materialesById = new Map(materiales.map((m) => [m.inventarioId, m]));

    // Indexar operaciones por inventarioId (incluye su signo: +1 compra, -1 venta)
    const opsByMat = new Map();
    materiales.forEach((m) => opsByMat.set(m.inventarioId, []));
    for (const c of compras) {
      if (!opsByMat.has(c.inventarioId)) opsByMat.set(c.inventarioId, []);
      const fecha = parseFecha(c.fechaCompra);
      if (fecha) {
        opsByMat.get(c.inventarioId).push({
          fecha,
          cantidad: Number(c.cantidad) || 0,
          signo: 1,
        });
      }
    }
    for (const v of ventas) {
      if (!opsByMat.has(v.inventarioId)) opsByMat.set(v.inventarioId, []);
      const fecha = parseFecha(v.fechaVenta);
      if (fecha) {
        opsByMat.get(v.inventarioId).push({
          fecha,
          cantidad: Number(v.cantidad) || 0,
          signo: -1,
        });
      }
    }
    state.operacionesByMaterial = opsByMat;

    // Defaults de fecha: inicio de mes → hoy (TZ Bogotá)
    const hoy = new Date();
    const inicioMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    document.getElementById("stockChartDesde").value = toISODate(inicioMes);
    document.getElementById("stockChartHasta").value = toISODate(hoy);

    renderListaMateriales();
    wireListeners();
    // Render inicial: gráfico oculto hasta que el usuario seleccione
    mostrarEstadoVacio(true);
    renderResumenVacio();
  }

  /* ============================================================ */
  /* 4. Render de checkboxes                                      */
  /* ============================================================ */
  function renderListaMateriales() {
    const cont = document.getElementById("stockChartMaterialesList");
    if (!cont) return;
    if (!state.materiales.length) {
      cont.innerHTML =
        '<small class="text-muted">No hay materiales en el inventario.</small>';
      actualizarBadgeMateriales();
      return;
    }
    cont.innerHTML = state.materiales
      .map(
        (m) => `
        <div class="form-check stock-chart-check">
          <input class="form-check-input" type="checkbox"
                 value="${escapeHtml(m.inventarioId)}"
                 id="stockMat_${escapeHtml(m.inventarioId)}"
                 data-nombre="${escapeHtml(m.nombre)}">
          <label class="form-check-label small" for="stockMat_${escapeHtml(m.inventarioId)}">
            ${escapeHtml(m.nombre)}
            <span class="text-muted">
              (${escapeHtml(m.unidadMedida || "")} · stock ${m.stockActual.toFixed(2)})
            </span>
          </label>
        </div>
      `,
      )
      .join("");
    cont.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.addEventListener("change", onCambioSeleccion);
    });
    actualizarBadgeMateriales();
  }

  function onCambioSeleccion(e) {
    const id = e.target.value;
    if (e.target.checked) state.seleccionados.add(id);
    else state.seleccionados.delete(id);
    actualizarBadgeMateriales();
    actualizar();
  }

  function actualizarBadgeMateriales() {
    const badge = document.getElementById("badgeCountMateriales");
    if (badge) badge.textContent = String(state.seleccionados.size);
  }

  /* ============================================================ */
  /* 5. Listeners                                                  */
  /* ============================================================ */
  function wireListeners() {
    const $ = (id) => document.getElementById(id);
    $("btnSeleccionarTodos")?.addEventListener("click", () => {
      state.materiales.forEach((m) => state.seleccionados.add(m.inventarioId));
      document
        .querySelectorAll('#stockChartMaterialesList input[type="checkbox"]')
        .forEach((cb) => {
          cb.checked = true;
        });
      actualizarBadgeMateriales();
      actualizar();
    });
    $("btnLimpiarMateriales")?.addEventListener("click", () => {
      state.seleccionados.clear();
      document
        .querySelectorAll('#stockChartMaterialesList input[type="checkbox"]')
        .forEach((cb) => {
          cb.checked = false;
        });
      actualizarBadgeMateriales();
      actualizar();
    });

    $("stockChartGranularidad")?.addEventListener("change", (e) => {
      state.granularidad = e.target.value;
      actualizar();
    });
    $("stockChartCapacidad")?.addEventListener("change", (e) => {
      state.mostrarCapacidad = e.target.checked;
      actualizar();
    });
    $("stockChartDesde")?.addEventListener("change", actualizar);
    $("stockChartHasta")?.addEventListener("change", actualizar);
    $("btnAplicarFiltrosStockChart")?.addEventListener("click", actualizar);
    $("btnExportarStockPng")?.addEventListener("click", exportarPng);
  }

  /* ============================================================ */
  /* 6. Cálculo de la serie temporal                              */
  /* ============================================================ */
  function construirSeries() {
    const desdeStr = document.getElementById("stockChartDesde").value;
    const hastaStr = document.getElementById("stockChartHasta").value;
    if (!desdeStr || !hastaStr) return null;
    const desde = parseFecha(desdeStr + "T00:00:00");
    const hasta = parseFecha(hastaStr + "T23:59:59");
    if (!desde || !hasta || desde > hasta) return null;

    const granularidad = state.granularidad;
    const buckets = generarBuckets(desde, hasta, granularidad);
    if (buckets.length > getMaxBuckets(granularidad)) {
      console.warn(
        `Rango demasiado grande (${buckets.length} buckets). Se recomienda acortar.`,
      );
    }

    const labels = buckets.map((b) => formatearLabelBucket(b, granularidad));
    const datasetsMateriales = [];
    const datasetsCapacidad = [];
    const resumenPorMaterial = [];

    const materialIds = Array.from(state.seleccionados);

    materialIds.forEach((id, idx) => {
      const material = state.materialesById.get(id);
      if (!material) return;
      const color = PALETA_COLORES[idx % PALETA_COLORES.length];
      const ops = state.operacionesByMaterial.get(id) || [];
      const stockAhora = material.stockActual;

      // 1) Mapear operaciones a buckets (solo las que caen en el rango o antes)
      const deltaPorBucket = new Map();
      let totalDeltaEnRango = 0;
      let comprasEnRango = 0;
      let ventasEnRango = 0;
      for (const op of ops) {
        if (op.fecha < desde || op.fecha > hasta) continue;
        const bucket = bucketDeFecha(op.fecha, granularidad);
        const delta = op.cantidad * op.signo;
        deltaPorBucket.set(bucket, (deltaPorBucket.get(bucket) || 0) + delta);
        totalDeltaEnRango += delta;
        if (op.signo > 0) comprasEnRango += op.cantidad;
        else ventasEnRango += op.cantidad;
      }

      // 2) Offset: deltas de operaciones POSTERIORES al fin del rango
      const finRango = buckets[buckets.length - 1];
      let offset = 0;
      for (const op of ops) {
        if (op.fecha > finRango) offset += op.cantidad * op.signo;
      }

      // 3) Walk-backward por buckets
      const data = new Array(buckets.length);
      let stockFinBucketSgte = stockAhora - offset;
      for (let i = buckets.length - 1; i >= 0; i--) {
        data[i] = round2(stockFinBucketSgte);
        const delta = deltaPorBucket.get(buckets[i]) || 0;
        stockFinBucketSgte -= delta; // retrocedemos un bucket
      }

      datasetsMateriales.push({
        label: material.nombre,
        data,
        borderColor: color,
        backgroundColor: hexToRgba(color, 0.15),
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        tension: 0.2,
        fill: false,
        unidad: material.unidadMedida,
        materialId: id,
      });

      if (state.mostrarCapacidad) {
        datasetsCapacidad.push({
          label: `${material.nombre} (cap. máx)`,
          data: new Array(buckets.length).fill(round2(material.capacidadMaxima)),
          borderColor: color,
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: false,
          tension: 0,
          unidad: material.unidadMedida,
          materialId: `${id}-cap`,
          esCapacidad: true,
        });
      }

      resumenPorMaterial.push({
        material,
        compras: comprasEnRango,
        ventas: ventasEnRango,
        variacion: totalDeltaEnRango,
        color,
      });
    });

    return {
      labels,
      datasets: [...datasetsMateriales, ...datasetsCapacidad],
      resumenPorMaterial,
      totalBuckets: buckets.length,
    };
  }

  function round2(n) {
    return Math.round((Number(n) || 0) * 100) / 100;
  }

  function hexToRgba(hex, alpha) {
    const limpio = hex.replace("#", "");
    const r = parseInt(limpio.substring(0, 2), 16);
    const g = parseInt(limpio.substring(2, 4), 16);
    const b = parseInt(limpio.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  /* ============================================================ */
  /* 7. Render del Chart                                          */
  /* ============================================================ */
  function renderChart(series) {
    const ctx = document.getElementById("stockTimeChart");
    if (!ctx) return;
    if (state.chart) {
      state.chart.destroy();
      state.chart = null;
    }
    state.chart = new Chart(ctx.getContext("2d"), {
      type: "line",
      data: {
        labels: series.labels,
        datasets: series.datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 14, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (item) => {
                const ds = item.dataset;
                const unidad = ds.unidad || "";
                const val = item.parsed.y;
                return `${ds.label}: ${formatearNumero(val)} ${unidad}`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: "Nivel de inventario" },
            ticks: { callback: (v) => formatearNumero(v) },
          },
          x: {
            title: { display: true, text: "Periodo" },
            ticks: { maxRotation: 60, autoSkip: true, maxTicksLimit: 12 },
          },
        },
      },
    });
  }

  function formatearNumero(v) {
    return Number(v).toLocaleString("es-CO", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }

  /* ============================================================ */
  /* 8. Resumen (cards)                                           */
  /* ============================================================ */
  function renderResumen(resumenPorMaterial) {
    const cont = document.getElementById("stockChartResumen");
    if (!cont) return;
    if (!resumenPorMaterial || !resumenPorMaterial.length) {
      renderResumenVacio();
      return;
    }
    cont.innerHTML = resumenPorMaterial
      .map(
        (r) => `
        <div class="col-12 col-md-6 col-lg-3">
          <div class="card border-0 shadow-sm h-100 stock-chart-resumen-card"
               style="border-left: 4px solid ${r.color} !important;">
            <div class="card-body p-3">
              <small class="text-muted fw-semibold text-uppercase d-block mb-1"
                     style="font-size: 0.7rem;">
                ${escapeHtml(r.material.nombre)}
              </small>
              <div class="d-flex justify-content-between align-items-baseline mb-1">
                <span class="text-muted small">Stock actual</span>
                <span class="fw-bold text-dark">
                  ${formatearNumero(r.material.stockActual)} ${escapeHtml(r.material.unidadMedida || "")}
                </span>
              </div>
              <div class="d-flex justify-content-between align-items-baseline mb-1">
                <span class="text-muted small">Entradas (rango)</span>
                <span class="fw-semibold text-success">
                  +${formatearNumero(r.compras)}
                </span>
              </div>
              <div class="d-flex justify-content-between align-items-baseline mb-1">
                <span class="text-muted small">Salidas (rango)</span>
                <span class="fw-semibold text-danger">
                  -${formatearNumero(r.ventas)}
                </span>
              </div>
              <div class="d-flex justify-content-between align-items-baseline">
                <span class="text-muted small">Variación neta</span>
                <span class="fw-bold ${r.variacion >= 0 ? "text-success" : "text-danger"}">
                  ${r.variacion >= 0 ? "+" : ""}${formatearNumero(r.variacion)}
                </span>
              </div>
            </div>
          </div>
        </div>
      `,
      )
      .join("");
  }

  function renderResumenVacio() {
    const cont = document.getElementById("stockChartResumen");
    if (!cont) return;
    cont.innerHTML = `
      <div class="col-12 text-muted small">
        <em>Selecciona al menos un material para ver el resumen.</em>
      </div>
    `;
  }

  /* ============================================================ */
  /* 9. Estado vacío / orquestación                               */
  /* ============================================================ */
  function mostrarEstadoVacio(vacio) {
    const empty = document.getElementById("stockChartEmpty");
    const wrap = document.getElementById("stockChartWrapper");
    if (!empty || !wrap) return;
    if (vacio) {
      empty.classList.remove("d-none");
      wrap.classList.add("d-none");
    } else {
      empty.classList.add("d-none");
      wrap.classList.remove("d-none");
    }
  }

  function actualizar() {
    const badge = document.getElementById("badgeStockChartCount");
    if (badge) badge.textContent = `${state.seleccionados.size} materiales`;

    if (!state.seleccionados.size) {
      mostrarEstadoVacio(true);
      renderResumenVacio();
      return;
    }
    const series = construirSeries();
    if (!series) {
      mostrarEstadoVacio(true);
      renderResumenVacio();
      return;
    }
    mostrarEstadoVacio(false);
    renderChart(series);
    renderResumen(series.resumenPorMaterial);
  }

  /* ============================================================ */
  /* 10. Export PNG                                               */
  /* ============================================================ */
  function exportarPng() {
    if (!state.chart) {
      if (window.Swal) {
        Swal.fire({
          icon: "info",
          title: "Sin gráfica",
          text: "Selecciona al menos un material y aplica los filtros.",
        });
      }
      return;
    }
    try {
      const canvas = state.chart.canvas;
      const enlace = document.createElement("a");
      enlace.href = canvas.toDataURL("image/png");
      enlace.download = `stock_${new Date().toISOString().slice(0, 10)}.png`;
      document.body.appendChild(enlace);
      enlace.click();
      document.body.removeChild(enlace);
    } catch (err) {
      console.error("Error exportando PNG", err);
    }
  }

  /* ============================================================ */
  /* 11. Bootstrap                                                */
  /* ============================================================ */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initStockChart);
  } else {
    initStockChart();
  }
})();
