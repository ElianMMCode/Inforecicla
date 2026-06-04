# Plan Detallado — Refactor `Inventario` en Punto ECA

> **Documento vivo**: registro exhaustivo del plan acordado entre el usuario y el asistente.
> Cualquier desviación debe consultarse primero con el usuario.

---

## 1. Contexto y objetivo

### 1.1 Negocio
InfoRecicla es una plataforma Django 6.0.2 + Python 3.14 + PostgreSQL + Channels (Redis) para gestión
de Centros de Acopio (ECA). Ver `README.md` y `AGENTS.md` para contexto del repo.

### 1.2 Objetivo
Unificar las secciones **Materiales** y **Movimientos** del Punto ECA en una única sección
llamada **Inventario**, accesible desde la ruta `/inventario/`. Las rutas viejas
`/materiales/` y `/movimientos/` deben devolver 404 duro. La implementación se inspira en un
mockup estático validado visualmente con el usuario.

### 1.3 Estado de la conversación (resumen ejecutivo)
- Se construyó un mockup HTML autocontenido (CDN: Bootstrap 5, Bootstrap Icons, jQuery, Chart.js,
  SweetAlert2) en la raíz del proyecto: **`mockup-inventario.html`** (renombrado a
  `mockup-inventario-golden.html` durante Fase 0).
- El mockup cubre 5 tabs en "Otras vistas" (Inventario · Buscar/Crear · Historial General ·
  Flujo de Stock · Carga Masiva) y un workspace con 5 tabs (Datos · Compra · Venta · Historial ·
  Flujo).
- 8 modales: Picker, Editar Inventario, Eliminar, Bulk, Detalle Compra, Detalle Venta,
  Editar Compra, Editar Venta.
- Todas las decisiones de UX/UI fueron validadas visualmente con capturas headless de Chromium.
- Servidor local de revisión: `python3 -m http.server 8765 --bind 127.0.0.1`.

---

## 2. Decisiones cerradas (inmutables salvo acuerdo explícito)

| # | Decisión | Detalle |
|---|----------|---------|
| D1 | Alcance del flujo | Por material seleccionado (no global). |
| D2 | URLs | Una sola ruta nueva `/inventario/`; **404 duro** para `/materiales/` y `/movimientos/`. |
| D3 | JS tests | No se escriben tests JS; solo tests Django. |
| D4 | Context bar | No sticky, header normal. |
| D5 | Bulk import | Solo en landing (tab `ovtab-carga-masiva`). |
| D6 | Tabs de "Otras vistas" | 5: Inventario · Buscar/Crear · Historial General · Flujo de Stock · Carga Masiva. |
| D7 | Sidebar | Un único dropdown "Inventario" con 7 sub-ítems. |
| D8 | Tabs de workspace | 5: Datos · Compra · Venta · Historial · Flujo. |
| D9 | Form de creación de inventario | **Inline** en tab `ovtab-buscar` (no en modal). El modal picker abre primero; al seleccionar material, se activa la tab y se muestra el form. |
| D10 | Picker | **Todos** los items (en inventario o no) abren el form. Match exacto con producción (`section-materiales.html:586-622`). |
| D11 | ECA NUNCA crea materiales | Campo "Material" en forms de creación **siempre readonly**. |
| D12 | Cards de inventario | Toda la tarjeta clickeable (sin botones "Ver"/"Operar" separados). |
| D13 | Modales eliminados | "Ver Hoja Técnica" legacy y `modalDetalles` eliminados del mockup (no se portan). |
| D14 | Filtros cards inventario | Funcionales: nombre, categoría, tipo, estado (OK/Alerta/Crítico), ocupación (rangos 0-15, 15-40, 40-70, 70-100). |
| D15 | Banner mockup | Indica: "Click en cualquier tarjeta del inventario para entrar al workspace". |
| D16 | Modales separados por tipo | Historial: 4 modales (Detalle Compra, Detalle Venta, Editar Compra, Editar Venta) — match `section-movimientos.html:1522-1962`. |
| D17 | Orden botones en card-footer | "Editar" antes de "Eliminar". |
| D18 | KPI compactos | 3 bloques en una sola fila: Estado Físico y Capacidad (verde) · Salud del Inventario (rojo) · Resumen Financiero (amarillo). Menos de 1/4 de pantalla. |
| D19 | Snapshot strategy | `snapshot-pre-inventario/` con espejo de path + `mockup-inventario-golden.html` renombrado. |
| D20 | Template de producción | Limpio, inspirado en mockup, con `{% static %}` (no CDNs). |
| D21 | Chart de stock | **Portar** lógica de `static/js/ecas/movimientos/stock-chart.js` a `inventario.js` (no añadir Chart.js como dependencia). |
| D22 | Forms Compra/Venta | Dentro del workspace (tabs `tab-compra` y `tab-venta`). |
| D23 | Hash deep-linking | Helper de testing en mockup. **NO se porta a producción.** |

### 2.1 IDs de inputs/elementos a preservar (mocks con mismo shape)

Estos IDs ya están en el mockup y deben portarse al template de producción (o mapearse 1:1):

- Forms: `formEntrada`, `formSalida`
- Tablas: `tablasEntradasBody`, `tablasSalidasBody`, `tablasHistorialBody`
- Charts: `stockTimeChart`
- Modales: `modalCargaMasiva`
- Filtros: `filtroCompra*`, `filtroVenta*`, `filtroHistorial*`
- Botones export: `btnExport*`
- Badges: `badge*Count`
- Paginación: `paginacion*`

### 2.2 Constantes / settings

