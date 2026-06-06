function registrarValidacion(campo, handler) {
  if (!campo) {
    return;
  }

  const eventName = campo.tagName === "SELECT" ? "change" : "input";
  campo.addEventListener(eventName, handler);
  campo.addEventListener("blur", () => actualizarEstadoCampo(campo));
}

function validarTexto(campo, minimo, maximo, patron, mensajeMinimo, mensajeMaximo, mensajePatron) {
  if (!campo) {
    return true;
  }

  const valor = campo.value.trim();

  if (!valor) {
    campo.setCustomValidity(campo.required ? "Este campo es obligatorio." : "");
    actualizarEstadoCampo(campo);
    return !campo.required;
  }

  if (valor.length < minimo) {
    campo.setCustomValidity(mensajeMinimo);
    actualizarEstadoCampo(campo);
    return false;
  }

  if (valor.length > maximo) {
    campo.setCustomValidity(mensajeMaximo);
    actualizarEstadoCampo(campo);
    return false;
  }

  if (patron && !patron.test(valor)) {
    campo.setCustomValidity(mensajePatron);
    actualizarEstadoCampo(campo);
    return false;
  }

  campo.setCustomValidity("");
  actualizarEstadoCampo(campo);
  return true;
}

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

  const nombresRegex = /^[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-']+$/;
  const tiposDocumentoValidos = new Set(["CC", "TI", "CE", "PA", "NIT"]);
  const tiposUsuarioValidos = new Set(["ADM", "CIU", "GECA"]);
  const estadosValidos = new Set(["activo", "inactivo"]);

  const hoy = new Date();
  const fechaMinima = new Date(hoy);
  fechaMinima.setFullYear(fechaMinima.getFullYear() - 100);
  const fechaMaxima = new Date(hoy);
  fechaMaxima.setFullYear(fechaMaxima.getFullYear() - 18);

  function validarNombres() {
    return validarTexto(
      nombresInput,
      3,
      30,
      nombresRegex,
      "Los nombres deben tener al menos 3 caracteres.",
      "Los nombres no pueden superar 30 caracteres.",
      "Los nombres solo pueden contener letras, espacios, guiones o apóstrofes.",
    );
  }

  function validarApellidos() {
    return validarTexto(
      apellidosInput,
      3,
      40,
      nombresRegex,
      "Los apellidos deben tener al menos 3 caracteres.",
      "Los apellidos no pueden superar 40 caracteres.",
      "Los apellidos solo pueden contener letras, espacios, guiones o apóstrofes.",
    );
  }

  function validarTipoDocumento() {
    if (!tipoDocumentoInput) {
      return true;
    }

    const valor = String(tipoDocumentoInput.value || "").trim();
    const esValido = valor === "" || tiposDocumentoValidos.has(valor);
    tipoDocumentoInput.setCustomValidity(esValido ? "" : "Selecciona un tipo de documento válido.");
    actualizarEstadoCampo(tipoDocumentoInput);
    return esValido;
  }

  function validarTipoUsuario() {
    if (!tipoUsuarioInput) {
      return true;
    }

    const valor = String(tipoUsuarioInput.value || "").trim();
    const esValido = valor === "" || tiposUsuarioValidos.has(valor);
    tipoUsuarioInput.setCustomValidity(esValido ? "" : "Selecciona un tipo de usuario válido.");
    actualizarEstadoCampo(tipoUsuarioInput);
    return esValido;
  }

  function validarEstadoUsuario() {
    if (!estadoUsuarioInput) {
      return true;
    }

    const valor = String(estadoUsuarioInput.value || "").trim().toLowerCase();
    const esValido = estadosValidos.has(valor);
    estadoUsuarioInput.setCustomValidity(esValido ? "" : "Selecciona un estado válido.");
    actualizarEstadoCampo(estadoUsuarioInput);
    return esValido;
  }

  function validarFormulario() {
    validarNombres();
    validarApellidos();
    validarCelular(celularInput);
    validarLocalidad(localidadInput, "Selecciona una localidad válida o deja la opción en blanco.");
    validarTipoDocumento();
    validarNumeroDocumento(numeroDocumentoInput);
    validarTipoUsuario();
    validarEstadoUsuario();
    validarFechaNacimientoRango(fechaNacimientoInput, fechaMinima, fechaMaxima, "La fecha debe corresponder a una persona entre 18 y 100 años.");

    campos.forEach((campo) => actualizarEstadoCampo(campo));
    return form.checkValidity();
  }

  registrarValidacion(nombresInput, validarNombres);
  registrarValidacion(apellidosInput, validarApellidos);
  registrarValidacion(celularInput, () => validarCelular(celularInput));
  registrarValidacion(localidadInput, () => validarLocalidad(localidadInput, "Selecciona una localidad válida o deja la opción en blanco."));
  registrarValidacion(tipoDocumentoInput, validarTipoDocumento);
  registrarValidacion(numeroDocumentoInput, () => validarNumeroDocumento(numeroDocumentoInput));
  registrarValidacion(tipoUsuarioInput, validarTipoUsuario);
  registrarValidacion(estadoUsuarioInput, validarEstadoUsuario);
  registrarValidacion(fechaNacimientoInput, () => validarFechaNacimientoRango(fechaNacimientoInput, fechaMinima, fechaMaxima, "La fecha debe corresponder a una persona entre 18 y 100 años."));

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

  form.addEventListener("submit", (evento) => {
    if (!validarFormulario()) {
      evento.preventDefault();
      evento.stopPropagation();
      form.classList.add("was-validated");
      mostrarErroresSwal(obtenerErroresFormulario(campos));
      return;
    }

    evento.preventDefault();
    form.classList.add("was-validated");

    confirmarEnvioSwal({
      title: "¿Guardar cambios?",
      text: "Los datos están completos y listos para actualizarse.",
      confirmText: "Sí, guardar",
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        form.submit();
      }
    });
  });
});
