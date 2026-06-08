document.addEventListener("DOMContentLoaded", () => {
  var form = document.getElementById("createMaterialForm") || document.getElementById("editMaterialForm");
  if (!form) return;
  var esCrear = form.id === "createMaterialForm";
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
      title: esCrear ? "¿Crear material?" : "¿Guardar cambios?",
      text: esCrear ? "El formulario está completo y listo para enviarse." : "Se actualizará la información del material.",
      confirmText: esCrear ? "Sí, crear" : "Sí, guardar",
    },
  });
});
