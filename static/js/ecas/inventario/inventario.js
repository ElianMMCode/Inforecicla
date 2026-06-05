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

    // --- Helpers de formato ---
    const formatCOP = (n) => "$ " + Number(n || 0).toLocaleString("es-CO");
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
        poblarWorkspace(inv);
        document.getElementById("estado-landing")?.classList.remove("active");
        document.getElementById("estado-workspace")?.classList.add("active");
        if (tabId) activarTab(tabId);
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
    }

    function activarTab(tabId) {
        document.querySelectorAll("#workspaceTabs .nav-link").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-pane-stack").forEach((p) => p.classList.remove("active"));
        const btn = document.querySelector(`#workspaceTabs [data-tab="${tabId}"]`);
        const pane = document.getElementById(tabId);
        if (btn) btn.classList.add("active");
        if (pane) pane.classList.add("active");
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
    function filaHistorial(mov, tipo) {
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
        return `<tr>
            <td class="small">${escapeHtml(fecha)}</td>
            <td>${tipoBadge}</td>
            <td class="small">${escapeHtml(material)}</td>
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
        const tbody = document.getElementById("tablasHistorialBody");
        if (!tbody) return;
        const rows = [];
        comprasDB.filter((c) => String(c.inventarioId) === String(invId)).forEach((c) => rows.push(filaHistorial(c, "compra")));
        ventasDB.filter((v) => String(v.inventarioId) === String(invId)).forEach((v) => rows.push(filaHistorial(v, "venta")));
        tbody.innerHTML = rows.join("") || '<tr><td colspan="8" class="text-center text-muted py-3">Sin movimientos</td></tr>';
        const p = document.getElementById("paginacionHistorial");
        if (p) p.textContent = `${rows.length} movimientos`;
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
    // EVENT LISTENERS (delegación + específicos)
    // ============================================================
    function bind() {
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

        // Acciones en tablas (delegado)
        ["inv-tablasHistorialBody", "tablasHistorialBody", "tablasEntradasBody", "tablasSalidasBody"]
            .forEach((tbodyId) => {
                document.getElementById(tbodyId)?.addEventListener("click", (e) => {
                    const btn = e.target.closest("button[data-accion]");
                    if (!btn) return;
                    const id = btn.dataset.id;
                    const tipo = btn.dataset.tipo;
                    if (btn.dataset.accion === "ver") verMovimiento(tipo, id);
                    if (btn.dataset.accion === "editar") editarMovimiento(tipo, id);
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
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.cantidad = Number(payload.cantidad);
        payload.precioCompra = Number(payload.precioCompra);
        payload.inventarioId = payload.inventarioId;
        payload.puntoId = Number(payload.puntoId);
        fetch("/punto-eca/movimientos/registrar-compra/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || d?.message || "Error al registrar");
                Swal.fire({ icon: "success", title: "Compra registrada", text: d.mensaje || "Operación exitosa", timer: 1500, showConfirmButton: false });
                setTimeout(() => window.location.reload(), 1500);
            })
            .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
    }
    function submitSalida(e) {
        if (e) e.preventDefault();
        const form = document.getElementById("formSalida");
        if (!form.checkValidity()) { form.reportValidity(); return; }
        const centro = document.getElementById("formSalidaCentro");
        if (centro && !centro.value) { centro.reportValidity(); return; }
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.cantidad = Number(payload.cantidad);
        payload.precioVenta = Number(payload.precioVenta);
        payload.centroAcopioId = payload.centroAcopioId;
        payload.puntoId = Number(payload.puntoId);
        fetch("/punto-eca/movimientos/registrar-venta/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(payload),
        })
            .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
            .then(({ ok, d }) => {
                if (!ok) throw new Error(d?.mensaje || d?.message || "Error al registrar");
                Swal.fire({ icon: "success", title: "Venta registrada", text: d.mensaje || "Operación exitosa", timer: 1500, showConfirmButton: false });
                setTimeout(() => window.location.reload(), 1500);
            })
            .catch((err) => Swal.fire({ icon: "error", title: "Error", text: err.message }));
    }

    // ============================================================
    // SUBMIT: EDITAR COMPRA / VENTA (modales)
    // ============================================================
    function submitEditarCompra() {
        const form = document.getElementById("inv-form-editar-compra");
        if (!form.checkValidity()) { form.reportValidity(); return; }
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.cantidad = Number(payload.cantidad);
        payload.precioCompra = Number(payload.precioCompra);
        fetch(`/punto-eca/movimientos/editar-compra/${payload.id}/`, {
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
    }
    function submitEditarVenta() {
        const form = document.getElementById("inv-form-editar-venta");
        if (!form.checkValidity()) { form.reportValidity(); return; }
        const centro = document.getElementById("inv-edit-venta-centro");
        if (centro && !centro.value) { centro.reportValidity(); return; }
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.cantidad = Number(payload.cantidad);
        payload.precioVenta = Number(payload.precioVenta);
        fetch(`/punto-eca/movimientos/editar-venta/${payload.id}/`, {
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
        const materialId = document.getElementById("inv-hfiltro-material")?.value;
        const materialNombre = _lookupMaterialNombreByInventarioId(materialId);
        const categoria = document.getElementById("inv-hfiltro-categoria")?.value;
        const tipoMaterial = document.getElementById("inv-hfiltro-tipo-material")?.value;
        const tipo = document.getElementById("inv-hfiltro-tipo")?.value;
        const desde = document.getElementById("inv-hfiltro-desde")?.value;
        const hasta = document.getElementById("inv-hfiltro-hasta")?.value;
        const centro = document.getElementById("inv-hfiltro-centro")?.value;
        const cantidadMin = document.getElementById("inv-hfiltro-cantidad-min")?.value;
        const cantidadMax = document.getElementById("inv-hfiltro-cantidad-max")?.value;
        const montoMin = document.getElementById("inv-hfiltro-monto-min")?.value;
        const montoMax = document.getElementById("inv-hfiltro-monto-max")?.value;
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
        const materialId = document.getElementById("inv-hfiltro-material")?.value || "";
        const categoria = document.getElementById("inv-hfiltro-categoria")?.value || "";
        const tipoMaterial = document.getElementById("inv-hfiltro-tipo-material")?.value || "";
        const tipo = document.getElementById("inv-hfiltro-tipo")?.value || "";
        const desde = document.getElementById("inv-hfiltro-desde")?.value;
        const hasta = document.getElementById("inv-hfiltro-hasta")?.value;
        const centro = document.getElementById("inv-hfiltro-centro")?.value || "";
        const cantidadMin = parseFloat(document.getElementById("inv-hfiltro-cantidad-min")?.value);
        const cantidadMax = parseFloat(document.getElementById("inv-hfiltro-cantidad-max")?.value);
        const montoMin = parseFloat(document.getElementById("inv-hfiltro-monto-min")?.value);
        const montoMax = parseFloat(document.getElementById("inv-hfiltro-monto-max")?.value);
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
                if (materialId && String(c.inventarioId) !== String(materialId)) return;
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
                if (materialId && String(v.inventarioId) !== String(materialId)) return;
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

    function _poblarCentrosAcopio() {
        const sel = document.getElementById("inv-hfiltro-centro");
        if (!sel) return;
        const nombres = new Set();
        ventasDB.forEach((v) => {
            if (v.nombreCentroAcopio) nombres.add(v.nombreCentroAcopio);
        });
        const opts = ['<option value="">—</option>']
            .concat(Array.from(nombres).sort().map((n) => `<option value="${escapeHtml(n)}">${escapeHtml(n)}</option>`));
        sel.innerHTML = opts.join("");
    }

    function _toggleCentroAcopioLock() {
        const tipo = document.getElementById("inv-hfiltro-tipo")?.value;
        const sel = document.getElementById("inv-hfiltro-centro");
        if (!sel) return;
        const enabled = tipo === "venta";
        sel.disabled = !enabled;
        if (!enabled) sel.value = "";
    }

    function renderPager(total, current) {
        const pager = document.getElementById("inv-hpager");
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
        const tbody = document.getElementById("inv-tablasHistorialBody");
        const footer = document.getElementById("inv-hfooter-count");
        const badge = document.getElementById("inv-hbadge-count");
        if (!tbody) return;
        const rows = getCurrentHistorialRows();
        const total = rows.length;
        const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
        if (historialPage > pages) historialPage = pages;
        const start = (historialPage - 1) * PAGE_SIZE;
        const slice = rows.slice(start, start + PAGE_SIZE);
        if (slice.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">Sin movimientos con los filtros aplicados</td></tr>';
        } else {
            tbody.innerHTML = slice.map((r) => filaHistorial(r, r._tipo)).join("");
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
            const el = document.getElementById(id);
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

    function renderChart(canvasId, materiales, gran, mostrarCap) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const W = canvas.clientWidth || 600;
        const H = canvas.clientHeight || 300;
        canvas.width = W * (window.devicePixelRatio || 1);
        canvas.height = H * (window.devicePixelRatio || 1);
        ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        ctx.clearRect(0, 0, W, H);
        if (!materiales.length) {
            ctx.fillStyle = "#6c757d";
            ctx.font = "14px system-ui, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("Selecciona al menos un material.", W / 2, H / 2);
            return;
        }
        const hoy = new Date();
        const inicioMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
        const desde = inicioMes;
        const hasta = hoy;
        const buckets = generarBuckets(desde, hasta, gran);
        const labels = buckets.map((b) => formatearLabelBucket(b, gran));
        const series = materiales.map((m) => ({
            nombre: m.nombre,
            color: PALETA[materiales.indexOf(m) % PALETA.length],
            valores: construirSerieMaterial(m, comprasDB, ventasDB, desde, hasta, gran),
            capacidad: Number(m.capacidadMaxima) || 0,
        }));
        // Calcular rango Y
        let maxY = 0;
        series.forEach((s) => s.valores.forEach((v) => { if (v > maxY) maxY = v; }));
        if (mostrarCap) series.forEach((s) => { if (s.capacidad > maxY) maxY = s.capacidad; });
        if (maxY === 0) maxY = 1;
        const padL = 50, padR = 10, padT = 10, padB = 30;
        const innerW = W - padL - padR;
        const innerH = H - padT - padB;
        // Grid
        ctx.strokeStyle = "#e9ecef";
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padT + (innerH * i) / 4;
            ctx.beginPath();
            ctx.moveTo(padL, y);
            ctx.lineTo(W - padR, y);
            ctx.stroke();
            ctx.fillStyle = "#6c757d";
            ctx.font = "10px system-ui, sans-serif";
            ctx.textAlign = "right";
            const val = maxY - (maxY * i) / 4;
            ctx.fillText(val.toFixed(0), padL - 4, y + 3);
        }
        // Eje X labels (samplear)
        const stepX = Math.max(1, Math.floor(labels.length / 8));
        ctx.fillStyle = "#6c757d";
        ctx.textAlign = "center";
        labels.forEach((lbl, i) => {
            if (i % stepX === 0) {
                const x = padL + (innerW * i) / Math.max(1, buckets.length - 1);
                ctx.fillText(lbl, x, H - 10);
            }
        });
        // Líneas
        const xAt = (i) => padL + (innerW * i) / Math.max(1, buckets.length - 1);
        const yAt = (v) => padT + innerH - (innerH * v) / maxY;
        series.forEach((s) => {
            // Capacidad (línea punteada)
            if (mostrarCap && s.capacidad > 0) {
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
        const ly = padT + 12;
        series.forEach((s) => {
            const txt = s.nombre;
            const tw = ctx.measureText(txt).width + 16;
            ctx.fillStyle = s.color;
            ctx.fillRect(lx, ly - 8, 10, 10);
            ctx.fillStyle = "#212529";
            ctx.fillText(txt, lx + 14, ly);
            lx += tw;
            if (lx > W - 60) return;
        });
    }

    function renderOvtabChart() {
        const checks = document.querySelectorAll('#inv-flujo-materiales-list input[type="checkbox"]:checked');
        const ids = Array.from(checks).map((c) => c.value);
        const mats = materialesDB.filter((m) => ids.includes(String(m.inventarioId)));
        const gran = document.getElementById("inv-flujo-granularidad")?.value || "dia";
        const cap = document.getElementById("inv-flujo-cap")?.checked;
        renderChart("inv-stock-time-chart", mats, gran, cap);
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
    function renderWsChart() {
        if (!currentMaterial) return;
        const gran = "dia";
        renderChart("stockTimeChart", [currentMaterial], gran, true);
        const invId = currentMaterial.inventarioId;
        const cm = comprasDB.filter((c) => String(c.inventarioId) === String(invId));
        const vm = ventasDB.filter((v) => String(v.inventarioId) === String(invId));
        const setKpi = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        setKpi("inv-ws-flujo-stock", `${Number(currentMaterial.stockActual).toLocaleString("es-CO")} ${currentMaterial.unidad}`);
        setKpi("inv-ws-flujo-movs", cm.length + vm.length);
        setKpi("inv-ws-flujo-compras", cm.length);
        setKpi("inv-ws-flujo-ventas", vm.length);
    }

    function renderFlujoMaterialesList() {
        const cont = document.getElementById("inv-flujo-materiales-list");
        if (!cont) return;
        cont.innerHTML = materialesDB.map((m, i) => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${escapeHtml(m.inventarioId)}" id="inv-flujo-mat-${i}" checked>
                <label class="form-check-label small" for="inv-flujo-mat-${i}">
                    <span style="display:inline-block;width:10px;height:10px;background:${PALETA[i % PALETA.length]};border-radius:2px;margin-right:4px"></span>
                    ${escapeHtml(m.nombre)}
                </label>
            </div>
        `).join("") || '<small class="text-muted">No hay materiales en el inventario.</small>';
        cont.querySelectorAll('input[type="checkbox"]').forEach((cb) => cb.addEventListener("change", renderOvtabChart));
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

        // Exportar historial con filtros
        document.getElementById("btnExportHistorialExcel")?.addEventListener("click", exportarHistorialExcel);
        document.getElementById("btnExportHistorialPdf")?.addEventListener("click", exportarHistorialPdf);
        // Exportar historial general desde ovtab (nuevos botones con ID)
        document.getElementById("inv-btn-export-historial-excel")?.addEventListener("click", exportarHistorialExcel);
        document.getElementById("inv-btn-export-historial-pdf")?.addEventListener("click", exportarHistorialPdf);

        // Filtros historial
        document.getElementById("inv-hfiltro-aplicar")?.addEventListener("click", aplicarFiltrosHistorial);
        document.getElementById("inv-hfiltro-limpiar")?.addEventListener("click", limpiarFiltrosHistorial);
        // Centro de acopio se habilita sólo si tipo=venta
        document.getElementById("inv-hfiltro-tipo")?.addEventListener("change", _toggleCentroAcopioLock);

        // Chart ovtab
        document.getElementById("inv-flujo-aplicar")?.addEventListener("click", renderOvtabChart);
        document.getElementById("inv-flujo-granularidad")?.addEventListener("change", renderOvtabChart);
        document.getElementById("inv-flujo-cap")?.addEventListener("change", renderOvtabChart);
        document.getElementById("inv-flujo-todos")?.addEventListener("click", () => {
            document.querySelectorAll('#inv-flujo-materiales-list input[type="checkbox"]').forEach((c) => { c.checked = true; });
            renderOvtabChart();
        });
        document.getElementById("inv-flujo-ninguno")?.addEventListener("click", () => {
            document.querySelectorAll('#inv-flujo-materiales-list input[type="checkbox"]').forEach((c) => { c.checked = false; });
            renderOvtabChart();
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

    // --- Init ---
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bind);
    } else {
        bind();
    }
})();
