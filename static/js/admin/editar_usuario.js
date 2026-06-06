function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function actualizarEstadoCampo(campo) {
  if (!campo) {
    return;
  }

  const valido = campo.checkValidity();
  const tieneValor = String(campo.value || "").trim() !== "";

  campo.classList.toggle("is-valid", valido && tieneValor);
  campo.classList.toggle("is-invalid", !valido && (tieneValor || campo.required));
}

function escaparHtml(texto) {
  return String(texto).replace(/[&<>"']/g, (caracter) => {
    const mapa = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };

    return mapa[caracter] || caracter;
  });
}

function mostrarErroresSwal(errores) {
  if (typeof Swal === "undefined" || !errores || errores.length === 0) {
    return;
  }

  Swal.fire({
    icon: "error",
    title: "Corrige los campos",
    html: `<div class="text-start"><ul class="mb-0 ps-3">${errores
      .map((error) => `<li>${escaparHtml(error)}</li>`)
      .join("")}</ul></div>`,
    confirmButtonColor: "#198754",
  });
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

function registrarValidacion(campo, handler) {
  if (!campo) {
    return;
  }

  const eventName = campo.tagName === "SELECT" ? "change" : "input";
  campo.addEventListener(eventName, handler);
  campo.addEventListener("blur", () => actualizarEstadoCampo(campo));
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
  const numeroDocumentoRegex = /^\d{6,20}$/;
  const celularRegex = /^3\d{9}$/;
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
      apellidosInput ? nombresRegex : null,
      "Los apellidos deben tener al menos 3 caracteres.",
      "Los apellidos no pueden superar 40 caracteres.",
      "Los apellidos solo pueden contener letras, espacios, guiones o apóstrofes.",
    );
  }

  function validarCelular() {
    if (!celularInput) {
      return true;
    }

    const valor = celularInput.value.trim();
    if (!valor) {
      celularInput.setCustomValidity("El celular es obligatorio.");
      actualizarEstadoCampo(celularInput);
      return false;
    }

    const esValido = celularRegex.test(valor);
    celularInput.setCustomValidity(esValido ? "" : "Debe iniciar con 3 y tener exactamente 10 dígitos.");
    actualizarEstadoCampo(celularInput);
    return esValido;
  }

  function validarLocalidad() {
    if (!localidadInput) {
      return true;
    }

    const valor = String(localidadInput.value || "").trim();
    const esValido = valor === "" || Array.from(localidadInput.options).some((opcion) => opcion.value === valor);
    localidadInput.setCustomValidity(esValido ? "" : "Selecciona una localidad válida o deja la opción en blanco.");
    actualizarEstadoCampo(localidadInput);
    return esValido;
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

  function validarNumeroDocumento() {
    if (!numeroDocumentoInput) {
      return true;
    }

    const valor = numeroDocumentoInput.value.trim();
    if (!valor) {
      numeroDocumentoInput.setCustomValidity("El número de documento es obligatorio.");
      actualizarEstadoCampo(numeroDocumentoInput);
      return false;
    }

    const esValido = numeroDocumentoRegex.test(valor);
    numeroDocumentoInput.setCustomValidity(esValido ? "" : "Ingresa entre 6 y 20 dígitos, sin letras ni caracteres especiales.");
    actualizarEstadoCampo(numeroDocumentoInput);
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

  function validarFechaNacimiento() {
    if (!fechaNacimientoInput) {
      return true;
    }

    const valor = String(fechaNacimientoInput.value || "").trim();
    if (!valor) {
      fechaNacimientoInput.setCustomValidity("");
      actualizarEstadoCampo(fechaNacimientoInput);
      return true;
    }

    const fecha = new Date(`${valor}T00:00:00`);
    if (Number.isNaN(fecha.getTime())) {
      fechaNacimientoInput.setCustomValidity("Formato de fecha inválido.");
      actualizarEstadoCampo(fechaNacimientoInput);
      return false;
    }

    const esMayor = fecha <= fechaMaxima;
    const esMenorDeCien = fecha >= fechaMinima;
    const esValida = esMayor && esMenorDeCien;

    fechaNacimientoInput.setCustomValidity(esValida ? "" : "La fecha debe corresponder a una persona entre 18 y 100 años.");
    actualizarEstadoCampo(fechaNacimientoInput);
    return esValida;
  }

  function obtenerErroresFormulario() {
    return Array.from(new Set(campos.map((campo) => campo.validationMessage).filter(Boolean)));
  }

  function validarFormulario() {
    validarNombres();
    validarApellidos();
    validarCelular();
    validarLocalidad();
    validarTipoDocumento();
    validarNumeroDocumento();
    validarTipoUsuario();
    validarEstadoUsuario();
    validarFechaNacimiento();

    campos.forEach((campo) => actualizarEstadoCampo(campo));
    return form.checkValidity();
  }

  registrarValidacion(nombresInput, validarNombres);
  registrarValidacion(apellidosInput, validarApellidos);
  registrarValidacion(celularInput, validarCelular);
  registrarValidacion(localidadInput, validarLocalidad);
  registrarValidacion(tipoDocumentoInput, validarTipoDocumento);
  registrarValidacion(numeroDocumentoInput, validarNumeroDocumento);
  registrarValidacion(tipoUsuarioInput, validarTipoUsuario);
  registrarValidacion(estadoUsuarioInput, validarEstadoUsuario);
  registrarValidacion(fechaNacimientoInput, validarFechaNacimiento);

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
      mostrarErroresSwal(obtenerErroresFormulario());
      return;
    }

    evento.preventDefault();
    form.classList.add("was-validated");

    if (typeof Swal === "undefined") {
      form.submit();
      return;
    }

    Swal.fire({
      icon: "question",
      title: "¿Guardar cambios?",
      text: "Los datos están completos y listos para actualizarse.",
      showCancelButton: true,
      confirmButtonText: "Sí, guardar",
      cancelButtonText: "Cancelar",
      confirmButtonColor: "#198754",
      cancelButtonColor: "#6c757d",
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        form.submit();
      }
    });
  });
});