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
    // --- Helpers de fetch (centralizan CSRF + parseo + manejo de errores) ---
    const _jsonHeaders = () => ({ "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() });
    const _parseJsonResponse = (r) => r.json().then((d) => ({ ok: r.ok, d }));
    const _showFetchError = (err) => Swal.fire({ icon: "error", title: "Error", text: err.message });
    const _readFormAsObject = (formEl) => Object.fromEntries(new FormData(formEl).entries());
    const _showSuccessSwal = (title, html, timerMs = 1200) => Swal.fire({
        icon: "success",
        title,
        html,
        timer: timerMs,
        showConfirmButton: false,
    });
    // Helper de stringificación segura: solo convierte a String si el valor
    // es un primitivo (string, number, boolean). Para objetos/arrays retorna
    // "" para evitar el "[object Object]" de String() sobre no-primitivos.
    const _safeStr = (v) => {
        if (v == null) return "";
        const t = typeof v;
        if (t === "string" || t === "number" || t === "boolean") return String(v);
        return "";
    };
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
        if (Number.isNaN(d.getTime())) return iso;
        const pad = (x) => String(x).padStart(2, "0");
        return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    };
    const escapeHtml = (s) => {
        if (s == null) return "";
        return String(s)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll("\"", "&quot;")
            .replaceAll("'", "&#039;");
    };
    const _estadoLabel = (e) => {
        if (e === "critico") return "Crítico";
        if (e === "alerta") return "Alerta";
        return "OK";
    };
    const _estadoClass = (e) => {
        if (e === "critico") return "bg-danger";
        if (e === "alerta") return "bg-warning text-dark";
        return "bg-success";
    };
    const _estadoClassShort = (e) => {
        if (e === "critico") return "bg-danger";
        if (e === "alerta") return "bg-warning";
        return "bg-success";
    };
    const _margenClass = (margen) => {
        if (margen >= 20) return "text-success";
        if (margen >= 10) return "text-warning";
        return "text-danger";
    };

    // ============================================================
    // NAVEGACIÓN ENTRE ESTADOS (landing ↔ workspace)
    // ============================================================
    function irLanding() {
        // Full page reload a la URL base de la sección, sin query params.
        // El reload garantiza datos frescos desde el backend (listas de
        // materiales, KPIs, ocupaciones) — no nos quedamos con el snapshot
        // cacheado en memoria del workspace. Es el equivalente a un "back
        // físico" al inventario general, no un toggle de visibilidad.
        //
        // Antes de la navegación recargamos la ovtab a "ovtab-inventario"
        // para que al recargar la URL limpia el server no devuelva otra
        // sub-pane activa por defecto.
        activarOvTab("ovtab-inventario");
        globalThis.location.href = globalThis.location.pathname;
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
        globalThis.scrollTo({ top: 0, behavior: "smooth" });
    }

    function poblarWorkspace(inv) {
        const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v ?? "—"; };
        const nombre = inv.nombre;
        const estadoLower = inv.estado;
        const estadoLabel = _estadoLabel(estadoLower);
        const estadoClass = _estadoClass(estadoLower);
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
            wsProgress.className = "progress-bar " + _estadoClassShort(estadoLower);
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
        // Reset de URL: si el usuario llegó aquí via deep-link
        // (?inv=&tab=) tras una compra/venta y ahora cambia de tab,
        // la URL ya no debe mantener el snapshot de la tab anterior.
        // replaceState limpia los query params sin recargar la página.
        // El workspace sigue abierto via state JS, pero la URL queda
        // en el "punto de entrada" — un reload posterior lleva al
        // landing, no a la tab vieja.
        if (globalThis.location.search) {
            globalThis.history.replaceState(null, "", globalThis.location.pathname);
        }
    }

    function _reinitSelect2InPane(pane) {
        if (globalThis.jQuery === undefined || globalThis.jQuery.fn.select2 === undefined) return;
        const $ = globalThis.jQuery;
        const base = { theme: "bootstrap-5", language: "es", width: "100%" };
        const $selects = $(pane).find("select").not("#inv-hfiltro-tipo").not("#inv-ws-hfiltro-tipo");
        $selects.each(function () {
            const $el = $(this);
            if ($el.data("select2")) $el.select2("destroy");
            $el.select2({...base});
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
        const showMaterial = opts?.showMaterial !== false;
        const fecha = formatDateCO(mov.fechaCompra || mov.fechaVenta);
        const cantidad = mov.cantidad;
        const precio = tipo === "compra" ? mov.precioCompra : mov.precioVenta;
        const total = Number(cantidad || 0) * Number(precio || 0);
        const material = mov.nombreMaterial || "—";
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
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
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
        const cats = Array.from(new Set(pickerCatalogo.map((m) => m.nmbCategoria).filter(Boolean))).sort((a, b) => a.localeCompare(b, "es"));
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
        const payload = _readFormAsObject(form);
        payload.stockActual = Number(payload.stockInicial);
        payload.capacidadMaxima = Number(payload.capacidadMaxima);
        payload.precioCompra = Number(payload.precioCompra);
        payload.precioVenta = Number(payload.precioVenta);
        payload.umbralAlerta = Number(payload.umbralAlerta);
        payload.umbralCritico = Number(payload.umbralCritico);
        payload.puntoEcaId = _safeStr(payload.puntoId);
        payload.materialId = _safeStr(payload.materialId);
        delete payload.puntoId;
        delete payload.stockInicial;

        fetch("/punto-eca/inventario/agregar/", {
            method: "POST",
            headers: _jsonHeaders(),
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) throw new Error(data?.mensaje || data?.message || "Error al guardar");
                Swal.fire({ icon: "success", title: "¡Material agregado!", text: data.mensaje || "Operación exitosa", confirmButtonColor: "#198754" });
                setTimeout(() => globalThis.location.reload(), 1500);
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
        if (globalThis.jQuery === undefined || globalThis.jQuery.fn.select2 === undefined) {
            console.warn("[inventario] Select2 no está cargado; los filtros quedan como <select> nativos.");
            return;
        }
        const $ = globalThis.jQuery;
        const base = { theme: "bootstrap-5", language: "es", width: "100%" };

        const apply = (selector, extra) => {
            const $els = $(selector);
            if (!$els.length) return;
            $els.each(function () {
                const $el = $(this);
                if ($el.data("select2")) $el.select2("destroy");
                $el.select2({...base, ...extra});
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

    // Helper: bind de eventos compatible con Select2.
    // Los <select> de filtros están envueltos con Select2. Cuando el usuario
    // escoge una opción, Select2 dispara 'input'/'change' con jQuery.trigger(),
    // que SOLO invoca handlers registrados vía jQuery.on() o el handler inline
    // element.oninput — NO los listeners nativos de addEventListener. Por eso
    // un addEventListener('change', …) sobre un <select> Select2 nunca
    // dispara cuando el usuario cambia el valor vía la UI de Select2.
    // Esta función usa jQuery.on() (si está disponible) y cae a
    // addEventListener como fallback si jQuery no está cargado (modo
    // degradado sin Select2, donde el evento nativo sí funciona).
    function _bindChange(selector, handler) {
        if (globalThis.jQuery) {
            const $els = globalThis.jQuery(selector);
            $els.on("change input", handler);
        } else {
            document.querySelectorAll(selector).forEach((el) => {
                el.addEventListener("change", handler);
            });
        }
    }

    function bind() {
        _initSelect2InSection();
        // Listeners de cálculo de total (cantidad × precio) en forms crear
        _bindFormTotalListeners();
        // Validación estandarizada para los 4 formularios de Compra/Venta
        // (crear y editar). Suprime globos nativos del navegador y
        // activa el patrón Bootstrap 5 'was-validated' + .invalid-feedback
        // + Swal de notificación global con color verde institucional.
        _installFormValidation("formEntrada");
        _installFormValidation("formSalida");
        _installFormValidation("inv-form-editar-compra");
        _installFormValidation("inv-form-editar-venta");
        // Tabs
        document.querySelectorAll("#otrasVistasTabs [data-ovtab]").forEach((btn) => {
            btn.addEventListener("click", () => activarOvTab(btn.dataset.ovtab));
        });
        document.querySelectorAll("#workspaceTabs [data-tab]").forEach((btn) => {
            btn.addEventListener("click", () => activarTab(btn.dataset.tab));
        });

        // Filtros landing
        // Los <select> de filtros están inicializados con Select2 (ver
        // _initSelect2InSection). Cuando el usuario escoge una opción,
        // Select2 dispara los eventos 'input'/'change' con
        // jQuery.trigger(), que SOLO invoca handlers registrados vía
        // jQuery.on() o el handler inline element.oninput — NO los
        // listeners nativos de addEventListener. Por eso el filtro por
        // nombre (input text) funcionaba pero los selects no: el browser
        // dispara 'input' nativamente al tipear, pero Select2 nunca
        // hace dispatchEvent nativo. Registramos con jQuery.on() para
        // que el handler quede en el sistema de eventos de jQuery.
        if (globalThis.jQuery) {
            const $filtrosLanding = globalThis.jQuery(
                "#inv-filter-nombre, #inv-filter-categoria, #inv-filter-tipo, #inv-filter-estado, #inv-filter-ocupacion"
            );
            $filtrosLanding.on("input change", aplicarFiltrosCards);
        } else {
            ["inv-filter-nombre", "inv-filter-categoria", "inv-filter-tipo", "inv-filter-estado", "inv-filter-ocupacion"]
                .forEach((id) => document.getElementById(id)?.addEventListener("input", aplicarFiltrosCards));
        }
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
        // Cualquier botón con data-bs-target="#inv-modal-picker" (incluido el
        // verde "Agregar material nuevo" de la pestaña Inventario) abre el
        // modal vía atributos data-*, pero Bootstrap NO llama a cargarCatalogo.
        // Interceptamos el click para garantizar que se cargue el catálogo y
        // se reseteen los filtros sin importar qué botón lo dispara.
        document.querySelector("section[data-seccion='inventario']")?.addEventListener("click", (e) => {
            const trigger = e.target.closest('[data-bs-target="#inv-modal-picker"]');
            if (!trigger) return;
            e.preventDefault();
            abrirPicker();
        });
        // Reset + carga del catálogo cada vez que el modal se muestra,
        // cubriendo también aperturas vía show.bs.modal (ej. JS imperativo).
        const pickerModalEl = document.getElementById("inv-modal-picker");
        if (pickerModalEl) {
            pickerModalEl.addEventListener("show.bs.modal", () => {
                const buscar = document.getElementById("inv-picker-buscar");
                const cat = document.getElementById("inv-picker-categoria");
                const mostrar = document.getElementById("inv-picker-mostrar");
                if (buscar) buscar.value = "";
                if (cat) cat.value = "";
                if (mostrar) mostrar.value = "todos";
                cargarCatalogo();
            });
            pickerModalEl.addEventListener("shown.bs.modal", () => {
                setTimeout(() => document.getElementById("inv-picker-buscar")?.focus(), 50);
            });
        }
        ["inv-picker-buscar"].forEach((id) => document.getElementById(id)?.addEventListener("input", renderPicker));
        // inv-picker-categoria / inv-picker-mostrar están envueltos en Select2
        // (ver _initSelect2InSection). Usar _bindChange para que jQuery.on()
        // registre el handler en el sistema de eventos de jQuery (Select2
        // dispara change/input vía jQuery.trigger(), que no llega a
        // addEventListener nativo).
        _bindChange("#inv-picker-categoria, #inv-picker-mostrar", renderPicker);
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
                    tbody.addEventListener("click", _handleAccionTabla);
                });
            });

        // Render inicial
        renderHistorialGeneral();
        bindExtras();
        renderFlujoMaterialesList();
        // Deep-link desde sidebar: ?ovtab=ovtab-xxx
        const urlOvtab = new URLSearchParams(globalThis.location.search).get("ovtab");
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

    function _handleAccionTabla(e) {
        const btn = e.target.closest("button[data-accion]");
        if (!btn) return;
        const id = btn.dataset.id;
        const tipo = btn.dataset.tipo;
        if (btn.dataset.accion === "ver") verMovimiento(tipo, id);
        if (btn.dataset.accion === "editar") editarMovimiento(tipo, id);
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
            headers: _jsonHeaders(),
            body: JSON.stringify(payload),
        })
            .then(_parseJsonResponse)
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al guardar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-editar-inventario"))?.hide();
                Swal.fire({ icon: "success", title: "¡Cambios guardados!", text: "La hoja técnica se actualizó.", confirmButtonColor: "#0d6efd" });
                setTimeout(() => globalThis.location.reload(), 1200);
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
            headers: _jsonHeaders(),
            body: JSON.stringify({ puntoId: Number(document.querySelector("section[data-seccion='inventario']").dataset.puntoEcaId) }),
        })
            .then(_parseJsonResponse)
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al eliminar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-eliminar"))?.hide();
                Swal.fire({ icon: "success", title: "Eliminado", text: "Material removido del inventario.", confirmButtonColor: "#dc3545" });
                setTimeout(() => globalThis.location.reload(), 1200);
            })
            .catch(_showFetchError);
    });

    // ============================================================
    // SUBMIT: REGISTRAR COMPRA / VENTA (workspace forms)
    // ============================================================
    function submitEntrada(e) {
        if (e) e.preventDefault();
        const form = document.getElementById("formEntrada");
        if (!_validateForm("formEntrada")) return;
        const btn = e?.currentTarget || document.getElementById("inv-btn-guardar-entrada");
        const raw = _readFormAsObject(form);
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
        const stockBase = Number(document.getElementById("formEntradaStockActual")?.value || 0);
        const cant = Number(raw.cantidad);
        const promise = fetch("/punto-eca/movimientos/registrar-compra/", {
            method: "POST",
            headers: _jsonHeaders(),
            body: JSON.stringify(payload),
        })
            .then(_parseJsonResponse)
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || d?.message || "Error al registrar");
                // Mostrar comprobante con todos los campos de la compra.
                // Al cerrarlo, redirigimos a la misma página con un deep-link
                // (?inv=<id>&tab=tab-compra) para que el workspace se
                // re-renderice con la nueva compra visible en el historial
                // y el stock actualizado. La recarga es necesaria para que
                // la lista de compras del backend se vuelva a pedir.
                Swal.fire({
                    icon: null,
                    title: null,
                    html: renderComprobante("compra", {
                        materialNombre: currentMaterial?.nombre || "—",
                        materialTipo: document.getElementById("formEntradaMaterialTipo")?.value || "—",
                        materialCategoria: document.getElementById("formEntradaMaterialCategoria")?.value || "—",
                        unidad: document.getElementById("formEntradaMaterialUnidad")?.value || "",
                        cantidad: cant,
                        precioUnitario: Number(raw.precioCompra) || 0,
                        total: cant * (Number(raw.precioCompra) || 0),
                        stockResultante: stockBase + cant,
                        observaciones: raw.observaciones || "",
                        fechaLegible: formatDateCO(raw.fecha) || raw.fecha,
                    }),
                    showConfirmButton: true,
                    confirmButtonText: "Cerrar",
                    confirmButtonColor: "#dc3545",
                    width: "480px",
                }).then(() => {
                    if (!currentMaterial) return;
                    const url = new URL(globalThis.location.href);
                    url.searchParams.set("inv", currentMaterial.inventarioId);
                    url.searchParams.set("tab", "tab-compra");
                    globalThis.location.href = url.toString();
                });
            })
            .catch(_showFetchError);
        withLoading(btn, () => promise);
    }
    function submitSalida(e) {
        if (e) e.preventDefault();
        if (!_validateForm("formSalida")) return;
        const form = document.getElementById("formSalida");
        const btn = e?.currentTarget || document.getElementById("inv-btn-guardar-salida");
        const raw = _readFormAsObject(form);
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
        const stockBase = Number(document.getElementById("formSalidaStockActual")?.value || 0);
        const cant = Number(raw.cantidad);
        // Buscar el nombre del centro seleccionado para mostrarlo en el comprobante
        const centroSel = document.getElementById("formSalidaCentro");
        const centroNombre = centroSel?.options[centroSel.selectedIndex]?.text || "";
        const promise = fetch("/punto-eca/movimientos/registrar-venta/", {
            method: "POST",
            headers: _jsonHeaders(),
            body: JSON.stringify(payload),
        })
            .then(_parseJsonResponse)
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || d?.message || "Error al registrar");
                // Mostrar comprobante con todos los campos de la venta.
                // Al cerrarlo, redirigimos a la misma página con un deep-link
                // (?inv=<id>&tab=tab-venta) para que el workspace se
                // re-renderice con la nueva venta visible en el historial
                // y el stock actualizado.
                Swal.fire({
                    icon: null,
                    title: null,
                    html: renderComprobante("venta", {
                        materialNombre: currentMaterial?.nombre || "—",
                        materialTipo: document.getElementById("formSalidaMaterialTipo")?.value || "—",
                        materialCategoria: document.getElementById("formSalidaMaterialCategoria")?.value || "—",
                        unidad: document.getElementById("formSalidaMaterialUnidad")?.value || "",
                        cantidad: cant,
                        precioUnitario: Number(raw.precioVenta) || 0,
                        total: cant * (Number(raw.precioVenta) || 0),
                        stockResultante: stockBase - cant,
                        observaciones: raw.observaciones || "",
                        fechaLegible: formatDateCO(raw.fecha) || raw.fecha,
                        centroNombre: centroNombre,
                    }),
                    showConfirmButton: true,
                    confirmButtonText: "Cerrar",
                    confirmButtonColor: "#198754",
                    width: "480px",
                }).then(() => {
                    if (!currentMaterial) return;
                    const url = new URL(globalThis.location.href);
                    url.searchParams.set("inv", currentMaterial.inventarioId);
                    url.searchParams.set("tab", "tab-venta");
                    globalThis.location.href = url.toString();
                });
            })
            .catch(_showFetchError);
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
        // Sugerir cantidad=0 como punto de partida, si el campo está vacío.
        // El usuario lo sobrescribe; con 0 el Total queda vacío y el
        // stock preview muestra el stock base (sin cambio). Obliga al
        // usuario a tipear la cantidad real, evitando registrar valores
        // случайные (ej. 1) que el usuario podría olvidar cambiar.
        const cantEl = document.getElementById(`${prefix}Cantidad`);
        if (cantEl && !cantEl.value) cantEl.value = 0;
        // Recalcular total con el precio recién autorrellenado
        if (prefix === "formEntrada") actualizarTotalEntrada();
        if (prefix === "formSalida") actualizarTotalVenta();
        // Pintar el preview de stock resultante con el stock base del material
        // (aunque el usuario todavía no haya tipeado cantidad, queremos ver
        // el stock actual como punto de partida).
        actualizarStockPreview(prefix);
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
    // quedará tras aplicar este movimiento. Incluye barra de progreso,
    // labels de capacidad y texto de disponibles. Color verde si el
    // resultado es válido; amarillo si supera 70%; rojo si supera 90%
    // o excede la capacidad máxima. Es solo referencia visual; el
    // backend re-valida.

    /** Determina la clase de color para la barra de progreso según el porcentaje. */
    function _claseBarraStock(pct, sobreCapacidad) {
        if (sobreCapacidad || pct >= 90) return "bg-danger";
        if (pct >= 70) return "bg-warning";
        return "bg-success";
    }

    /** Determina la clase de color para la barra de stock restante (venta). */
    function _claseBarraRestante(pct, negativo) {
        if (negativo || pct <= 10) return "bg-danger";
        if (pct <= 30) return "bg-warning";
        return "bg-success";
    }

    /** Actualiza barra de progreso, disponibles y estilo del input de stock. */
    function _renderStockBar(bar, disponibles, stockEl, unidad, opts) {
        const fmt = (v) => v.toLocaleString("es-CO", { maximumFractionDigits: 2 });
        const { resultado, capacidad,stockBase, esEntrada } = opts;
        if (!bar || !stockEl) return;

        if (capacidad > 0) {
            const pct = esEntrada
                ? Math.min((resultado / capacidad) * 100, 100)
                : Math.max((resultado / capacidad) * 100, 0);
            const clase = esEntrada
                ? _claseBarraStock(pct, resultado > capacidad)
                : _claseBarraRestante(pct, resultado < 0);
            bar.style.width = Math.min(pct, 100) + "%";
            bar.className = "progress-bar " + clase;
            if (disponibles) {
                disponibles.textContent = `${fmt(Math.max(resultado, 0))} ${unidad}`;
            }
        } else {
            bar.style.width = "0%";
            bar.className = "progress-bar bg-success";
            if (disponibles) disponibles.textContent = "—";
        }

        const excede = esEntrada ? (capacidad > 0 && resultado > capacidad) : resultado < 0;
        stockEl.style.backgroundColor = excede ? "#f8d7da" : "#d1e7dd";
        stockEl.style.color = excede ? "#58151c" : "#0a3622";
    }

    function actualizarStockPreviewEntrada() {
        const stockEl = document.getElementById("formEntradaStockResultante");
        const unidadEl = document.getElementById("formEntradaStockResultanteUnidad");
        if (!stockEl) return;
        const stockBase = Number(document.getElementById("formEntradaStockActual")?.value || 0);
        const capacidad = Number(document.getElementById("formEntradaCapacidadMaxima")?.value || 0);
        const cant = Number(document.getElementById("formEntradaCantidad")?.value || 0);
        const unidad = document.getElementById("formEntradaMaterialUnidad")?.value || "";
        const resultante = stockBase + cant;

        stockEl.value = resultante.toLocaleString("es-CO", { maximumFractionDigits: 2 });
        if (unidadEl) unidadEl.textContent = unidad || "unidades";

        const fmt = (v) => v.toLocaleString("es-CO", { maximumFractionDigits: 2 });
        const actualLabel = document.getElementById("formEntradaStockActualLabel");
        const capMaxLabel = document.getElementById("formEntradaCapMaxLabel");
        if (actualLabel) actualLabel.textContent = `${fmt(stockBase)} ${unidad}`;
        if (capMaxLabel) capMaxLabel.textContent = `${fmt(capacidad)} ${unidad}`;

        _renderStockBar(
            document.getElementById("formEntradaStockBar"),
            document.getElementById("formEntradaDisponibles"),
            stockEl, unidad,
            { resultado: resultante, capacidad, stockBase, esEntrada: true }
        );
    }

    function actualizarStockPreviewSalida() {
        const stockEl = document.getElementById("formSalidaStockRestante");
        const unidadEl = document.getElementById("formSalidaStockRestanteUnidad");
        if (!stockEl) return;
        const stockBase = Number(document.getElementById("formSalidaStockActual")?.value || 0);
        const capacidad = Number(document.getElementById("formSalidaCapacidadMaxima")?.value || 0);
        const cant = Number(document.getElementById("formSalidaCantidad")?.value || 0);
        const unidad = document.getElementById("formSalidaMaterialUnidad")?.value || "";
        const restante = stockBase - cant;

        stockEl.value = restante.toLocaleString("es-CO", { maximumFractionDigits: 2 });
        if (unidadEl) unidadEl.textContent = unidad || "unidades";

        const fmt = (v) => v.toLocaleString("es-CO", { maximumFractionDigits: 2 });
        const actualLabel = document.getElementById("formSalidaStockActualLabel");
        const capMaxLabel = document.getElementById("formSalidaCapMaxLabel");
        if (actualLabel) actualLabel.textContent = `${fmt(stockBase)} ${unidad}`;
        if (capMaxLabel) capMaxLabel.textContent = `${fmt(capacidad)} ${unidad}`;

        _renderStockBar(
            document.getElementById("formSalidaStockBar"),
            document.getElementById("formSalidaDisponibles"),
            stockEl, unidad,
            { resultado: restante, capacidad, stockBase, esEntrada: false }
        );
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
    // VALIDACIÓN ESTANDARIZADA DE FORMULARIOS
    // ============================================================
    // Patrón uniforme para los 4 formularios de Compra/Venta (crear
    // y editar). Cumple el contrato institucional:
    //   1. Supresión de globos nativos: captura de 'invalid' en fase
    //      de captura (useCapture=true) + preventDefault() bloquea los
    //      tooltips por defecto de Chromium/WebKit.
    //   2. Validación centralizada en submit con form.checkValidity().
    //   3. Si inválido: preventDefault() + stopPropagation() para
    //      abortar el submit de inmediato y no propagar al handler real.
    //   4. Activación de 'was-validated' en el <form> para que
    //      Bootstrap 5 pinte los bordes rojos y muestre los
    //      <div class="invalid-feedback"> bajo cada campo.
    //   5. Notificación global con Swal.fire() (color verde
    //      institucional #198754) para que el usuario sepa que hay
    //      campos pendientes, sin importar cuál sea.
    //
    // Uso:
    //   const ok = _validateForm("formEntrada");
    //   if (!ok) return;  // el form NO se envía
    //   ...continuar con el submit real...
    function _validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        const valid = form.checkValidity();
        if (!valid) {
            // Disparar manualmente el evento 'invalid' en cada input/select
            // con constraint violations, para que Bootstrap 5 aplique los
            // estilos :invalid y muestre los .invalid-feedback.
            form.querySelectorAll("input, select, textarea").forEach((el) => {
                if (!el.checkValidity()) {
                    el.dispatchEvent(new Event("invalid", { bubbles: false, cancelable: true }));
                }
            });
            form.classList.add("was-validated");
            _showMissingFieldsAlert(form);
        }
        return valid;
    }

    // Muestra un Swal genérico y amigable cuando faltan campos obligatorios
    // en un formulario. Mensaje institucional (no técnico), botón verde
    // (#198754), icono warning. Reutilizado por _validateForm y por el
    // listener de submit de _installFormValidation.
    function _showMissingFieldsAlert(form) {
        if (!globalThis.Swal?.fire) return;
        // Listar los labels de los campos pendientes para que el mensaje
        // sea concreto y útil (no genérico).
        const labels = [];
        form.querySelectorAll("input, select, textarea").forEach((el) => {
            if (!el.checkValidity() && el.required) {
                const label = form.querySelector(`label[for="${el.id}"]`);
                if (label) labels.push(label.textContent.trim().replace(/\*$/, "").trim());
            }
        });
        const detalle = labels.length
            ? `Pendientes: ${labels.join(", ")}.`
            : "Revisa los campos marcados en rojo y completa la información.";
        Swal.fire({
            icon: "warning",
            title: "Faltan campos obligatorios por diligenciar",
            html: detalle,
            confirmButtonText: "Entendido",
            confirmButtonColor: "#198754",
        });
    }

    // Instala los listeners de validación en un formulario:
    //   - Captura 'invalid' en fase de captura (useCapture=true) para
    //     bloquear los globos nativos del navegador.
    //   - Captura 'submit' en fase de captura para abortar el envío
    //     si el form es inválido (preventDefault + stopPropagation).
    //
    // Esta función se llama UNA VEZ en bind() para cada form de CV.
    // NO interfiere con los handlers reales (submitEntrada, etc.) que
    // están enganchados en el botón (no en el form), siempre que esos
    // handlers llamen a _validateForm(formId) al inicio.
    function _installFormValidation(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        // 1. Suprimir globos nativos del navegador (Chromium/WebKit)
        //    capturando el evento 'invalid' en fase de captura.
        form.addEventListener(
            "invalid",
            (e) => { e.preventDefault(); },
            true, // useCapture: true → bloquea antes del bubble
        );
        // 2. Capturar el submit en fase de captura para abortar envío.
        //    Si el form es inválido, preventDefault() + stopPropagation()
        //    impide que el handler real reciba el evento.
        form.addEventListener(
            "submit",
            (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                    form.classList.add("was-validated");
                    _showMissingFieldsAlert(form);
                }
            },
            true, // useCapture: true → corre antes que handlers de submit
        );
    }

    // ============================================================
    // SUBMIT: EDITAR COMPRA / VENTA (modales)
    // ============================================================
    function submitEditarCompra() {
        if (!_validateForm("inv-form-editar-compra")) return;
        const form = document.getElementById("inv-form-editar-compra");
        const btn = document.getElementById("inv-btn-guardar-editar-compra");
        const raw = _readFormAsObject(form);
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
            compraId: _safeStr(raw.id),
            fechaCompra: raw.fecha,
            cantidad: nuevaCant,
            precioCompra: Number(raw.precioCompra),
            observaciones: raw.observaciones || "",
        };
        const promise = fetch(`/punto-eca/movimientos/editar-compra/${_safeStr(raw.id)}/`, {
            method: "PATCH",
            headers: _jsonHeaders(),
            body: JSON.stringify(payload),
        })
            .then(_parseJsonResponse)
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al editar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-editar-compra"))?.hide();
                _showSuccessSwal("Compra actualizada", undefined, 1500);
                setTimeout(() => globalThis.location.reload(), 1500);
            })
            .catch(_showFetchError);
        withLoading(btn, () => promise);
    }
    function submitEditarVenta() {
        if (!_validateForm("inv-form-editar-venta")) return;
        const form = document.getElementById("inv-form-editar-venta");
        const btn = document.getElementById("inv-btn-guardar-editar-venta");
        const raw = _readFormAsObject(form);
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
            ventaId: _safeStr(raw.id),
            fechaVenta: raw.fecha,
            cantidad: nuevaCant,
            precioVenta: Number(raw.precioVenta),
            observaciones: raw.observaciones || "",
        };
        const centroSel = document.getElementById("inv-edit-venta-centro");
        if (centroSel?.value) payload.centroAcopioId = centroSel.value;
        const promise = fetch(`/punto-eca/movimientos/editar-venta/${_safeStr(raw.id)}/`, {
            method: "PATCH",
            headers: _jsonHeaders(),
            body: JSON.stringify(payload),
        })
            .then(_parseJsonResponse)
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || "Error al editar");
                bootstrap.Modal.getInstance(document.getElementById("inv-modal-editar-venta"))?.hide();
                _showSuccessSwal("Venta actualizada", undefined, 1500);
                setTimeout(() => globalThis.location.reload(), 1500);
            })
            .catch(_showFetchError);
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
            if (r.isConfirmed) _ejecutarEliminacion(url);
        });
    }
    function _ejecutarEliminacion(url) {
        fetch(url, {
            method: "DELETE",
            headers: _jsonHeaders(),
        })
            .then((res) => res.json().then((d) => ({ ok: res.ok, d })))
            .then(_mostrarResultadoEliminacion)
            .catch(_showFetchError);
    }
    function _mostrarResultadoEliminacion({ ok, d }) {
        if (!ok) throw new Error(d?.mensaje || "Error al eliminar");
        _showSuccessSwal("Eliminado", undefined, 1200);
        setTimeout(() => globalThis.location.reload(), 1200);
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
        if (m?.nombreMaterial) return m.nombreMaterial;
        const c = comprasDB.find((x) => String(x.inventarioId) === String(inventarioId));
        if (c?.nombreMaterial) return c.nombreMaterial;
        const v = ventasDB.find((x) => String(x.inventarioId) === String(inventarioId));
        return v?.nombreMaterial || "";
    }

    function buildExportQuery(base) {
        const params = new URLSearchParams();
        const materialIdFiltro = _q("inv-hfiltro-material")?.value;
        const materialIdEfectivo = isWorkspaceHistorial && currentMaterialId
            ? String(currentMaterialId)
            : materialIdFiltro;
        const materialNombre = _resolverNombreMaterialExport(materialIdEfectivo);
        const filtros = [
            ["material", materialNombre],
            ["categoria", _q("inv-hfiltro-categoria")?.value],
            ["tipo", _q("inv-hfiltro-tipo-material")?.value],
            ["tipo_movimiento", _q("inv-hfiltro-tipo")?.value],
            ["fecha_desde", _q("inv-hfiltro-desde")?.value],
            ["fecha_hasta", _q("inv-hfiltro-hasta")?.value],
            ["centro_acopio", _q("inv-hfiltro-centro")?.value],
            ["cantidad_min", _q("inv-hfiltro-cantidad-min")?.value],
            ["cantidad_max", _q("inv-hfiltro-cantidad-max")?.value],
            ["monto_min", _q("inv-hfiltro-monto-min")?.value],
            ["monto_max", _q("inv-hfiltro-monto-max")?.value],
        ];
        for (const [key, value] of filtros) {
            if (value) params.append(key, value);
        }
        const qs = params.toString();
        return qs ? `${base}?${qs}` : base;
    }
    function _resolverNombreMaterialExport(materialIdEfectivo) {
        if (!materialIdEfectivo) return "";
        if (currentMaterial && String(currentMaterial.inventarioId) === String(materialIdEfectivo)) {
            return currentMaterial.nombre;
        }
        return _lookupMaterialNombreByInventarioId(materialIdEfectivo);
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
        globalThis.location.href = buildExportQuery(base);
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
        const filtros = _leerFiltrosHistorial();
        const enRango = _crearPredicateEnRango(filtros.desdeD, filtros.hastaD);
        const rows = [];
        const aceptaCompra = !filtros.tipo || filtros.tipo === "compra";
        const aceptaVenta = !filtros.tipo || filtros.tipo === "venta";

        if (aceptaCompra) {
            comprasDB.forEach((c) => {
                if (_coincideFiltrosHistorial(c, "compra", filtros, enRango)) {
                    rows.push({ ...c, _tipo: "compra", _ts: c.fechaCompra });
                }
            });
        }
        if (aceptaVenta) {
            ventasDB.forEach((v) => {
                if (_coincideFiltrosHistorial(v, "venta", filtros, enRango)) {
                    rows.push({ ...v, _tipo: "venta", _ts: v.fechaVenta });
                }
            });
        }
        rows.sort((a, b) => new Date(b._ts) - new Date(a._ts));
        return rows;
    }
    function _leerFiltrosHistorial() {
        const filtroMaterialId = _q("inv-hfiltro-material")?.value || "";
        const effectiveMaterialId = isWorkspaceHistorial && currentMaterialId
            ? String(currentMaterialId)
            : filtroMaterialId;
        const desde = _q("inv-hfiltro-desde")?.value;
        const hasta = _q("inv-hfiltro-hasta")?.value;
        return {
            effectiveMaterialId,
            categoria: _q("inv-hfiltro-categoria")?.value || "",
            tipoMaterial: _q("inv-hfiltro-tipo-material")?.value || "",
            tipo: _q("inv-hfiltro-tipo")?.value || "",
            centro: _q("inv-hfiltro-centro")?.value || "",
            cantidadMin: Number.parseFloat(_q("inv-hfiltro-cantidad-min")?.value),
            cantidadMax: Number.parseFloat(_q("inv-hfiltro-cantidad-max")?.value),
            montoMin: Number.parseFloat(_q("inv-hfiltro-monto-min")?.value),
            montoMax: Number.parseFloat(_q("inv-hfiltro-monto-max")?.value),
            desdeD: desde ? new Date(desde + "T00:00:00") : null,
            hastaD: hasta ? new Date(hasta + "T23:59:59") : null,
        };
    }
    function _crearPredicateEnRango(desdeD, hastaD) {
        if (!desdeD && !hastaD) return () => true;
        return (iso) => {
            const d = new Date(iso);
            if (Number.isNaN(d.getTime())) return false;
            if (desdeD && d < desdeD) return false;
            if (hastaD && d > hastaD) return false;
            return true;
        };
    }
    function _coincideFiltrosHistorial(row, tipoMov, filtros, enRango) {
        if (!_coincideIdentidad(row, filtros)) return false;
        if (!_coincideCategoriaTipo(row, filtros)) return false;
        if (tipoMov === "venta" && !_coincideCentro(row, filtros)) return false;
        const fecha = tipoMov === "compra" ? row.fechaCompra : row.fechaVenta;
        if (!enRango(fecha)) return false;
        return _coincideCantidadYMonto(row, tipoMov, filtros);
    }
    function _coincideIdentidad(row, filtros) {
        if (!filtros.effectiveMaterialId) return true;
        return String(row.inventarioId) === String(filtros.effectiveMaterialId);
    }
    function _coincideCategoriaTipo(row, filtros) {
        if (filtros.categoria && row.nombreCategoria !== filtros.categoria) return false;
        if (filtros.tipoMaterial && row.nombreTipo !== filtros.tipoMaterial) return false;
        return true;
    }
    function _coincideCentro(row, filtros) {
        if (!filtros.centro) return true;
        return row.nombreCentroAcopio === filtros.centro;
    }
    function _coincideCantidadYMonto(row, tipoMov, filtros) {
        const cant = Number(row.cantidad || 0);
        if (!_enRangoNumerico(cant, filtros.cantidadMin, filtros.cantidadMax)) return false;
        const precio = tipoMov === "compra" ? row.precioCompra : row.precioVenta;
        const monto = cant * Number(precio || 0);
        if (!_enRangoNumerico(monto, filtros.montoMin, filtros.montoMax)) return false;
        return true;
    }
    function _enRangoNumerico(valor, min, max) {
        if (!Number.isNaN(min) && valor < min) return false;
        if (!Number.isNaN(max) && valor > max) return false;
        return true;
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
        if (globalThis.jQuery !== undefined && globalThis.jQuery.fn.select2 !== undefined && globalThis.jQuery(sel).data("select2")) {
            globalThis.jQuery(sel).select2("destroy");
            globalThis.jQuery(sel).select2({ theme: "bootstrap-5", language: "es", width: "100%" });
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
        parts.push(
            mkBtn("«", 1, { disabled: current === 1 }),
            mkBtn("‹", current - 1, { disabled: current === 1 })
        );
        const max = pages;
        const pagerWindow = 2;
        const start = Math.max(1, current - pagerWindow);
        const end = Math.min(max, current + pagerWindow);
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
        parts.push(
            mkBtn("›", current + 1, { disabled: current === pages }),
            mkBtn("»", pages, { disabled: current === pages })
        );
        pager.innerHTML = parts.join("");
        pager.querySelectorAll("a.page-link").forEach((a) => {
            a.addEventListener("click", (ev) => {
                ev.preventDefault();
                const p = Number.parseInt(a.dataset.page, 10);
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
     * Construye la serie histórica de STOCK (cantidad física) para un material.
     *
     * La serie representa el stock al FINAL de cada bucket (después de aplicar
     * las ops que cayeron en ese bucket). Anclamos en `stockActual` (el stock
     * de "ahora") y caminamos hacia atrás restando las ops de cada bucket.
     *
     * Ejemplo: stockActual=110, ops=[(+10, día2), (-5, día3), (+5, día5)]
     *   - día5 (último bucket): serie[4] = 110; stock tras restar ops_día5 = 105
     *   - día4: serie[3] = 105; sin ops en día4 → stock sigue 105
     *   - día3: serie[2] = 105; restando ops_día3 (-5) → 110
     *   - día2: serie[1] = 110; restando ops_día2 (+10) → 100
     *   - día1: serie[0] = 100
     * Serie final: [100, 110, 105, 105, 110]
     *
     * Así, una COMPRA eleva la línea en su bucket y una VENTA la baja, y los
     * puntos reflejan fielmente cada movimiento del día.
     */
    function construirSerieMaterial(material, compras, ventas, desde, hasta, gran) {
        const buckets = generarBuckets(desde, hasta, gran);
        const invId = String(material.inventarioId);
        // Calcular delta neto por bucket: compras suman, ventas restan.
        const deltas = buckets.map(() => 0);
        for (const c of compras) {
            if (String(c.inventarioId) !== invId || !c.fechaCompra) continue;
            const idx = bucketIndexFor(new Date(c.fechaCompra), buckets, gran);
            if (idx >= 0) deltas[idx] += Number(c.cantidad || 0);
        }
        for (const v of ventas) {
            if (String(v.inventarioId) !== invId || !v.fechaVenta) continue;
            const idx = bucketIndexFor(new Date(v.fechaVenta), buckets, gran);
            if (idx >= 0) deltas[idx] -= Number(v.cantidad || 0);
        }
        // Walk backwards: empezamos con stockActual (fin del último bucket).
        // Para cada bucket, serie[i] = stock al final del bucket.
        // El stock al final del bucket i = stock al final del bucket i+1
        // menos las ops que ocurrieron en el bucket i+1 (porque esas ops
        // son las que cambiaron el stock entre i e i+1).
        // Equivalentemente, tras emitir serie[i], restamos deltas[i] para
        // preparar la siguiente iteración.
        const serie = new Array(buckets.length);
        let stock = Number(material.stockActual) || 0;
        for (let i = buckets.length - 1; i >= 0; i--) {
            serie[i] = Math.max(0, stock);
            stock -= deltas[i];
        }
        return serie;
    }

    function construirSerieGanancias(materiales, compras, ventas, desde, hasta, gran) {
        // Retorna { ingresos: number[], costos: number[], ganancia: number[] }
        //
        // SEMÁNTICA: cada bucket muestra el VALOR DIARIO (no acumulado).
        //   - ingresos[i] = suma de (cantidad * precioVenta) de las ventas del bucket i
        //   - costos[i]   = suma de (cantidad * precioCompra) de las compras del bucket i
        //   - ganancia[i] = ingresos[i] - costos[i]
        //
        // Esto refleja los movimientos del día: una línea que sube con las
        // ventas, baja con las compras (costos) y la ganancia muestra el
        // resultado neto del día. Si no hay ops, el punto queda en 0.
        const buckets = generarBuckets(desde, hasta, gran);
        const invIds = new Set(materiales.map((m) => String(m.inventarioId)));
        const ingresos = buckets.map(() => 0);
        const costos = buckets.map(() => 0);
        for (const c of compras) {
            if (!invIds.has(String(c.inventarioId)) || !c.fechaCompra) continue;
            const idx = bucketIndexFor(new Date(c.fechaCompra), buckets, gran);
            if (idx < 0) continue;
            costos[idx] += Number(c.cantidad || 0) * Number(c.precioCompra || 0);
        }
        for (const v of ventas) {
            if (!invIds.has(String(v.inventarioId)) || !v.fechaVenta) continue;
            const idx = bucketIndexFor(new Date(v.fechaVenta), buckets, gran);
            if (idx < 0) continue;
            ingresos[idx] += Number(v.cantidad || 0) * Number(v.precioVenta || 0);
        }
        const ganancia = buckets.map((_, i) => ingresos[i] - costos[i]);
        return { ingresos, costos, ganancia, buckets };
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
        const dpr = globalThis.devicePixelRatio || 1;
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
                { nombre: "Ingresos",       color: "#0d6efd", valores: gan.ingresos, capacidad: 0 },
                { nombre: "Costos",         color: "#fd7e14", valores: gan.costos,   capacidad: 0 },
                { nombre: "Ganancia neta",  color: "#198754", valores: gan.ganancia, capacidad: 0, esProfit: true },
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
        // Línea de y=0 (referencia para ganancia negativa)
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
            // Puntos: marcamos TODOS los buckets, no cada stepX. Así cada
            // movimiento del día (compra que sube el stock, venta que lo baja,
            // ingreso/costo del día) queda visible como un punto. Radio
            // pequeño para no saturar el chart cuando hay muchos buckets.
            ctx.fillStyle = s.color;
            const radio = s.valores.length > 60 ? 1.5 : 2.5;
            s.valores.forEach((v, i) => {
                ctx.beginPath();
                ctx.arc(xAt(i), yAt(v), radio, 0, Math.PI * 2);
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
        const ids = new Set(Array.from(checks).map((c) => c.value));
        const mats = materialesDB.filter((m) => ids.has(String(m.inventarioId)));
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
        const ids = new Set(Array.from(checks).map((c) => c.value));
        const mats = materialesDB.filter((m) => ids.has(String(m.inventarioId)));
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
        setKpiClass("inv-flujo-gan-kpi-margen", _margenClass(margen));
        setKpi("inv-flujo-gan-kpi-top", top ? top.nombre : "—");
        setKpi("inv-flujo-gan-kpi-top-val", top ? formatearCOP(top.profit) : "—");
        setKpi("inv-flujo-gan-kpi-perdida", movsPerdida);
        const badge = document.getElementById("inv-flujo-gan-badge");
        if (badge) badge.textContent = `${mats.length} material${mats.length === 1 ? "" : "es"}`;
        renderChart("inv-ganancias-chart", { modo: "ganancia", materiales: mats, gran, desde, hasta, buckets });
    }

    function renderWsChart() {
        if (!currentMaterial) return;
        const gran = document.getElementById("inv-ws-flujo-stock-granularidad")?.value || "dia";
        const desde = _parseFecha("inv-ws-flujo-stock-desde") || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
        const hasta = _parseFecha("inv-ws-flujo-stock-hasta") || new Date();
        const cap = document.getElementById("inv-ws-flujo-stock-cap")?.checked ?? true;
        const buckets = generarBuckets(desde, hasta, gran);
        renderChart("stockTimeChart", {
            modo: "stock", materiales: [currentMaterial], gran, mostrarCap: cap,
            desde, hasta, buckets,
        });
        const invId = currentMaterial.inventarioId;
        const cm = comprasDB.filter((c) => String(c.inventarioId) === String(invId)
            && _enRango(c.fechaCompra, desde, hasta));
        const vm = ventasDB.filter((v) => String(v.inventarioId) === String(invId)
            && _enRango(v.fechaVenta, desde, hasta));
        const setKpi = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        setKpi("inv-ws-flujo-stock", `${Number(currentMaterial.stockActual).toLocaleString("es-CO")} ${currentMaterial.unidad}`);
        setKpi("inv-ws-flujo-movs", cm.length + vm.length);
        setKpi("inv-ws-flujo-compras", cm.length);
        setKpi("inv-ws-flujo-ventas", vm.length);
        const badge = document.getElementById("inv-ws-flujo-stock-badge");
        if (badge) badge.textContent = `${cm.length + vm.length} movs en rango`;
    }

    function renderWsGananciasChart() {
        if (!currentMaterial) return;
        const gran = document.getElementById("inv-ws-flujo-gan-granularidad")?.value || "dia";
        const desde = _parseFecha("inv-ws-flujo-gan-desde") || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
        const hasta = _parseFecha("inv-ws-flujo-gan-hasta") || new Date();
        const buckets = generarBuckets(desde, hasta, gran);
        const invId = currentMaterial.inventarioId;
        const cm = comprasDB.filter((c) => String(c.inventarioId) === String(invId)
            && _enRango(c.fechaCompra, desde, hasta));
        const vm = ventasDB.filter((v) => String(v.inventarioId) === String(invId)
            && _enRango(v.fechaVenta, desde, hasta));
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
        setKpiClass("inv-ws-flujo-gan-margen", _margenClass(margen));
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
        const badge = document.getElementById("inv-ws-flujo-gan-badge");
        if (badge) badge.textContent = `${cm.length + vm.length} movs en rango`;
    }

    // Helper: true si la fecha (string o Date) cae dentro de [desde, hasta].
    // Acepta strings ISO o timestamps que el backend devuelve. Usado por
    // los renderers de flujo del workspace para aplicar el rango
    // seleccionado en los inputs Desde/Hasta.
    function _enRango(fecha, desde, hasta) {
        if (!fecha) return false;
        const t = new Date(fecha).getTime();
        if (Number.isNaN(t)) return false;
        return t >= desde.getTime() && t <= new Date(hasta.getTime() + 86400000 - 1).getTime();
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
    function _handleOvSubTabClick(btn) {
        const sub = btn.dataset.ovsub;
        document.querySelectorAll('#ovFlujoSubtabs .nav-link').forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".ovsub-pane").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        const pane = document.getElementById(sub);
        if (pane) {
            pane.classList.add("active");
            _reinitSelect2InPane(pane);
            setTimeout(() => {
                if (sub === "ovstock") renderOvtabChart();
                else if (sub === "ovgan") renderOvGananciasChart();
            }, 50);
        }
    }
    function _handleWsSubTabClick(btn) {
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
    }
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
        // inv-flujo-stock-granularidad está envuelto en Select2 (ver
        // _reinitSelect2InPane). _bindChange usa jQuery.on() para que el
        // handler quede registrado en el sistema de eventos de jQuery.
        _bindChange("#inv-flujo-stock-granularidad", renderOvtabChart);
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
        _bindChange("#inv-flujo-gan-granularidad", renderOvGananciasChart);
        document.getElementById("inv-flujo-gan-desde")?.addEventListener("change", renderOvGananciasChart);
        document.getElementById("inv-flujo-gan-hasta")?.addEventListener("change", renderOvGananciasChart);

        // Chart workspace flujo — Stock
        // Mismo patrón que el landing: auto-rerender en cada change de
        // cualquier input + botón Aplicar explícito por paridad. La sub-pane
        // es de UN solo material, por eso no hay picker de materiales.
        document.getElementById("inv-ws-flujo-stock-aplicar")?.addEventListener("click", renderWsChart);
        // inv-ws-flujo-stock-granularidad está envuelto en Select2
        // (ver _reinitSelect2InPane). Select2 dispara 'change' vía
        // jQuery.trigger() que no llega a addEventListener nativo, por
        // eso usamos _bindChange (jQuery.on). Los demás son date/checkbox
        // nativos, addEventListener funciona bien.
        _bindChange("#inv-ws-flujo-stock-granularidad", renderWsChart);
        ["inv-ws-flujo-stock-desde", "inv-ws-flujo-stock-hasta", "inv-ws-flujo-stock-cap"]
            .forEach((id) => document.getElementById(id)?.addEventListener("change", renderWsChart));

        // Chart workspace flujo — Ganancias
        document.getElementById("inv-ws-flujo-gan-aplicar")?.addEventListener("click", renderWsGananciasChart);
        _bindChange("#inv-ws-flujo-gan-granularidad", renderWsGananciasChart);
        ["inv-ws-flujo-gan-desde", "inv-ws-flujo-gan-hasta"]
            .forEach((id) => document.getElementById(id)?.addEventListener("change", renderWsGananciasChart));

        // Sub-tabs internas del flujo (Stock / Ganancias)
        document.querySelectorAll('#ovFlujoSubtabs [data-ovsub]').forEach((btn) => {
            btn.addEventListener("click", () => _handleOvSubTabClick(btn));
        });
        document.querySelectorAll('#wsFlujoSubtabs [data-wssub]').forEach((btn) => {
            btn.addEventListener("click", () => _handleWsSubTabClick(btn));
        });

        // Render ovtab chart cuando se abre
        document.querySelector('#otrasVistasTabs [data-ovtab="ovtab-flujo"]')?.addEventListener("click", () => {
            setTimeout(renderOvtabChart, 50);
        });
        // Render ws chart cuando se abre su tab
        document.querySelector('#workspaceTabs [data-tab="tab-flujo"]')?.addEventListener("click", () => {
            setTimeout(renderWsChart, 50);
        });

        // Carga masiva CSV: bind del submit, cards pre-set tipo y link
        // dinámico de plantilla según el select.
        document.getElementById("inv-btn-ejecutar-carga")?.addEventListener("click", ejecutarCargaMasiva);
        // inv-carga-tipo está envuelto en Select2 (ver _initSelect2InSection).
        // _bindChange usa jQuery.on() para que el handler quede registrado
        // en el sistema de eventos de jQuery.
        _bindChange("#inv-carga-tipo", _actualizarLinkPlantilla);
        document.querySelectorAll("[data-bulk-tipo]").forEach((el) => {
            el.addEventListener("click", () => {
                const tipo = el.dataset.bulkTipo;
                const sel = document.getElementById("inv-carga-tipo");
                if (sel) {
                    sel.value = tipo;
                    // Si Select2 está inicializado, refrescar visual
                    if (typeof $ === "function" && $(sel).data("select2")) {
                        $(sel).trigger("change.select2");
                    }
                }
                _actualizarLinkPlantilla();
            });
        });
        // Inicializar el link de plantilla con el tipo por defecto
        _actualizarLinkPlantilla();
    }

    // ============================================================
    // COMPROBANTE POST-OPERACIÓN
    // ============================================================
    // Genera un resumen visual tipo "comprobante" con todos los campos
    // de la compra o venta recién registrada. No es una factura legal;
    // es un resumen para que el gestor confirme visualmente lo que
    // acaba de registrar antes de cerrar el modal.
    function renderComprobante(tipo, datos) {
        const tituloTipo = tipo === "compra" ? "Compra registrada" : "Venta registrada";
        const colorHeader = tipo === "compra" ? "#dc3545" : "#198754";
        const esVenta = tipo === "venta";
        const row = (label, value) => `
            <tr>
                <td class="text-muted text-start pe-2" style="width: 45%;">${label}</td>
                <td class="fw-semibold text-end">${value}</td>
            </tr>`;
        const observaciones = datos.observaciones
            ? row("Observaciones", `<span class="fst-italic text-muted">${escapeHtml(datos.observaciones)}</span>`)
            : "";
        const centro = esVenta && datos.centroNombre
            ? row("Centro de acopio", escapeHtml(datos.centroNombre))
            : "";
        return `
            <div class="text-start" style="font-size: 0.9rem;">
                <div class="d-flex justify-content-between align-items-center pb-2 mb-2" style="border-bottom: 2px solid ${colorHeader};">
                    <strong style="color: ${colorHeader};">${tituloTipo}</strong>
                    <small class="text-muted">${escapeHtml(datos.fechaLegible)}</small>
                </div>
                <table class="table table-sm table-borderless mb-0">
                    <tbody>
                        ${row("Material", escapeHtml(datos.materialNombre))}
                        ${row("Tipo", escapeHtml(datos.materialTipo))}
                        ${row("Categoría", escapeHtml(datos.materialCategoria))}
                        ${row("Cantidad", `${datos.cantidad.toLocaleString("es-CO", { maximumFractionDigits: 2 })} ${escapeHtml(datos.unidad)}`)}
                        ${row("Precio unitario", formatearCOP(datos.precioUnitario))}
                        ${row("Total", `<span style="color: ${colorHeader};">${formatearCOP(datos.total)}</span>`)}
                        ${centro}
                        ${row("Stock resultante", `${datos.stockResultante.toLocaleString("es-CO", { maximumFractionDigits: 2 })} ${escapeHtml(datos.unidad)}`)}
                        ${observaciones}
                    </tbody>
                </table>
            </div>`;
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

    // ============================================================
    // CARGA MASIVA CSV
    // ============================================================
    // Construye la URL del archivo plantilla según el tipo seleccionado
    // en el modal de carga masiva. La URL base viene del atributo
    // data-plantilla-url del modal (generado por Django en el template).
    // Se llama al cambiar el select y al abrir el modal vía card.
    function _actualizarLinkPlantilla() {
        const link = document.getElementById("inv-link-plantilla-ejemplo");
        if (!link) return;
        const base = link.dataset.plantillaUrl || "";
        if (!base) return;
        const tipoEl = document.getElementById("inv-carga-tipo");
        const tipo = tipoEl?.value || "compra";
        link.setAttribute("href", `${base}?tipo=${tipo}`);
    }

    // Lee el archivo CSV del input, lo envía por multipart/form-data al
    // endpoint bulk_import correspondiente al tipo (compra/venta) y
    // muestra un Swal con el resumen. Cierra el modal al terminar con éxito.
    // Decisión: usar withLoading para evitar doble-click y dar feedback
    // visual durante el procesamiento (puede tardar con 600 filas).
    function ejecutarCargaMasiva() {
        const fileEl = document.getElementById("inv-carga-archivo");
        const tipoEl = document.getElementById("inv-carga-tipo");
        const btn = document.getElementById("inv-btn-ejecutar-carga");
        if (!_validarArchivoCargaMasiva(fileEl)) return;
        const file = fileEl.files[0];
        const tipo = tipoEl?.value || "compra";
        const url = `/punto-eca/movimientos/${tipo}s/bulk_import/`;
        const fd = new FormData();
        fd.append("file", file);

        withLoading(btn, () => fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            body: fd,
        })
            .then(_parsearJsonComoRespuestaBulk)
            .then((res) => _procesarRespuestaCargaMasiva(res, fileEl))
            .catch(_manejarErrorCargaMasiva));
    }
    function _parsearJsonComoRespuestaBulk(r) {
        return r.json().then((data) => ({ ok: r.ok, status: r.status, data }));
    }
    function _validarArchivoCargaMasiva(fileEl) {
        if (!fileEl?.files?.length) {
            Swal.fire({
                icon: "warning",
                title: "Selecciona un archivo CSV",
                confirmButtonColor: "#0d6efd",
            });
            return false;
        }
        if (!fileEl.files[0].name.toLowerCase().endsWith(".csv")) {
            Swal.fire({
                icon: "warning",
                title: "El archivo debe ser .csv",
                confirmButtonColor: "#0d6efd",
            });
            return false;
        }
        return true;
    }
    function _procesarRespuestaCargaMasiva({ ok, status, data }, fileEl) {
        if (!ok || data.status === "error") {
            const msg = data?.mensaje || "Error al procesar el archivo";
            throw new Error(msg);
        }
        // Reset input para permitir re-subir el mismo archivo
        fileEl.value = "";
        // Cerrar modal
        const modalEl = document.getElementById("inv-modalCargaMasiva");
        bootstrap.Modal.getInstance(modalEl)?.hide();
        _mostrarResumenCargaMasiva(data);
    }
    function _mostrarResumenCargaMasiva(data) {
        const r = data.resumen || {};
        const exitosas = r.exitosas || 0;
        const conErrores = r.con_errores || 0;
        const total = r.total_filas || (exitosas + conErrores);
        const color = conErrores > 0 ? "#fd7e14" : "#198754";
        const primerError = (data.detalles || []).find((d) => d.status === "error");
        const detalleHtml = primerError
            ? `<small class="text-muted d-block mt-2">Primer error: ${escapeHtml(primerError.mensaje)}</small>`
            : "";
        Swal.fire({
            icon: conErrores > 0 ? "warning" : "success",
            title: "Carga masiva completada",
            html: `<p class="mb-1"><strong>${exitosas}</strong> exitosas de <strong>${total}</strong> totales</p>
                   <p class="mb-0">${conErrores} con errores</p>${detalleHtml}`,
            confirmButtonText: "OK",
            confirmButtonColor: color,
        });
    }
    function _manejarErrorCargaMasiva(err) {
        Swal.fire({
            icon: "error",
            title: "Error en la carga",
            text: err.message,
            confirmButtonColor: "#dc3545",
        });
    }

    // --- Init ---
    function _initDeepLink() {
        // Si el template inyectó un deep-link (porque la URL traía
        // ?inv=<id>&tab=<tabId>), navegamos al workspace de ese material.
        // Lo hacemos en el init, antes de que el usuario interactúe, para
        // que la página "aparezca" ya en el contexto correcto.
        const el = document.getElementById("inv-deeplink");
        if (!el) return;
        let dl;
        try {
            dl = JSON.parse(el.textContent);
        } catch (parseErr) {
            // Si el deep-link está malformado, simplemente no se navega
            // (no queremos romper la carga de la página por un JSON inválido).
            console.warn("[inv] deep-link JSON inválido:", parseErr?.message || parseErr);
            return;
        }
        if (!dl?.inv || !dl?.tab) return;
        // materialesDB se carga via inv-data (json_script) en el mismo
        // render del server, así que ya está disponible al ejecutar este
        // script. Pero poblarInfoMaterial y poblarWorkspace asumen que el
        // currentMaterial existe, así que las llamamos via irWorkspace.
        const inv = materialesDB.find((m) => String(m.inventarioId) === String(dl.inv));
        if (inv) {
            irWorkspace(dl.inv, dl.tab);
        } else {
            console.warn("[inv] deep-link apunta a inventarioId inexistente:", dl.inv);
        }
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => { _initDeepLink(); bind(); });
    } else {
        _initDeepLink();
        bind();
    }
})();