- `AUTH_USER_MODEL = "users.Usuario"` (no `User`).
- `UnidadMedida` en `config/constants.py:102-106`: KG, UN, TON, MC.
- Locale `es-co`, TZ `America/Bogota`. Tests y vistas con fechas tz-aware.
- Límite de uploads: 5 MB imágenes, 12 MB datos (`settings.py:188-189`).
- Sanitización XSS: escapar siempre con `django.utils.html.escape` (auditado por SonarCloud).

---

## 3. Estado actual (post-mockup, pre-implementación)

### 3.1 Mockup dorado
- **`mockup-inventario.html`** en raíz del proyecto, 2694 líneas.
- Validado con `node -e "new Function(script)"` (0 errores de sintaxis).
- Screenshots de verificación guardados en `/tmp/` (no commiteados): detalle-compra, detalle-venta,
  editar-compra, editar-venta, cada uno con y sin datos.
- Server local: `python3 -m http.server 8765 --bind 127.0.0.1`.

### 3.2 Producción sin tocar
| Archivo | Líneas | Hash snapshot |
|---------|-------:|--------------|
| `templates/ecas/section-materiales.html` | 2237 | por crear en Fase 0 |
| `templates/ecas/section-movimientos.html` | 1967 | por crear en Fase 0 |
| `templates/ecas/partials/sidebar.html` | 84 | por crear en Fase 0 |
| `templates/ecas/puntoECA-layout.html` | 84 | por crear en Fase 0 |
| `static/js/ecas/movimientos/movimientos.js` | 3451 | por crear en Fase 0 |
| `static/js/ecas/movimientos/stock-chart.js` | 892 | por crear en Fase 0 |
| `static/css/ecas/movimientos.css` | 69 | por crear en Fase 0 |
| `static/css/sidebar.css` | 122 | por crear en Fase 0 |
| `apps/ecas/views.py` | 659 | por crear en Fase 0 |
| `apps/ecas/urls.py` | 67 | por crear en Fase 0 |
| `apps/ecas/constants.py` | 19 | por crear en Fase 0 |
| `apps/inventory/views.py` | 248 | por crear en Fase 0 |
| `apps/inventory/urls.py` | 39 | por crear en Fase 0 |
| `apps/operations/views.py` | 893+ | por crear en Fase 0 |
| `apps/operations/urls.py` | 79 | por crear en Fase 0 |

Total: ~8.1k líneas de producción, intactas hasta Fase 7.

### 3.3 Datos del mockup (referencia visual, no se copian a producción)

```js
// Catálogo (14 items, 6 en inventario, 8 fuera)
const catalogo = [
  { materialId: 1, nmbMaterial: 'Plástico PET', dscMaterial: 'Botellas PET',
    nmbTipo: 'Reciclable', nmbCategoria: 'Plásticos', unidad: 'kg',
    imagenUrl: '...', enInventario: true },
  { materialId: 2, nmbMaterial: 'Cartón Corrugado', ... },
  // 12 más
];
```

```js
// 6 cards de inventario
const inventarios = [
  { inventarioId: 1, materialId: 1, nmbMaterial: 'Plástico PET',
    stockActual: 950, capacidadMaxima: 1000, ocupacion: 95,
    estado: 'OK', precioCompra: 850, precioVenta: 1200, ... },
  // 5 más
];
```

```js
// Movimientos en historial general
const movimientos = [
  { id: 1001, tipo: 'compra', material: 'Plástico PET', fecha: '2026-06-02T10:32',
    cantidad: 200, unidad: 'kg', precio: 850, total: 170000, ... },
  // 4 más
];
```

---

## 4. Archivos en alcance (paths exactos)

### 4.1 Frontend a crear
- `templates/ecas/section-inventario.html` (nuevo)
- `static/js/ecas/inventario/inventario.js` (nuevo)
- `static/css/ecas/inventario/inventario.css` (nuevo)

### 4.2 Frontend a modificar
- `templates/ecas/partials/sidebar.html`
- `static/css/sidebar.css` (solo si hace falta ajustar anchos)

### 4.3 Backend a modificar
- `apps/ecas/views.py` (agregar `_build_inventario_context`, eliminar ramas viejas en Fase 7)
- `apps/ecas/urls.py` (agregar `inventario/`, hacer 404 las viejas en Fase 6)
- `apps/ecas/constants.py` (agregar `"inventario"`, eliminar `"detalles_materiales"` huérfano)

### 4.4 Backend NO a modificar (consumido por AJAX)
- `apps/inventory/views.py` — todos los endpoints se mantienen con misma firma
- `apps/inventory/urls.py` — sin cambios
- `apps/operations/views.py` — sin cambios (Fase 7 elimina `_build_movimientos_context` ya que nadie lo usa)
- `apps/operations/urls.py` — sin cambios

### 4.5 Tests a crear
- `apps/inventory/tests/test_inventario_endpoints.py` (nuevo)
- `apps/operations/tests/test_movimientos_endpoints.py` (nuevo)

### 4.6 Frontend a eliminar (Fase 7)
- `templates/ecas/section-materiales.html`
- `templates/ecas/section-movimientos.html`
- `static/js/ecas/movimientos/movimientos.js`
- `static/js/ecas/movimientos/stock-chart.js`
- `static/css/ecas/movimientos.css`

---

## 5. Plan por fases

### **Fase 0 — Snapshot y preparación** (read-mostly)

**Objetivo**: blindar la foto del estado actual antes de cualquier cambio.

