document.addEventListener("DOMContentLoaded", () => {
  var form = document.getElementById("createTipoMaterialForm") || document.getElementById("editTipoMaterialForm");
  if (!form) return;
  var esCrear = form.id === "createTipoMaterialForm";
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
      title: esCrear ? "¿Crear tipo de material?" : "¿Guardar cambios?",
      text: esCrear ? "El formulario está completo y listo para enviarse." : "Se actualizará la información del tipo de material.",
      confirmText: esCrear ? "Sí, crear" : "Sí, guardar",
    },
  });
});
