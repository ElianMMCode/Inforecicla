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

  // "DD MMM HH:MM" en zona horaria Bogotá. Usado cuando hay varios
  // movimientos el mismo día y cada uno es su propio punto en el eje X.
  function formatearFechaHora(fecha) {
    const dd = String(fecha.getDate()).padStart(2, "0");
    const mes = fecha.toLocaleDateString("es-CO", {
      month: "short",
      timeZone: TZ_BOGOTA,
    });
    const hh = String(fecha.getHours()).padStart(2, "0");
    const min = String(fecha.getMinutes()).padStart(2, "0");
    return `${dd} ${mes} ${hh}:${min}`;
  }

  function getNumeroSemana(d) {
    // ISO week number
    const fecha = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    const dia = fecha.getUTCDay() || 7;
    fecha.setUTCDate(fecha.getUTCDate() + 4 - dia);
    const inicioAnio = new Date(Date.UTC(fecha.getUTCFullYear(), 0, 1));
    return Math.ceil(((fecha - inicioAnio) / 86400000 + 1) / 7);
  }

  function bucketKey(fecha, granularidad) {
    // Clave STRING comparable para indexar buckets en el Map.
    // Importante: las Date se comparan por referencia en Map.get; usar strings
    // garantiza que la misma "fecha-bucket" siempre produzca la misma clave.
    if (granularidad === "day") {
      return toISODate(fecha);
    }
    if (granularidad === "week") {
      const inicioSemana = inicioDeSemana(fecha);
      return `W${String(getNumeroSemana(inicioSemana)).padStart(2, "0")}-${inicioSemana.getFullYear()}`;
    }
    return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, "0")}`;
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

  function finDeBucket(bucket, granularidad) {
    // Retorna el inicio del SIGUIENTE bucket (= fin exclusivo del actual).
    // Se usa para saber qué operaciones caen "después" del último bucket.
    const fin = new Date(bucket);
    if (granularidad === "day") fin.setDate(fin.getDate() + 1);
    else if (granularidad === "week") fin.setDate(fin.getDate() + 7);
    else fin.setMonth(fin.getMonth() + 1);
    return fin;
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

    // DEBUG: Verificar que los datos se inyectaron correctamente
    console.group("🟢 [Stock Chart] initStockChart()");
    console.log("Materiales cargados:", materiales.length);
    for (const m of materiales) {
      const ops = opsByMat.get(m.inventarioId) || [];
      console.log(`  • ${m.nombre}: stockActual=${m.stockActual} (${typeof m.stockActual}), ops=${ops.length}`);
      if (ops.length > 0) {
        const ej = ops[0];
        console.log(`    ej. op: cantidad=${ej.cantidad} (${typeof ej.cantidad}), signo=${ej.signo}, fecha=${ej.fecha.toISOString()}`);
      }
    }
    console.groupEnd();

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

    // Al expandir el acordeón por primera vez, el canvas pasa de 0×0 a
    // tener tamaño real; forzamos un resize del chart para que no quede
    // aplastado ni desbordado.
    const collapseEl = document.getElementById("collapseStockChart");
    if (collapseEl) {
      collapseEl.addEventListener("shown.bs.collapse", () => {
        if (state.chart) state.chart.resize();
      });
    }
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

    const gran = state.granularidad;
    const materialIds = Array.from(state.seleccionados);
    if (!materialIds.length) return null;

    // DEBUG: Diagnóstico temporal
    console.group("🔍 [Stock Chart] construirSeries()");
    console.log("Rango:", desdeStr, "→", hastaStr);
    console.log("Granularidad:", gran);
    console.log("Materiales seleccionados:", materialIds);
    for (const id of materialIds) {
      const m = state.materialesById.get(id);
      const ops = state.operacionesByMaterial.get(id) || [];
      console.log(`  • ${m?.nombre} (${id})`);
      console.log(`    stockActual:`, m?.stockActual, `(tipo: ${typeof m?.stockActual})`);
      console.log(`    ops totales:`, ops.length);
      const opsInRange = ops.filter((o) => o.fecha >= desde && o.fecha <= hasta);
      console.log(`    ops en rango:`, opsInRange.length);
      if (opsInRange.length > 0) {
        const totalDelta = opsInRange.reduce((s, o) => s + o.cantidad * o.signo, 0);
        console.log(`    totalDelta:`, totalDelta, `→ stock inicial = ${m.stockActual - totalDelta}`);
      }
    }
    console.groupEnd();

    if (gran === "day") {
      return construirSeriesPorMovimiento(materialIds, desde, hasta);
    }
    return construirSeriesPorBucket(materialIds, desde, hasta, gran);
  }

  // Vista por DÍA: 1 punto por movimiento (varios en el mismo día → varios puntos).
  function construirSeriesPorMovimiento(materialIds, desde, hasta) {
    const eventosByMaterial = new Map();
    const timestampsSet = new Set();

    materialIds.forEach((id) => {
      const material = state.materialesById.get(id);
      if (!material) return;
      const ops = state.operacionesByMaterial.get(id) || [];
      const opsInRange = ops
        .filter((o) => o.fecha >= desde && o.fecha <= hasta)
        .sort((a, b) => a.fecha - b.fecha);

      const totalDelta = opsInRange.reduce(
        (s, o) => s + o.cantidad * o.signo,
        0,
      );

      const eventos = [];
      let cumStock = material.stockActual - totalDelta;
      for (const op of opsInRange) {
        cumStock += op.cantidad * op.signo;
        eventos.push({
          ts: op.fecha.getTime(),
          fecha: op.fecha,
          delta: op.cantidad * op.signo,
          stockDespues: cumStock,
        });
        timestampsSet.add(op.fecha.getTime());
      }

      eventosByMaterial.set(id, { material, eventos, totalDelta });
    });

    if (timestampsSet.size === 0) {
      return {
        labels: [],
        datasets: [],
        resumenPorMaterial: [],
        totalBuckets: 0,
        sinMovimientos: true,
      };
    }

    const sharedKeysList = Array.from(timestampsSet).sort((a, b) => a - b);
    const sharedLabels = sharedKeysList.map((t) =>
      formatearFechaHora(new Date(t)),
    );

    return ensamblarDatasets(
      materialIds,
      eventosByMaterial,
      sharedKeysList,
      sharedLabels,
      "ts",
    );
  }

  // Vista por SEMANA/MES: 1 punto por bucket con movimiento. Sin carry-forward.
  function construirSeriesPorBucket(materialIds, desde, hasta, gran) {
    const buckets = generarBuckets(desde, hasta, gran);
    if (buckets.length > getMaxBuckets(gran)) {
      console.warn(
        `Rango demasiado grande (${buckets.length} buckets). Se recomienda acortar.`,
      );
    }

    const eventosByMaterial = new Map();
    const sharedKeysSet = new Set();

    materialIds.forEach((id) => {
      const material = state.materialesById.get(id);
      if (!material) return;
      const ops = state.operacionesByMaterial.get(id) || [];
      const opsInRange = ops
        .filter((o) => o.fecha >= desde && o.fecha <= hasta)
        .sort((a, b) => a.fecha - b.fecha);

      // Agrupar deltas por bucket
      const deltaPorBucket = new Map();
      let totalDelta = 0;
      let comprasEnRango = 0;
      let ventasEnRango = 0;
      for (const op of opsInRange) {
        const key = bucketKey(op.fecha, gran);
        const delta = op.cantidad * op.signo;
        deltaPorBucket.set(key, (deltaPorBucket.get(key) || 0) + delta);
        totalDelta += delta;
        if (op.signo > 0) comprasEnRango += op.cantidad;
        else ventasEnRango += op.cantidad;
      }

      // Walk-backward para stock al final de cada bucket (sobre TODOS los buckets,
      // para mantener coherencia del offset entre buckets vacíos).
      const finRango = buckets[buckets.length - 1];
      const finExclusivo = finDeBucket(finRango, gran);
      let offset = 0;
      for (const op of ops) {
        if (op.fecha >= finExclusivo) offset += op.cantidad * op.signo;
      }
      const stockFinBucket = new Map();
      let stockFinBucketSgte = material.stockActual - offset;
      for (let i = buckets.length - 1; i >= 0; i--) {
        const key = bucketKey(buckets[i], gran);
        stockFinBucket.set(key, stockFinBucketSgte);
        const delta = deltaPorBucket.get(key) || 0;
        stockFinBucketSgte -= delta;
      }

      // Emitir 1 "evento" por bucket con movimiento, con stock al final del bucket
      const eventos = [];
      for (const [key, delta] of deltaPorBucket.entries()) {
        eventos.push({
          key,
          fecha: buckets.find((b) => bucketKey(b, gran) === key) || new Date(),
          delta,
          stockDespues: stockFinBucket.get(key),
        });
        sharedKeysSet.add(key);
      }
      // Ordenar por key (las keys de week/month son comparables como string)
      eventos.sort((a, b) => (a.key < b.key ? -1 : a.key > b.key ? 1 : 0));

      eventosByMaterial.set(id, { material, eventos, totalDelta });
    });

    if (sharedKeysSet.size === 0) {
      return {
        labels: [],
        datasets: [],
        resumenPorMaterial: [],
        totalBuckets: 0,
        sinMovimientos: true,
      };
    }

    const sharedKeysList = Array.from(sharedKeysSet).sort();
    const keyToBucket = new Map();
    for (const b of buckets) {
      const k = bucketKey(b, gran);
      if (!keyToBucket.has(k)) keyToBucket.set(k, b);
    }
    const sharedLabels = sharedKeysList.map((k) =>
      formatearLabelBucket(keyToBucket.get(k), gran),
    );

    return ensamblarDatasets(
      materialIds,
      eventosByMaterial,
      sharedKeysList,
      sharedLabels,
      "key",
    );
  }

  // Ensambla los datasets Chart.js a partir de eventos por material y eje X compartido.
  // Cada material solo tiene datos en sus propias keys; las demás son null
  // → con spanGaps:false la línea se corta donde no hay datos.
  function ensamblarDatasets(
    materialIds,
    eventosByMaterial,
    sharedKeysList,
    sharedLabels,
    keyField,
  ) {
    const datasetsMateriales = [];
    const datasetsCapacidad = [];
    const resumenPorMaterial = [];

    materialIds.forEach((id, idx) => {
      const data = eventosByMaterial.get(id);
      if (!data) return;
      const { material, eventos, totalDelta } = data;

      const dataArr = new Array(sharedKeysList.length).fill(null);
      for (const ev of eventos) {
        const evKey = keyField === "ts" ? ev.ts : ev.key;
        const pos = sharedKeysList.indexOf(evKey);
        if (pos !== -1) {
          dataArr[pos] = round2(ev.stockDespues);
        }
      }

      const color = PALETA_COLORES[idx % PALETA_COLORES.length];

      datasetsMateriales.push({
        label: material.nombre,
        data: dataArr,
        borderColor: color,
        backgroundColor: hexToRgba(color, 0.15),
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: color,
        tension: 0,
        fill: false,
        spanGaps: false,
        unidad: material.unidadMedida,
        materialId: material.inventarioId,
      });

      if (state.mostrarCapacidad) {
        datasetsCapacidad.push({
          label: `${material.nombre} (cap. máx)`,
          data: sharedKeysList.map(() => round2(material.capacidadMaxima)),
          borderColor: color,
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: false,
          tension: 0,
          spanGaps: false,
          unidad: material.unidadMedida,
          materialId: `${material.inventarioId}-cap`,
          esCapacidad: true,
        });
      }

      resumenPorMaterial.push({
        material,
        compras: eventos
          .filter((e) => e.delta > 0)
          .reduce((s, e) => s + e.delta, 0),
        ventas: Math.abs(
          eventos.filter((e) => e.delta < 0).reduce((s, e) => s + e.delta, 0),
        ),
        variacion: totalDelta,
        color,
      });
    });

    // DEBUG: Verificar valores calculados
    console.group("📊 [Stock Chart] Datasets finales");
    for (const ds of datasetsMateriales) {
      console.log(`  ${ds.label}:`, ds.data);
    }
    console.groupEnd();

    return {
      labels: sharedLabels,
      datasets: [...datasetsMateriales, ...datasetsCapacidad],
      resumenPorMaterial,
      totalBuckets: sharedKeysList.length,
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
    if (!ctx) {
      console.error("❌ [Stock Chart] No se encontró el canvas #stockTimeChart");
      return;
    }
    if (state.chart) {
      state.chart.destroy();
      state.chart = null;
    }
    try {
      console.group("🎨 [Stock Chart] renderChart()");
      console.log("Labels:", series.labels);
      console.log("Datasets a renderizar:", series.datasets.map((d) => ({
        label: d.label,
        data: d.data,
        spanGaps: d.spanGaps,
        tension: d.tension,
      })));
      const ctx2d = ctx.getContext("2d");
      console.log("Canvas context:", ctx2d ? "OK" : "NULL");
      console.log("Canvas size:", ctx.width, "x", ctx.height);

      state.chart = new Chart(ctx2d, {
        type: "line",
        data: {
          labels: series.labels,
          datasets: series.datasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          interaction: { mode: "index", intersect: false },
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 14, font: { size: 11 } },
            },
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
              title: { display: true, text: "Fecha del movimiento" },
              ticks: { maxRotation: 45, autoSkip: false, font: { size: 10 } },
            },
          },
        },
      });
      console.log("Chart creado:", state.chart);
      // Verificar el estado interno del chart tras creación
      setTimeout(() => {
        if (state.chart) {
          console.log("📦 Chart.data.datasets[0].data (interno):",
            state.chart.data.datasets[0]?.data);
          console.log("📦 Chart.scales.y.min/max:",
            state.chart.scales.y?.min, "/", state.chart.scales.y?.max);
          console.log("📦 Chart.canvas size:",
            state.chart.canvas.width, "x", state.chart.canvas.height);
        }
      }, 100);
      // Forzar resize por si el canvas estaba oculto al crearse
      requestAnimationFrame(() => {
        if (state.chart) {
          state.chart.resize();
          console.log("Chart redimensionado");
        }
      });
      console.groupEnd();
    } catch (err) {
      console.error("❌ [Stock Chart] Error creando Chart.js:", err);
      console.groupEnd();
    }
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
    if (series.sinMovimientos) {
      // Hay materiales seleccionados pero ninguno tiene operaciones en el rango.
      mostrarEstadoVacio(true);
      // Mostrar resumen igual (entradas/salidas en 0, stock actual visible).
      renderResumen(series.resumenPorMaterial);
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