1. **Crear estructura espejo** en `snapshot-pre-inventario/`:
   ```
   snapshot-pre-inventario/
   ├── templates/ecas/section-materiales.html
   ├── templates/ecas/section-movimientos.html
   ├── templates/ecas/partials/sidebar.html
   ├── templates/ecas/puntoECA-layout.html
   ├── static/js/ecas/movimientos/movimientos.js
   ├── static/js/ecas/movimientos/stock-chart.js
   ├── static/css/ecas/movimientos.css
   ├── static/css/sidebar.css
   ├── apps/ecas/views.py
   ├── apps/ecas/urls.py
   ├── apps/ecas/constants.py
   ├── apps/inventory/views.py
   ├── apps/inventory/urls.py
   ├── apps/operations/views.py
   └── apps/operations/urls.py
   ```
   Los archivos se copian con `git show HEAD:<path> > snapshot-pre-inventario/<path>` (o
   `cp` simple, ya que están en disco y tracked por git).

2. **Renombrar mockup**:
   - `git mv mockup-inventario.html mockup-inventario-golden.html`
   - Crear stub `mockup-inventario.html` con redirect/comentario al golden.

3. **Commit**: `chore: snapshot pre-fase-inventario`.

4. **Verificación Fase 0**:
   - `python manage.py test` → verde (no debiera romperse nada).
   - `diff snapshot-pre-inventario/templates/ecas/section-materiales.html templates/ecas/section-materiales.html` → 0 diferencias.

---

### **Fase 1 — Backend: agregar nueva sección (sin tocar viejas)**

**Objetivo**: tener la ruta `/inventario/` operativa sirviendo una versión inicial (mínima) del template, mientras la app vieja sigue viva.

1. **`apps/ecas/constants.py`**:
   - Agregar `"inventario": "ecas/section-inventario.html"`.
   - **Eliminar** la entrada huérfana `"detalles_materiales": "ecas/section-detalles-materiales.html"`.
     Verificar primero con `grep -r "detalles_materiales" apps/ templates/ static/`.

2. **`apps/ecas/urls.py`**:
   - Agregar:
     ```python
     path("inventario/", render_seccion, {"seccion": "inventario"}, name="inventario"),
     ```
   - **No tocar** las rutas viejas `/materiales/` y `/movimientos/`.

3. **`apps/ecas/views.py`**:
   - En `render_seccion` (línea 118), agregar rama:
     ```python
     elif seccion == "inventario":
         context = _build_inventario_context(punto)
     ```
   - Crear función `_build_inventario_context(punto)` que retorna:
     ```python
     {
         "punto": punto,
         "seccion": "inventario",
         "section_template": SECTION_TEMPLATES["inventario"],
         # Datos consolidados (mismos que producía _build_materiales_context hoy)
         "materiales_inventario": [...],
         "total_stock": ...,
         "total_capacidad": ...,
         "total_ok": ...,
         "total_alerta": ...,
         "total_critico": ...,
         "ocupacion_porcentaje": ...,
         "categoria_inventario": [...],
         "tipo_inventario": [...],
         "material_mayor_ocupacion": ...,
         "material_mas_caro": ...,
         "material_mas_barato": ...,
         "costo_total_inventario": ...,
         "materiales_criticos": [...],
         "unidades_medida": cons.UnidadMedida.choices,
         # Datos de movimientos (mismos que producía _build_movimientos_context)
         # (importar selectivamente lo necesario)
     }
     ```
   - Reutilizar funciones internas de `apps/inventory/views.py` y `apps/operations/views.py`
     mediante import o reescritura local. Preferir **reescritura local** en `apps/ecas/views.py`
     para no acoplar el módulo.

4. **Verificación Fase 1**:
   - `python manage.py check` → 0 issues.
   - `python manage.py test` → verde.
   - Login manual en dev server, navegar a `/inventario/` → 200 OK con template (aunque sea
     placeholder).

---

### **Fase 2 — Template limpio `section-inventario.html`**

**Objetivo**: crear el template de producción basado en el mockup.

1. **Estructura del template**:
   - Bloque `<section>` con el contenido visual del mockup.
   - 5 tabs "Otras vistas" como `nav nav-tabs` (Bootstrap 5, no accordion).
   - 5 tabs workspace como `nav nav-tabs` (oculto hasta que se selecciona material).
   - **Inline form** en `ovtab-buscar` (no modal).
   - 4 modales propios: `modalPickerResultados`, `modalEditarInventario`, `modalEliminar`,
     `modalCargaMasiva`.
   - 4 modales portados de `section-movimientos.html:1522-1962`:
     `modalDetalleCompra`, `modalDetalleVenta`, `modalEditarCompra`, `modalEditarVenta`.
   - Renombrar IDs con prefijo `inv-` para evitar colisiones con otros templates cargados
     (ej. `inv-filtroCompraMaterial`, `inv-stockTimeChart`).
   - Mantener compatibilidad con IDs definidos en §2.1.

2. **Incluir assets al final**:
   ```html
   <link rel="stylesheet" href="{% static 'css/ecas/inventario/inventario.css' %}">
   <script src="{% static 'js/ecas/inventario/inventario.js' %}"></script>
   ```
   (Chart.js NO se incluye — se portará la lógica de `stock-chart.js`.)

3. **Reglas XSS**: escapar todo `{{ var }}` con `|escape` o usar `{% autoescape on %}`.

4. **Verificación Fase 2**:
   - `python manage.py runserver` → login → `/inventario/` → render correcto de las 5 tabs.
   - Click en una card → workspace renderiza con los 5 tabs.
   - Botón "Ver" en historial → modal detalle abre con datos.
   - Botón "Editar" en historial → modal edit abre con form prellenado.

---

### **Fase 3 — JS: `static/js/ecas/inventario/inventario.js`**

**Objetivo**: lógica del frontend unificada.

