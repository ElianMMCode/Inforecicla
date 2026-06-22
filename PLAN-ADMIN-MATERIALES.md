# Plan: Mejora de Sección Materiales — Admin

**Rama:** `feature/admin-materiales-flujos`  
**Worktree:** `../main-admin-mat-flujos`  
**Mockup:** `mockup-materiales-admin.html` (1526 líneas, 7 tabs)  
**Referencia Puntos ECA:** `../admin-punto-eca/` (implementación real)

---

## Estado General

| Fase | Estado |
|------|--------|
| Worktree creado | ✅ |
| Mockup HTML standalone | ✅ v5 — 1526 líneas, 7 tabs, 6 modales, Select2, paginación, export |
| Análisis impacto cruzado PuntoECA | ✅ |
| Constantes (`ClasificacionMaterial`) | ⏳ |
| Modelos (Material +clasificacion, Categoria -tipo) | ⏳ |
| Migraciones | ⏳ |
| `panel_admin/service.py` | ⏳ |
| `panel_admin/views.py` | ⏳ |
| `inventory/service.py` + `ecas/views.py` | ⏳ |
| Templates admin de Materiales | ⏳ |
| Sidebar | ⏳ |
| CSV carga masiva | ⏳ |
| `python manage.py test` | ⏳ |

---

## Mockup HTML — Funcionalidades completas

### 7 Tabs

| Tab | Contenido |
|-----|-----------|
| **Catálogo** | Charts doughnut (Categoría, Clasificación, Estado) + tabla paginada 20/page con filtros integrados (buscar, categoría, clasificación, estado) + botones Excel/PDF + botones ver/editar por fila |
| **Inventario por Material** | Selector de material → KPIs (stock total, ocupación, valor, críticos) → cards por punto ECA con stock, cap%, estado, precios, margen. Filtros por estado y orden |
| **Flujo de Materiales** | Chips multi-select de materiales + filtros (fechas, granularidad) + 4 KPIs + chart líneas + subtabs Stock/Ganancias/Detalle (stacked bar + ranking rentabilidad) |
| **Historial Global** | 8 filtros (material, categoría, tipo mov, fechas, punto, rangos cantidad/monto) + 4 KPIs + tabla paginada 20/page con Excel/PDF + botón limpiar |
| **KPIs Agregados** | 6 mini-KPIs + 4 charts (Top Stock, Top Valor, Salud, Flujo Neto) + doughnut Clasificaciones + stacked bar Top 10 Puntos + tabla resumen con 11 columnas |
| **Categorías** | Tabla paginada 20/page: nombre, descripción, # materiales, estado (Activo/Inactivo), editar + botón Nueva + Excel/PDF |
| **Clasificaciones** | Tabla paginada 20/page: nombre (badge coloreado ESTANDAR/MANEJO_ESPECIAL/PELIGROSO/HAZMAT), descripción de advertencia, # materiales, editar + botón Nueva + Excel/PDF |

### 6 Modales

| Modal | Campos |
|-------|--------|
| Nuevo Material | nombre*, descripción, categoría*, clasificación*, estado |
| Editar Material | precarga datos del material seleccionado |
| Nueva Categoría | nombre*, descripción |
| Editar Categoría | nombre*, descripción, estado (Activar/Desactivar) |
| Nueva Clasificación | nombre* (ej: BIOLÓGICO), descripción de advertencia* |
| Editar Clasificación | precarga nombre y descripción |

### Features transversales

- **Select2** en todos los `<select>` (jQuery + Select2 + Bootstrap 5 theme)
- **Paginación 20/page** en Catálogo, Historial, Categorías, Clasificaciones
- **Exportación Excel/PDF** simulada (respeta filtros activos) en las 4 tablas
- **Botón limpiar filtros** en Catálogo, Historial, Flujo, Estados
- **Clasificación dinámica**: selects se pueblan desde array `clasificaciones[]`, se actualizan al crear/editar
- **Gráficos independientes de filtros**: charts del Catálogo solo se construyen una vez, no se re-renderizan al filtrar

---

## Modelo de Datos — Cambios

### `Material` (`apps/inventory/models.py`)

