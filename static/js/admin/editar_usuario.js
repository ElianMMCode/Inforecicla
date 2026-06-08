document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".needs-validation");
  if (!form) {
    return;
  }

  const nombresInput = form.querySelector('[name="nombres"]');
  const apellidosInput = form.querySelector('[name="apellidos"]');
  const celularInput = form.querySelector('[name="celular"]');
  const localidadInput = form.querySelector('[name="localidad"]');
  const tipoDocumentoInput = form.querySelector('[name="tipoDocumento"]');
  const numeroDocumentoInput = form.querySelector('[name="numeroDocumento"]');
  const tipoUsuarioInput = form.querySelector('[name="tipo_usuario"]');
  const estadoUsuarioInput = form.querySelector('[name="estado_usuario"]');
  const fechaNacimientoInput = form.querySelector('[name="fechaNacimiento"]');

  const campos = [
    nombresInput,
    apellidosInput,
    celularInput,
    localidadInput,
    tipoDocumentoInput,
    numeroDocumentoInput,
    tipoUsuarioInput,
    estadoUsuarioInput,
    fechaNacimientoInput,
  ].filter(Boolean);

  function validarNombres() {
    return validarTexto(
      nombresInput,
      USUARIO_LIMITE_NOMBRES_MIN,
      USUARIO_LIMITE_NOMBRES_MAX,
      USUARIO_PATTERN_NOMBRES,
      "Los nombres deben tener al menos 3 caracteres.",
      "Los nombres no pueden superar 30 caracteres.",
      "Los nombres solo pueden contener letras, espacios, guiones o apóstrofes.",
    );
  }

  function validarApellidos() {
    return validarTexto(
      apellidosInput,
      USUARIO_LIMITE_APELLIDOS_MIN,
      USUARIO_LIMITE_APELLIDOS_MAX,
      USUARIO_PATTERN_NOMBRES,
      "Los apellidos deben tener al menos 3 caracteres.",
      "Los apellidos no pueden superar 40 caracteres.",
      "Los apellidos solo pueden contener letras, espacios, guiones o apóstrofes.",
    );
  }

  function validarFormulario() {
    validarNombres();
    validarApellidos();
    validarCelular(celularInput);
    validarLocalidad(localidadInput, "Selecciona una localidad válida o deja la opción en blanco.");
    validarOpcionSeleccion(
      tipoDocumentoInput,
      USUARIO_TIPOS_DOCUMENTO_VALIDOS,
      "Selecciona un tipo de documento válido.",
    );
    validarNumeroDocumento(numeroDocumentoInput);
    validarOpcionSeleccion(
      tipoUsuarioInput,
      USUARIO_TIPOS_USUARIO_VALIDOS,
      "Selecciona un tipo de usuario válido.",
    );
    validarOpcionSeleccion(
      estadoUsuarioInput,
      USUARIO_ESTADOS_VALIDOS,
      "Selecciona un estado válido.",
      { caseSensitive: false },
    );
    validarNormalizarFechaNacimiento(fechaNacimientoInput, 18);
    campos.forEach((campo) => actualizarEstadoCampo(campo));
    return form.checkValidity();
  }

  registrarValidacionCampo(nombresInput, validarNombres);
  registrarValidacionCampo(apellidosInput, validarApellidos);
  registrarValidacionCampo(celularInput, () => validarCelular(celularInput));
  registrarValidacionCampo(localidadInput, () =>
    validarLocalidad(localidadInput, "Selecciona una localidad válida o deja la opción en blanco."),
  );
  registrarValidacionCampo(tipoDocumentoInput, () =>
    validarOpcionSeleccion(tipoDocumentoInput, USUARIO_TIPOS_DOCUMENTO_VALIDOS, "Selecciona un tipo de documento válido."),
  );
  registrarValidacionCampo(numeroDocumentoInput, () => validarNumeroDocumento(numeroDocumentoInput));
  registrarValidacionCampo(tipoUsuarioInput, () =>
    validarOpcionSeleccion(tipoUsuarioInput, USUARIO_TIPOS_USUARIO_VALIDOS, "Selecciona un tipo de usuario válido."),
  );
  registrarValidacionCampo(estadoUsuarioInput, () =>
    validarOpcionSeleccion(estadoUsuarioInput, USUARIO_ESTADOS_VALIDOS, "Selecciona un estado válido.", { caseSensitive: false }),
  );
  registrarValidacionCampo(fechaNacimientoInput, () =>
    validarNormalizarFechaNacimiento(fechaNacimientoInput, 18),
  );

  form.addEventListener(
    "invalid",
    (evento) => {
      evento.preventDefault();
      actualizarEstadoCampo(evento.target);
    },
    true,
  );

  campos.forEach((campo) => actualizarEstadoCampo(campo));
  validarFormulario();

  bindSubmitUsuario({
    formulario: form,
    camposValidacion: campos,
    confirmar: {
      title: "¿Guardar cambios?",
      text: "Los datos están completos y listos para actualizarse.",
      confirmText: "Sí, guardar",
    },
    antesDeEnviar: () => validarFormulario(),
  });
});
