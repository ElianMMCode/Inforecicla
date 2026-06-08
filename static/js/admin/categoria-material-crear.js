document.addEventListener("DOMContentLoaded", () => {
  var CATEGORIA_IDS = ["createCategoriaMaterialForm", "editCategoriaMaterialForm"];
  var TIPO_IDS = ["createTipoMaterialForm", "editTipoMaterialForm"];
  var todos = CATEGORIA_IDS.concat(TIPO_IDS);
  var form = null;
  var esCategoria = false;
  for (var i = 0; i < todos.length; i++) {
    var f = document.getElementById(todos[i]);
    if (f) { form = f; esCategoria = CATEGORIA_IDS.indexOf(todos[i]) !== -1; break; }
  }
  if (!form) return;
  var esCrear = form.id.indexOf("create") === 0;
  var entidad = esCategoria ? "categoría" : "tipo";
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