```python
# NUEVO
clasificacion = models.CharField(
    max_length=20,
    choices=ClasificacionMaterial.choices,
    null=False, blank=False,
    verbose_name="Clasificación de manejo",
    help_text="Nivel de riesgo/manejo especial del material",
)
# DEPRECADO (queda en BD, no se muestra)
tipo = FK(TipoMaterial)  # columna huérfana
```

### `CategoriaMaterial` (`apps/inventory/models.py`)

```python
# ELIMINAR
tipo = FK(TipoMaterial)  # ya no tiene relación con TipoMaterial
```

### `ClasificacionMaterial` (nueva constante en `config/constants.py`)

```python
class ClasificacionMaterial(models.TextChoices):
    ESTANDAR = "ESTANDAR", "Estándar"
    MANEJO_ESPECIAL = "MANEJO_ESPECIAL", "Manejo Especial"
    PELIGROSO = "PELIGROSO", "Peligroso"
    HAZMAT = "HAZMAT", "HAZMAT"
```

---

## Archivos a modificar por commit

### Commit 1: `config/constants.py` — Agregar ClasificacionMaterial

```python
class ClasificacionMaterial(models.TextChoices):
    ESTANDAR = "ESTANDAR", _("Estándar")
    MANEJO_ESPECIAL = "MANEJO_ESPECIAL", _("Manejo Especial")
    PELIGROSO = "PELIGROSO", _("Peligroso")
    HAZMAT = "HAZMAT", _("HAZMAT")
```

### Commit 2: `apps/inventory/models.py` + migración

- Agregar `clasificacion` CharField a `Material`
- Eliminar `tipo = FK(TipoMaterial)` de `CategoriaMaterial`
- `python manage.py makemigrations inventory`

### Commit 3: `apps/panel_admin/service.py`

- `_validar_material_data()`: remover `tipo = categoria.tipo`, validar `clasificacion`
- `crear_material()`: remover `tipo = categoria.tipo`, usar `clasificacion` del payload
- `actualizar_material()`: misma lógica
- `obtener_distribucion_materiales_por_tipo()`: cambiar a `_por_clasificacion()` o eliminar

### Commit 4: `apps/panel_admin/views.py`

- `material_to_dict()`: cambiar `tipo_nombre`/`tipo_id` → `clasificacion`
- `gestion_materiales()`: quitar `dist_tipo_mat`, actualizar context con `dist_clasificacion_mat`
- Export Excel/PDF: quitar columna `tipo`, agregar `clasificacion`
- Quitar `select_related("tipo")` de queries

### Commit 5: `apps/inventory/service.py` + `apps/ecas/views.py`

- inventory/service.py: `nmbTipo` → `nmbClasificacion`
- ecas/views.py: `material.tipo.nombre` → `material.clasificacion`

### Commit 6: Templates admin — CRUD forms

- `templates/admin/Materiales/createMaterial.html`: selector `clasificacion` en vez de `tipo`
- `templates/admin/Materiales/editMaterial.html`: mismo cambio
- `templates/admin/Materiales/_autofill_tipo_js.html`: eliminar include
- `templates/admin/Materiales/materiales_pdf.html`: `m.tipo.nombre` → `m.clasificacion`

### Commit 7: Templates admin — `materiales_gestion.html` y tabs_materiales

- Reemplazar tab "Tipos" por "Clasificaciones"
- Actualizar charts (quitar `dist_tipo_mat`, agregar `dist_clasificacion_mat`)
- Actualizar filtros y columnas de tabla

### Commit 8: Templates — `admin/partials/sidebar.html`

- "Tipos de Materiales" → "Clasificaciones"
- Actualizar rutas de los 3 sub-items del dropdown Materiales

### Commit 9: Otros templates y JS

- `templates/ecas/section-inventario.html`: `tipo.nombre` → `clasificacion`
- `templates/ecas/section-calendario.html`: mismo
- `templates/operations/compras_pdf.html` y `ventas_pdf.html`
- `static/js/Mapa/mapa-interactivo.js`

### Commit 10: `docs/carga_masiva/materiales.csv`

- Eliminar `tipo_nombre`, agregar `clasificacion`

---

## Impacto Cruzado con PuntoECA Dashboard

**El dashboard PuntoECA NO se rompe** — `inv_data` usa solo `material.nombre` y `material.categoria.nombre`.

15 archivos referencian `material.tipo` y requieren ajuste (detalle en sección anterior del plan).

