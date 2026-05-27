document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createUserForm");

  if (!form) {
    return;
  }

  const fechaNacimientoInput = form.querySelector('[name="fechaNacimiento"]');
  const celularInput = form.querySelector('[name="celular"]');
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

  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const today = new Date();
  const fechaMaximaMenorEdad = new Date(today);
  fechaMaximaMenorEdad.setFullYear(fechaMaximaMenorEdad.getFullYear() - 18);
  fechaMaximaMenorEdad.setDate(fechaMaximaMenorEdad.getDate() - 1);

  if (fechaNacimientoInput) {
    fechaNacimientoInput.max = formatDate(fechaMaximaMenorEdad);
    fechaNacimientoInput.addEventListener("input", validarFechaNacimiento);
    fechaNacimientoInput.addEventListener("blur", validarFechaNacimiento);
  }

  if (celularInput) {
    celularInput.addEventListener("input", () => {
      celularInput.value = celularInput.value.replace(/\D/g, "").slice(0, 10);
      validarCelular();
      actualizarEstadoCampo(celularInput);
    });
    celularInput.addEventListener("blur", () => {
      validarCelular();
      actualizarEstadoCampo(celularInput);
    });
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
    actualizarRequisito(reqLongitud, tieneLongitud, `Mínimo 8 caracteres${password.length > 0 ? ` (${password.length}/8)` : ""}`);
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
      if (campo === fechaNacimientoInput) {
        validarFechaNacimiento();
      }
      if (campo === celularInput) {
        validarCelular();
      }

      campo.setCustomValidity(campo.checkValidity() ? "" : campo.validationMessage);
      actualizarEstadoCampo(campo);
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

  camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));

  form.addEventListener("submit", (evento) => {
    actualizarCoincidenciaContrasena();
    validarFechaNacimiento();
    validarCelular();

    camposObligatorios.forEach((campo) => actualizarEstadoCampo(campo));
    actualizarEstadoCampo(passwordInput);
    actualizarEstadoCampo(passwordConfirmInput);

    if (!form.checkValidity()) {
      evento.preventDefault();
      evento.stopPropagation();
      form.classList.add("was-validated");

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