1. **Portar del mockup**:
   - `irLanding(e)`, `irWorkspace(e, tab)` — navegación entre estados
   - `irLandingYPicker(e)`, `irLandingYHistorial(e)`, `irLandingYFlujo(e)`,
     `irLandingYCargaMasiva(e)` — accesos directos
   - `activarOvTab(tabId)` — switch de tabs "Otras vistas"
   - `activarTab(tabId)` — switch de tabs workspace
   - `cerrarModal(id)` — wrapper
   - `filtrarTarjetas()` — filtros de las 6 cards inventario (data attributes)
   - `limpiarFiltros()` — reset
   - `initStockChartLanding()`, `initStockChartWorkspace()` — inicialización perezosa
   - `initKpiOcupacionBar()` — color dinámico JS (≥90% rojo, ≥70% amarillo, <70% verde)
   - `filtrarCatalogo(query, categoria, filtro)` — filtrado del picker
   - `renderPicker()` — render del list-group
   - `escapeHtml(str)` — helper XSS
   - `abrirModalBuscar(e)` — abre picker desde sidebar
   - `seleccionarMaterialParaCrear(materialId)` — flujo picker → tab → form
   - `limpiarSeleccionMaterial()` — vuelve al placeholder
   - `submitCrearInventario(e)` — POST a endpoint, valida, SweetAlert éxito
   - `submitEditarInventario()` — PUT a endpoint, valida, SweetAlert éxito
   - `verMovimiento(tipo, data)` — abre detalle compra o venta
   - `editarMovimientoDesdeDetalle()` — switch de detalle a edit
   - `editarMovimiento(tipo, dataOrId)` — abre form edit, lookup por id
   - `submitEditarCompra()`, `submitEditarVenta()` — PUTs
   - Helpers de formato: `formatCOP(n)`, `formatQty(n, u)`, `formatDateCO(iso)`

2. **Portar lógica de `static/js/ecas/movimientos/stock-chart.js`** (líneas 1-892):
   - Adaptar al nuevo look (sin Chart.js).
   - Mantener API: llamada a endpoint que devuelve series temporales, render en canvas.

3. **NO portar**:
   - Hash-based deep linking (testing).
   - Datos ficticios hardcoded (reemplazar por llamadas AJAX).

4. **CSS companion** (`static/css/ecas/inventario/inventario.css`):
   - `.tarjeta-hover` (efecto al pasar mouse sobre cards)
   - `.kpi-bar-color-*` (3 variantes de color)
   - `.tabla-movimientos-compacta` (filas densas)
   - `.picker-item-selected` (highlight en picker)

5. **Verificación Fase 3**:
   - Click en cualquier filtro → cards se filtran sin recargar.
   - Abrir picker → escribir en input → lista se filtra.
   - Seleccionar material en picker → form aparece con datos readonly.
   - Click "Guardar" en form crear → POST real, SweetAlert, card aparece en landing.
   - Click "Ver" → modal abre con todos los campos llenos.

---

### **Fase 4 — Sidebar**

**Objetivo**: consolidar navegación.

1. **`templates/ecas/partials/sidebar.html`** (84 líneas):
   - Eliminar los items sueltos "Inventario" y "Movimientos" viejos.
   - Crear dropdown "Inventario" con 7 sub-ítems:
     1. **Inventario** (link directo a `/inventario/`, abre en landing, tab Inventario)
     2. **Buscar Material** (link a `/inventario/`, abre picker modal)
     3. **Vista General** (link a `/inventario/`, tab Historial General)
     4. **Compra** (link a `/inventario/`, en workspace abre tab-compra)
     5. **Venta** (link a `/inventario/`, en workspace abre tab-venta)
     6. **Historial General** (link a `/inventario/`, tab Historial General)
     7. **Flujo de Stock** (link a `/inventario/`, tab Flujo de Stock)
     8. **Carga Masiva** (link a `/inventario/`, tab Carga Masiva)
   - Cada link usa `{% url 'punto-eca:inventario' %}` con `?tab=<tabId>` o similar.

2. **`static/css/sidebar.css`** (122 líneas):
   - Ajustar solo si el nuevo bloque se ve mal (medir con captura).

3. **Verificación Fase 4**:
   - Click en cada sub-ítem → navega al tab correcto.

---

### **Fase 5 — Tests de regresión** (CRÍTICA, antes del switch)

**Objetivo**: blindar los endpoints AJAX para no romper nada durante el switch.

1. **`apps/inventory/tests/test_inventario_endpoints.py`** (nuevo):
   - `test_buscar_materiales_catalogo_view_ok`
   - `test_buscar_materiales_catalogo_view_filtros`
   - `test_agregar_al_inventario_view_ok`
   - `test_agregar_al_inventario_view_duplicate` (mismo material 2 veces)
   - `test_agregar_al_inventario_view_unauthorized`
   - `test_actualizar_inventario_view_ok`
   - `test_eliminar_inventario_view_ok`
   - `test_detalle_inventario_view_ok`
   - `test_buscar_materiales_inventario_view_ok`

2. **`apps/operations/tests/test_movimientos_endpoints.py`** (nuevo):
   - `test_registros_compras_ok`
   - `test_registros_compras_validacion_stock`
   - `test_registros_ventas_ok`
   - `test_registros_ventas_validacion_stock`
   - `test_editar_compra_ok`
   - `test_editar_venta_ok`
   - `test_borrar_compra_ok`
   - `test_borrar_venta_ok`
   - `test_bulk_import_compras_ok`
   - `test_bulk_import_compras_validacion_columnas`
   - `test_bulk_import_ventas_ok`
   - `test_exportar_compras_excel_ok`
   - `test_exportar_compras_pdf_ok`
   - `test_exportar_ventas_excel_ok`
   - `test_exportar_ventas_pdf_ok`
   - `test_exportar_historial_excel_ok`
   - `test_exportar_historial_pdf_ok`

