document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createUserForm");
  if (!form) {
    return;
  }

  initPasswordVisibilityToggle();

  const fechaNacimientoInput = form.querySelector('[name="fechaNacimiento"]');
  const nombresInput = form.querySelector('[name="nombres"]');
  const apellidosInput = form.querySelector('[name="apellidos"]');
  const emailInput = form.querySelector('[name="email"]');
  const celularInput = form.querySelector('[name="celular"]');
  const tipoDocumentoInput = form.querySelector('[name="tipoDocumento"]');
  const localidadInput = form.querySelector('[name="localidad"]');
  const numeroDocumentoInput = form.querySelector('[name="numeroDocumento"]');
  const passwordInput = form.querySelector('[name="password"]');
  const passwordConfirmInput = form.querySelector('[name="passwordConfirm"]');
  const mensajeCoincidencia = document.getElementById("mensajeCoincidencia");
  const passwordRequirementsBox = document.getElementById("passwordRequirementsBox");
  const camposObligatorios = Array.from(form.querySelectorAll("[required]"));
  const camposValidacionRapida = [
    nombresInput,
    apellidosInput,
    emailInput,
    celularInput,
    tipoDocumentoInput,
    localidadInput,
    numeroDocumentoInput,
    fechaNacimientoInput,
    passwordInput,
    passwordConfirmInput,
  ].filter(Boolean);

  const fechaMaximaMenorEdad = formatDate(
    new Date(new Date().getFullYear() - 18, new Date().getMonth(), new Date().getDate() - 1),
  );

  function actualizarEstadoCajaContrasena(cumpleTodo) {
    if (!passwordRequirementsBox) {
      return;
    }
    passwordRequirementsBox.classList.remove(
      "alert-light",
      "alert-success",
      "border-success",
      "bg-success",
      "bg-opacity-10",
    );
    if (cumpleTodo) {
      passwordRequirementsBox.classList.add("alert-success", "border-success", "bg-success", "bg-opacity-10");
      return;
    }
    passwordRequirementsBox.classList.add("alert-light", "border");
  }

  function sincronizarValidacionCampo(campo) {
    if (!campo) {
      return;
    }
    campo.setCustomValidity(campo.checkValidity() ? "" : campo.validationMessage);
    actualizarEstadoCampo(campo);
  }

  function ejecutarValidacionesCrearUsuario() {
    validarTexto(
      nombresInput,
      USUARIO_LIMITE_NOMBRES_MIN,
      USUARIO_LIMITE_NOMBRES_MAX,
      null,
      "El nombre debe tener al menos 3 caracteres.",
      "El nombre no puede superar 30 caracteres.",
    );
    validarTexto(
      apellidosInput,
      USUARIO_LIMITE_APELLIDOS_MIN,
      USUARIO_LIMITE_APELLIDOS_MAX,
      null,
      "Los apellidos deben tener al menos 3 caracteres.",
      "Los apellidos no pueden superar 40 caracteres.",
    );
    validarEmail(emailInput);
    if (passwordInput && passwordConfirmInput) {
      const cumpleTodo = contrasenaCumpleReglas(passwordInput.value);
      passwordInput.setCustomValidity(cumpleTodo ? "" : "La contraseña no cumple los requisitos.");
      actualizarEstadoCajaContrasena(cumpleTodo);
    }
    validarFechaNacimiento(fechaNacimientoInput, fechaMaximaMenorEdad);
    validarCelular(celularInput);
    validarNumeroDocumento(numeroDocumentoInput);
    validarLocalidad(localidadInput, "Selecciona una localidad.");
    camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));
    actualizarEstadoCampo(passwordInput);
    actualizarEstadoCampo(passwordConfirmInput);
  }

  form.addEventListener(
    "invalid",
    (evento) => {
      evento.preventDefault();
      actualizarEstadoCampo(evento.target);
    },
    true,
  );

  camposObligatorios.forEach((campo) => {
    const eventName = campo.tagName === "SELECT" ? "change" : "input";
    campo.addEventListener(eventName, () => {
      if (campo === nombresInput) {
        validarTexto(
          nombresInput,
          USUARIO_LIMITE_NOMBRES_MIN,
          USUARIO_LIMITE_NOMBRES_MAX,
          null,
          "El nombre debe tener al menos 3 caracteres.",
          "El nombre no puede superar 30 caracteres.",
        );
        return;
      }
      if (campo === apellidosInput) {
        validarTexto(
          apellidosInput,
          USUARIO_LIMITE_APELLIDOS_MIN,
          USUARIO_LIMITE_APELLIDOS_MAX,
          null,
          "Los apellidos deben tener al menos 3 caracteres.",
          "Los apellidos no pueden superar 40 caracteres.",
        );
        return;
      }
      if (campo === emailInput) {
        validarEmail(emailInput);
        return;
      }
      if (campo === fechaNacimientoInput) {
        validarFechaNacimiento(fechaNacimientoInput, fechaMaximaMenorEdad);
        return;
      }
      if (campo === celularInput) {
        validarCelular(celularInput);
        return;
      }
      if (campo === numeroDocumentoInput) {
        validarNumeroDocumento(numeroDocumentoInput);
        return;
      }
      if (campo === localidadInput) {
        validarLocalidad(localidadInput, "Selecciona una localidad.");
        return;
      }
      sincronizarValidacionCampo(campo);
    });
    campo.addEventListener("blur", () => actualizarEstadoCampo(campo));
  });

  bindPasswordRealtime(passwordInput, passwordConfirmInput, mensajeCoincidencia);

  camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));

  bindSubmitUsuario({
    formulario: form,
    camposValidacion: camposValidacionRapida,
    confirmar: {
      title: "¿Crear usuario?",
      text: "El formulario está completo y listo para enviarse.",
      confirmText: "Sí, crear",
    },
    antesDeEnviar: ejecutarValidacionesCrearUsuario,
  });
});
