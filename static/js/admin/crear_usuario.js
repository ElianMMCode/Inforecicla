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

  return texto.slice(0, primerArroba + 1) + texto.slice(primerArroba + 1).replaceAll("@", "");
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
  const fechaMaximaMenorEdad = formatDate(new Date(today.getFullYear() - 18, today.getMonth(), today.getDate() - 1));

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
    if (!dominio.endsWith((".com", ".co", ".edu.co", ".com.co"))) {
      emailInput.setCustomValidity("El correo electrónico debe terminar en .com, .co, .edu.co o .com.co.");
      actualizarEstadoCampo(emailInput);
      return false;
    }

    emailInput.setCustomValidity("");
    actualizarEstadoCampo(emailInput);
    return true;
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
        validarFechaNacimiento(fechaNacimientoInput, fechaMaximaMenorEdad);
      }

      if (campo === celularInput) {
        validarCelular(celularInput);
      }

      if (campo === numeroDocumentoInput) {
        validarNumeroDocumento(numeroDocumentoInput);
      }

      if (campo === localidadInput) {
        validarLocalidad(localidadInput, "Selecciona una localidad.");
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
    numeroDocumentoInput.addEventListener("input", () => validarNumeroDocumento(numeroDocumentoInput));
  }

  if (localidadInput) {
    localidadInput.addEventListener("change", () => validarLocalidad(localidadInput, "Selecciona una localidad."));
    localidadInput.addEventListener("input", () => validarLocalidad(localidadInput, "Selecciona una localidad."));
  }

  if (celularInput) {
    celularInput.addEventListener("input", () => validarCelular(celularInput));
  }

  if (fechaNacimientoInput) {
    fechaNacimientoInput.addEventListener("input", () => validarFechaNacimiento(fechaNacimientoInput, fechaMaximaMenorEdad));
  }

  camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));

  validarNombreCompleto(nombresInput, 3, 30, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres.");
  validarNombreCompleto(apellidosInput, 3, 40, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres.");
  validarEmail();
  validarNumeroDocumento(numeroDocumentoInput);
  validarLocalidad(localidadInput, "Selecciona una localidad.");
  validarCelular(celularInput);
  validarFechaNacimiento(fechaNacimientoInput, fechaMaximaMenorEdad);

  form.addEventListener("submit", (evento) => {
    validarNombreCompleto(nombresInput, 3, 30, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres.");
    validarNombreCompleto(apellidosInput, 3, 40, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres.");
    validarEmail();
    actualizarCoincidenciaContrasena();
    validarFechaNacimiento(fechaNacimientoInput, fechaMaximaMenorEdad);
    validarCelular(celularInput);
    validarNumeroDocumento(numeroDocumentoInput);
    validarLocalidad(localidadInput, "Selecciona una localidad.");

    camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));
    actualizarEstadoCampo(passwordInput);
    actualizarEstadoCampo(passwordConfirmInput);

    if (!form.checkValidity()) {
      evento.preventDefault();
      evento.stopPropagation();
      form.classList.add("was-validated");
      mostrarErroresSwal(obtenerErroresFormulario(camposValidacionRapida));

      return;
    }

    evento.preventDefault();
    form.classList.add("was-validated");

    confirmarEnvioSwal({
      title: "¿Crear usuario?",
      text: "El formulario está completo y listo para enviarse.",
      confirmText: "Sí, crear",
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        form.submit();
      }
    });
  });
});