3. **Verificación Fase 5**:
   - `python manage.py test apps.inventory apps.operations` → todos verdes.
   - Cobertura mínima: 80% de los endpoints AJAX.

---

### **Fase 6 — Switch de tráfico** (reversible, punto de control)

**Objetivo**: `/materiales/` y `/movimientos/` devuelven 404. Toda la navegación va a `/inventario/`.

1. **Auditoría previa** (grep en todo el repo):
   ```bash
   grep -rn "punto-eca:materiales\|punto-eca:movimientos" \
        --include="*.py" --include="*.html" --include="*.js" \
        apps/ templates/ static/
   ```
   Resultado esperado: 0 referencias (excepto comentarios históricos).

2. **`apps/ecas/urls.py`**:
   - Convertir las rutas viejas en 404 explícito:
     ```python
     # /materiales/ y /movimientos/ eliminadas en Fase 6 — ver PLAN-INVENTARIO.md
     ```
   - Borrar las entradas:
     ```python
     path("materiales/", render_seccion, {"seccion": "materiales"}, name="materiales"),
     path("movimientos/", render_seccion, {"seccion": "movimientos"}, name="movimientos"),
     ```
   - El `path("<str:seccion>/", ...)` (catch-all) puede capturar esas URLs y caer en el 404
     natural (porque `seccion not in SECTION_TEMPLATES`).

3. **`apps/ecas/views.py`**:
   - En `render_seccion` (línea 118), agregar early-return para 404:
     ```python
     if seccion in ("materiales", "movimientos"):
         raise Http404("Sección migrada a /inventario/")
     ```

4. **Verificación Fase 6**:
   - `curl -I http://localhost:8000/punto-eca/materiales/` → 404.
   - `curl -I http://localhost:8000/punto-eca/movimientos/` → 404.
   - `curl -I http://localhost:8000/punto-eca/inventario/` → 200.
   - Login manual: navegar sidebar, todas las opciones abren `/inventario/`.
   - Smoke test E2E: crear inventario → registrar compra → registrar venta → editar → eliminar
     → bulk import → export Excel → export PDF. Sin errores 500.

5. **Punto de control**: confirmar con el usuario antes de Fase 7.

---

### **Fase 7 — Limpieza final**

**Objetivo**: eliminar archivos viejos. La nueva sección es la única.

1. **Borrar archivos frontend**:
   ```bash
   git rm templates/ecas/section-materiales.html
   git rm templates/ecas/section-movimientos.html
   git rm static/js/ecas/movimientos/movimientos.js
   git rm static/js/ecas/movimientos/stock-chart.js
   git rm static/css/ecas/movimientos.css
   ```

2. **`apps/ecas/views.py`**:
   - Eliminar las ramas `seccion == "materiales"` y `seccion == "movimientos"` de
     `render_seccion` (líneas 138-141).
   - Eliminar el early-return 404 de Fase 6 (ya no se necesita).
   - Eliminar el helper `_build_default_context` si quedó huérfano.

3. **`apps/inventory/views.py`**:
   - Eliminar `_build_materiales_context` (línea 14) si nadie más la usa.
   - Verificar con `grep -r "_build_materiales_context" apps/`.

4. **`apps/operations/views.py`**:
   - Eliminar `_build_movimientos_context` (línea 590) si nadie más la usa.
   - Verificar con `grep -r "_build_movimientos_context" apps/`.

5. **Verificación Fase 7**:
   - `python manage.py test` → verde.
   - `grep -r "section-materiales\|section-movimientos\|movimientos.js\|stock-chart.js\|movimientos.css" \
          apps/ templates/ static/` → 0 referencias.
   - Smoke test E2E idéntico a Fase 6.

---

## 6. Detalles de implementación (recetas técnicas)

### 6.1 Cómo portar un modal de movimientos al nuevo template

Los 4 modales de movimientos en `section-movimientos.html` usan IDs prefijados
(`detallesEntradaModal`, `editarCompraModal`, etc.). En el nuevo template, prefijar con `inv-`:

| ID viejo | ID nuevo |
|----------|----------|
| `detallesEntradaModal` | `inv-modalDetalleCompra` |
| `editarCompraModal` | `inv-modalEditarCompra` |
| `detallesSalidaModal` | `inv-modalDetalleVenta` |
| `editarVentaModal` | `inv-modalEditarVenta` |

Actualizar todas las referencias en el template y en el JS.

### 6.2 Patrón de fetch AJAX para endpoints existentes

```js
// Ejemplo: cargar catálogo
fetch(`{% url 'punto-eca/materiales:buscar_materiales_catalogo_view' %}?puntoId={{ punto.id }}`)
  .then(r => r.json())
  .then(data => renderPicker(data));

// Ejemplo: editar compra
fetch(`{% url 'punto-eca/movimientos:editar_compra' compra_id=0 %}`.replace('/0/', `/${id}/`), {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
  body: JSON.stringify(payload)
})
  .then(r => r.json())
  .then(data => Swal.fire({ icon: 'success', ... }));
```

### 6.3 Mapeo endpoint → URL name → acción JS

