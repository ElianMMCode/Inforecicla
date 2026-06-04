# Snapshot pre-fase-inventario

Foto del estado de los archivos de producción **antes** de implementar la unificación de las
secciones **Materiales** y **Movimientos** en una única sección **Inventario**.

## ¿Por qué existe?

Como red de seguridad durante el refactor. Si algo sale mal durante las Fases 1-7 del plan
(ver [`/PLAN-INVENTARIO.md`](../PLAN-INVENTARIO.md)), se puede restaurar cualquier archivo desde
acá con:

```bash
cp snapshot-pre-inventario/<ruta-archivo> <ruta-archivo>
```

## Estructura (espejo de path)

```
snapshot-pre-inventario/
├── apps/
│   ├── ecas/
│   │   ├── constants.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── inventory/
│   │   ├── urls.py
│   │   └── views.py
│   └── operations/
│       ├── urls.py
│       └── views.py
├── static/
│   ├── css/
│   │   ├── ecas/movimientos.css
│   │   └── sidebar.css
│   └── js/ecas/movimientos/
│       ├── movimientos.js
│       └── stock-chart.js
└── templates/ecas/
    ├── partials/sidebar.html
    ├── puntoECA-layout.html
    ├── section-materiales.html
    └── section-movimientos.html
```

## Inventario

| Archivo | Líneas | Rol |
|---|---:|---|
| `templates/ecas/section-materiales.html` | 2237 | Acordeón + modales de materiales (origen del nuevo template) |
| `templates/ecas/section-movimientos.html` | 1967 | Acordeón + modales separados compra/venta (origen de los 4 modales) |
| `templates/ecas/partials/sidebar.html` | 84 | Sidebar del Punto ECA (origen del nuevo dropdown unificado) |
| `templates/ecas/puntoECA-layout.html` | 84 | Layout base |
| `static/js/ecas/movimientos/movimientos.js` | 3451 | Lógica JS de movimientos (a reescribir en `inventario.js`) |
| `static/js/ecas/movimientos/stock-chart.js` | 892 | Lógica de gráfico de stock (a portar a `inventario.js`) |
| `static/css/ecas/movimientos.css` | 69 | Estilos de movimientos |
| `static/css/sidebar.css` | 122 | Estilos del sidebar |
| `apps/ecas/views.py` | 659 | Vista `render_seccion` con switch por sección |
| `apps/ecas/urls.py` | 67 | Rutas del Punto ECA |
| `apps/ecas/constants.py` | 19 | `SECTION_TEMPLATES` (incluye `detalles_materiales` huérfano) |
| `apps/inventory/views.py` | 248 | Endpoints CRUD inventario (no se tocan) |
| `apps/inventory/urls.py` | 39 | URLs inventario (no se tocan) |
| `apps/operations/views.py` | 906 | `_build_movimientos_context` + endpoints CRUD (no se tocan) |
| `apps/operations/urls.py` | 79 | URLs movimientos (no se tocan) |

**Total: 15 archivos, ~10.9k líneas.**

## Referencia visual

El mockup dorado validado con el usuario está en:
- [`/mockup-inventario-golden.html`](../mockup-inventario-golden.html) (2694 líneas)

## Cuándo eliminar

Este snapshot se elimina en **Fase 7** del plan, una vez que:
1. La nueva sección `/inventario/` esté 100% operativa.
2. Las rutas viejas `/materiales/` y `/movimientos/` devuelvan 404.
3. Los tests E2E pasen.

Si todo va bien, esta carpeta queda como registro histórico y se borra en una limpieza posterior
del repo.
