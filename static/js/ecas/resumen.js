/* ============================================================
   RESUMEN PUNTO ECA - Lógica de cliente
   - Lee datos iniciales del <script type="application/json" id="resumen-data">
   - Re-pinta toda la UI desde un dict JS
   - Botón "Actualizar" hace fetch asíncrono a /punto-eca/resumen/data/
   ============================================================ */
(function () {
    "use strict";

    const DATA_URL = "/punto-eca/resumen/data/";
    const JSON_ID = "resumen-data";

    let _datos = null;

    /* ------------------------------ Helpers ------------------------------ */
    function getDatosIniciales() {
        const bloque = document.getElementById(JSON_ID);
        if (!bloque) return null;
        try {
            return JSON.parse(bloque.textContent.trim());
        } catch (e) {
            console.error("[resumen] No se pudo parsear el JSON inicial:", e);
            return null;
        }
    }

    function fmtNum(n, decimales = 2) {
        if (n === null || n === undefined || isNaN(n)) return "0";
        return Number(n).toLocaleString("es-CO", {
            minimumFractionDigits: decimales,
            maximumFractionDigits: decimales,
        });
    }

    function fmtInt(n) {
        if (n === null || n === undefined || isNaN(n)) return "0";
        return Number(n).toLocaleString("es-CO");
    }

    function fmtCOP(n) {
        if (n === null || n === undefined || isNaN(n) || n === 0) return "$0";
        return new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: "COP",
            maximumFractionDigits: 0,
        }).format(Number(n));
    }

    function fmtFecha(fecha) {
        if (!fecha || fecha === "N/A") return "N/A";
        try {
            const d = new Date(fecha);
            const hoy = new Date();
            hoy.setHours(0, 0, 0, 0);
            const dSolo = new Date(d);
            dSolo.setHours(0, 0, 0, 0);
            if (dSolo.getTime() === hoy.getTime()) {
                return d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
            }
            return d.toLocaleDateString("es-CO", {
                weekday: "short",
                day: "numeric",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch (e) {
            return fecha;
        }
    }

    function fmtFechaCorta(iso) {
        if (!iso) return "";
        try {
            const d = new Date(iso + "T00:00:00");
            return d.toLocaleDateString("es-CO", { weekday: "short", day: "numeric" });
        } catch (e) {
            return iso;
        }
    }

    function fmtHoraRelativa(iso) {
        if (!iso) return "";
        try {
            const d = new Date(iso);
            return d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
        } catch (e) {
            return "";
        }
    }

    function escapeHTML(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function pctClase(pct) {
        if (pct >= 80) return "kpi-progress-danger";
        if (pct >= 60) return "kpi-progress-warn";
        return "kpi-progress-ok";
    }

    function trendIcono(valor) {
        if (valor > 0) return '<i class="bi bi-arrow-up-short"></i>';
        if (valor < 0) return '<i class="bi bi-arrow-down-short"></i>';
        return '<i class="bi bi-dash"></i>';
    }

    function trendClase(valor) {
        if (valor > 0) return "kpi-trend-up";
        if (valor < 0) return "kpi-trend-down";
        return "kpi-trend-flat";
    }

    /* ------------------------------ Pintar: header ------------------------------ */
    function pintarHeader(d) {
        const salud = (d.saludPunto || "OK").toUpperCase();
        const saludEl = document.getElementById("resumenSaludBadge");
        if (saludEl) {
            saludEl.className = "salud-badge " + (
                salud === "CRITICO" ? "salud-badge-danger" :
                salud === "ATENCION" ? "salud-badge-warn" : "salud-badge-ok"
            );
            const icon = salud === "CRITICO" ? "bi-exclamation-octagon-fill" :
                         salud === "ATENCION" ? "bi-exclamation-triangle-fill" :
                         "bi-check-circle-fill";
            saludEl.innerHTML = `<i class="bi ${icon}"></i> ${salud === "OK" ? "Salud OK" : salud}`;
        }
        const updEl = document.getElementById("resumenUltimaActualizacion");
        if (updEl && d.ultimaActualizacion) {
            const dUpd = new Date(d.ultimaActualizacion);
            updEl.textContent = "Actualizado: " + dUpd.toLocaleTimeString("es-CO", {
                hour: "2-digit", minute: "2-digit"
            });
        }
    }

    /* ------------------------------ Pintar: KPIs ------------------------------ */
    function pintarKPI(d) {
        const capPct = Number(d.capacidadPorcentaje) || 0;
        const mesAnt = d.mesAnterior || {};

        // Inventario
        setKPI({
            id: "kpiInventario",
            label: "Inventario",
            value: fmtNum(d.inventarioTotal, 0) + " kg",
            sub: fmtNum(d.capacidadTotal, 0) + " kg capacidad",
            pct: capPct,
            pctLabel: capPct.toFixed(1) + "% de capacidad",
            icon: "bi-box-seam",
            iconClass: "bg-success bg-opacity-25 text-success",
            cardClass: "kpi-success",
            trend: null,
        });

        // Entradas
        setKPI({
            id: "kpiEntradas",
            label: "Entradas",
            value: fmtNum(d.entradasMes, 0) + " kg",
            sub: "Este mes",
            pct: null,
            icon: "bi-arrow-down-circle",
            iconClass: "bg-info bg-opacity-25 text-info",
            cardClass: "kpi-info",
            trend: {
                value: mesAnt.variacionEntradas,
                suffix: " vs mes anterior",
            },
        });

        // Salidas
        setKPI({
            id: "kpiSalidas",
            label: "Salidas",
            value: fmtNum(d.salidasMes, 0) + " kg",
            sub: "Este mes",
            pct: null,
            icon: "bi-arrow-up-circle",
            iconClass: "bg-warning bg-opacity-25 text-warning",
            cardClass: "kpi-warning",
            trend: {
                value: mesAnt.variacionSalidas,
                suffix: " vs mes anterior",
            },
        });

        // Balance neto
        const balance = Number(d.balanceNetoMes) || 0;
        const balanceClass = balance > 0 ? "kpi-success" : balance < 0 ? "kpi-danger" : "kpi-dark";
        setKPI({
            id: "kpiBalance",
            label: "Balance",
            value: (balance > 0 ? "+" : "") + fmtNum(balance, 0) + " kg",
            sub: fmtInt(d.transaccionesMes) + " operaciones",
            pct: null,
            icon: balance > 0 ? "bi-plus-circle" : balance < 0 ? "bi-dash-circle" : "bi-equals",
            iconClass: balance > 0
                ? "bg-success bg-opacity-25 text-success"
                : balance < 0
                ? "bg-danger bg-opacity-25 text-danger"
                : "bg-secondary bg-opacity-25 text-secondary",
            cardClass: balanceClass,
            trend: null,
        });

        // Materiales
        const criticos = Array.isArray(d.materialesCriticos) ? d.materialesCriticos.length : 0;
        const alertas = Array.isArray(d.materialesAlertas) ? d.materialesAlertas.length : 0;
        setKPI({
            id: "kpiMateriales",
            label: "Materiales",
            value: fmtInt(d.materialesCount),
            sub: "tipos diferentes",
            pct: null,
            icon: "bi-grid-3x3-gap",
            iconClass: "bg-primary bg-opacity-25 text-primary",
            cardClass: "kpi-primary",
            extra: `
                <div class="d-flex gap-2 mt-2">
                    <span class="badge bg-danger">${criticos} críticos</span>
                    <span class="badge bg-warning text-dark">${alertas} alertas</span>
                </div>
            `,
        });

        // Valor inventario
        setKPI({
            id: "kpiValor",
            label: "Valor inventario",
            value: fmtCOP(d.valorTotalInventario),
            sub: d.diasUltimoMovimiento !== null && d.diasUltimoMovimiento !== undefined
                ? "Última op: hace " + d.diasUltimoMovimiento + "d"
                : "Sin operaciones",
            pct: null,
            icon: "bi-cash-coin",
            iconClass: "bg-dark bg-opacity-25 text-dark",
            cardClass: "kpi-dark",
            trend: null,
        });
    }

    function setKPI(opts) {
        const root = document.getElementById(opts.id);
        if (!root) return;
        const trendHTML = opts.trend
            ? `<span class="kpi-trend ${trendClase(opts.trend.value)}">${trendIcono(opts.trend.value)}${Math.abs(opts.trend.value).toFixed(1)}%</span>`
            : "";
        const pctHTML = opts.pct !== null && opts.pct !== undefined
            ? `
                <div class="kpi-progress ${pctClase(opts.pct)} mt-2">
                    <div class="progress-bar" role="progressbar" style="width: ${Math.min(opts.pct, 100)}%"></div>
                </div>
                <small class="text-muted mt-1 d-block">${escapeHTML(opts.pctLabel || "")}</small>
            `
            : "";
        root.className = "kpi-card " + opts.cardClass;
        root.innerHTML = `
            <div class="p-3">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="min-w-0">
                        <div class="kpi-label">${opts.label}</div>
                        <div class="kpi-value">${opts.value}</div>
                        <div class="kpi-sub">${escapeHTML(opts.sub || "")}</div>
                        ${trendHTML}
                    </div>
                    <span class="kpi-icon-circle ${opts.iconClass}">
                        <i class="bi ${opts.icon}"></i>
                    </span>
                </div>
                ${pctHTML}
                ${opts.extra || ""}
            </div>
        `;
    }

    /* ------------------------------ Pintar: sparkline tendencia 7d ------------------------------ */
    function pintarTendencia(d) {
        const cont = document.getElementById("resumenTendencia");
        if (!cont) return;
        const serie = Array.isArray(d.tendenciaDiaria) ? d.tendenciaDiaria : [];
        if (serie.length === 0) {
            cont.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-bar-chart text-muted" style="font-size: 1.8rem;"></i>
                    <p class="text-muted small mt-2 mb-0">Sin datos de tendencia</p>
                </div>
            `;
            return;
        }
        const maxVal = Math.max(
            1,
            ...serie.flatMap(s => [Number(s.entradas) || 0, Number(s.salidas) || 0])
        );
        const diasHTML = serie.map((s, idx) => {
            const ent = Number(s.entradas) || 0;
            const sal = Number(s.salidas) || 0;
            const hEnt = Math.max(2, (ent / maxVal) * 70);
            const hSal = Math.max(2, (sal / maxVal) * 70);
            return `
                <div class="sparkline-day" title="${escapeHTML(fmtFechaCorta(s.fecha))}">
                    <div class="sparkline-bars">
                        <div class="sparkline-bar bar-entradas" style="height:${hEnt}px; animation-delay:${idx * 60}ms"></div>
                        <div class="sparkline-bar bar-salidas" style="height:${hSal}px; animation-delay:${idx * 60 + 30}ms"></div>
                    </div>
                    <div class="sparkline-day-value">${fmtInt(ent + sal)}</div>
                    <div class="sparkline-day-label">${escapeHTML(fmtFechaCorta(s.fecha).split(" ")[1] || fmtFechaCorta(s.fecha))}</div>
                </div>
            `;
        }).join("");
        cont.innerHTML = `
            <div class="sparkline-container">${diasHTML}</div>
            <div class="sparkline-legend">
                <span><span class="sparkline-legend-swatch" style="background: var(--resumen-success);"></span>Entradas</span>
                <span><span class="sparkline-legend-swatch" style="background: var(--resumen-warning);"></span>Salidas</span>
            </div>
        `;
    }

    /* ------------------------------ Pintar: top materiales ------------------------------ */
    function pintarTopMateriales(d) {
        const cont = document.getElementById("resumenTopMateriales");
        if (!cont) return;
        const items = Array.isArray(d.topMateriales) ? d.topMateriales : [];
        if (items.length === 0) {
            cont.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-trophy text-muted" style="font-size: 1.8rem;"></i>
                    <p class="text-muted small mt-2 mb-0">Sin movimientos este mes</p>
                </div>
            `;
            return;
        }
        cont.innerHTML = items.map((m, idx) => `
            <div class="top-material-item">
                <span class="top-material-rank">${idx + 1}</span>
                <span class="top-material-nombre" title="${escapeHTML(m.nombre)}">${escapeHTML(m.nombre)}</span>
                <div class="top-material-stats">
                    <div class="top-material-kg">${fmtNum(m.totalKg, 0)} kg</div>
                    <div class="top-material-movs">${fmtInt(m.movimientos)} ops</div>
                </div>
            </div>
        `).join("");
    }

    /* ------------------------------ Pintar: distribución por categoría ------------------------------ */
    function pintarCategorias(d) {
        const cont = document.getElementById("resumenCategorias");
        if (!cont) return;
        const cats = Array.isArray(d.categoriaBreakdown) ? d.categoriaBreakdown : [];
        if (cats.length === 0) {
            cont.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-pie-chart text-muted" style="font-size: 1.8rem;"></i>
                    <p class="text-muted small mt-2 mb-0">Sin categorías registradas</p>
                </div>
            `;
            return;
        }
        // Barra apilada horizontal: una sola fila con segmentos proporcionales
        const segmentos = cats.map((c, idx) => {
            const colorIdx = (idx % 6) + 1;
            const width = Math.max(c.porcentaje, 0);
            return `<div class="categoria-segment cat-color-${colorIdx}" style="width: ${width}%" title="${escapeHTML(c.nombre)}: ${c.porcentaje.toFixed(1)}%"></div>`;
        }).join("");
        // Leyenda en grid 2 columnas con dot + nombre + meta + porcentaje
        const legend = cats.map((c, idx) => {
            const colorIdx = (idx % 6) + 1;
            return `
                <div class="categoria-legend-item">
                    <span class="categoria-legend-dot cat-color-${colorIdx}"></span>
                    <div class="categoria-legend-info">
                        <div class="categoria-legend-nombre" title="${escapeHTML(c.nombre)}">${escapeHTML(c.nombre)}</div>
                        <div class="categoria-legend-meta">${fmtNum(c.kg, 0)} kg · ${c.items} it</div>
                    </div>
                    <span class="categoria-legend-pct">${c.porcentaje.toFixed(1)}%</span>
                </div>
            `;
        }).join("");
        cont.innerHTML = `
            <div class="categorias-stacked-bar">${segmentos}</div>
            <div class="categorias-legend">${legend}</div>
        `;
    }

    /* ------------------------------ Pintar: alertas ------------------------------ */
    function pintarAlertas(d) {
        const seccion = document.getElementById("seccionAlertas");
        const criticos = Array.isArray(d.materialesCriticos) ? d.materialesCriticos : [];
        const alertas = Array.isArray(d.materialesAlertas) ? d.materialesAlertas : [];
        if (!seccion) return;
        if (criticos.length === 0 && alertas.length === 0) {
            seccion.style.display = "none";
            return;
        }
        seccion.style.display = "block";
        const criticosHTML = criticos.length === 0
            ? '<p class="text-muted small mb-0"><i class="bi bi-check2-circle me-1"></i>Sin materiales críticos</p>'
            : criticos.map(m => `
                <div class="d-flex align-items-center justify-content-between p-2 mb-2 bg-danger bg-opacity-10 rounded">
                    <div class="min-w-0">
                        <strong class="text-danger d-block text-truncate">${escapeHTML(m.nombre)}</strong>
                        <small class="text-muted">${fmtNum(m.stock_actual, 1)} / ${fmtNum(m.capacidad_maxima, 1)} ${escapeHTML(m.unidad || "")}</small>
                    </div>
                    <span class="badge bg-danger flex-shrink-0 ms-2">${fmtNum(m.ocupacion, 0)}%</span>
                </div>
            `).join("");
        const alertasHTML = alertas.length === 0
            ? '<p class="text-muted small mb-0"><i class="bi bi-check2-circle me-1"></i>Sin alertas de stock</p>'
            : alertas.map(m => `
                <div class="d-flex align-items-center justify-content-between p-2 mb-2 bg-warning bg-opacity-10 rounded">
                    <div class="min-w-0">
                        <strong class="text-warning d-block text-truncate">${escapeHTML(m.nombre)}</strong>
                        <small class="text-muted">${fmtNum(m.stock_actual, 1)} / ${fmtNum(m.capacidad_maxima, 1)} ${escapeHTML(m.unidad || "")}</small>
                    </div>
                    <span class="badge bg-warning text-dark flex-shrink-0 ms-2">${fmtNum(m.ocupacion, 0)}%</span>
                </div>
            `).join("");
        const el1 = document.getElementById("materialesCriticosList");
        const el2 = document.getElementById("materialesAlertasList");
        if (el1) el1.innerHTML = criticosHTML;
        if (el2) el2.innerHTML = alertasHTML;
    }

    /* ------------------------------ Pintar: eventos ------------------------------ */
    function pintarEventos(d) {
        const cont = document.getElementById("proximosEventos");
        if (!cont) return;
        const eventos = Array.isArray(d.eventosProximos) ? d.eventosProximos : [];
        if (eventos.length === 0) {
            cont.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-calendar-x text-muted" style="font-size: 1.8rem;"></i>
                    <p class="text-muted small mt-2 mb-0">No hay eventos próximos</p>
                </div>
            `;
            return;
        }
        cont.innerHTML = '<div class="list-group list-group-flush">' + eventos.map((e, idx) => {
            const inicio = e.fecha_inicio ? new Date(e.fecha_inicio) : null;
            const fin = e.fecha_fin ? new Date(e.fecha_fin) : null;
            const fmtIni = inicio ? inicio.toLocaleDateString("es-CO", {
                weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
            }) : "Sin fecha";
            const borderClass = idx === 0 ? "" : "border-top";
            return `
                <div class="list-group-item ${borderClass} px-3 py-3">
                    <div class="d-flex align-items-start gap-3">
                        <div class="text-primary"><i class="bi bi-calendar-event" style="font-size: 1.2rem;"></i></div>
                        <div class="flex-grow-1 min-w-0">
                            <h6 class="mb-1 fw-bold text-dark text-truncate">${escapeHTML(e.titulo || "Evento")}</h6>
                            <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
                                <small class="text-muted"><i class="bi bi-clock me-1"></i>${fmtIni}</small>
                                <span class="badge bg-primary bg-opacity-25 text-primary small">${escapeHTML(e.tipo || "Único")}</span>
                            </div>
                            ${e.observaciones ? `<small class="text-muted d-block text-truncate">${escapeHTML(e.observaciones)}</small>` : ""}
                        </div>
                    </div>
                </div>
            `;
        }).join("") + "</div>";
    }

    /* ------------------------------ Pintar: centros (contact card) ------------------------------ */
    function pintarCentros(d) {
        const cont = document.getElementById("centrosAcopio");
        if (!cont) return;
        const centros = d.centrosAcopio || { propios: [], globales: [] };
        const propios = Array.isArray(centros.propios) ? centros.propios : [];
        const globales = Array.isArray(centros.globales) ? centros.globales : [];
        if (propios.length === 0 && globales.length === 0) {
            cont.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-geo-alt text-muted" style="font-size: 1.8rem;"></i>
                    <p class="text-muted small mt-2 mb-0">No hay centros asociados</p>
                </div>
            `;
            return;
        }
        cont.innerHTML =
            renderSeccionCentros("Propios", "bi-building", "contact-card-propios", propios) +
            renderSeccionCentros("Globales", "bi-globe-americas", "contact-card-globales", globales);
    }

    function renderSeccionCentros(titulo, icono, cardClass, lista) {
        if (lista.length === 0) return "";
        const cards = lista.map(c => renderContactCard(c, cardClass)).join("");
        return `
            <div class="contact-cards-section mb-3">
                <h6 class="contact-cards-section-title">
                    <i class="bi ${icono} me-1"></i>${escapeHTML(titulo)}
                    <span class="contact-cards-section-count">${lista.length}</span>
                </h6>
                <div class="contact-cards-grid">${cards}</div>
            </div>
        `;
    }

    function renderContactCard(c, variantClass) {
        const tipo = (c.tipo || "Centro").replace(/_/g, " ");
        const ubicacion = [c.ciudad, c.localidad].filter(Boolean).join(" · ");
        const direccionFull = [c.direccion, ubicacion].filter(Boolean).join(", ");
        const detalleDir = direccionFull
            ? `<div class="contact-card-detail"><i class="bi bi-geo-alt"></i><span>${escapeHTML(direccionFull)}</span></div>`
            : "";
        const detalleTel = c.celular
            ? `<div class="contact-card-detail"><i class="bi bi-telephone"></i><a href="tel:${escapeHTML(c.celular)}">${escapeHTML(c.celular)}</a></div>`
            : "";
        const detalleEmail = c.email
            ? `<div class="contact-card-detail"><i class="bi bi-envelope"></i><a href="mailto:${escapeHTML(c.email)}">${escapeHTML(c.email)}</a></div>`
            : "";
        const detalleHorario = c.horario
            ? `<div class="contact-card-detail"><i class="bi bi-clock"></i><span>${escapeHTML(c.horario)}</span></div>`
            : "";
        const detalleWeb = c.sitio_web
            ? `<div class="contact-card-detail"><i class="bi bi-globe"></i><a href="${escapeHTML(c.sitio_web)}" target="_blank" rel="noopener noreferrer">${escapeHTML(c.sitio_web.replace(/^https?:\/\//, ""))}</a></div>`
            : "";
        const descripcion = c.descripcion
            ? `<p class="contact-card-desc">${escapeHTML(c.descripcion)}</p>`
            : "";
        return `
            <div class="contact-card ${variantClass}">
                <div class="contact-card-header">
                    <div class="contact-card-icon"><i class="bi bi-building"></i></div>
                    <div class="contact-card-title">
                        <h6 title="${escapeHTML(c.nombre)}">${escapeHTML(c.nombre)}</h6>
                        <span class="contact-card-badge">${escapeHTML(tipo)}</span>
                    </div>
                </div>
                ${descripcion}
                <div class="contact-card-details">
                    ${detalleDir}${detalleTel}${detalleEmail}${detalleHorario}${detalleWeb}
                </div>
            </div>
        `;
    }

    /* ------------------------------ Pintar: info punto (compacto) ------------------------------ */
    function pintarInfoPunto(d) {
        const cont = document.getElementById("infoPuntoECA");
        if (!cont) return;
        const p = d.puntoEca || {};
        const g = d.gestor || {};
        if (!p.nombre && !g.nombre) {
            cont.innerHTML = `
                <div class="text-center py-3">
                    <i class="bi bi-info-circle text-muted" style="font-size: 1.6rem;"></i>
                    <p class="text-muted small mt-2 mb-0">Información no disponible</p>
                </div>
            `;
            return;
        }
        const nombreHTML = p.nombre
            ? `<h6 class="info-punto-nombre">${escapeHTML(p.nombre)}</h6>`
            : "";
        const direccionHTML = p.direccion
            ? `<div class="info-punto-line"><i class="bi bi-geo-alt"></i><span>${escapeHTML(p.direccion)}</span></div>`
            : "";
        const telefonoHTML = p.telefono
            ? `<div class="info-punto-line"><i class="bi bi-telephone"></i><a href="tel:${escapeHTML(p.telefono)}">${escapeHTML(p.telefono)}</a></div>`
            : "";
        const responsableHTML = g.nombre
            ? `<div class="info-punto-responsable">
                    <i class="bi bi-person-circle"></i>
                    <div>
                        <span class="info-punto-resp-nombre">${escapeHTML(g.nombre)}</span>
                        <span class="info-punto-resp-contacto">
                            ${g.celular ? `<a href="tel:${escapeHTML(g.celular)}" title="Llamar"><i class="bi bi-telephone"></i></a>` : ""}
                            ${g.email ? `<a href="mailto:${escapeHTML(g.email)}" title="Email"><i class="bi bi-envelope"></i></a>` : ""}
                        </span>
                    </div>
                </div>`
            : "";
        cont.innerHTML = `
            <div class="info-punto-compact">
                ${nombreHTML}
                <div class="info-punto-detalles">
                    ${direccionHTML}${telefonoHTML}
                    ${p.horario ? `<div class="info-punto-line info-punto-horario"><i class="bi bi-clock"></i><span>${escapeHTML(p.horario)}</span></div>` : ""}
                </div>
                ${responsableHTML}
            </div>
        `;
    }

    /* ------------------------------ Pintar: timeline de movimientos ------------------------------ */
    function pintarMovimientos(d) {
        const cont = document.getElementById("ultimosMovimientos");
        if (!cont) return;
        const movs = Array.isArray(d.movimientos) ? d.movimientos : [];
        if (movs.length === 0) {
            cont.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-inbox text-muted" style="font-size: 2rem;"></i>
                    <p class="text-muted small mt-2 mb-0">Sin movimientos registrados</p>
                </div>
            `;
            return;
        }
        cont.innerHTML = movs.map(mov => {
            const esSalida = (mov.tipo || "").toLowerCase() === "salida";
            const cls = esSalida ? "timeline-salida" : "";
            return `
                <div class="timeline-movimiento ${cls}">
                    <div class="mov-header">
                        <div class="mov-header-left">
                            <span class="mov-tipo ${esSalida ? 'text-warning' : 'text-success'}">${escapeHTML(mov.tipo || "")}</span>
                            <span class="mov-material text-truncate">${escapeHTML(mov.descripcion || "")}</span>
                        </div>
                        <span class="mov-cantidad">${fmtNum(mov.cantidad, 1)} kg</span>
                    </div>
                    <div class="mov-meta">
                        <i class="bi bi-person me-1"></i>${escapeHTML(mov.usuario || "Sistema")}
                        <span class="mx-1">·</span>
                        <i class="bi bi-clock me-1"></i>${escapeHTML(fmtFecha(mov.fecha))}
                    </div>
                </div>
            `;
        }).join("");
    }

    /* ------------------------------ Pintar todo ------------------------------ */
    function pintarTodo(d) {
        _datos = d;
        pintarHeader(d);
        pintarKPI(d);
        pintarTendencia(d);
        pintarTopMateriales(d);
        pintarCategorias(d);
        pintarAlertas(d);
        pintarEventos(d);
        pintarCentros(d);
        pintarInfoPunto(d);
        pintarMovimientos(d);
    }

    /* ------------------------------ Refrescar asíncrono ------------------------------ */
    async function refrescar() {
        const btn = document.getElementById("btnActualizarResumen");
        if (btn) btn.disabled = true;
        try {
            const resp = await fetch(DATA_URL, {
                method: "GET",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "same-origin",
            });
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();
            // Actualizar el bloque JSON para que un eventual reload del servidor tenga datos frescos
            const bloque = document.getElementById(JSON_ID);
            if (bloque) bloque.textContent = JSON.stringify(data);
            pintarTodo(data);
        } catch (e) {
            console.error("[resumen] Error refrescando:", e);
            if (window.Swal) {
                Swal.fire({
                    icon: "error",
                    title: "No se pudo actualizar",
                    text: "Inténtalo de nuevo en unos segundos.",
                    timer: 2500,
                    showConfirmButton: false,
                });
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    /* ------------------------------ Init ------------------------------ */
    function init() {
        const datos = getDatosIniciales();
        if (!datos) return;
        pintarTodo(datos);

        const btn = document.getElementById("btnActualizarResumen");
        if (btn) btn.addEventListener("click", refrescar);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    // Exponer para depuración
    window.__resumen = { refrescar, get datos() { return _datos; } };
})();