| Endpoint | URL name | Acción JS |
|----------|----------|-----------|
| `apps.inventory.views.buscar_materiales_catalogo_view` | `punto-eca/materiales:buscar_materiales_catalogo_view` | `GET` desde picker |
| `apps.inventory.views.buscar_materiales_inventario_view` | `punto-eca/materiales:buscar_materiales_inventario` | `GET` desde landing |
| `apps.inventory.views.agregar_al_inventario_view` | `punto-eca/materiales:agregar_al_inventario` | `POST` desde form crear |
| `apps.inventory.views.actualizar_inventario_view` | `punto-eca/materiales:actualizar_inventario` | `POST` desde form editar |
| `apps.inventory.views.eliminar_inventario_view` | `punto-eca/materiales:eliminar_material` | `POST` desde modal eliminar |
| `apps.inventory.views.detalle_iventario_view` | `punto-eca/materiales:detalle_inventario_view` | `GET` desde workspace |
| `apps.operations.views.registros_compras` | `punto-eca/movimientos:registrar_entrada` | `POST` desde tab-compra |
| `apps.operations.views.registros_ventas` | `punto-eca/movimientos:registrar_venta` | `POST` desde tab-venta |
| `apps.operations.views.editar_compra` | `punto-eca/movimientos:editar_compra` | `POST` desde modal editar compra |
| `apps.operations.views.editar_venta` | `punto-eca/movimientos:editar_venta` | `POST` desde modal editar venta |
| `apps.operations.views.borrar_compra` | `punto-eca/movimientos:borrar_compra` | `POST` desde confirmación |
| `apps.operations.views.borrar_venta` | `punto-eca/movimientos:borrar_venta` | `POST` desde confirmación |
| `apps.operations.views.bulk_import_compras` | `punto-eca/movimientos:bulk_import_compras` | `POST` desde modal bulk |
| `apps.operations.views.bulk_import_ventas` | `punto-eca/movimientos:bulk_import_ventas` | `POST` desde modal bulk |
| `apps.operations.views.exportar_*` | `punto-eca/movimientos:exportar_*` | `GET` desde botones export |

### 6.4 Estructura del objeto `data` que el JS espera de los endpoints

Basado en el mockup, los endpoints deben devolver (o el frontend debe mapear a):

```js
// Catálogo (buscar_materiales_catalogo_view)
{
  materialId: number,
  nmbMaterial: string,
  dscMaterial: string,
  nmbTipo: string,
  nmbCategoria: string,
  unidad: 'kg' | 'un' | 'ton' | 'mc',
  imagenUrl: string,
  enInventario: boolean
}

// Inventario (buscar_materiales_inventario_view)
{
  inventarioId: number,
  materialId: number,
  nmbMaterial: string,
  dscMaterial: string,
  nmbTipo: string,
  nmbCategoria: string,
  stockActual: number,
  capacidadMaxima: number,
  ocupacion: number, // 0-100
  estado: 'ok' | 'alerta' | 'critico',
  umbralAlerta: number,
  umbralCritico: number,
  precioCompra: number,
  precioVenta: number,
  unidad: 'kg' | 'un' | 'ton' | 'mc',
  ultimaActualizacion: ISO8601
}

// Movimiento historial
{
  id: number,
  tipo: 'compra' | 'venta',
  material: string,
  categoria: string,
  fecha: ISO8601,
  cantidad: number,
  unidad: string,
  precio: number,
  total: number,
  stockActual: number,
  capacidad: number,
  centro: string | null, // solo ventas
  observaciones: string,
  usuario: string
}
```

Si los endpoints actuales no devuelven exactamente este shape, agregar **funciones de mapeo**
en el frontend (`mapCatalogoItem(raw)`, `mapInventarioItem(raw)`, `mapMovimiento(raw)`) en
`inventario.js` en lugar de cambiar el backend.

### 6.5 Patrón de validación de formularios

```js
function submitCrearInventario(e) {
  e.preventDefault();
  const form = e.target;
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  const data = Object.fromEntries(new FormData(form));
  fetch(url, { method: 'POST', headers, body: JSON.stringify(data) })
    .then(r => r.json())
    .then(handleSuccess)
    .catch(handleError);
}
```

### 6.6 Patrón de SweetAlert

```js
Swal.fire({
  icon: 'success',
  title: 'Inventario creado',
  text: 'El material se agregó al inventario.',
  timer: 1800,
  showConfirmButton: false,
});
```

### 6.7 Sanitización XSS (regla de oro)

```js
function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
```

En el template, usar siempre `{{ var|escape }}` o `{% autoescape on %}`.

---

## 7. Convenciones y restricciones del repo

### 7.1 AGENTS.md (extracto relevante)
- `AUTH_USER_MODEL = "users.Usuario"`. Importar con `get_user_model()`.
- Roles: Ciudadano / Gestor ECA / Administrador. Decoradores en `apps/core/decorators.py`.
- Middleware: `apps.core.middleware.CustomErrorMiddleware`.
- Handlers globales `400/403/404/500` en `apps/core/views` (registrados en
  `config/urls.py:70-73`).
- Tests: `python manage.py test` (no `pytest`).
- Test único: `python manage.py test apps.<app>.tests.<Clase>.<metodo>`.
- `apps/chat` usa directorio `tests/`; el resto usa `tests.py`.

### 7.2 Migraciones
- Si se modifican modelos (no planeado): `python manage.py makemigrations` → `migrate`.

### 7.3 Lint / typecheck
- No hay comando de lint formal. Después de cada cambio: `python manage.py check`.
- `node -e "new Function(script)"` para validar JS (mockup).

### 7.4 Git
- Solo commitear cuando el usuario lo pida explícitamente.
- Commits propuestos:
  - `chore: snapshot pre-fase-inventario` (Fase 0)
  - `feat(ecas): nueva sección /inventario/` (Fase 1+2+3+4)
  - `test(inventory,operations): cobertura endpoints AJAX sección inventario` (Fase 5)
  - `feat(ecas): switch de tráfico /materiales y /movimientos → /inventario` (Fase 6)
  - `chore(ecas): cleanup sección inventario unificada` (Fase 7)

### 7.5 CI / PRs
- `.github/workflows/sonarcloud.yml` corre solo en PRs hacia `main`.
- Cualquier cambio al template `section-inventario.html` se audita por SonarCloud.

### 7.6 Variable de entorno
- `USE_REDIS=True` opcional en Linux (Channels). En Windows cae a `InMemoryChannelLayer`.

