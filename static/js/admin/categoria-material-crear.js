document.addEventListener("DOMContentLoaded", () => {
  const CATEGORIA_IDS = ["createCategoriaMaterialForm", "editCategoriaMaterialForm"];
  const TIPO_IDS = ["createTipoMaterialForm", "editTipoMaterialForm"];
  const todos = CATEGORIA_IDS.concat(TIPO_IDS);
  let form = null;
  let esCategoria = false;
  for (const id of todos) {
    const f = document.getElementById(id);
    if (f) { form = f; esCategoria = CATEGORIA_IDS.includes(id); break; }
  }
  if (!form) return;
  const esCrear = form.id.startsWith("create");
  const entidad = esCategoria ? "categoría" : "tipo";
  materialesInicializarFormulario({
    formularioId: form.id,
    campos: [
      {
        name: "nombre",
        maxLength: MATERIALES_LIMITE_NOMBRE_MAX,
        mensaje: "El nombre es obligatorio.",
        mensajeOpcional: `El nombre no puede superar ${MATERIALES_LIMITE_NOMBRE_MAX} caracteres.`,
      },
      {
        name: "descripcion",
        maxLength: MATERIALES_LIMITE_DESCRIPCION_MAX,
        mensajeOpcional: `La descripción no puede superar ${MATERIALES_LIMITE_DESCRIPCION_MAX} caracteres.`,
      },
      { name: "estado", esSelect: true, mensaje: "Selecciona un estado." },
    ],
    confirmar: {
      title: esCrear ? "¿Crear " + entidad + " de material?" : "¿Guardar cambios?",
      text: esCrear ? "El formulario está completo y listo para enviarse." : "Se actualizará la información del " + entidad + ".",
      confirmText: esCrear ? "Sí, crear" : "Sí, guardar",
    },
  });
});
