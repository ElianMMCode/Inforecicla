document.addEventListener("DOMContentLoaded", () => {
  materialesInicializarFormulario({
    formularioId: "editMaterialForm",
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
      { name: "categoria_id", esSelect: true },
      { name: "tipo_id", esSelect: true },
      { name: "estado", esSelect: true, mensaje: "Selecciona un estado." },
    ],
    imagen: {
      inputId: "material_imagen",
      alertaId: "alertMaterialImagen",
      maxBytes: MATERIALES_LIMITE_IMAGEN_BYTES,
    },
    confirmar: {
      title: "¿Guardar cambios?",
      text: "Se actualizará la información del material.",
      confirmText: "Sí, guardar",
    },
  });
});