---

## 8. Verificación final (checklist E2E)

### 8.1 Pre-Fase 6
- [ ] `python manage.py test` verde.
- [ ] `python manage.py check` sin issues.
- [ ] Login manual → `/inventario/` 200.
- [ ] Click en cada uno de los 7 sub-ítems del sidebar → navega correctamente.
- [ ] Crear inventario desde picker → aparece card en landing.
- [ ] Editar inventario desde card → modal prellenado, guardar, cambios reflejados.
- [ ] Eliminar inventario desde card → confirmación, desaparece.
- [ ] Click en card → workspace con 5 tabs visibles.
- [ ] Tab Compra → registrar compra → aparece en historial.
- [ ] Tab Venta → registrar venta → aparece en historial.
- [ ] Tab Historial → Ver/Editar compra/venta → modales correctos.
- [ ] Tab Flujo de Stock → gráfico renderiza.
- [ ] Tab Carga Masiva (landing) → importar CSV → registros creados.
- [ ] Botones Excel/PDF → archivos descargan.
- [ ] Filtrar cards por nombre, categoría, tipo, estado, ocupación → filtrado correcto.
- [ ] Picker: buscar, filtrar por categoría, mostrar todos/en inventario/fuera → correcto.
- [ ] Form crear: todos los campos required, validación HTML5, no envía si falta algo.

### 8.2 Post-Fase 6
- [ ] `curl -I /punto-eca/materiales/` → 404.
- [ ] `curl -I /punto-eca/movimientos/` → 404.
- [ ] `curl -I /punto-eca/inventario/` → 200.
- [ ] Repetir E2E de §8.1.

### 8.3 Post-Fase 7
- [ ] `grep -r "section-materiales\|section-movimientos" apps/ templates/ static/` → 0 refs.
- [ ] `grep -r "_build_materiales_context\|_build_movimientos_context" apps/` → 0 refs.
- [ ] `python manage.py test` verde.
- [ ] Repetir E2E de §8.1.

---

## 9. Critical context (todo lo no obvio)

### 9.1 Lo que el mockup tiene y producción no
- 3 bloques KPI compactos (producción tiene 5 KPIs separados en `section-materiales.html:13-130`).
- Tabs "Otras vistas" (producción usa accordion de 4 items en `section-movimientos.html`).
- 4 modales separados para compra/venta detalle/edición (producción los tiene pero con
  IDs `detallesEntradaModal`, etc., no `modalDetalleCompra`).
- Filtros funcionales en las cards de inventario (producción no tiene filtros).
- Picker modal de 14 items (producción tiene `buscarMaterialModal` en
  `section-materiales.html:410-445`).
- Form inline en tab `ovtab-buscar` (producción lo tiene en modal separado).
- 5 tabs en workspace (producción tiene accordion).

### 9.2 Lo que producción tiene y mockup no
- Datos reales del backend (mockup usa hardcoded).
- Validaciones server-side (mockup solo tiene HTML5).
- Manejo de errores 500/403/404.
- Integración con Channels (chat interno).
- Importación real de CSV con preview y rollback.
- Permisos por rol (ciudadano no ve esta sección).
- Paginación real (mockup muestra 1 página estática).

### 9.3 Decisiones que pueden requerir ajuste durante implementación
- **StockChart**: la lógica de `stock-chart.js` actual asume un set específico de datos.
  Si el endpoint devuelve un shape distinto, ajustar el parser en `inventario.js` (no en el JS viejo,
  ya que se borra en Fase 7).
- **Catálogo**: el endpoint `buscar_materiales_catalogo_view` actualmente filtra materiales **fuera**
  del inventario. Si el mockup muestra "todos" (D10), hay que ajustar el endpoint o agregar un
  parámetro `?incluir_en_inventario=true`. **Acción**: revisar `apps/inventory/views.py:118-139` y
  `apps/inventory/service.py` antes de Fase 3.
- **Categorías de picker**: el mockup muestra categorías estáticas ("Plásticos", "Metales", etc.).
  Las categorías reales vienen de la BD; verificar que `catalogo_categorias` o equivalente se
  inyecte al contexto.
- **Centros de acopio en modal editar venta**: el mockup tiene 4 centros hardcoded. Los centros
  reales vienen de la BD; el contexto debe incluirlos.

### 9.4 Riesgos identificados
- **R1**: `stock-chart.js` puede usar APIs deprecated o asumir DOM específico.
  **Mitigación**: portar cuidadosamente, agregar tests de humo.
- **R2**: Algún endpoint puede no estar autenticado para todos los roles. **Mitigación**: tests
  en Fase 5 cubren `unauthorized`.
- **R3**: El sidebar de producción puede tener JS que asuma IDs viejos. **Mitigación**:
  `grep -rn "sidebar.js\|sidebar_subsections" static/` antes de Fase 4.
- **R4**: Si hay fixtures que cargan datos con FK a `Inventario` viejo, pueden romperse. **Mitigación**:
  revisar `fixtures/*.json` antes de Fase 7.
- **R5**: Los emails transaccionales pueden tener links a `/materiales/` o `/movimientos/`.
  **Mitigación**: grep en `templates/emails/` y `apps/*/templates/*/emails/`.

### 9.5 Archivos a NO tocar (read-only durante implementación)
- `config/settings.py` (salvo si se descubre que hace falta un nuevo setting).
- `config/urls.py` (los handlers globales).
- `config/asgi.py` y `config/wsgi.py`.
- `apps/chat/*` (no relacionado).
- `apps/publicaciones/*` (no relacionado).
- `apps/users/*` (no relacionado).
- `apps/scheduling/*` (no relacionado).
- `apps/map/*` (no relacionado).
- `apps/panel_admin/*` (no relacionado).

