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

function normalizarSoloDigitos(campo) {
  if (!campo) {
    return;
  }

  const valor = campo.value;
  const soloDigitos = valor.replace(/\D/g, "");

  if (valor !== soloDigitos) {
    campo.value = soloDigitos;
  }
}

function validarCelular(celularInput) {
  if (!celularInput) {
    return true;
  }

  normalizarSoloDigitos(celularInput);

  const esValido = /^3\d{9}$/.test(celularInput.value);
  celularInput.setCustomValidity(esValido ? "" : "El celular debe iniciar con 3 y tener 10 dígitos.");
  actualizarEstadoCampo(celularInput);
  return esValido;
}

function validarNumeroDocumento(numeroDocumentoInput) {
  if (!numeroDocumentoInput) {
    return true;
  }

  normalizarSoloDigitos(numeroDocumentoInput);

  if (!numeroDocumentoInput.value) {
    numeroDocumentoInput.setCustomValidity("");
    actualizarEstadoCampo(numeroDocumentoInput);
    return true;
  }

  const esValido = /^\d{6,20}$/.test(numeroDocumentoInput.value);
  numeroDocumentoInput.setCustomValidity(esValido ? "" : "El número de documento debe tener entre 6 y 20 dígitos, sin letras ni caracteres especiales.");
  actualizarEstadoCampo(numeroDocumentoInput);
  return esValido;
}

function validarLocalidad(localidadInput, mensajeVacio) {
  if (!localidadInput) {
    return true;
  }

  const tieneLocalidad = String(localidadInput.value || "").trim() !== "";
  localidadInput.setCustomValidity(tieneLocalidad ? "" : (mensajeVacio || "Selecciona una localidad."));
  actualizarEstadoCampo(localidadInput);
  return tieneLocalidad;
}

function validarFechaNacimiento(fechaInput, fechaMaxima) {
  if (!fechaInput) {
    return true;
  }

  if (!fechaInput.value) {
    fechaInput.setCustomValidity("");
    actualizarEstadoCampo(fechaInput);
    return true;
  }

  const cumple = fechaInput.value <= fechaMaxima;

  if (!cumple) {
    fechaInput.setCustomValidity("La fecha debe corresponder a un menor de edad.");
    actualizarEstadoCampo(fechaInput);
    return false;
  }

  fechaInput.setCustomValidity("");
  actualizarEstadoCampo(fechaInput);
  return true;
}

function validarFechaNacimientoRango(fechaInput, fechaMinima, fechaMaxima, mensajeInvalido) {
  if (!fechaInput) {
    return true;
  }

  const valor = String(fechaInput.value || "").trim();
  if (!valor) {
    fechaInput.setCustomValidity("");
    actualizarEstadoCampo(fechaInput);
    return true;
  }

  const fecha = new Date(`${valor}T00:00:00`);
  if (Number.isNaN(fecha.getTime())) {
    fechaInput.setCustomValidity("Formato de fecha inválido.");
    actualizarEstadoCampo(fechaInput);
    return false;
  }

  const esValida = fecha <= fechaMaxima && fecha >= fechaMinima;
  fechaInput.setCustomValidity(esValida ? "" : (mensajeInvalido || "La fecha está fuera del rango permitido."));
  actualizarEstadoCampo(fechaInput);
  return esValida;
}

function obtenerErroresFormulario(campos) {
  return Array.from(new Set(campos.map((campo) => campo.validationMessage).filter(Boolean)));
}

function registrarValidacionCampo(campo, handler) {
  if (!campo) {
    return;
  }

  const eventName = campo.tagName === "SELECT" ? "change" : "input";
  campo.addEventListener(eventName, handler);
  campo.addEventListener("blur", () => actualizarEstadoCampo(campo));
}

function confirmarEnvioSwal(mensaje) {
  const configuracion = {
    icon: "question",
    title: mensaje.title || "¿Confirmar?",
    text: mensaje.text || "",
    showCancelButton: true,
    confirmButtonText: mensaje.confirmText || "Sí",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#198754",
    cancelButtonColor: "#6c757d",
  };

  if (typeof Swal === "undefined") {
    return Promise.resolve({ isConfirmed: window.confirm(mensaje.text || mensaje.title) });
  }

  return Swal.fire(configuracion);
}
