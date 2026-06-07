document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createMaterialForm");
  if (!form) {
    return;
  }

  const inputNombre = form.querySelector('[name="nombre"]');
  const inputDescripcion = form.querySelector('[name="descripcion"]');
  const selectCategoria = form.querySelector('[name="categoria_id"]');
  const selectTipo = form.querySelector('[name="tipo_id"]');
  const selectEstado = form.querySelector('[name="estado"]');
  const inputImagen = document.getElementById("material_imagen");
  const alertaImagen = document.getElementById("alertMaterialImagen");

  const camposValidacion = [
    inputNombre,
    inputDescripcion,
    selectCategoria,
    selectTipo,
    selectEstado,
  ].filter(Boolean);

  materialesSuprimirValidacionNativa(form);

  function validarTamanoImagen() {
    if (!inputImagen || !inputImagen.files || inputImagen.files.length === 0) {
      if (alertaImagen) {
        alertaImagen.classList.add("d-none");
        alertaImagen.textContent = "";
      }
      materialesActualizarEstadoCampo(inputImagen);
      return true;
    }
    const archivo = inputImagen.files[0];
    const resultado = materialesValidarTamanoImagen(
      archivo,
      MATERIALES_LIMITE_IMAGEN_BYTES,
    );
    if (!resultado.valido) {
      if (alertaImagen) {
        alertaImagen.textContent = resultado.mensaje;
        alertaImagen.classList.remove("d-none");
      }
      inputImagen.value = "";
      materialesActualizarEstadoCampo(inputImagen);
      return false;
    }
    if (alertaImagen) {
      alertaImagen.classList.add("d-none");
      alertaImagen.textContent = "";
    }
    materialesActualizarEstadoCampo(inputImagen);
    return true;
  }

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
  materialesRegistrarValidacionCampo(selectCategoria, () =>
    materialesValidarSelect(selectCategoria),
  );
  materialesRegistrarValidacionCampo(selectTipo, () =>
    materialesValidarSelect(selectTipo),
  );

  if (inputImagen) {
    inputImagen.addEventListener("change", validarTamanoImagen);
  }

  function ejecutarValidacionesCrearMaterial() {
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
    materialesValidarSelect(selectCategoria);
    materialesValidarSelect(selectTipo);
    camposValidacion.forEach(materialesActualizarEstadoCampo);
    return validarTamanoImagen();
  }

  camposValidacion.forEach(materialesActualizarEstadoCampo);

  materialesBindEnvio({
    formulario: form,
    camposValidacion,
    confirmar: {
      title: "¿Crear material?",
      text: "El formulario está completo y listo para enviarse.",
      confirmText: "Sí, crear",
    },
    antesDeEnviar: ejecutarValidacionesCrearMaterial,
  });
});