---

## 10. Estado de la conversación (snapshot textual)

### 10.1 Hitos
1. Análisis inicial del codebase, identificación de archivos en alcance.
2. Construcción iterativa del mockup HTML con 5 tabs.
3. Refinamiento: eliminación de "modalDetalles", tabs "Editar", adición de `modalEditarInventario`.
4. Fix de bug: picker abría workspace para items en inventario; ahora todos abren form.
5. Reorganización de KPIs en 3 bloques compactos.
6. Adición de los 4 modales separados para compra/venta (D16).
7. Wirear botones Ver/Editar en tablas de historial general y workspace.
8. Validación visual con Chromium headless.
9. Decisión de estructura de snapshot (D19).
10. Decisión de template limpio (D20).
11. Decisión de portar stock-chart.js (D21).
12. Decisión de forms Compra/Venta en workspace (D22).

### 10.2 Frases textuales del usuario que guiaron decisiones
- "Flujo por material seleccionado" → D1
- "404 duro para /materiales/ y /movimientos/" → D2
- "Sin tests JS" → D3
- "Form inline en tab, no modal" → D9
- "Todos los items del picker abren el form" → D10
- "Modales separados por tipo de movimiento" → D16
- "Editar antes de Eliminar" → D17
- "Snapshot + golden renombrado" → D19
- "Inspirado en mockup, limpio" → D20
- "Portar stock-chart.js" → D21
- "Dentro del workspace" → D22
- "no hagas nada mas" (al pedir plan documentado) → único deliverable de este turno

### 10.3 Lo que NO se hizo (explícitamente)
- No se creó el snapshot todavía (Fase 0 pendiente).
- No se renombró el mockup a golden todavía (Fase 0 pendiente).
- No se creó ninguna rama de git todavía.
- No se modificó ningún archivo de producción.
- No se corrieron tests.

---

## 11. Referencias cruzadas

### 11.1 Producción
- `apps/ecas/views.py:118-151` — `render_seccion` con switch por sección
- `apps/ecas/views.py:14` — `_build_materiales_context` (en `apps/inventory/views.py`)
- `apps/ecas/views.py:16` — `_build_movimientos_context` (en `apps/operations/views.py`)
- `apps/ecas/constants.py:9-18` — `SECTION_TEMPLATES` (con `detalles_materiales` huérfano)
- `apps/ecas/urls.py:30-33` — rutas viejas a eliminar en Fase 6
- `apps/ecas/urls.py:44-55` — include de `apps.inventory.urls` y `apps.operations.urls`
- `apps/inventory/urls.py:9` — endpoint catálogo/buscar
- `apps/inventory/views.py:90` — `unidades_medida: cons.UnidadMedida.choices`
- `apps/inventory/views.py:118-179` — endpoints CRUD inventario
- `apps/operations/views.py:590-708` — `_build_movimientos_context`
- `apps/operations/views.py:710-893` — endpoints CRUD movimientos + bulk + exports
- `apps/operations/urls.py:7-78` — todas las URLs de movimientos
- `config/constants.py:102-106` — `UnidadMedida` con KG/UN/TON/MC
- `config/urls.py:70-73` — handlers globales
- `.github/instructions/memory.instruction.md` — fix del modal "Ver Hoja Técnica" (preservar)
- `templates/ecas/section-materiales.html:586-622` — flujo picker→form (match D10)
- `templates/ecas/section-materiales.html:145-241` — acordeón "Agregar Material al Inventario"
- `templates/ecas/section-materiales.html:242-409` — modal `agregarInventarioModal`
- `templates/ecas/section-materiales.html:410-445` — modal `buscarMaterialModal`
- `templates/ecas/section-movimientos.html:1522-1962` — modales separados compra/venta
- `static/js/ecas/movimientos/movimientos.js` — 3451 líneas (reemplazar)
- `static/js/ecas/movimientos/stock-chart.js` — 892 líneas (portar lógica)
- `static/js/ecas/dashboard/sidebar_subsections.js:24-39` — agnóstico al nombre
- `templates/ecas/partials/sidebar.html:109-131` — bloque de sidebar a reemplazar

### 11.2 Mockup (referencia dorada)
- `mockup-inventario-golden.html` (post-Fase 0) — 2694 líneas
- Servidor local: `python3 -m http.server 8765 --bind 127.0.0.1`

### 11.3 Tests pre-existentes (referencia de estilo)
- `docs/casos_prueba_unitaria/CU-09_monitoreo_inventario_test_cases.md`
- `docs/casos_prueba_unitaria/CU-10_exportacion_historial_test_cases.md`

---

## 12. Cómo usar este documento

1. **Antes de empezar cada fase**: releer la sección correspondiente en §5.
2. **Si hay duda sobre una decisión**: buscar en §2 (D#) o §10.2.
3. **Si una feature del mockup no está clara**: `mockup-inventario-golden.html` es la
   verdad visual; consultar directamente.
4. **Si un endpoint se comporta raro**: §6.3-6.4 mapean URL name → endpoint → shape esperado.
5. **Si encuentro un riesgo nuevo**: agregar a §9.4.
6. **Si el usuario cambia de opinión**: actualizar §2 (decisión cerrada) y §10 (historial).

---

## 13. Estado actual de implementación

- [ ] Fase 0 — Snapshot y preparación
- [ ] Fase 1 — Backend nueva sección
- [ ] Fase 2 — Template limpio
- [ ] Fase 3 — JS inventario
- [ ] Fase 4 — Sidebar
- [ ] Fase 5 — Tests de regresión
- [ ] Fase 6 — Switch de tráfico
- [ ] Fase 7 — Limpieza final
