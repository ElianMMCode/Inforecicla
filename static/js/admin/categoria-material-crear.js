document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createCategoriaMaterialForm");
  if (!form) {
    return;
  }

  const inputNombre = form.querySelector('[name="nombre"]');
  const inputDescripcion = form.querySelector('[name="descripcion"]');
  const selectEstado = form.querySelector('[name="estado"]');

  const camposValidacion = [inputNombre, inputDescripcion, selectEstado].filter(Boolean);

  materialesSuprimirValidacionNativa(form);

  materialesRegistrarValidacionCampo(inputNombre, () =>
    materialesValidarTexto(
      inputNombre,
      MATERIALES_LIMITE_NOMBRE_MAX,
      "El nombre es obligatorio.",
      `El nombre no puede superar ${MATERIALES_LIMITE_NOMBRE_MAX} caracteres.`,
    ),
  );
  materialesRegistrarValidacionCampo(inputDescripcion, () =>
    materialesValidarTexto(
      inputDescripcion,
      MATERIALES_LIMITE_DESCRIPCION_MAX,
      "",
      `La descripción no puede superar ${MATERIALES_LIMITE_DESCRIPCION_MAX} caracteres.`,
    ),
  );
  materialesRegistrarValidacionCampo(selectEstado, () =>
    materialesValidarSelect(selectEstado, "Selecciona un estado."),
  );

  function ejecutarValidacionesCrearCategoria() {
    materialesValidarTexto(
      inputNombre,
      MATERIALES_LIMITE_NOMBRE_MAX,
      "El nombre es obligatorio.",
      `El nombre no puede superar ${MATERIALES_LIMITE_NOMBRE_MAX} caracteres.`,
    );
    materialesValidarTexto(
      inputDescripcion,
      MATERIALES_LIMITE_DESCRIPCION_MAX,
      "",
      `La descripción no puede superar ${MATERIALES_LIMITE_DESCRIPCION_MAX} caracteres.`,
    );
    materialesValidarSelect(selectEstado, "Selecciona un estado.");
    camposValidacion.forEach(materialesActualizarEstadoCampo);
    return true;
  }

  camposValidacion.forEach(materialesActualizarEstadoCampo);

  materialesBindEnvio({
    formulario: form,
    camposValidacion,
    confirmar: {
      title: "¿Crear categoría de material?",
      text: "El formulario está completo y listo para enviarse.",
      confirmText: "Sí, crear",
    },
    antesDeEnviar: ejecutarValidacionesCrearCategoria,
  });
});
