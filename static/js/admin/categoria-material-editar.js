document.addEventListener("DOMContentLoaded", () => {
  materialesInicializarFormulario({
    formularioId: "editCategoriaMaterialForm",
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
      title: "¿Guardar cambios?",
      text: "Se actualizará la información de la categoría.",
      confirmText: "Sí, guardar",
    },
  });
});
