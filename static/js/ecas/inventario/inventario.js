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
        const tbody = document.getElementById("inv-tablasHistorialBody");
        if (!tbody) return;
        const rows = [];
        comprasDB.forEach((c) => rows.push(filaHistorial(c, "compra")));
        ventasDB.forEach((v) => rows.push(filaHistorial(v, "venta")));
        tbody.innerHTML = rows.join("") || '<tr><td colspan="8" class="text-center text-muted py-3">Sin movimientos</td></tr>';
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
        const url = `/punto-eca/materiales/catalogo/buscar/?puntoId=${encodeURIComponent(puntoId)}`;
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
        const form = document.getElementById("inv-form-crear-inventario");
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.stockInicial = Number(payload.stockInicial);
        payload.capacidadMaxima = Number(payload.capacidadMaxima);
        payload.precioCompra = Number(payload.precioCompra);
        payload.precioVenta = Number(payload.precioVenta);
        payload.umbralAlerta = Number(payload.umbralAlerta);
        payload.umbralCritico = Number(payload.umbralCritico);
        payload.puntoId = Number(payload.puntoId);
        payload.materialId = Number(payload.materialId);

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

        // Cards → workspace
        document.querySelectorAll(".inv-tarjeta-material").forEach((card) => {
            const go = () => irWorkspace(card.dataset.invId, "tab-datos");
            card.querySelector(".inv-tarjeta")?.addEventListener("click", go);
            card.querySelector(".inv-tarjeta")?.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); }
            });
        });

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
        const invId = document.getElementById("inv-edit-inventario-id").value;
        const payload = {
            stockInicial: Number(document.getElementById("inv-edit-stock-inicial").value),
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

    // --- Init ---
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bind);
    } else {
        bind();
    }
})();
