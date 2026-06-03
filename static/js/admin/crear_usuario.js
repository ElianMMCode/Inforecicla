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
  const tieneValor = campo.value !== "";

  campo.classList.toggle("is-valid", valido && tieneValor);
  campo.classList.toggle("is-invalid", !valido && (tieneValor || campo.required));
}

function actualizarRequisito(elemento, cumple, texto) {
  if (!elemento) {
    return;
  }

  elemento.classList.toggle("text-success", cumple);
  elemento.classList.toggle("text-danger", !cumple);
  elemento.classList.toggle("fw-semibold", cumple);
  elemento.innerHTML = cumple
    ? `✅ <span class="text-success">${texto}</span>`
    : `❌ <span class="text-danger">${texto}</span>`;
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

function initPasswordVisibilityToggle() {
  document.querySelectorAll(".toggle-password-button").forEach((button) => {
    button.addEventListener("click", (evento) => {
      evento.preventDefault();

      const targetSelector = button.dataset.target || button.querySelector(".toggle-password")?.dataset.target;
      if (!targetSelector) {
        return;
      }

      const input = document.querySelector(targetSelector);
      if (!input) {
        return;
      }

      const esPassword = input.type === "password";
      input.type = esPassword ? "text" : "password";

      const icono = button.querySelector(".toggle-password");
      if (icono) {
        icono.classList.toggle("bi-eye", !esPassword);
        icono.classList.toggle("bi-eye-slash", esPassword);
      }
    });
  });
}

function limitarUnSoloArroba(valor) {
  const texto = String(valor || "");
  const primerArroba = texto.indexOf("@");

  if (primerArroba === -1) {
    return texto;
  }

  return texto.slice(0, primerArroba + 1) + texto.slice(primerArroba + 1).replace(/@/g, "");
}

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
  const reqMinusculas = document.getElementById("reqMinusculas");
  const reqMayusculas = document.getElementById("reqMayusculas");
  const reqNumeros = document.getElementById("reqNumeros");
  const reqEspeciales = document.getElementById("reqEspeciales");
  const reqLongitud = document.getElementById("reqLongitud");
  const mensajeCoincidencia = document.getElementById("mensajeCoincidencia");
  const passwordRequirementsBox = document.getElementById("passwordRequirementsBox");
  const camposObligatorios = Array.from(form.querySelectorAll("[required]"));
  const camposValidacionRapida = [nombresInput, apellidosInput, emailInput, celularInput, tipoDocumentoInput, localidadInput, numeroDocumentoInput, fechaNacimientoInput, passwordInput, passwordConfirmInput].filter(Boolean);
  const today = new Date();
  const fechaMaximaMenorEdad = new Date(today);

  fechaMaximaMenorEdad.setFullYear(fechaMaximaMenorEdad.getFullYear() - 18);
  fechaMaximaMenorEdad.setDate(fechaMaximaMenorEdad.getDate() - 1);

  function actualizarEstadoCajaContrasena(cumpleTodo) {
    if (!passwordRequirementsBox) {
      return;
    }

    passwordRequirementsBox.classList.remove("alert-light", "alert-success", "border-success", "bg-success", "bg-opacity-10");

    if (cumpleTodo) {
      passwordRequirementsBox.classList.add("alert-success", "border-success", "bg-success", "bg-opacity-10");
      return;
    }

    passwordRequirementsBox.classList.add("alert-light", "border");
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

  function validarLongitudTexto(campo, minimo, maximo, mensajeMinimo, mensajeMaximo) {
    if (!campo) {
      return true;
    }

    const valor = campo.value.trim();

    if (!valor) {
      campo.setCustomValidity("");
      actualizarEstadoCampo(campo);
      return true;
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

    campo.setCustomValidity("");
    actualizarEstadoCampo(campo);
    return true;
  }

  function validarEmail() {
    if (!emailInput) {
      return true;
    }

    const emailNormalizado = limitarUnSoloArroba(emailInput.value.trim().toLowerCase());

    if (emailInput.value !== emailNormalizado) {
      emailInput.value = emailNormalizado;
    }

    const email = emailNormalizado;
    if (!email) {
      emailInput.setCustomValidity("");
      actualizarEstadoCampo(emailInput);
      return true;
    }

    if (email.includes(" ")) {
      emailInput.setCustomValidity("El correo electrónico no puede contener espacios.");
      actualizarEstadoCampo(emailInput);
      return false;
    }

    const cantidadArrobas = (email.match(/@/g) || []).length;
    if (cantidadArrobas !== 1) {
      emailInput.setCustomValidity("El correo electrónico debe contener exactamente 1 símbolo @.");
      actualizarEstadoCampo(emailInput);
      return false;
    }

    const dominio = email.split("@").pop() || "";
    const dominioValido = /^(?:[A-Za-z0-9-]+\.)+(?:com|co|edu\.co|com\.co)$/i.test(dominio);

    if (!dominioValido) {
      emailInput.setCustomValidity("El correo electrónico debe terminar en .com, .co, .edu.co o .com.co.");
      actualizarEstadoCampo(emailInput);
      return false;
    }

    emailInput.setCustomValidity("");
    actualizarEstadoCampo(emailInput);
    return true;
  }

  function validarNumeroDocumento() {
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

  function validarLocalidad() {
    if (!localidadInput) {
      return true;
    }

    const tieneLocalidad = String(localidadInput.value || "").trim() !== "";
    localidadInput.setCustomValidity(tieneLocalidad ? "" : "Selecciona una localidad.");
    actualizarEstadoCampo(localidadInput);
    return tieneLocalidad;
  }

  function validarNombreCompleto(campo, minimo, maximo, mensajeMinimo, mensajeMaximo) {
    return validarLongitudTexto(campo, minimo, maximo, mensajeMinimo, mensajeMaximo);
  }

  function sincronizarValidacionCampo(campo) {
    if (!campo) {
      return;
    }

    campo.setCustomValidity(campo.checkValidity() ? "" : campo.validationMessage);
    actualizarEstadoCampo(campo);
  }

  function obtenerErroresFormulario() {
    return Array.from(new Set(
      camposValidacionRapida
        .map((campo) => campo.validationMessage)
        .filter((mensaje) => Boolean(mensaje)),
    ));
  }

  function validarFechaNacimiento() {
    if (!fechaNacimientoInput) {
      return true;
    }

    if (!fechaNacimientoInput.value) {
      fechaNacimientoInput.setCustomValidity("");
      actualizarEstadoCampo(fechaNacimientoInput);
      return true;
    }

    const esMenor = fechaNacimientoInput.value <= formatDate(fechaMaximaMenorEdad);

    if (!esMenor) {
      fechaNacimientoInput.setCustomValidity("La fecha debe corresponder a un menor de edad.");
      actualizarEstadoCampo(fechaNacimientoInput);
      return false;
    }

    fechaNacimientoInput.setCustomValidity("");
    actualizarEstadoCampo(fechaNacimientoInput);
    return true;
  }

  function validarCelular() {
    if (!celularInput) {
      return true;
    }

    normalizarSoloDigitos(celularInput);

    const esValido = /^3\d{9}$/.test(celularInput.value);
    celularInput.setCustomValidity(esValido ? "" : "El celular debe iniciar con 3 y tener 10 dígitos.");
    actualizarEstadoCampo(celularInput);
    return esValido;
  }

  function actualizarCoincidenciaContrasena() {
    if (!passwordInput || !passwordConfirmInput) {
      return;
    }

    const password = passwordInput.value;
    const passwordConfirm = passwordConfirmInput.value;
    const tieneMin = /[a-z]/.test(password);
    const tieneMay = /[A-Z]/.test(password);
    const tieneNum = /\d/.test(password);
    const tieneEsp = /[@$!%*?&]/.test(password);
    const tieneLongitud = password.length >= 8;
    const cumpleTodo = tieneMin && tieneMay && tieneNum && tieneEsp && tieneLongitud;

    actualizarRequisito(reqMinusculas, tieneMin, "Mínimo una letra minúscula (a-z)");
    actualizarRequisito(reqMayusculas, tieneMay, "Mínimo una letra mayúscula (A-Z)");
    actualizarRequisito(reqNumeros, tieneNum, "Mínimo un número (0-9)");
    actualizarRequisito(reqEspeciales, tieneEsp, "Mínimo un carácter especial (@$!%*?&)");
    actualizarRequisito(reqLongitud, tieneLongitud, "Mínimo 8 caracteres" + (password.length > 0 ? " (" + password.length + "/8)" : ""));
    actualizarEstadoCajaContrasena(cumpleTodo);

    if (passwordConfirm.length === 0) {
      passwordConfirmInput.setCustomValidity("");
      if (mensajeCoincidencia) {
        mensajeCoincidencia.textContent = "";
      }
      actualizarEstadoCampo(passwordInput);
      actualizarEstadoCampo(passwordConfirmInput);
      return;
    }

    passwordInput.setCustomValidity(cumpleTodo ? "" : "La contraseña no cumple los requisitos.");

    if (password !== passwordConfirm) {
      passwordConfirmInput.setCustomValidity("Las contraseñas no coinciden.");
      if (mensajeCoincidencia) {
        mensajeCoincidencia.innerHTML = '<span class="text-danger">✗ No coinciden</span>';
      }
      actualizarEstadoCampo(passwordInput);
      actualizarEstadoCampo(passwordConfirmInput);
      return;
    }

    passwordConfirmInput.setCustomValidity("");
    if (mensajeCoincidencia) {
      mensajeCoincidencia.innerHTML = '<span class="text-success">✓ Coinciden</span>';
    }

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
        validarNombreCompleto(nombresInput, 3, 30, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres.");
      }

      if (campo === apellidosInput) {
        validarNombreCompleto(apellidosInput, 3, 40, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres.");
      }

      if (campo === emailInput) {
        validarEmail();
      }

      if (campo === fechaNacimientoInput) {
        validarFechaNacimiento();
      }

      if (campo === celularInput) {
        validarCelular();
      }

      if (campo === numeroDocumentoInput) {
        validarNumeroDocumento();
      }

      if (campo === localidadInput) {
        validarLocalidad();
        return;
      }

      if (campo === tipoDocumentoInput) {
        sincronizarValidacionCampo(campo);
        return;
      }

      sincronizarValidacionCampo(campo);
    });

    campo.addEventListener("blur", () => {
      actualizarEstadoCampo(campo);
    });
  });

  if (passwordInput && passwordConfirmInput) {
    passwordInput.addEventListener("input", actualizarCoincidenciaContrasena);
    passwordConfirmInput.addEventListener("input", actualizarCoincidenciaContrasena);
    actualizarCoincidenciaContrasena();
  }

  if (nombresInput) {
    nombresInput.addEventListener("input", () => validarNombreCompleto(nombresInput, 3, 30, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres."));
  }

  if (apellidosInput) {
    apellidosInput.addEventListener("input", () => validarNombreCompleto(apellidosInput, 3, 40, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres."));
  }

  if (emailInput) {
    emailInput.addEventListener("input", validarEmail);
  }

  if (numeroDocumentoInput) {
    numeroDocumentoInput.addEventListener("input", validarNumeroDocumento);
  }

  if (localidadInput) {
    localidadInput.addEventListener("change", validarLocalidad);
    localidadInput.addEventListener("input", validarLocalidad);
  }

  if (celularInput) {
    celularInput.addEventListener("input", validarCelular);
  }

  if (fechaNacimientoInput) {
    fechaNacimientoInput.addEventListener("input", validarFechaNacimiento);
  }

  camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));

  validarNombreCompleto(nombresInput, 3, 30, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres.");
  validarNombreCompleto(apellidosInput, 3, 40, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres.");
  validarEmail();
  validarNumeroDocumento();
  validarLocalidad();
  validarCelular();
  validarFechaNacimiento();

  form.addEventListener("submit", (evento) => {
    validarNombreCompleto(nombresInput, 3, 30, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres.");
    validarNombreCompleto(apellidosInput, 3, 40, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres.");
    validarEmail();
    actualizarCoincidenciaContrasena();
    validarFechaNacimiento();
    validarCelular();
    validarNumeroDocumento();
    validarLocalidad();

    camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));
    actualizarEstadoCampo(passwordInput);
    actualizarEstadoCampo(passwordConfirmInput);

    if (!form.checkValidity()) {
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
      title: "¿Crear usuario?",
      text: "El formulario está completo y listo para enviarse.",
      showCancelButton: true,
      confirmButtonText: "Sí, crear",
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