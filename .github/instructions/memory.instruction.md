---
applyTo: '**'
---

**Modal "Ver Hoja Técnica" - Fix y Documentación**

1. Diagnóstico:
- El modal para ver detalles de cada material fallaba tras filtrar la grilla, porque el dataset de la tarjeta (card) no mapeaba correctamente el inventarioId.
- El backend (view buscar_materiales_inventario) retorna siempre el campo inventarioId en el JSON, tanto filtrado como sin filtrar.

2. Fix aplicado:
- En el renderizador de tarjetas JS (section-materiales.html), se modificó el mapping de IDs:
  - Ahora se prioriza inv.inventarioId como campo principal para el dataset.
  - Si falta, el mapping hace fallback a otros posibles nombres (inv.id, mat.inventarioId, mat.id, etc.) pero siempre inventarioId es el primero.
  - Esto asegura que la UI nunca pierda el ID tras operaciones de filtro y el modal funciona robusto.

3. Pruebas y Validación:
- Se retesteó el flujo completo: aplicar filtro, abrir el modal, verificar logs y datos.
- El modal ahora abre siempre correctamente después de filtrar.

4. Extra:
- Se documenta esta solución para futuras referencias.

Fix final, issue cerrado.

