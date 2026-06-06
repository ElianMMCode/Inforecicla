// ============================================================
// Sección /inventario/ — Lógica de cliente (Fase 2)
// ============================================================
// Esta implementación es un primer puerto del mockup dorado. Se
// enfoca en: navegación entre estados, tabs, picker, filtros de
// cards, formularios de crear/registrar y modales. Chart y reglas
// de validación avanzadas se completarán en Fases 3+.
// ============================================================

(function () {
    "use strict";

    // --- Datos inyectados por el template (json_script) ---
    const dataEl = document.getElementById("inv-data");
    const invData = dataEl ? JSON.parse(dataEl.textContent) : { materiales_inventario: [] };
    const materialesDB = invData.materiales_inventario || [];
    const comprasDB = invData.historial_compras || [];
    const ventasDB = invData.historial_ventas || [];

    // --- Estado en memoria ---
    let currentMaterialId = null;
    let currentMaterial = null;
    let isWorkspaceHistorial = false;

    // --- Helpers de formato ---
    // Moneda: todos los precios de la app son pesos colombianos (COP).
    //   - formatCOP      -> formato completo es-CO: "$ 1.500.000" (KPIs, modales, totales).
    //   - formatearCOP   -> alias largo (mismo formato), usado por los handlers del flujo.
    //   - formatearCOPCorto -> formato compacto con sufijos K/M/B: "$ 1.5M" (eje Y de chart).
    const formatCOP = (n) => "$ " + Number(n || 0).toLocaleString("es-CO", { maximumFractionDigits: 0 });
    const formatearCOP = (n) => formatCOP(n);
    const formatearCOPCorto = (n) => {
        const v = Number(n) || 0;
        const abs = Math.abs(v);
        const sign = v < 0 ? "-$ " : "$ ";
        if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(1)}B`;
        if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(1)}M`;
        if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(0)}K`;
        return `${sign}${abs.toFixed(0)}`;
    };
    const formatQty = (n, u) => `${Number(n || 0).toLocaleString("es-CO")} ${u || ""}`.trim();
    const formatDateCO = (iso) => {
        if (!iso) return "—";
        const d = new Date(iso);
        if (isNaN(d)) return iso;
        const pad = (x) => String(x).padStart(2, "0");
        return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    };
    const escapeHtml = (s) => {
        if (s == null) return "";
        return String(s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    // ============================================================
    // NAVEGACIÓN ENTRE ESTADOS (landing ↔ workspace)
    // ============================================================
    function irLanding() {
        document.getElementById("estado-landing")?.classList.add("active");
        document.getElementById("estado-workspace")?.classList.remove("active");
        currentMaterialId = null;
        currentMaterial = null;
        isWorkspaceHistorial = false;
        activarOvTab("ovtab-inventario");
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function irWorkspace(invId, tabId) {
        const inv = materialesDB.find((m) => String(m.inventarioId) === String(invId));
        if (!inv) {
            console.warn("[inv] inventarioId no encontrado:", invId);
            return;
        }
        currentMaterialId = invId;
        currentMaterial = inv;
        isWorkspaceHistorial = tabId === "tab-historial";
        poblarWorkspace(inv);
        // Auto-rellenar campos readonly de material en forms de crear
        // (sólo si vamos a un tab donde se usan, evita llenar en historial).
        if (tabId === "tab-compra" || tabId === "tab-venta" || !tabId) {
            poblarInfoMaterial("formEntrada");
            poblarInfoMaterial("formSalida");
        }
        document.getElementById("estado-landing")?.classList.remove("active");
        document.getElementById("estado-workspace")?.classList.add("active");
        if (tabId) activarTab(tabId);
        if (isWorkspaceHistorial) {
            historialPage = 1;
            _poblarCentrosAcopio();
            _toggleCentroAcopioLock();
            renderHistorialGeneralPaged();
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function poblarWorkspace(inv) {
        const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v ?? "—"; };
        const nombre = inv.nombre;
        const estadoLower = inv.estado;
        const estadoLabel = estadoLower === "critico" ? "Crítico" : estadoLower === "alerta" ? "Alerta" : "OK";
        const estadoClass = estadoLower === "critico" ? "bg-danger" : estadoLower === "alerta" ? "bg-warning text-dark" : "bg-success";
        const ocupacionNum = Number(inv.ocupacion);
        setText("inv-ws-nombre", nombre);
        setText("inv-ws-categoria", inv.categoria);
        setText("inv-ws-tipo", inv.tipo);
        setText("inv-ws-ultact", "—");
        setText("inv-ws-stock", `${formatQty(inv.stockActual, inv.unidad)} (${ocupacionNum.toFixed(0)}%)`);
        setText("inv-ws-pcompra", Number(inv.precioCompra).toLocaleString("es-CO"));
        setText("inv-ws-pventa", Number(inv.precioVenta).toLocaleString("es-CO"));
        setText("inv-ws-unidad-c", inv.unidad);
        setText("inv-ws-unidad-v", inv.unidad);
        const wsEstado = document.getElementById("inv-ws-estado");
        if (wsEstado) {
            wsEstado.className = "badge ms-2 " + estadoClass;
            wsEstado.textContent = estadoLabel;
        }
        const wsProgress = document.getElementById("inv-ws-progress");
        if (wsProgress) {
            wsProgress.className = "progress-bar " + (estadoLower === "critico" ? "bg-danger" : estadoLower === "alerta" ? "bg-warning" : "bg-success");
            wsProgress.style.width = Math.min(100, Math.max(0, ocupacionNum)) + "%";
        }
        // Tab datos
        setText("inv-ws-datos-nombre", nombre);
        setText("inv-ws-datos-material", nombre);
        setText("inv-ws-datos-categoria", inv.categoria);
        setText("inv-ws-datos-tipo", inv.tipo);
        setText("inv-ws-datos-cap", `${formatQty(inv.capacidadMaxima, inv.unidad)}`);
        setText("inv-ws-datos-stock", `${formatQty(inv.stockActual, inv.unidad)} (${ocupacionNum.toFixed(0)}%)`);
        setText("inv-ws-datos-unidad", inv.unidad);
        setText("inv-ws-datos-umbral-a", `${inv.umbralAlerta}%`);
        setText("inv-ws-datos-umbral-c", `${inv.umbralCritico}%`);
        const datosEstado = document.getElementById("inv-ws-datos-estado");
        if (datosEstado) {
            datosEstado.className = "badge " + estadoClass;
            datosEstado.textContent = estadoLabel;
        }
        setText("inv-ws-datos-pcompra", "$ " + Number(inv.precioCompra).toLocaleString("es-CO"));
        setText("inv-ws-datos-pventa", "$ " + Number(inv.precioVenta).toLocaleString("es-CO"));
        // Tab nombres
        document.querySelectorAll(".inv-ws-tab-nombre").forEach((el) => { el.textContent = nombre; });
        // Formularios compra/venta
        const fInMat = document.getElementById("formEntradaMaterial");
        if (fInMat) fInMat.value = nombre;
        const fOutMat = document.getElementById("formSalidaMaterial");
        if (fOutMat) fOutMat.value = nombre;
        const fInId = document.getElementById("formEntradaInventarioId");
        if (fInId) fInId.value = inv.inventarioId;
        const fOutId = document.getElementById("formSalidaInventarioId");
        if (fOutId) fOutId.value = inv.inventarioId;
        // Edit modal prefill
        const editInvId = document.getElementById("inv-edit-inventario-id");
        if (editInvId) editInvId.value = inv.inventarioId;
        document.getElementById("inv-edit-stock-inicial").value = inv.stockActual;
        document.getElementById("inv-edit-capacidad-maxima").value = inv.capacidadMaxima;
        document.getElementById("inv-edit-unidad-medida").value = inv.unidad;
        document.getElementById("inv-edit-umbral-alerta").value = inv.umbralAlerta;
        document.getElementById("inv-edit-umbral-critico").value = inv.umbralCritico;
        document.getElementById("inv-edit-precio-compra").value = inv.precioCompra;
        document.getElementById("inv-edit-precio-venta").value = inv.precioVenta;
        document.getElementById("inv-edit-inv-titulo").textContent = nombre;
        document.getElementById("inv-eliminar-nombre").textContent = nombre;
        // Historial
        renderHistorialMaterial(inv.inventarioId);
        renderEntradasMaterial(inv.inventarioId);
        renderSalidasMaterial(inv.inventarioId);
        // Flujo
        const fstock = document.getElementById("inv-ws-flujo-stock");
        if (fstock) fstock.textContent = formatQty(inv.stockActual, inv.unidad);
    }

    // ============================================================
    // TABS
    // ============================================================
    function activarOvTab(tabId) {
        document.querySelectorAll("#otrasVistasTabs .nav-link").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".ovtab-pane").forEach((p) => p.classList.remove("active"));
        const btn = document.querySelector(`#otrasVistasTabs [data-ovtab="${tabId}"]`);
        const pane = document.getElementById(tabId);
        if (btn) btn.classList.add("active");
        if (pane) pane.classList.add("active");
        // Re-init Select2 sobre los selects del pane AHORA visible.
        // Sin esto, los Select2 inicializados en bind() sobre paneles ocultos
        // muestran wrappers con width incorrecto (Select2 mide al init).
        if (pane) _reinitSelect2InPane(pane);
        // Re-render de los charts del pane (canvas.clientWidth era 0 al
        // render inicial porque el pane estaba oculto).
        if (pane) setTimeout(() => _reinitChartsInPane(pane), 50);
    }

    function activarTab(tabId) {
        document.querySelectorAll("#workspaceTabs .nav-link").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-pane-stack").forEach((p) => p.classList.remove("active"));
        const btn = document.querySelector(`#workspaceTabs [data-tab="${tabId}"]`);
        const pane = document.getElementById(tabId);
        if (btn) btn.classList.add("active");
        if (pane) pane.classList.add("active");
        if (pane) _reinitSelect2InPane(pane);
        if (pane) setTimeout(() => _reinitChartsInPane(pane), 50);
        // Re-poblar info de material (readonly + precio unitario) al entrar
        // a los tabs de crear. Es idempotente: poblarInfoMaterial no
        // sobrescribe precios que el usuario ya haya tipeado.
        if (tabId === "tab-compra") poblarInfoMaterial("formEntrada");
        if (tabId === "tab-venta") poblarInfoMaterial("formSalida");
    }

    function _reinitSelect2InPane(pane) {
        if (typeof window.jQuery === "undefined" || typeof window.jQuery.fn.select2 === "undefined") return;
        const $ = window.jQuery;
        const base = { theme: "bootstrap-5", language: "es", width: "100%" };
        const $selects = $(pane).find("select").not("#inv-hfiltro-tipo").not("#inv-ws-hfiltro-tipo");
        $selects.each(function () {
            const $el = $(this);
            if ($el.data("select2")) $el.select2("destroy");
            $el.select2(Object.assign({}, base));
        });
    }

    function _reinitChartsInPane(pane) {
        if (!pane) return;
        // Re-renderiza todos los <canvas> del pane AHORA visible para que
        // clientWidth refleje el ancho real (era 0 al render inicial
        // porque el pane estaba oculto).
        const canvases = pane.querySelectorAll("canvas");
        canvases.forEach((canvas) => {
            const id = canvas.id;
            if (id === "inv-stock-time-chart") renderOvtabChart();
            else if (id === "inv-ganancias-chart") renderOvGananciasChart();
            else if (id === "stockTimeChart") renderWsChart();
            else if (id === "inv-ws-ganancias-chart") renderWsGananciasChart();
        });
    }

    // ============================================================
    // FILTROS DE CARDS EN LANDING
    // ============================================================
    function aplicarFiltrosCards() {
        const nombre = (document.getElementById("inv-filter-nombre")?.value || "").toLowerCase().trim();
        const cat = document.getElementById("inv-filter-categoria")?.value || "";
        const tipo = document.getElementById("inv-filter-tipo")?.value || "";
        const estado = document.getElementById("inv-filter-estado")?.value || "";
        const ocupacionSel = document.getElementById("inv-filter-ocupacion")?.value || "";

        let visibles = 0;
        const total = materialesDB.length;

        document.querySelectorAll(".inv-tarjeta-material").forEach((card) => {
            const matchNombre = !nombre || (card.dataset.nombre || "").includes(nombre);
            const matchCat = !cat || card.dataset.categoria === cat;
            const matchTipo = !tipo || card.dataset.tipo === tipo;
            const matchEstado = !estado || card.dataset.estado === estado;
            let matchOcup = true;
            if (ocupacionSel) {
                const [lo, hi] = ocupacionSel.split("-").map(Number);
                const o = Number(card.dataset.ocupacion || 0);
                matchOcup = o >= lo && o <= hi;
            }
            const show = matchNombre && matchCat && matchTipo && matchEstado && matchOcup;
            card.style.display = show ? "" : "none";
            if (show) visibles++;
        });

        const counter = document.getElementById("inv-filter-counter");
        if (counter) counter.textContent = `Mostrando ${visibles} de ${total} materiales`;
        const badge = document.getElementById("inv-filter-total-badge");
        if (badge) badge.textContent = `${total} items`;
        const vacio = document.getElementById("inv-mensaje-sin-resultados");
        if (vacio) vacio.style.display = visibles === 0 ? "block" : "none";
    }

    function limpiarFiltrosCards() {
        ["inv-filter-nombre", "inv-filter-categoria", "inv-filter-tipo", "inv-filter-estado", "inv-filter-ocupacion"]
            .forEach((id) => { const el = document.getElementById(id); if (el) el.value = ""; });
        aplicarFiltrosCards();
    }

    // ============================================================
    // RENDER HISTORIAL / ENTRADAS / SALIDAS
    // ============================================================
    function filaHistorial(mov, tipo, opts) {
        const showMaterial = !opts || opts.showMaterial !== false;
        const fecha = formatDateCO(mov.fechaCompra || mov.fechaVenta);
        const cantidad = mov.cantidad;
        const precio = tipo === "compra" ? mov.precioCompra : mov.precioVenta;
        const total = Number(cantidad || 0) * Number(precio || 0);
        const material = mov.nombreMaterial || "—";
        const categoria = mov.nombreCategoria || "—";
        const tipoBadge = tipo === "compra"
            ? '<span class="badge bg-danger-subtle text-danger">Compra</span>'
            : '<span class="badge bg-success-subtle text-success">Venta</span>';
        const centro = mov.nombreCentroAcopio || "—";
        const materialCell = showMaterial
            ? `<td class="small">${escapeHtml(material)}</td>`
            : "";
        return `<tr>
            <td class="small">${escapeHtml(fecha)}</td>
            <td>${tipoBadge}</td>
            ${materialCell}
            <td class="small text-end">${formatQty(cantidad, "")}</td>
            <td class="small text-end">${formatCOP(precio)}</td>
            <td class="small">${formatCOP(total)}</td>
            <td class="small text-muted">${escapeHtml(centro)}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-secondary" type="button" data-accion="ver" data-tipo="${tipo}" data-id="${mov.compraId || mov.ventaId}" title="Ver"><i class="bi bi-eye"></i></button>
                <button class="btn btn-sm btn-outline-primary" type="button" data-accion="editar" data-tipo="${tipo}" data-id="${mov.compraId || mov.ventaId}" title="Editar"><i class="bi bi-pencil"></i></button>
            </td>
        </tr>`;
    }

    function renderHistorialGeneral() {
        _poblarCentrosAcopio();
        _toggleCentroAcopioLock();
        renderHistorialGeneralPaged();
    }

    function renderHistorialMaterial(invId) {
        currentMaterialId = invId;
        isWorkspaceHistorial = true;
        historialPage = 1;
        _poblarCentrosAcopio();
        _toggleCentroAcopioLock();
        renderHistorialGeneralPaged();
    }

    function renderEntradasMaterial(invId) {
        const tbody = document.getElementById("tablasEntradasBody");
        const badge = document.getElementById("badgeEntradasCount");
        if (!tbody) return;
        const rows = [];
        comprasDB.filter((c) => String(c.inventarioId) === String(invId)).forEach((c) => {
            const total = Number(c.cantidad || 0) * Number(c.precioCompra || 0);
            rows.push(`<tr>
                <td class="small">${formatDateCO(c.fechaCompra)}</td>
                <td class="small text-end">${formatQty(c.cantidad, "")}</td>
                <td class="small text-end">${formatCOP(c.precioCompra)}</td>
                <td class="small">${formatCOP(total)}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-secondary" type="button" data-accion="ver" data-tipo="compra" data-id="${c.compraId}" title="Ver"><i class="bi bi-eye"></i></button>
                    <button class="btn btn-sm btn-outline-primary" type="button" data-accion="editar" data-tipo="compra" data-id="${c.compraId}" title="Editar"><i class="bi bi-pencil"></i></button>
                </td>
            </tr>`);
        });
        tbody.innerHTML = rows.join("") || '<tr><td colspan="5" class="text-center text-muted py-3">Sin entradas</td></tr>';
        if (badge) badge.textContent = rows.length;
    }

    function renderSalidasMaterial(invId) {
        const tbody = document.getElementById("tablasSalidasBody");
        const badge = document.getElementById("badgeSalidasCount");
        if (!tbody) return;
        const rows = [];
        ventasDB.filter((v) => String(v.inventarioId) === String(invId)).forEach((v) => {
            const total = Number(v.cantidad || 0) * Number(v.precioVenta || 0);
            rows.push(`<tr>
                <td class="small">${formatDateCO(v.fechaVenta)}</td>
                <td class="small text-end">${formatQty(v.cantidad, "")}</td>
                <td class="small text-end">${formatCOP(v.precioVenta)}</td>
                <td class="small">${formatCOP(total)}</td>
                <td class="small">${escapeHtml(v.nombreCentroAcopio || "—")}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-secondary" type="button" data-accion="ver" data-tipo="venta" data-id="${v.ventaId}" title="Ver"><i class="bi bi-eye"></i></button>
                    <button class="btn btn-sm btn-outline-primary" type="button" data-accion="editar" data-tipo="venta" data-id="${v.ventaId}" title="Editar"><i class="bi bi-pencil"></i></button>
                </td>
            </tr>`);
        });
        tbody.innerHTML = rows.join("") || '<tr><td colspan="6" class="text-center text-muted py-3">Sin ventas</td></tr>';
        if (badge) badge.textContent = rows.length;
    }

    // ============================================================
    // PICKER DE CATÁLOGO
    // ============================================================
    let pickerCatalogo = [];

    function abrirPicker() {
        const modalEl = document.getElementById("inv-modal-picker");
        if (!modalEl) return;
        document.getElementById("inv-picker-buscar").value = "";
        document.getElementById("inv-picker-categoria").value = "";
        document.getElementById("inv-picker-mostrar").value = "todos";
        cargarCatalogo();
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
        setTimeout(() => document.getElementById("inv-picker-buscar")?.focus(), 300);
    }

    function cargarCatalogo() {
        const cont = document.getElementById("inv-picker-contador");
        if (cont) cont.textContent = "Cargando catálogo...";
        const puntoId = document.getElementById("inv-crear-punto-id")?.value || "";
        const url = `/punto-eca/inventario/catalogo/buscar/?puntoId=${encodeURIComponent(puntoId)}`;
        fetch(url, { headers: { Accept: "application/json" } })
            .then((r) => r.json())
            .then((data) => {
                pickerCatalogo = Array.isArray(data) ? data : [];
                const idsEnInv = new Set(materialesDB.map((m) => String(m.materialId)));
                pickerCatalogo.forEach((m) => { m.enInventario = idsEnInv.has(String(m.materialId)); });
                popularCategoriasPicker();
                renderPicker();
            })
            .catch(() => {
                pickerCatalogo = [];
                if (cont) cont.textContent = "Error cargando catálogo";
            });
    }

    function popularCategoriasPicker() {
        const sel = document.getElementById("inv-picker-categoria");
        if (!sel) return;
        const cats = Array.from(new Set(pickerCatalogo.map((m) => m.nmbCategoria).filter(Boolean))).sort();
        sel.innerHTML = '<option value="">Todas</option>' + cats.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
    }

    function renderPicker() {
        const q = (document.getElementById("inv-picker-buscar")?.value || "").toLowerCase().trim();
        const cat = document.getElementById("inv-picker-categoria")?.value || "";
        const filtro = document.getElementById("inv-picker-mostrar")?.value || "todos";
        const lista = document.getElementById("inv-picker-lista");
        const vacio = document.getElementById("inv-picker-vacio");
        const cont = document.getElementById("inv-picker-contador");
        if (!lista) return;

        const filtrados = pickerCatalogo.filter((m) => {
            const matchQ = !q || (m.nmbMaterial || "").toLowerCase().includes(q) || (m.dscMaterial || "").toLowerCase().includes(q) || (m.nmbTipo || "").toLowerCase().includes(q);
            const matchC = !cat || m.nmbCategoria === cat;
            const matchF = filtro === "todos" || (filtro === "en-inventario" && m.enInventario) || (filtro === "disponibles" && !m.enInventario);
            return matchQ && matchC && matchF;
        });

        if (cont) cont.textContent = `Mostrando ${filtrados.length} de ${pickerCatalogo.length} materiales`;
        if (filtrados.length === 0) {
            lista.innerHTML = "";
            if (vacio) vacio.style.display = "block";
            return;
        }
        if (vacio) vacio.style.display = "none";
        lista.innerHTML = filtrados.map((m) => {
            const accion = m.enInventario ? "Seleccionar" : "Agregar a mi inventario";
            const estado = m.enInventario
                ? '<span class="badge bg-success ms-2">En mi inventario</span>'
                : '<span class="badge bg-warning text-dark ms-2">Disponible para agregar</span>';
            return `<button type="button" class="list-group-item list-group-item-action d-flex align-items-start gap-3" data-mat-id="${escapeHtml(m.materialId)}">
                <div class="inv-mini-img"><i class="bi bi-box-seam"></i></div>
                <div class="flex-grow-1 text-start">
                    <div class="fw-semibold">${escapeHtml(m.nmbMaterial)}</div>
                    <small class="text-muted d-block mb-1">${escapeHtml(m.dscMaterial || "")}</small>
                    <span class="badge bg-primary me-1">${escapeHtml(m.nmbTipo || "")}</span>
                    <span class="badge bg-secondary">${escapeHtml(m.nmbCategoria || "")}</span>
                    <span class="badge bg-light text-dark ms-1">${escapeHtml(m.unidad || "")}</span>
                    ${estado}
                </div>
                <span class="badge bg-success rounded-pill align-self-start">${accion}</span>
            </button>`;
        }).join("");
    }

    function seleccionarMaterialPicker(materialId) {
        const item = pickerCatalogo.find((m) => String(m.materialId) === String(materialId));
        if (!item) return;
        bootstrap.Modal.getInstance(document.getElementById("inv-modal-picker"))?.hide();
        document.getElementById("inv-crear-material-id").value = item.materialId;
        document.getElementById("inv-crear-material-nombre").value = item.nmbMaterial || "";
        const sel = document.getElementById("inv-crear-unidad-medida");
        if (sel && item.unidad) sel.value = item.unidad;
        document.getElementById("inv-tab-buscar-placeholder").style.display = "none";
        document.getElementById("inv-tab-buscar-form-container").style.display = "block";
        activarOvTab("ovtab-buscar");
        setTimeout(() => {
            document.getElementById("inv-tab-buscar-form-container")?.scrollIntoView({ behavior: "smooth", block: "start" });
            setTimeout(() => document.getElementById("inv-crear-stock-inicial")?.focus(), 400);
        }, 200);
    }

    function limpiarSeleccionCrear() {
        ["inv-crear-material-id", "inv-crear-material-nombre", "inv-crear-stock-inicial",
         "inv-crear-capacidad-maxima", "inv-crear-unidad-medida", "inv-crear-precio-compra",
         "inv-crear-precio-venta", "inv-crear-umbral-alerta", "inv-crear-umbral-critico"]
            .forEach((id) => { const el = document.getElementById(id); if (el) { el.value = ""; el.classList.remove("is-invalid"); } });
        document.getElementById("inv-crear-mensaje-estado").style.display = "none";
        document.getElementById("inv-tab-buscar-form-container").style.display = "none";
        document.getElementById("inv-tab-buscar-placeholder").style.display = "block";
    }

    // ============================================================
    // FORM SUBMIT: CREAR INVENTARIO
    // ============================================================
    function validarOrdenUmbrales(alertaId, criticoId, errorId) {
        const alertaInput = document.getElementById(alertaId);
        const criticoInput = document.getElementById(criticoId);
        const errorEl = document.getElementById(errorId);
        const alerta = Number(alertaInput?.value);
        const critico = Number(criticoInput?.value);
        if (Number.isFinite(alerta) && Number.isFinite(critico) && alerta >= critico) {
            if (errorEl) errorEl.style.display = "block";
            if (alertaInput) alertaInput.classList.add("is-invalid");
            if (criticoInput) criticoInput.classList.add("is-invalid");
            return false;
        }
        if (errorEl) errorEl.style.display = "none";
        if (alertaInput) alertaInput.classList.remove("is-invalid");
        if (criticoInput) criticoInput.classList.remove("is-invalid");
        return true;
    }

    function submitCrearInventario(e) {
        if (e) e.preventDefault();
        const required = [
            { id: "inv-crear-stock-inicial", val: document.getElementById("inv-crear-stock-inicial").value },
            { id: "inv-crear-capacidad-maxima", val: document.getElementById("inv-crear-capacidad-maxima").value },
            { id: "inv-crear-unidad-medida", val: document.getElementById("inv-crear-unidad-medida").value },
            { id: "inv-crear-precio-compra", val: document.getElementById("inv-crear-precio-compra").value },
            { id: "inv-crear-precio-venta", val: document.getElementById("inv-crear-precio-venta").value },
            { id: "inv-crear-umbral-alerta", val: document.getElementById("inv-crear-umbral-alerta").value },
            { id: "inv-crear-umbral-critico", val: document.getElementById("inv-crear-umbral-critico").value },
        ];
        let invalid = false;
        required.forEach((r) => {
            const el = document.getElementById(r.id);
            if (!r.val && r.val !== 0) { el.classList.add("is-invalid"); invalid = true; }
            else { el.classList.remove("is-invalid"); }
        });
        if (invalid) {
            const msg = document.getElementById("inv-crear-mensaje-estado");
            msg.className = "alert alert-danger mt-4";
            document.getElementById("inv-crear-texto-mensaje").textContent = "Por favor completa todos los campos requeridos.";
            msg.style.display = "block";
            return;
        }
        if (!validarOrdenUmbrales(
            "inv-crear-umbral-alerta",
            "inv-crear-umbral-critico",
            "inv-crear-umbral-orden-error"
        )) {
            const msg = document.getElementById("inv-crear-mensaje-estado");
            msg.className = "alert alert-danger mt-4";
            document.getElementById("inv-crear-texto-mensaje").textContent =
                "El umbral de alerta debe ser menor al umbral crítico (la alerta se dispara antes que el estado crítico).";
            msg.style.display = "block";
            return;
        }
        const form = document.getElementById("inv-form-crear-inventario");
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.stockActual = Number(payload.stockInicial);
        payload.capacidadMaxima = Number(payload.capacidadMaxima);
        payload.precioCompra = Number(payload.precioCompra);
        payload.precioVenta = Number(payload.precioVenta);
        payload.umbralAlerta = Number(payload.umbralAlerta);
        payload.umbralCritico = Number(payload.umbralCritico);
        payload.puntoEcaId = String(payload.puntoId || "");
        payload.materialId = String(payload.materialId || "");
        delete payload.puntoId;
        delete payload.stockInicial;

        fetch("/punto-eca/inventario/agregar/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) throw new Error(data?.mensaje || data?.message || "Error al guardar");
                Swal.fire({ icon: "success", title: "¡Material agregado!", text: data.mensaje || "Operación exitosa", confirmButtonColor: "#198754" });
                setTimeout(() => window.location.reload(), 1500);
            })
            .catch((err) => {
                const msg = document.getElementById("inv-crear-mensaje-estado");
                msg.className = "alert alert-danger mt-4";
                document.getElementById("inv-crear-texto-mensaje").textContent = err.message || "Error al guardar";
                msg.style.display = "block";
            });
    }

    // ============================================================
    // SELECT2 — Inicialización de los 17 selects de la sección.
    // Select2 + jQuery + i18n es + bootstrap-5-theme ya están
    // cargados por templates/ecas/puntoECA-layout.html (CDN).
    // Re-init idempotente: select2('destroy') antes de select2().
    // ============================================================

    function _initSelect2InSection() {
        if (typeof window.jQuery === "undefined" || typeof window.jQuery.fn.select2 === "undefined") {
            console.warn("[inventario] Select2 no está cargado; los filtros quedan como <select> nativos.");
            return;
        }
        const $ = window.jQuery;
        const base = { theme: "bootstrap-5", language: "es", width: "100%" };

        const apply = (selector, extra) => {
            const $els = $(selector);
            if (!$els.length) return;
            $els.each(function () {
                const $el = $(this);
                if ($el.data("select2")) $el.select2("destroy");
                $el.select2(Object.assign({}, base, extra || {}));
            });
        };

        // 1) Filtros landing (cards)
        apply("#inv-filter-categoria, #inv-filter-tipo, #inv-filter-estado, #inv-filter-ocupacion");

        // 2) Filtros historial general (Select2 en todos MENOS tipo de
        // movimiento, que debe permanecer como <select> nativo para que el
        // listener de 'change' dispare confiablemente el toggle del centro
        // de acopio al elegir "Venta").
        apply("#inv-hfiltro-material, #inv-hfiltro-categoria, #inv-hfiltro-tipo-material, #inv-hfiltro-centro");

        // 3) Filtro chart
        apply("#inv-flujo-granularidad");

        // 4) Form inputs inline (ovtab-buscar, workspace)
        apply("#inv-crear-unidad-medida, #formSalidaCentro");

        // 5) Selects en modales → dropdownParent requerido
        apply("#inv-picker-categoria, #inv-picker-mostrar", { dropdownParent: $("#inv-modal-picker") });
        apply("#inv-edit-unidad-medida", { dropdownParent: $("#inv-modal-editar-inventario") });
        apply("#inv-carga-tipo", { dropdownParent: $("#inv-modalCargaMasiva") });
        apply("#inv-edit-venta-centro", { dropdownParent: $("#inv-modal-editar-venta") });
    }

    // ============================================================
    // EVENT LISTENERS (delegación + específicos)
    // ============================================================

    function bind() {
        _initSelect2InSection();
        // Listeners de cálculo de total (cantidad × precio) en forms crear
        _bindFormTotalListeners();
        // Tabs
        document.querySelectorAll("#otrasVistasTabs [data-ovtab]").forEach((btn) => {
            btn.addEventListener("click", () => activarOvTab(btn.dataset.ovtab));
        });
        document.querySelectorAll("#workspaceTabs [data-tab]").forEach((btn) => {
            btn.addEventListener("click", () => activarTab(btn.dataset.tab));
        });

        // Filtros landing
        ["inv-filter-nombre", "inv-filter-categoria", "inv-filter-tipo", "inv-filter-estado", "inv-filter-ocupacion"]
            .forEach((id) => document.getElementById(id)?.addEventListener("input", aplicarFiltrosCards));
        document.getElementById("inv-filter-limpiar")?.addEventListener("click", limpiarFiltrosCards);
        document.getElementById("inv-filter-limpiar-vacio")?.addEventListener("click", limpiarFiltrosCards);

        // Cards → workspace (delegado en el grid, captura clicks en card o botón)
        const cardsGrid = document.getElementById("inv-cards-grid");
        if (cardsGrid) {
            const goFromCard = (target) => {
                const card = target.closest(".inv-tarjeta-material");
                if (!card) return;
                irWorkspace(card.dataset.invId, "tab-datos");
            };
            cardsGrid.addEventListener("click", (e) => goFromCard(e.target));
            cardsGrid.addEventListener("keydown", (e) => {
                if (e.key !== "Enter" && e.key !== " ") return;
                if (!e.target.closest(".inv-tarjeta")) return;
                e.preventDefault();
                goFromCard(e.target);
            });
        }

        // Volver / cambiar
        document.getElementById("inv-btn-volver-landing")?.addEventListener("click", irLanding);
        document.getElementById("inv-btn-cambiar-material")?.addEventListener("click", irLanding);
        document.getElementById("inv-btn-cambiar-material-compra")?.addEventListener("click", irLanding);
        document.getElementById("inv-btn-cambiar-material-venta")?.addEventListener("click", irLanding);

        // Picker
        document.getElementById("inv-btn-abrir-picker")?.addEventListener("click", (e) => { e.preventDefault(); abrirPicker(); });
        ["inv-picker-buscar"].forEach((id) => document.getElementById(id)?.addEventListener("input", renderPicker));
        ["inv-picker-categoria", "inv-picker-mostrar"].forEach((id) => document.getElementById(id)?.addEventListener("change", renderPicker));
        document.getElementById("inv-picker-lista")?.addEventListener("click", (e) => {
            const btn = e.target.closest("button[data-mat-id]");
            if (btn) seleccionarMaterialPicker(btn.dataset.matId);
        });
        document.getElementById("inv-btn-limpiar-seleccion")?.addEventListener("click", limpiarSeleccionCrear);
        document.getElementById("inv-btn-cancelar-crear")?.addEventListener("click", limpiarSeleccionCrear);
        document.getElementById("inv-form-crear-inventario")?.addEventListener("submit", submitCrearInventario);

        // Acciones en tablas (delegado). inv-tablasHistorialBody existe en
        // landing y workspace, por eso se bindea a TODOS los elementos.
        // (workspace usa prefijo inv-ws- para evitar IDs duplicados).
        ["inv-tablasHistorialBody", "tablasEntradasBody", "tablasSalidasBody"]
            .forEach((tbodyId) => {
                const tbodySelector = tbodyId.startsWith("inv-")
                    ? `[id="${tbodyId}"], [id="inv-ws-${tbodyId.slice(4)}"]`
                    : `#${tbodyId}`;
                document.querySelectorAll(tbodySelector).forEach((tbody) => {
                    tbody.addEventListener("click", (e) => {
                        const btn = e.target.closest("button[data-accion]");
                        if (!btn) return;
                        const id = btn.dataset.id;
                        const tipo = btn.dataset.tipo;
                        if (btn.dataset.accion === "ver") verMovimiento(tipo, id);
                        if (btn.dataset.accion === "editar") editarMovimiento(tipo, id);
                    });
                });
            });

        // Render inicial
        renderHistorialGeneral();
        bindExtras();
        renderFlujoMaterialesList();
        // Deep-link desde sidebar: ?ovtab=ovtab-xxx
        const urlOvtab = new URLSearchParams(window.location.search).get("ovtab");
        if (urlOvtab) {
            const valid = ["ovtab-inventario", "ovtab-buscar", "ovtab-bulk", "ovtab-historial", "ovtab-flujo"];
            if (valid.includes(urlOvtab)) activarOvTab(urlOvtab);
        }
        // Render charts tras primer paint (espera CSS)
        setTimeout(() => {
            if (document.getElementById("inv-stock-time-chart")) renderOvtabChart();
            if (document.getElementById("stockTimeChart") && currentMaterial) renderWsChart();
        }, 100);
    }

    // ============================================================
    // DETALLE / EDITAR MOVIMIENTO (compra/venta)
    // ============================================================
    function findMovimiento(tipo, id) {
        const list = tipo === "compra" ? comprasDB : ventasDB;
        return list.find((m) => String(m.compraId || m.ventaId) === String(id));
    }

    function verMovimiento(tipo, id) {
        const m = findMovimiento(tipo, id);
        if (!m) return;
        const prefix = tipo === "compra" ? "inv-detalle-compra" : "inv-detalle-venta";
        const set = (suffix, v) => { const el = document.getElementById(`${prefix}-${suffix}`); if (el) el.textContent = v; };
        const total = Number(m.cantidad || 0) * Number(tipo === "compra" ? m.precioCompra : m.precioVenta);
        set("material", m.nombreMaterial || "—");
        set("categoria", m.nombreCategoria || "—");
        set("fecha", formatDateCO(tipo === "compra" ? m.fechaCompra : m.fechaVenta));
        set("cantidad", m.cantidad);
        set("precio", tipo === "compra" ? formatCOP(m.precioCompra) : formatCOP(m.precioVenta));
        set("total", formatCOP(total));
        set("id", m.compraId || m.ventaId);
        set("observaciones", m.observaciones || "—");
        if (tipo === "venta") set("centro", m.nombreCentroAcopio || "—");
        bootstrap.Modal.getOrCreateInstance(document.getElementById(`inv-modal-detalle-${tipo}`)).show();
    }

    function editarMovimiento(tipo, id) {
        const m = findMovimiento(tipo, id);
        if (!m) return;
        const modalEl = document.getElementById(`inv-modal-detalle-${tipo}`);
        if (modalEl) bootstrap.Modal.getInstance(modalEl)?.hide();
        const prefix = tipo === "compra" ? "inv-edit-compra" : "inv-edit-venta";
        document.getElementById(`${prefix}-id`).value = m.compraId || m.ventaId;
        document.getElementById(`${prefix}-inventario-id`).value = m.inventarioId;
        document.getElementById(`${prefix}-material-id`).value = m.materialId;
        document.getElementById(`${prefix}-material`).value = m.nombreMaterial || "";
        document.getElementById(`${prefix}-fecha`).value = (tipo === "compra" ? m.fechaCompra : m.fechaVenta || "").slice(0, 16);
        document.getElementById(`${prefix}-cantidad`).value = m.cantidad || "";
        document.getElementById(`${prefix}-precio`).value = (tipo === "compra" ? m.precioCompra : m.precioVenta) || "";
        document.getElementById(`${prefix}-observaciones`).value = m.observaciones || "";
        // Hidden de validación de stock (Decisión de Commit 2): se usan
        // para evitar que la edición deje el inventario en estado inválido
        // (ej. venta que lleva el stock a negativo). El JS hace la validación
        // y el backend la hace de nuevo de forma autoritativa.
        if (currentMaterial) {
            document.getElementById(`${prefix}-stock-actual`).value = currentMaterial.stockActual ?? "";
            document.getElementById(`${prefix}-capacidad-maxima`).value = currentMaterial.capacidadMaxima ?? "";
        }
        document.getElementById(`${prefix}-cantidad-original`).value = m.cantidad ?? "";
        if (tipo === "venta") {
            const sel = document.getElementById(`${prefix}-centro`);
            if (sel) sel.value = m.centroAcopioId || "";
        }
        setTimeout(() => bootstrap.Modal.getOrCreateInstance(document.getElementById(`inv-modal-editar-${tipo}`)).show(), 200);
    }

    // --- Editar inventario (hoja técnica) ---
    function submitEditarInventario() {
        const required = ["inv-edit-stock-inicial", "inv-edit-capacidad-maxima", "inv-edit-unidad-medida",
            "inv-edit-umbral-alerta", "inv-edit-umbral-critico", "inv-edit-precio-compra", "inv-edit-precio-venta"];
        let invalid = false;
        required.forEach((id) => { const el = document.getElementById(id); if (!el.value && el.value !== 0) { el.classList.add("is-invalid"); invalid = true; } else { el.classList.remove("is-invalid"); } });
        if (invalid) {
            const msg = document.getElementById("inv-edit-mensaje-estado");
            msg.className = "alert alert-danger mt-4";
            document.getElementById("inv-edit-texto-mensaje").textContent = "Por favor completa todos los campos requeridos.";
            msg.style.display = "block";
            return;
        }
        if (!validarOrdenUmbrales(
            "inv-edit-umbral-alerta",
            "inv-edit-umbral-critico",
            "inv-edit-umbral-orden-error"
        )) {
            const msg = document.getElementById("inv-edit-mensaje-estado");
            msg.className = "alert alert-danger mt-4";
            document.getElementById("inv-edit-texto-mensaje").textContent =
                "El umbral de alerta debe ser menor al umbral crítico (la alerta se dispara antes que el estado crítico).";
            msg.style.display = "block";
            return;
        }
        const invId = document.getElementById("inv-edit-inventario-id").value;
        const payload = {
            stockActual: Number(document.getElementById("inv-edit-stock-inicial").value),
            capacidadMaxima: Number(document.getElementById("inv-edit-capacidad-maxima").value),
            unidadMedida: document.getElementById("inv-edit-unidad-medida").value,
            umbralAlerta: Number(document.getElementById("inv-edit-umbral-alerta").value),
            umbralCritico: Number(document.getElementById("inv-edit-umbral-critico").value),
            precioCompra: Number(document.getElementById("inv-edit-precio-compra").value),
            precioVenta: Number(document.getElementById("inv-edit-precio-venta").value),
        };
        fetch(`/punto-eca/inventario/actualizar/${invId}/`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al guardar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-editar-inventario"))?.hide();
                Swal.fire({ icon: "success", title: "¡Cambios guardados!", text: "La hoja técnica se actualizó.", confirmButtonColor: "#0d6efd" });
                setTimeout(() => window.location.reload(), 1200);
            })
            .catch((err) => {
                const msg = document.getElementById("inv-edit-mensaje-estado");
                msg.className = "alert alert-danger mt-4";
                document.getElementById("inv-edit-texto-mensaje").textContent = err.message;
                msg.style.display = "block";
            });
    }
    document.getElementById("inv-btn-guardar-editar-inventario")?.addEventListener("click", submitEditarInventario);

    // --- Detalle → Editar (en cadena) ---
    document.getElementById("inv-btn-detalle-compra-editar")?.addEventListener("click", () => {
        const id = document.getElementById("inv-detalle-compra-id").textContent;
        editarMovimiento("compra", id);
    });
    document.getElementById("inv-btn-detalle-venta-editar")?.addEventListener("click", () => {
        const id = document.getElementById("inv-detalle-venta-id").textContent;
        editarMovimiento("venta", id);
    });

    // --- Eliminar inventario ---
    document.getElementById("inv-btn-confirmar-eliminar")?.addEventListener("click", () => {
        if (!currentMaterial) return;
        const invId = currentMaterial.inventarioId;
        fetch(`/punto-eca/inventario/eliminar/${invId}/`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify({ puntoId: Number(document.querySelector("section[data-seccion='inventario']").dataset.puntoEcaId) }),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al eliminar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-eliminar"))?.hide();
                Swal.fire({ icon: "success", title: "Eliminado", text: "Material removido del inventario.", confirmButtonColor: "#dc3545" });
                setTimeout(() => window.location.reload(), 1200);
            })
            .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
    });

    // ============================================================
    // SUBMIT: REGISTRAR COMPRA / VENTA (workspace forms)
    // ============================================================
    function submitEntrada(e) {
        if (e) e.preventDefault();
        const form = document.getElementById("formEntrada");
        if (!form.checkValidity()) { form.reportValidity(); return; }
        const btn = e?.currentTarget || document.getElementById("inv-btn-guardar-entrada");
        const raw = Object.fromEntries(new FormData(form).entries());
        // Mapear nombres del form al contrato del servicio
        // (servicio espera fechaCompra + puntoEcaId, no "fecha" + "puntoId").
        const payload = {
            inventarioId: raw.inventarioId,
            materialId: currentMaterial?.materialId,
            cantidad: Number(raw.cantidad),
            fechaCompra: raw.fecha,
            precioCompra: Number(raw.precioCompra),
            observaciones: raw.observaciones || "",
            puntoEcaId: raw.puntoId,
        };
        const promise = fetch("/punto-eca/movimientos/registrar-compra/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || d?.message || "Error al registrar");
                Swal.fire({ icon: "success", title: "Compra registrada", text: d.mensaje || "Operación exitosa", timer: 1500, showConfirmButton: false });
                // Reset del form para que un nuevo registro no herede valores
                form.reset();
                setTimeout(() => window.location.reload(), 1500);
            })
            .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
        withLoading(btn, () => promise);
    }
    function submitSalida(e) {
        if (e) e.preventDefault();
        const form = document.getElementById("formSalida");
        if (!form.checkValidity()) { form.reportValidity(); return; }
        const centro = document.getElementById("formSalidaCentro");
        if (centro && !centro.value) { centro.reportValidity(); return; }
        const btn = e?.currentTarget || document.getElementById("inv-btn-guardar-salida");
        const raw = Object.fromEntries(new FormData(form).entries());
        // Mapear nombres del form al contrato del servicio
        // (servicio espera fechaVenta + puntoEcaId, no "fecha" + "puntoId").
        const payload = {
            inventarioId: raw.inventarioId,
            materialId: currentMaterial?.materialId,
            cantidad: Number(raw.cantidad),
            fechaVenta: raw.fecha,
            precioVenta: Number(raw.precioVenta),
            observaciones: raw.observaciones || "",
            centroAcopioId: raw.centroAcopioId,
            puntoEcaId: raw.puntoId,
        };
        const promise = fetch("/punto-eca/movimientos/registrar-venta/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || d?.message || "Error al registrar");
                Swal.fire({ icon: "success", title: "Venta registrada", text: d.mensaje || "Operación exitosa", timer: 1500, showConfirmButton: false });
                form.reset();
                setTimeout(() => window.location.reload(), 1500);
            })
            .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
        withLoading(btn, () => promise);
    }

    // ============================================================
    // INFO MATERIAL: poblar campos readonly (Tipo/Categoría/Unidad/Stock/Cap)
    // y total auto-calculado (cantidad × precio) en tiempo real.
    // Se invoca desde irWorkspace() y cada vez que se selecciona un material.
    // ============================================================
    function poblarInfoMaterial(prefix) {
        if (!currentMaterial) return;
        const inv = currentMaterial;
        const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v ?? ""; };
        setVal(`${prefix}MaterialTipo`, inv.tipo);
        setVal(`${prefix}MaterialCategoria`, inv.categoria);
        setVal(`${prefix}MaterialUnidad`, inv.unidad);
        setVal(`${prefix}StockActual`, inv.stockActual);
        setVal(`${prefix}CapacidadMaxima`, inv.capacidadMaxima);
        // Autorrellenar precio unitario desde el backend (el usuario puede
        // sobrescribirlo). Es un buen default porque evita teclear el precio
        // estándar del material y reduce errores.
        if (prefix === "formEntrada") {
            const precioEl = document.getElementById("formEntradaPrecio");
            if (precioEl && inv.precioCompra != null && !precioEl.value) {
                precioEl.value = inv.precioCompra;
            }
        } else if (prefix === "formSalida") {
            const precioEl = document.getElementById("formSalidaPrecio");
            if (precioEl && inv.precioVenta != null && !precioEl.value) {
                precioEl.value = inv.precioVenta;
            }
        }
        // Sugerir cantidad=1 como punto de partida, si el campo está vacío.
        // El usuario lo sobrescribe; la idea es que vea el Total calculado
        // (1 × precio) apenas entra al form, sin tener que tipear cantidad.
        const cantEl = document.getElementById(`${prefix}Cantidad`);
        if (cantEl && !cantEl.value) cantEl.value = 1;
        // Recalcular total con el precio recién autorrellenado
        if (prefix === "formEntrada") actualizarTotalEntrada();
        if (prefix === "formSalida") actualizarTotalVenta();
        // Pintar el preview de stock resultante con el stock base del material
        // (aunque el usuario todavía no haya tipeado cantidad, queremos ver
        // el stock actual como punto de partida).
        actualizarStockPreview(prefix);
    }
    function poblarInfoMaterialEdicion(tipo) {
        // Para los modales de edición: poblar los 3 hidden de validación
        // de stock desde la fila del historial de la compra/venta seleccionada.
        // `currentMaterial` tiene stockActual/capacidadMaxima, y la cantidad
        // original se pasa en la firma de la función.
        if (!currentMaterial) return;
        const inv = currentMaterial;
        const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v ?? ""; };
        const prefix = tipo === "compra" ? "inv-edit-compra" : "inv-edit-venta";
        setVal(`${prefix}-stock-actual`, inv.stockActual);
        setVal(`${prefix}-capacidad-maxima`, inv.capacidadMaxima);
        // cantidadOriginal se setea desde editarMovimiento() al abrir el modal
    }
    function actualizarTotalEntrada() {
        const cant = Number(document.getElementById("formEntradaCantidad")?.value || 0);
        const precio = Number(document.getElementById("formEntradaPrecio")?.value || 0);
        const total = cant * precio;
        const el = document.getElementById("formEntradaTotalCompra");
        if (el) el.value = total > 0 ? total.toLocaleString("es-CO", { maximumFractionDigits: 0 }) : "";
        actualizarStockPreviewEntrada();
    }
    function actualizarTotalVenta() {
        const cant = Number(document.getElementById("formSalidaCantidad")?.value || 0);
        const precio = Number(document.getElementById("formSalidaPrecio")?.value || 0);
        const total = cant * precio;
        const el = document.getElementById("formSalidaTotalVenta");
        if (el) el.value = total > 0 ? total.toLocaleString("es-CO", { maximumFractionDigits: 0 }) : "";
        actualizarStockPreviewSalida();
    }
    // Preview de stock resultante: muestra en tiempo real cuánto stock
    // quedará tras aplicar este movimiento. Color verde si el resultado
    // es válido; rojo si excede la capacidad máxima (compra) o resulta
    // negativo (venta). Es solo referencia visual; el backend re-valida.
    function actualizarStockPreviewEntrada() {
        const stockEl = document.getElementById("formEntradaStockResultante");
        const unidadEl = document.getElementById("formEntradaStockResultanteUnidad");
        const capEl = document.getElementById("formEntradaStockResultanteCap");
        if (!stockEl) return;
        const stockBase = Number(document.getElementById("formEntradaStockActual")?.value || 0);
        const capacidad = Number(document.getElementById("formEntradaCapacidadMaxima")?.value || 0);
        const cant = Number(document.getElementById("formEntradaCantidad")?.value || 0);
        const unidad = document.getElementById("formEntradaMaterialUnidad")?.value || "";
        const resultante = stockBase + cant;
        stockEl.value = resultante.toLocaleString("es-CO", { maximumFractionDigits: 2 });
        if (unidadEl) unidadEl.textContent = unidad || "unidades";
        if (capEl) capEl.textContent = capacidad > 0 ? `/ máx. ${capacidad.toLocaleString("es-CO", { maximumFractionDigits: 2 })}` : "";
        if (capacidad > 0 && resultante > capacidad) {
            stockEl.style.backgroundColor = "#f8d7da";
            stockEl.style.color = "#58151c";
        } else {
            stockEl.style.backgroundColor = "#d1e7dd";
            stockEl.style.color = "#0a3622";
        }
    }
    function actualizarStockPreviewSalida() {
        const stockEl = document.getElementById("formSalidaStockRestante");
        const unidadEl = document.getElementById("formSalidaStockRestanteUnidad");
        if (!stockEl) return;
        const stockBase = Number(document.getElementById("formSalidaStockActual")?.value || 0);
        const cant = Number(document.getElementById("formSalidaCantidad")?.value || 0);
        const unidad = document.getElementById("formSalidaMaterialUnidad")?.value || "";
        const restante = stockBase - cant;
        stockEl.value = restante.toLocaleString("es-CO", { maximumFractionDigits: 2 });
        if (unidadEl) unidadEl.textContent = unidad || "unidades";
        if (restante < 0) {
            stockEl.style.backgroundColor = "#f8d7da";
            stockEl.style.color = "#58151c";
        } else {
            stockEl.style.backgroundColor = "#d1e7dd";
            stockEl.style.color = "#0a3622";
        }
    }
    function actualizarStockPreview(prefix) {
        if (prefix === "formEntrada") actualizarStockPreviewEntrada();
        else if (prefix === "formSalida") actualizarStockPreviewSalida();
    }
    function _bindFormTotalListeners() {
        const fECant = document.getElementById("formEntradaCantidad");
        const fEPrecio = document.getElementById("formEntradaPrecio");
        if (fECant) fECant.addEventListener("input", actualizarTotalEntrada);
        if (fEPrecio) fEPrecio.addEventListener("input", actualizarTotalEntrada);
        const fSCant = document.getElementById("formSalidaCantidad");
        const fSPrecio = document.getElementById("formSalidaPrecio");
        if (fSCant) fSCant.addEventListener("input", actualizarTotalVenta);
        if (fSPrecio) fSPrecio.addEventListener("input", actualizarTotalVenta);
    }

    // ============================================================
    // SUBMIT: EDITAR COMPRA / VENTA (modales)
    // ============================================================
    function submitEditarCompra() {
        const form = document.getElementById("inv-form-editar-compra");
        if (!form.checkValidity()) { form.reportValidity(); return; }
        const btn = document.getElementById("inv-btn-guardar-editar-compra");
        const raw = Object.fromEntries(new FormData(form).entries());
        // Validar stock resultante con la edición. El stock actual ya
        // incluye esta compra, así que el nuevo stock = actual - original + nuevo.
        const stockActual = Number(document.getElementById("inv-edit-compra-stock-actual")?.value || 0);
        const capacidad = Number(document.getElementById("inv-edit-compra-capacidad-maxima")?.value || 0);
        const cantOriginal = Number(document.getElementById("inv-edit-compra-cantidad-original")?.value || 0);
        const nuevaCant = Number(raw.cantidad);
        const stockResultante = stockActual - cantOriginal + nuevaCant;
        if (capacidad > 0 && stockResultante > capacidad) {
            Swal.fire({
                icon: "warning",
                title: "Stock excede capacidad",
                text: `El stock resultante (${stockResultante.toLocaleString("es-CO")}) supera la capacidad máxima (${capacidad.toLocaleString("es-CO")}). Ajustá la cantidad.`,
            });
            return;
        }
        // Mapear nombres del form al contrato del servicio.
        const payload = {
            compraId: raw.id,
            fechaCompra: raw.fecha,
            cantidad: nuevaCant,
            precioCompra: Number(raw.precioCompra),
            observaciones: raw.observaciones || "",
        };
        const promise = fetch(`/punto-eca/movimientos/editar-compra/${raw.id}/`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al editar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-editar-compra"))?.hide();
                Swal.fire({ icon: "success", title: "Compra actualizada", timer: 1500, showConfirmButton: false });
                setTimeout(() => window.location.reload(), 1500);
            })
            .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
        withLoading(btn, () => promise);
    }
    function submitEditarVenta() {
        const form = document.getElementById("inv-form-editar-venta");
        if (!form.checkValidity()) { form.reportValidity(); return; }
        const centro = document.getElementById("inv-edit-venta-centro");
        if (centro && !centro.value) { centro.reportValidity(); return; }
        const btn = document.getElementById("inv-btn-guardar-editar-venta");
        const raw = Object.fromEntries(new FormData(form).entries());
        // Validar stock restante con la edición. El stock actual ya
        // incluye esta venta, así que el stock nuevo = actual + original - nuevo.
        const stockActual = Number(document.getElementById("inv-edit-venta-stock-actual")?.value || 0);
        const cantOriginal = Number(document.getElementById("inv-edit-venta-cantidad-original")?.value || 0);
        const nuevaCant = Number(raw.cantidad);
        const stockResultante = stockActual + cantOriginal - nuevaCant;
        if (stockResultante < 0) {
            Swal.fire({
                icon: "warning",
                title: "Stock insuficiente",
                text: `El stock resultante (${stockResultante.toLocaleString("es-CO")}) sería negativo. Ajustá la cantidad.`,
            });
            return;
        }
        // Mapear nombres del form al contrato del servicio.
        const payload = {
            ventaId: raw.id,
            fechaVenta: raw.fecha,
            cantidad: nuevaCant,
            precioVenta: Number(raw.precioVenta),
            observaciones: raw.observaciones || "",
        };
        if (centro) payload.centroAcopioId = centro.value;
        const promise = fetch(`/punto-eca/movimientos/editar-venta/${raw.id}/`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al editar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-editar-venta"))?.hide();
                Swal.fire({ icon: "success", title: "Venta actualizada", timer: 1500, showConfirmButton: false });
                setTimeout(() => window.location.reload(), 1500);
            })
            .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
        withLoading(btn, () => promise);
    }

    // ============================================================
    // ELIMINAR COMPRA / VENTA
    // ============================================================
    function eliminarMovimiento(tipo, id) {
        if (!id) return;
        const url = `/punto-eca/movimientos/borrar-${tipo}/${id}/`;
        Swal.fire({
            title: "¿Eliminar?",
            text: `Esta acción no se puede deshacer.`,
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#dc3545",
            cancelButtonColor: "#6c757d",
            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar",
        }).then((r) => {
            if (!r.isConfirmed) return;
            fetch(url, {
                method: "DELETE",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            })
                .then((res) => res.json().then((d) => ({ ok: res.ok, d })))
                .then(({ ok, d }) => {
                    if (!ok) throw new Error(d?.mensaje || "Error al eliminar");
                    Swal.fire({ icon: "success", title: "Eliminado", timer: 1200, showConfirmButton: false });
                    setTimeout(() => window.location.reload(), 1200);
                })
                .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
        });
    }
    function eliminarCompraActual() {
        const id = document.getElementById("inv-edit-compra-id")?.value;
        eliminarMovimiento("compra", id);
    }
    function eliminarVentaActual() {
        const id = document.getElementById("inv-edit-venta-id")?.value;
        eliminarMovimiento("venta", id);
    }
    function eliminarDetalleCompra() {
        eliminarMovimiento("compra", document.getElementById("inv-detalle-compra-id")?.textContent.trim());
    }
    function eliminarDetalleVenta() {
        eliminarMovimiento("venta", document.getElementById("inv-detalle-venta-id")?.textContent.trim());
    }

    // ============================================================
    // EXPORTAR CON FILTROS APLICADOS
    // ============================================================
    const PAGE_SIZE = 25;
    let historialPage = 1;

    function _lookupMaterialNombreByInventarioId(inventarioId) {
        if (!inventarioId) return "";
        const m = materialesDB.find((x) => String(x.inventarioId) === String(inventarioId));
        if (m && m.nombreMaterial) return m.nombreMaterial;
        const c = comprasDB.find((x) => String(x.inventarioId) === String(inventarioId));
        if (c && c.nombreMaterial) return c.nombreMaterial;
        const v = ventasDB.find((x) => String(x.inventarioId) === String(inventarioId));
        return (v && v.nombreMaterial) || "";
    }

    function buildExportQuery(base) {
        const params = new URLSearchParams();
        const materialIdFiltro = _q("inv-hfiltro-material")?.value;
        const materialIdEfectivo = isWorkspaceHistorial && currentMaterialId
            ? String(currentMaterialId)
            : materialIdFiltro;
        const materialNombre = materialIdEfectivo
            ? (currentMaterial && String(currentMaterial.inventarioId) === String(materialIdEfectivo)
                ? currentMaterial.nombre
                : _lookupMaterialNombreByInventarioId(materialIdEfectivo))
            : "";
        const categoria = _q("inv-hfiltro-categoria")?.value;
        const tipoMaterial = _q("inv-hfiltro-tipo-material")?.value;
        const tipo = _q("inv-hfiltro-tipo")?.value;
        const desde = _q("inv-hfiltro-desde")?.value;
        const hasta = _q("inv-hfiltro-hasta")?.value;
        const centro = _q("inv-hfiltro-centro")?.value;
        const cantidadMin = _q("inv-hfiltro-cantidad-min")?.value;
        const cantidadMax = _q("inv-hfiltro-cantidad-max")?.value;
        const montoMin = _q("inv-hfiltro-monto-min")?.value;
        const montoMax = _q("inv-hfiltro-monto-max")?.value;
        if (materialNombre) params.append("material", materialNombre);
        if (categoria) params.append("categoria", categoria);
        if (tipoMaterial) params.append("tipo", tipoMaterial);
        if (tipo) {
            params.append("tipo_movimiento", tipo);
        }
        if (desde) params.append("fecha_desde", desde);
        if (hasta) params.append("fecha_hasta", hasta);
        if (centro) params.append("centro_acopio", centro);
        if (cantidadMin) params.append("cantidad_min", cantidadMin);
        if (cantidadMax) params.append("cantidad_max", cantidadMax);
        if (montoMin) params.append("monto_min", montoMin);
        if (montoMax) params.append("monto_max", montoMax);
        const qs = params.toString();
        return qs ? `${base}?${qs}` : base;
    }
    function _exportarHistorialConSweetAlert(formato) {
        const base = `/punto-eca/movimientos/exportar-historial-${formato}/`;
        if (getCurrentHistorialRows().length === 0) {
            if (globalThis.Swal?.fire) {
                globalThis.Swal.fire({
                    icon: "info",
                    title: "Sin resultados",
                    text: "No hay movimientos para exportar con los filtros aplicados.",
                    confirmButtonColor: "#0d6efd",
                });
            } else {
                alert("No hay movimientos para exportar con los filtros aplicados.");
            }
            return;
        }
        window.location.href = buildExportQuery(base);
    }
    function exportarHistorialExcel() {
        _exportarHistorialConSweetAlert("excel");
    }
    function exportarHistorialPdf() {
        _exportarHistorialConSweetAlert("pdf");
    }

    // ============================================================
    // FILTRO HISTORIAL GENERAL (landing)
    // ============================================================
    function getCurrentHistorialRows() {
        const filtroMaterialId = _q("inv-hfiltro-material")?.value || "";
        const effectiveMaterialId = isWorkspaceHistorial && currentMaterialId
            ? String(currentMaterialId)
            : filtroMaterialId;
        const categoria = _q("inv-hfiltro-categoria")?.value || "";
        const tipoMaterial = _q("inv-hfiltro-tipo-material")?.value || "";
        const tipo = _q("inv-hfiltro-tipo")?.value || "";
        const desde = _q("inv-hfiltro-desde")?.value;
        const hasta = _q("inv-hfiltro-hasta")?.value;
        const centro = _q("inv-hfiltro-centro")?.value || "";
        const cantidadMin = parseFloat(_q("inv-hfiltro-cantidad-min")?.value);
        const cantidadMax = parseFloat(_q("inv-hfiltro-cantidad-max")?.value);
        const montoMin = parseFloat(_q("inv-hfiltro-monto-min")?.value);
        const montoMax = parseFloat(_q("inv-hfiltro-monto-max")?.value);
        const desdeD = desde ? new Date(desde + "T00:00:00") : null;
        const hastaD = hasta ? new Date(hasta + "T23:59:59") : null;

        const enRango = (iso) => {
            if (!desdeD && !hastaD) return true;
            const d = new Date(iso);
            if (isNaN(d)) return false;
            if (desdeD && d < desdeD) return false;
            if (hastaD && d > hastaD) return false;
            return true;
        };

        const rows = [];
        const aceptaCompra = !tipo || tipo === "compra";
        const aceptaVenta = !tipo || tipo === "venta";

        if (aceptaCompra) {
            comprasDB.forEach((c) => {
                if (effectiveMaterialId && String(c.inventarioId) !== String(effectiveMaterialId)) return;
                if (categoria && c.nombreCategoria !== categoria) return;
                if (tipoMaterial && c.nombreTipo !== tipoMaterial) return;
                if (!enRango(c.fechaCompra)) return;
                const cant = Number(c.cantidad || 0);
                if (!isNaN(cantidadMin) && cant < cantidadMin) return;
                if (!isNaN(cantidadMax) && cant > cantidadMax) return;
                const monto = cant * Number(c.precioCompra || 0);
                if (!isNaN(montoMin) && monto < montoMin) return;
                if (!isNaN(montoMax) && monto > montoMax) return;
                rows.push({ ...c, _tipo: "compra", _ts: c.fechaCompra });
            });
        }
        if (aceptaVenta) {
            ventasDB.forEach((v) => {
                if (effectiveMaterialId && String(v.inventarioId) !== String(effectiveMaterialId)) return;
                if (categoria && v.nombreCategoria !== categoria) return;
                if (tipoMaterial && v.nombreTipo !== tipoMaterial) return;
                if (centro && v.nombreCentroAcopio !== centro) return;
                if (!enRango(v.fechaVenta)) return;
                const cant = Number(v.cantidad || 0);
                if (!isNaN(cantidadMin) && cant < cantidadMin) return;
                if (!isNaN(cantidadMax) && cant > cantidadMax) return;
                const monto = cant * Number(v.precioVenta || 0);
                if (!isNaN(montoMin) && monto < montoMin) return;
                if (!isNaN(montoMax) && monto > montoMax) return;
                rows.push({ ...v, _tipo: "venta", _ts: v.fechaVenta });
            });
        }
        rows.sort((a, b) => new Date(b._ts) - new Date(a._ts));
        return rows;
    }

    function _q(id) {
        const scope = isWorkspaceHistorial ? "#tab-historial" : "#ovtab-historial";
        // En workspace los IDs llevan prefijo `inv-ws-` para evitar duplicados
        // con landing. Traducimos automáticamente.
        if (
            isWorkspaceHistorial &&
            id.startsWith("inv-") &&
            !id.startsWith("inv-ws-")
        ) {
            id = "inv-ws-" + id.slice(4);
        }
        return document.querySelector(`${scope} #${id}`);
    }

    // Selecciona todos los elementos con un id (soporta el par landing/workspace).
    //   _qsa("inv-hfiltro-aplicar")
    //     => [inv-hfiltro-aplicar (landing), inv-ws-hfiltro-aplicar (workspace)]
    function _qsa(id) {
        const selectors = [`[id="${id}"]`];
        if (id.startsWith("inv-") && !id.startsWith("inv-ws-")) {
            selectors.push(`[id="inv-ws-${id.slice(4)}"]`);
        }
        return document.querySelectorAll(selectors.join(", "));
    }

    function _wrapWithScope(handler) {
        return (e) => {
            isWorkspaceHistorial = !!e.currentTarget.closest("#tab-historial");
            handler();
        };
    }

    function _poblarCentrosAcopio() {
        const sel = _q("inv-hfiltro-centro");
        if (!sel) return;
        const nombres = new Set();
        ventasDB.forEach((v) => {
            if (v.nombreCentroAcopio) nombres.add(v.nombreCentroAcopio);
        });
        const ordenados = Array.from(nombres).sort((a, b) => a.localeCompare(b, "es"));
        const opts = ['<option value="">—</option>']
            .concat(ordenados.map((n) => `<option value="${escapeHtml(n)}">${escapeHtml(n)}</option>`));
        sel.innerHTML = opts.join("");

        // Re-init Select2 (idempotente): destroy antes, select2 después.
        // Solo aplica si Select2 está cargado y el <select> ya fue inicializado.
        if (typeof window.jQuery !== "undefined" && typeof window.jQuery.fn.select2 !== "undefined" && window.jQuery(sel).data("select2")) {
            window.jQuery(sel).select2("destroy");
            window.jQuery(sel).select2({ theme: "bootstrap-5", language: "es", width: "100%" });
        }

        // Re-aplicar estado disabled después de re-poblar (puede haber sido
        // alterado por _toggleCentroAcopioLock).
        _toggleCentroAcopioLock();
    }

    function _toggleCentroAcopioLock() {
        const tipo = _q("inv-hfiltro-tipo")?.value;
        const sel = _q("inv-hfiltro-centro");
        if (!sel) return;
        const enabled = tipo === "venta";
        sel.disabled = !enabled;
        if (!enabled) sel.value = "";
    }

    function renderPager(total, current) {
        const pager = _q("inv-hpager");
        if (!pager) return;
        if (total === 0) {
            pager.innerHTML = "";
            return;
        }
        const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
        current = Math.min(Math.max(1, current), pages);
        const parts = [];
        const mkBtn = (label, page, opts = {}) => {
            const disabled = opts.disabled ? " disabled" : "";
            const active = opts.active ? " active" : "";
            return `<li class="page-item${disabled}${active}"><a class="page-link" href="#" data-page="${page}">${label}</a></li>`;
        };
        parts.push(mkBtn("«", 1, { disabled: current === 1 }));
        parts.push(mkBtn("‹", current - 1, { disabled: current === 1 }));
        const max = pages;
        const window = 2;
        const start = Math.max(1, current - window);
        const end = Math.min(max, current + window);
        if (start > 1) {
            parts.push(mkBtn("1", 1));
            if (start > 2) parts.push('<li class="page-item disabled"><span class="page-link">…</span></li>');
        }
        for (let p = start; p <= end; p++) {
            parts.push(mkBtn(String(p), p, { active: p === current }));
        }
        if (end < max) {
            if (end < max - 1) parts.push('<li class="page-item disabled"><span class="page-link">…</span></li>');
            parts.push(mkBtn(String(max), max));
        }
        parts.push(mkBtn("›", current + 1, { disabled: current === pages }));
        parts.push(mkBtn("»", pages, { disabled: current === pages }));
        pager.innerHTML = parts.join("");
        pager.querySelectorAll("a.page-link").forEach((a) => {
            a.addEventListener("click", (ev) => {
                ev.preventDefault();
                const p = parseInt(a.dataset.page, 10);
                if (Number.isFinite(p) && p >= 1 && p <= pages) {
                    historialPage = p;
                    renderHistorialGeneralPaged();
                }
            });
        });
    }

    function renderHistorialGeneralPaged() {
        const tbody = _q("inv-tablasHistorialBody");
        const footer = _q("inv-hfooter-count");
        const badge = _q("inv-hbadge-count");
        if (!tbody) return;
        const rows = getCurrentHistorialRows();
        const total = rows.length;
        const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
        if (historialPage > pages) historialPage = pages;
        const start = (historialPage - 1) * PAGE_SIZE;
        const slice = rows.slice(start, start + PAGE_SIZE);
        const showMaterial = !isWorkspaceHistorial;
        const colspan = showMaterial ? 8 : 7;
        const filaOpts = { showMaterial };
        if (slice.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${colspan}" class="text-center text-muted py-3">Sin movimientos con los filtros aplicados</td></tr>`;
        } else {
            tbody.innerHTML = slice.map((r) => filaHistorial(r, r._tipo, filaOpts)).join("");
        }
        if (footer) {
            const from = total === 0 ? 0 : start + 1;
            const to = Math.min(start + PAGE_SIZE, total);
            footer.textContent = total === 0
                ? "Sin registros"
                : `Mostrando ${from}–${to} de ${total}`;
        }
        if (badge) {
            badge.textContent = `${total} registros`;
        }
        renderPager(total, historialPage);
    }

    function aplicarFiltrosHistorial() {
        historialPage = 1;
        renderHistorialGeneralPaged();
    }
    function limpiarFiltrosHistorial() {
        [
            "inv-hfiltro-material",
            "inv-hfiltro-categoria",
            "inv-hfiltro-tipo-material",
            "inv-hfiltro-tipo",
            "inv-hfiltro-desde",
            "inv-hfiltro-hasta",
            "inv-hfiltro-centro",
            "inv-hfiltro-cantidad-min",
            "inv-hfiltro-cantidad-max",
            "inv-hfiltro-monto-min",
            "inv-hfiltro-monto-max",
        ].forEach((id) => {
            const el = _q(id);
            if (el) el.value = "";
        });
        _toggleCentroAcopioLock();
        historialPage = 1;
        renderHistorialGeneralPaged();
    }

    // ============================================================
    // CHART CUSTOM CANVAS (sin Chart.js, decisión 17)
    // ============================================================
    const PALETA = ["#0d6efd", "#dc3545", "#198754", "#ffc107", "#6f42c1", "#fd7e14", "#20c997", "#d63384", "#0dcaf0", "#6c757d"];
    const MAX_PUNTOS = 60;
    const chartState = {
        ovtab: { data: [], labels: [], series: new Map(), capacidad: new Map() },
        ws: { data: [], labels: [], series: new Map(), capacidad: new Map() },
    };

    function toISODate(d) {
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
    }
    function inicioDeSemana(d) {
        const c = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        const dia = c.getDay();
        c.setDate(c.getDate() + (dia === 0 ? -6 : 1 - dia));
        return c;
    }
    function bucketDeFecha(fecha, gran) {
        if (gran === "dia") return new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());
        if (gran === "semana") return inicioDeSemana(fecha);
        return new Date(fecha.getFullYear(), fecha.getMonth(), 1);
    }
    function bucketKey(fecha, gran) {
        if (gran === "dia") return toISODate(fecha);
        if (gran === "semana") return `W${toISODate(inicioDeSemana(fecha))}`;
        return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, "0")}`;
    }
    function generarBuckets(desde, hasta, gran) {
        const inicio = bucketDeFecha(desde, gran);
        const fin = bucketDeFecha(hasta, gran);
        const buckets = [];
        const cursor = new Date(inicio);
        while (cursor <= fin) {
            buckets.push(new Date(cursor));
            if (gran === "dia") cursor.setDate(cursor.getDate() + 1);
            else if (gran === "semana") cursor.setDate(cursor.getDate() + 7);
            else cursor.setMonth(cursor.getMonth() + 1);
            if (buckets.length > MAX_PUNTOS) break;
        }
        return buckets;
    }
    function formatearLabelBucket(fecha, gran) {
        if (gran === "dia") return fecha.toLocaleDateString("es-CO", { day: "2-digit", month: "short" });
        if (gran === "semana") return `Sem ${toISODate(fecha).slice(5)}`;
        return fecha.toLocaleDateString("es-CO", { month: "short", year: "numeric" });
    }

    /**
     * Construye la serie histórica para un material anclando en stockActual
     * y restando las operaciones FUTURAS al rango (delta inverso).
     */
    function construirSerieMaterial(material, compras, ventas, desde, hasta, gran) {
        const ops = [];
        compras.filter((c) => String(c.inventarioId) === String(material.inventarioId)).forEach((c) => {
            const f = c.fechaCompra ? new Date(c.fechaCompra) : null;
            if (f) ops.push({ fecha: f, delta: Number(c.cantidad) || 0 });
        });
        ventas.filter((v) => String(v.inventarioId) === String(material.inventarioId)).forEach((v) => {
            const f = v.fechaVenta ? new Date(v.fechaVenta) : null;
            if (f) ops.push({ fecha: f, delta: -(Number(v.cantidad) || 0) });
        });
        const buckets = generarBuckets(desde, hasta, gran);
        const serie = [];
        let stock = Number(material.stockActual) || 0;
        // Restar ops futuras al bucket más reciente
        const lastBucket = buckets[buckets.length - 1];
        if (lastBucket) {
            const futuroMax = new Date(lastBucket);
            if (gran === "dia") futuroMax.setDate(futuroMax.getDate() + 1);
            else if (gran === "semana") futuroMax.setDate(futuroMax.getDate() + 7);
            else futuroMax.setMonth(futuroMax.getMonth() + 1);
            ops.filter((o) => o.fecha >= lastBucket && o.fecha < futuroMax).forEach((o) => { stock -= o.delta; });
        }
        // Walk backwards, acumulando deltas negativos
        const opsIdx = [...ops].sort((a, b) => b.fecha - a.fecha);
        for (let i = buckets.length - 1; i >= 0; i--) {
            const b = buckets[i];
            const bKey = bucketKey(b, gran);
            const next = i + 1 < buckets.length ? buckets[i + 1] : (() => {
                const x = new Date(b);
                if (gran === "dia") x.setDate(x.getDate() + 1);
                else if (gran === "semana") x.setDate(x.getDate() + 7);
                else x.setMonth(x.getMonth() + 1);
                return x;
            })();
            while (opsIdx.length && opsIdx[0].fecha >= b && opsIdx[0].fecha < next) {
                stock -= opsIdx.shift().delta;
            }
            serie[i] = Math.max(0, stock);
        }
        return serie;
    }

    function construirSerieGanancias(materiales, compras, ventas, desde, hasta, gran) {
        // Retorna { ingresos: number[], costos: number[], profit: number[] }
        // Un valor por bucket, acumulado en el tiempo. La primera fila
        // contiene los ops del bucket 0; cada fila siguiente acumula el
        // bucket anterior + el actual.
        const buckets = generarBuckets(desde, hasta, gran);
        const invIds = new Set(materiales.map((m) => String(m.inventarioId)));
        const cs = compras.filter((c) => invIds.has(String(c.inventarioId)));
        const vs = ventas.filter((v) => invIds.has(String(v.inventarioId)));
        const ingresos = buckets.map(() => 0);
        const costos = buckets.map(() => 0);
        for (const c of cs) {
            if (!c.fechaCompra) continue;
            const idx = bucketIndexFor(new Date(c.fechaCompra), buckets, gran);
            if (idx < 0) continue;
            costos[idx] += Number(c.cantidad || 0) * Number(c.precioCompra || 0);
        }
        for (const v of vs) {
            if (!v.fechaVenta) continue;
            const idx = bucketIndexFor(new Date(v.fechaVenta), buckets, gran);
            if (idx < 0) continue;
            ingresos[idx] += Number(v.cantidad || 0) * Number(v.precioVenta || 0);
        }
        for (let i = 1; i < buckets.length; i++) {
            ingresos[i] += ingresos[i - 1];
            costos[i] += costos[i - 1];
        }
        const profit = buckets.map((_, i) => ingresos[i] - costos[i]);
        return { ingresos, costos, profit, buckets };
    }

    function bucketIndexFor(fecha, buckets, gran) {
        for (let i = 0; i < buckets.length; i++) {
            const b = buckets[i];
            const next = i + 1 < buckets.length ? buckets[i + 1] : (() => {
                const x = new Date(b);
                if (gran === "dia") x.setDate(x.getDate() + 1);
                else if (gran === "semana") x.setDate(x.getDate() + 7);
                else x.setMonth(x.getMonth() + 1);
                return x;
            })();
            if (fecha >= b && fecha < next) return i;
        }
        return -1;
    }

    function renderChart(canvasId, opts) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const W = canvas.clientWidth || 900;
        const H = canvas.clientHeight || 450;
        const dpr = window.devicePixelRatio || 1;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, W, H);
        const modo = opts.modo || "stock";
        if (modo === "stock" && !opts.materiales.length) {
            ctx.fillStyle = "#6c757d";
            ctx.font = "14px system-ui, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("Selecciona al menos un material.", W / 2, H / 2);
            return;
        }
        if (modo === "ganancia" && !opts.materiales.length) {
            ctx.fillStyle = "#6c757d";
            ctx.font = "14px system-ui, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("Selecciona al menos un material para ver ganancias.", W / 2, H / 2);
            return;
        }
        const buckets = opts.buckets;
        const labels = buckets.map((b) => formatearLabelBucket(b, opts.gran));
        // Construir series según modo
        let series = [];
        if (modo === "stock") {
            series = opts.materiales.map((m, idx) => ({
                nombre: m.nombre,
                color: PALETA[idx % PALETA.length],
                valores: construirSerieMaterial(m, comprasDB, ventasDB, opts.desde, opts.hasta, opts.gran),
                capacidad: Number(m.capacidadMaxima) || 0,
            }));
        } else {
            // modo === "ganancia"
            const gan = construirSerieGanancias(opts.materiales, comprasDB, ventasDB, opts.desde, opts.hasta, opts.gran);
            series = [
                { nombre: "Ingresos", color: "#0d6efd", valores: gan.ingresos, capacidad: 0 },
                { nombre: "Costos",   color: "#fd7e14", valores: gan.costos,   capacidad: 0 },
                { nombre: "Profit",   color: "#198754", valores: gan.profit,   capacidad: 0, esProfit: true },
            ];
        }
        // Calcular rango Y
        let maxY = 0;
        let minY = 0;
        series.forEach((s) => s.valores.forEach((v) => {
            if (v > maxY) maxY = v;
            if (v < minY) minY = v;
        }));
        if (opts.mostrarCap && modo === "stock") {
            series.forEach((s) => { if (s.capacidad > maxY) maxY = s.capacidad; });
        }
        if (maxY === minY) maxY = minY + 1;
        const padL = 70, padR = 20, padT = 10, padB = 30;
        const innerW = W - padL - padR;
        const innerH = H - padT - padB;
        // Grid
        ctx.strokeStyle = "#e9ecef";
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const t = i / 4;
            const y = padT + (innerH * i) / 4;
            ctx.beginPath();
            ctx.moveTo(padL, y);
            ctx.lineTo(W - padR, y);
            ctx.stroke();
            ctx.fillStyle = "#6c757d";
            ctx.font = "10px system-ui, sans-serif";
            ctx.textAlign = "right";
            const val = maxY - (maxY - minY) * t;
            // Eje Y: para ganancias usamos formato compacto (K/M/B) para no
            // saturar el chart con cifras largas. Los KPIs (que sí pueden
            // mostrar la cifra completa) usan formatearCOP() en su lugar.
            const labelTxt = modo === "ganancia" ? formatearCOPCorto(val) : val.toFixed(0);
            ctx.fillText(labelTxt, padL - 6, y + 3);
        }
        // Línea de y=0 (referencia para profit)
        if (modo === "ganancia" && minY < 0) {
            const y0 = padT + innerH - (innerH * (0 - minY)) / (maxY - minY);
            ctx.strokeStyle = "#dc3545";
            ctx.setLineDash([3, 3]);
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(padL, y0);
            ctx.lineTo(W - padR, y0);
            ctx.stroke();
            ctx.setLineDash([]);
        }
        // Eje X labels
        const stepX = Math.max(1, Math.floor(labels.length / 8));
        ctx.fillStyle = "#6c757d";
        ctx.textAlign = "center";
        labels.forEach((lbl, i) => {
            if (i % stepX === 0 || i === labels.length - 1) {
                const x = padL + (innerW * i) / Math.max(1, buckets.length - 1);
                ctx.fillText(lbl, x, H - 10);
            }
        });
        // Líneas
        const xAt = (i) => padL + (innerW * i) / Math.max(1, buckets.length - 1);
        const yAt = (v) => padT + innerH - (innerH * (v - minY)) / (maxY - minY);
        series.forEach((s) => {
            // Capacidad (línea punteada, solo modo stock)
            if (opts.mostrarCap && modo === "stock" && s.capacidad > 0) {
                ctx.strokeStyle = s.color + "55";
                ctx.setLineDash([4, 4]);
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padL, yAt(s.capacidad));
                ctx.lineTo(W - padR, yAt(s.capacidad));
                ctx.stroke();
                ctx.setLineDash([]);
            }
            // Serie
            ctx.strokeStyle = s.color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            s.valores.forEach((v, i) => {
                const x = xAt(i), y = yAt(v);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
            // Puntos
            ctx.fillStyle = s.color;
            s.valores.forEach((v, i) => {
                if (i % stepX !== 0 && i !== s.valores.length - 1) return;
                ctx.beginPath();
                ctx.arc(xAt(i), yAt(v), 3, 0, Math.PI * 2);
                ctx.fill();
            });
        });
        // Leyenda
        ctx.font = "11px system-ui, sans-serif";
        ctx.textAlign = "left";
        let lx = padL;
        const ly = padT + 14;
        series.forEach((s) => {
            const txt = s.nombre;
            const tw = ctx.measureText(txt).width + 18;
            ctx.fillStyle = s.color;
            ctx.fillRect(lx, ly - 9, 11, 11);
            ctx.fillStyle = "#212529";
            ctx.fillText(txt, lx + 16, ly);
            lx += tw;
            if (lx > W - 60) return;
        });
    }

    function renderOvtabChart() {
        const checks = document.querySelectorAll('#inv-flujo-materiales-list input[type="checkbox"]:checked');
        const ids = Array.from(checks).map((c) => c.value);
        const mats = materialesDB.filter((m) => ids.includes(String(m.inventarioId)));
        const gran = document.getElementById("inv-flujo-stock-granularidad")?.value || "dia";
        const cap = document.getElementById("inv-flujo-stock-cap")?.checked;
        const desde = _parseFecha("inv-flujo-stock-desde") || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
        const hasta = _parseFecha("inv-flujo-stock-hasta") || new Date();
        const buckets = generarBuckets(desde, hasta, gran);
        renderChart("inv-stock-time-chart", {
            modo: "stock", materiales: mats, gran, mostrarCap: cap,
            desde, hasta, buckets,
        });
        const badge = document.getElementById("inv-flujo-badge");
        if (badge) badge.textContent = `${mats.length} material${mats.length === 1 ? "" : "es"}`;
        const setKpi = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        setKpi("inv-flujo-kpi-materiales", mats.length);
        setKpi("inv-flujo-kpi-compras", comprasDB.length);
        setKpi("inv-flujo-kpi-ventas", ventasDB.length);
        const ocupacionPromedio = mats.length
            ? Math.round(mats.reduce((s, m) => s + Number(m.ocupacion || 0), 0) / mats.length)
            : 0;
        setKpi("inv-flujo-kpi-ocupacion", `${ocupacionPromedio}%`);
    }

    function renderOvGananciasChart() {
        const checks = document.querySelectorAll('#inv-flujo-gan-materiales-list input[type="checkbox"]:checked');
        const ids = Array.from(checks).map((c) => c.value);
        const mats = materialesDB.filter((m) => ids.includes(String(m.inventarioId)));
        const gran = document.getElementById("inv-flujo-gan-granularidad")?.value || "dia";
        const desde = _parseFecha("inv-flujo-gan-desde") || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
        const hasta = _parseFecha("inv-flujo-gan-hasta") || new Date();
        const buckets = generarBuckets(desde, hasta, gran);
        const setKpi = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        const setKpiClass = (id, cls) => { const el = document.getElementById(id); if (el) el.className = `fw-bold mb-0 ${cls || ""}`.trim(); };
        if (!mats.length) {
            setKpi("inv-flujo-gan-kpi-ingresos", "—");
            setKpi("inv-flujo-gan-kpi-costos", "—");
            setKpi("inv-flujo-gan-kpi-profit", "—");
            setKpi("inv-flujo-gan-kpi-margen", "—");
            setKpi("inv-flujo-gan-kpi-top", "—");
            setKpi("inv-flujo-gan-kpi-top-val", "—");
            setKpi("inv-flujo-gan-kpi-perdida", "—");
            const badge = document.getElementById("inv-flujo-gan-badge");
            if (badge) badge.textContent = "0 materiales";
            renderChart("inv-ganancias-chart", { modo: "ganancia", materiales: [], gran, desde, hasta, buckets });
            return;
        }
        // Calcular stats por material
        const invIds = new Set(mats.map((m) => String(m.inventarioId)));
        const cs = comprasDB.filter((c) => invIds.has(String(c.inventarioId)));
        const vs = ventasDB.filter((v) => invIds.has(String(v.inventarioId)));
        const ingresosTotal = vs.reduce((s, v) => s + Number(v.cantidad || 0) * Number(v.precioVenta || 0), 0);
        const costosTotal = cs.reduce((s, c) => s + Number(c.cantidad || 0) * Number(c.precioCompra || 0), 0);
        const profitTotal = ingresosTotal - costosTotal;
        const margen = ingresosTotal > 0 ? (profitTotal / ingresosTotal) * 100 : 0;
        // Top material por profit
        const profitPorMaterial = mats.map((m) => {
            const cm = cs.filter((c) => String(c.inventarioId) === String(m.inventarioId));
            const vm = vs.filter((v) => String(v.inventarioId) === String(m.inventarioId));
            const ing = vm.reduce((s, v) => s + Number(v.cantidad || 0) * Number(v.precioVenta || 0), 0);
            const cost = cm.reduce((s, c) => s + Number(c.cantidad || 0) * Number(c.precioCompra || 0), 0);
            return { nombre: m.nombre, profit: ing - cost };
        }).sort((a, b) => b.profit - a.profit);
        const top = profitPorMaterial[0];
        // Movs con pérdida: ventas donde precioVenta < precioCompra del material
        const movsPerdida = vs.filter((v) => {
            const compra = cs.find((c) => String(c.inventarioId) === String(v.inventarioId));
            if (!compra) return false;
            return Number(v.precioVenta || 0) < Number(compra.precioCompra || 0);
        }).length;
        setKpi("inv-flujo-gan-kpi-ingresos", formatearCOP(ingresosTotal));
        setKpi("inv-flujo-gan-kpi-costos", formatearCOP(costosTotal));
        setKpi("inv-flujo-gan-kpi-profit", formatearCOP(profitTotal));
        setKpiClass("inv-flujo-gan-kpi-profit", profitTotal >= 0 ? "text-success" : "text-danger");
        setKpi("inv-flujo-gan-kpi-margen", `${margen.toFixed(1)}%`);
        setKpiClass("inv-flujo-gan-kpi-margen", margen >= 20 ? "text-success" : margen >= 10 ? "text-warning" : "text-danger");
        setKpi("inv-flujo-gan-kpi-top", top ? top.nombre : "—");
        setKpi("inv-flujo-gan-kpi-top-val", top ? formatearCOP(top.profit) : "—");
        setKpi("inv-flujo-gan-kpi-perdida", movsPerdida);
        const badge = document.getElementById("inv-flujo-gan-badge");
        if (badge) badge.textContent = `${mats.length} material${mats.length === 1 ? "" : "es"}`;
        renderChart("inv-ganancias-chart", { modo: "ganancia", materiales: mats, gran, desde, hasta, buckets });
    }

    function renderWsChart() {
        if (!currentMaterial) return;
        const gran = "dia";
        const desde = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
        const hasta = new Date();
        const buckets = generarBuckets(desde, hasta, gran);
        renderChart("stockTimeChart", {
            modo: "stock", materiales: [currentMaterial], gran, mostrarCap: true,
            desde, hasta, buckets,
        });
        const invId = currentMaterial.inventarioId;
        const cm = comprasDB.filter((c) => String(c.inventarioId) === String(invId));
        const vm = ventasDB.filter((v) => String(v.inventarioId) === String(invId));
        const setKpi = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        setKpi("inv-ws-flujo-stock", `${Number(currentMaterial.stockActual).toLocaleString("es-CO")} ${currentMaterial.unidad}`);
        setKpi("inv-ws-flujo-movs", cm.length + vm.length);
        setKpi("inv-ws-flujo-compras", cm.length);
        setKpi("inv-ws-flujo-ventas", vm.length);
    }

    function renderWsGananciasChart() {
        if (!currentMaterial) return;
        const gran = "dia";
        const desde = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
        const hasta = new Date();
        const buckets = generarBuckets(desde, hasta, gran);
        const invId = currentMaterial.inventarioId;
        const cm = comprasDB.filter((c) => String(c.inventarioId) === String(invId));
        const vm = ventasDB.filter((v) => String(v.inventarioId) === String(invId));
        const ingresosTotal = vm.reduce((s, v) => s + Number(v.cantidad || 0) * Number(v.precioVenta || 0), 0);
        const costosTotal = cm.reduce((s, c) => s + Number(c.cantidad || 0) * Number(c.precioCompra || 0), 0);
        const profitTotal = ingresosTotal - costosTotal;
        const margen = ingresosTotal > 0 ? (profitTotal / ingresosTotal) * 100 : 0;
        const movsPerdida = vm.filter((v) => {
            const compra = cm.find((c) => String(c.inventarioId) === String(v.inventarioId));
            if (!compra) return false;
            return Number(v.precioVenta || 0) < Number(compra.precioCompra || 0);
        }).length;
        const ultimaVenta = vm.length ? vm.slice().sort((a, b) => new Date(b.fechaVenta) - new Date(a.fechaVenta))[0] : null;
        const setKpi = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        const setKpiClass = (id, cls) => { const el = document.getElementById(id); if (el) el.className = `fw-bold mb-0 ${cls || ""}`.trim(); };
        setKpi("inv-ws-flujo-gan-ingresos", formatearCOP(ingresosTotal));
        setKpi("inv-ws-flujo-gan-costos", formatearCOP(costosTotal));
        setKpi("inv-ws-flujo-gan-profit", formatearCOP(profitTotal));
        setKpiClass("inv-ws-flujo-gan-profit", profitTotal >= 0 ? "text-success" : "text-danger");
        setKpi("inv-ws-flujo-gan-margen", `${margen.toFixed(1)}%`);
        setKpiClass("inv-ws-flujo-gan-margen", margen >= 20 ? "text-success" : margen >= 10 ? "text-warning" : "text-danger");
        setKpi("inv-ws-flujo-gan-perdida", movsPerdida);
        if (ultimaVenta) {
            setKpi("inv-ws-flujo-gan-ultima", formatDateCO(ultimaVenta.fechaVenta));
            setKpi("inv-ws-flujo-gan-ultima-val", formatearCOP(Number(ultimaVenta.cantidad || 0) * Number(ultimaVenta.precioVenta || 0)));
        } else {
            setKpi("inv-ws-flujo-gan-ultima", "—");
            setKpi("inv-ws-flujo-gan-ultima-val", "—");
        }
        renderChart("inv-ws-ganancias-chart", {
            modo: "ganancia", materiales: [currentMaterial], gran,
            desde, hasta, buckets,
        });
    }

    function _parseFecha(id) {
        const v = document.getElementById(id)?.value;
        if (!v) return null;
        return new Date(v + "T00:00:00");
    }

    function renderFlujoMaterialesList() {
        const cont = document.getElementById("inv-flujo-materiales-list");
        const contGan = document.getElementById("inv-flujo-gan-materiales-list");
        const html = materialesDB.map((m, i) => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${escapeHtml(m.inventarioId)}" id="inv-flujo-mat-${i}" checked>
                <label class="form-check-label small" for="inv-flujo-mat-${i}">
                    <span style="display:inline-block;width:10px;height:10px;background:${PALETA[i % PALETA.length]};border-radius:2px;margin-right:4px"></span>
                    ${escapeHtml(m.nombre)}
                </label>
            </div>
        `).join("") || '<small class="text-muted">No hay materiales en el inventario.</small>';
        if (cont) {
            cont.innerHTML = html;
            cont.querySelectorAll('input[type="checkbox"]').forEach((cb) => cb.addEventListener("change", renderOvtabChart));
        }
        if (contGan) {
            contGan.innerHTML = html;
            contGan.querySelectorAll('input[type="checkbox"]').forEach((cb) => cb.addEventListener("change", renderOvGananciasChart));
        }
    }

    // ============================================================
    // BIND EXTRA
    // ============================================================
    function bindExtras() {
        // Submit forms workspace
        document.getElementById("formEntrada")?.addEventListener("submit", submitEntrada);
        document.getElementById("formSalida")?.addEventListener("submit", submitSalida);
        document.getElementById("inv-btn-guardar-entrada")?.addEventListener("click", (e) => { e.preventDefault(); submitEntrada(e); });
        document.getElementById("inv-btn-guardar-salida")?.addEventListener("click", (e) => { e.preventDefault(); submitSalida(e); });

        // Submit editar modales
        document.getElementById("inv-btn-guardar-editar-compra")?.addEventListener("click", submitEditarCompra);
        document.getElementById("inv-btn-guardar-editar-venta")?.addEventListener("click", submitEditarVenta);

        // Eliminar desde modales de edición (botón extra en footer)
        const editCompraFooter = document.querySelector("#inv-modal-editar-compra .modal-footer");
        if (editCompraFooter && !document.getElementById("inv-btn-eliminar-editar-compra")) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.id = "inv-btn-eliminar-editar-compra";
            btn.className = "btn btn-outline-danger me-auto";
            btn.innerHTML = '<i class="bi bi-trash me-1"></i>Eliminar';
            btn.addEventListener("click", eliminarCompraActual);
            editCompraFooter.prepend(btn);
        }
        const editVentaFooter = document.querySelector("#inv-modal-editar-venta .modal-footer");
        if (editVentaFooter && !document.getElementById("inv-btn-eliminar-editar-venta")) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.id = "inv-btn-eliminar-editar-venta";
            btn.className = "btn btn-outline-danger me-auto";
            btn.innerHTML = '<i class="bi bi-trash me-1"></i>Eliminar';
            btn.addEventListener("click", eliminarVentaActual);
            editVentaFooter.prepend(btn);
        }
        // Eliminar desde modales de detalle
        const detCompraFooter = document.querySelector("#inv-modal-detalle-compra .modal-footer");
        if (detCompraFooter && !document.getElementById("inv-btn-eliminar-detalle-compra")) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.id = "inv-btn-eliminar-detalle-compra";
            btn.className = "btn btn-outline-danger me-auto";
            btn.innerHTML = '<i class="bi bi-trash me-1"></i>Eliminar';
            btn.addEventListener("click", eliminarDetalleCompra);
            detCompraFooter.prepend(btn);
        }
        const detVentaFooter = document.querySelector("#inv-modal-detalle-venta .modal-footer");
        if (detVentaFooter && !document.getElementById("inv-btn-eliminar-detalle-venta")) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.id = "inv-btn-eliminar-detalle-venta";
            btn.className = "btn btn-outline-danger me-auto";
            btn.innerHTML = '<i class="bi bi-trash me-1"></i>Eliminar';
            btn.addEventListener("click", eliminarDetalleVenta);
            detVentaFooter.prepend(btn);
        }

        // Exportar historial (landing y workspace con prefijo inv-ws-).
        // _qsa() selecciona ambos.
        _qsa("inv-btn-export-historial-excel").forEach((el) => {
            el.addEventListener("click", _wrapWithScope(exportarHistorialExcel));
        });
        _qsa("inv-btn-export-historial-pdf").forEach((el) => {
            el.addEventListener("click", _wrapWithScope(exportarHistorialPdf));
        });

        // Filtros historial
        _qsa("inv-hfiltro-aplicar").forEach((el) => {
            el.addEventListener("click", _wrapWithScope(aplicarFiltrosHistorial));
        });
        _qsa("inv-hfiltro-limpiar").forEach((el) => {
            el.addEventListener("click", _wrapWithScope(limpiarFiltrosHistorial));
        });
        // Centro de acopio se habilita sólo si tipo=venta
        _qsa("inv-hfiltro-tipo").forEach((el) => {
            el.addEventListener("change", _wrapWithScope(_toggleCentroAcopioLock));
        });

        // Chart ovtab — Stock
        document.getElementById("inv-flujo-stock-aplicar")?.addEventListener("click", renderOvtabChart);
        document.getElementById("inv-flujo-stock-granularidad")?.addEventListener("change", renderOvtabChart);
        document.getElementById("inv-flujo-stock-cap")?.addEventListener("change", renderOvtabChart);
        document.getElementById("inv-flujo-stock-desde")?.addEventListener("change", renderOvtabChart);
        document.getElementById("inv-flujo-stock-hasta")?.addEventListener("change", renderOvtabChart);
        document.getElementById("inv-flujo-todos")?.addEventListener("click", () => {
            document.querySelectorAll('#inv-flujo-materiales-list input[type="checkbox"]').forEach((c) => { c.checked = true; });
            renderOvtabChart();
        });
        document.getElementById("inv-flujo-ninguno")?.addEventListener("click", () => {
            document.querySelectorAll('#inv-flujo-materiales-list input[type="checkbox"]').forEach((c) => { c.checked = false; });
            renderOvtabChart();
        });

        // Chart ovtab — Ganancias
        document.getElementById("inv-flujo-gan-aplicar")?.addEventListener("click", renderOvGananciasChart);
        document.getElementById("inv-flujo-gan-granularidad")?.addEventListener("change", renderOvGananciasChart);
        document.getElementById("inv-flujo-gan-desde")?.addEventListener("change", renderOvGananciasChart);
        document.getElementById("inv-flujo-gan-hasta")?.addEventListener("change", renderOvGananciasChart);

        // Sub-tabs internas del flujo (Stock / Ganancias)
        document.querySelectorAll('#ovFlujoSubtabs [data-ovsub]').forEach((btn) => {
            btn.addEventListener("click", () => {
                const sub = btn.dataset.ovsub;
                document.querySelectorAll('#ovFlujoSubtabs .nav-link').forEach((b) => b.classList.remove("active"));
                document.querySelectorAll(".ovsub-pane").forEach((p) => p.classList.remove("active"));
                btn.classList.add("active");
                const pane = document.getElementById(sub);
                if (pane) {
                    pane.classList.add("active");
                    // Re-init Select2 y re-render del chart con clientWidth correcto
                    _reinitSelect2InPane(pane);
                    setTimeout(() => {
                        if (sub === "ovstock") renderOvtabChart();
                        else if (sub === "ovgan") renderOvGananciasChart();
                    }, 50);
                }
            });
        });
        document.querySelectorAll('#wsFlujoSubtabs [data-wssub]').forEach((btn) => {
            btn.addEventListener("click", () => {
                const sub = btn.dataset.wssub;
                document.querySelectorAll('#wsFlujoSubtabs .nav-link').forEach((b) => b.classList.remove("active"));
                document.querySelectorAll(".wssub-pane").forEach((p) => p.classList.remove("active"));
                btn.classList.add("active");
                const pane = document.getElementById(sub);
                if (pane) {
                    pane.classList.add("active");
                    _reinitSelect2InPane(pane);
                    setTimeout(() => {
                        if (sub === "wsstock") renderWsChart();
                        else if (sub === "wsgan") renderWsGananciasChart();
                    }, 50);
                }
            });
        });

        // Render ovtab chart cuando se abre
        document.querySelector('#otrasVistasTabs [data-ovtab="ovtab-flujo"]')?.addEventListener("click", () => {
            setTimeout(renderOvtabChart, 50);
        });
        // Render ws chart cuando se abre su tab
        document.querySelector('#workspaceTabs [data-tab="tab-flujo"]')?.addEventListener("click", () => {
            setTimeout(renderWsChart, 50);
        });
    }

    // ============================================================
    // LOADING STATE en botones de submit
    // ============================================================
    // Reemplaza el contenido del botón con un spinner mientras la
    // operación está en curso. Restaura el contenido original al
    // terminar (éxito o error). Previene dobles clicks y da feedback
    // visual al usuario.
    function withLoading(btn, fn) {
        if (!btn) return fn();
        if (btn.disabled) return; // ya está procesando, ignorar
        const original = btn.innerHTML;
        const spinnerClass = btn.classList.contains("btn-sm") ? "spinner-border-sm" : "";
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border ${spinnerClass} me-2" role="status" aria-hidden="true"></span>Procesando...`;
        const restore = () => {
            btn.disabled = false;
            btn.innerHTML = original;
        };
        try {
            const result = fn();
            // Si devuelve una Promise, esperamos a que termine
            if (result && typeof result.then === "function") {
                return result.then((v) => { restore(); return v; },
                                   (e) => { restore(); throw e; });
            }
            restore();
            return result;
        } catch (e) {
            restore();
            throw e;
        }
    }

    // --- Init ---
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bind);
    } else {
        bind();
    }
})();
