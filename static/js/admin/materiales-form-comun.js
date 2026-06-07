// Helpers compartidos entre los formularios de Materiales, Tipos de Material
// y Categorías de Material del panel de administración.
// Cargado como script clásico (sin type="module") y expuesto en window para
// evitar colisiones con publicacion-form-comun.js y usuario-form-comun.js.
//
// API estilo espejo de usuario-form-comun.js:
//   - materialesActualizarEstadoCampo(campo)
//   - materialesValidarTexto(campo, maximo, mensajeVacio, mensajeMaximo)
//   - materialesValidarSelect(campo, mensajeVacio)
//   - materialesRegistrarValidacionCampo(campo, handler)
//   - materialesSincronizarEstadoCampo(campo)
//   - materialesSuprimirValidacionNativa(formulario)
//   - materialesObtenerErroresFormulario(campos)
//   - materialesMostrarErroresSwal(errores)
//   - materialesEscaparHtml(texto)
//   - materialesConfirmarEnvioSwal(mensaje)
//   - materialesValidarTamanoImagen(archivo, limiteBytes)
//   - materialesBindEnvio({ formulario, camposValidacion, confirmar, antesDeEnviar })
//   - materialesInicializarFormulario(opciones)  ← punto de entrada unificado

const MATERIALES_COLOR_CONFIRMAR = "#198754";
const MATERIALES_COLOR_CANCELAR = "#6c757d";
const MATERIALES_LIMITE_NOMBRE_MIN = 1;
const MATERIALES_LIMITE_NOMBRE_MAX = 30;
const MATERIALES_LIMITE_DESCRIPCION_MAX = 500;
const MATERIALES_LIMITE_IMAGEN_BYTES = 5 * 1024 * 1024;

function materialesSuprimirValidacionNativa(formulario) {
  if (!formulario) {
    return;
  }
  formulario.addEventListener(
    "invalid",
    (evento) => {
      evento.preventDefault();
    },
    true,
  );
}

function materialesObtenerErroresFormulario(campos) {
  return Array.from(
    new Set(campos.map((campo) => campo.validationMessage).filter(Boolean)),
  );
}

function materialesEscaparHtml(texto) {
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

function materialesMostrarErroresSwal(errores) {
  if (typeof Swal === "undefined" || !errores || errores.length === 0) {
    return;
  }
  const html = `<div class="text-start"><ul class="mb-0 ps-3">${errores
    .map((error) => `<li>${materialesEscaparHtml(error)}</li>`)
    .join("")}</ul></div>`;
  Swal.fire({
    icon: "error",
    title: "Corrige los campos",
    html,
    confirmButtonColor: MATERIALES_COLOR_CONFIRMAR,
  });
}

function materialesConfirmarEnvioSwal(mensaje) {
  const configuracion = {
    icon: "question",
    title: mensaje.title || "¿Confirmar?",
    text: mensaje.text || "",
    showCancelButton: true,
    confirmButtonText: mensaje.confirmText || "Sí",
    cancelButtonText: "Cancelar",
    confirmButtonColor: MATERIALES_COLOR_CONFIRMAR,
    cancelButtonColor: MATERIALES_COLOR_CANCELAR,
  };
  if (typeof Swal === "undefined") {
    return Promise.resolve({
      isConfirmed: window.confirm(mensaje.text || mensaje.title || ""),
    });
  }
  return Swal.fire(configuracion);
}

function materialesValidarTamanoImagen(archivo, limiteBytes) {
  if (!archivo) {
    return { valido: true };
  }
  if (archivo.size > limiteBytes) {
    return {
      valido: false,
      mensaje: `La imagen "${archivo.name}" supera el límite de 5 MB.`,
    };
  }
  return { valido: true };
}

function materialesActualizarEstadoCampo(campo) {
  if (!campo) {
    return;
  }
  const valido = campo.checkValidity();
  const tieneValor =
    campo.type === "file"
      ? campo.files && campo.files.length > 0
      : String(campo.value || "").trim() !== "";
  campo.classList.toggle("is-valid", valido && tieneValor);
  campo.classList.toggle("is-invalid", !valido && (tieneValor || campo.required));
}

function materialesSincronizarEstadoCampo(campo) {
  if (!campo) {
    return;
  }
  campo.setCustomValidity(campo.checkValidity() ? "" : campo.validationMessage);
  materialesActualizarEstadoCampo(campo);
}

function materialesValidarTexto(campo, maximo, mensajeVacio, mensajeMaximo) {
  if (!campo) {
    return true;
  }
  const valor = String(campo.value || "").trim();
  if (!valor) {
    campo.setCustomValidity(campo.required ? (mensajeVacio || "Este campo es obligatorio.") : "");
    materialesActualizarEstadoCampo(campo);
    return !campo.required;
  }
  if (valor.length > maximo) {
    campo.setCustomValidity(mensajeMaximo || `Máximo ${maximo} caracteres.`);
    materialesActualizarEstadoCampo(campo);
    return false;
  }
  campo.setCustomValidity("");
  materialesActualizarEstadoCampo(campo);
  return true;
}

function materialesValidarSelect(campo, mensajeVacio) {
  if (!campo) {
    return true;
  }
  const tieneValor = String(campo.value || "").trim() !== "";
  if (campo.required) {
    campo.setCustomValidity(tieneValor ? "" : (mensajeVacio || "Selecciona una opción."));
  } else {
    campo.setCustomValidity("");
  }
  materialesActualizarEstadoCampo(campo);
  return tieneValor || !campo.required;
}

function materialesRegistrarValidacionCampo(campo, handler) {
  if (!campo) {
    return;
  }
  const evento = campo.tagName === "SELECT" || campo.type === "file" ? "change" : "input";
  campo.addEventListener(evento, handler);
  campo.addEventListener("blur", () => materialesActualizarEstadoCampo(campo));
}

function materialesBindEnvio({ formulario, camposValidacion, confirmar, antesDeEnviar }) {
  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    evento.stopPropagation();
    if (typeof antesDeEnviar === "function") {
      const resultado = antesDeEnviar(formulario);
      if (resultado === false) {
        return;
      }
    }
    if (!formulario.checkValidity()) {
      formulario.classList.add("was-validated");
      materialesMostrarErroresSwal(
        materialesObtenerErroresFormulario(camposValidacion),
      );
      return;
    }
    formulario.classList.add("was-validated");
    materialesConfirmarEnvioSwal(confirmar).then((resultado) => {
      if (resultado.isConfirmed) {
        formulario.submit();
      }
    });
  });
}

function materialesValidarCampo(campo) {
  if (!campo) {
    return true;
  }
  return campo.esSelect
    ? materialesValidarSelect(campo.elemento, campo.mensaje || "")
    : materialesValidarTexto(
        campo.elemento,
        campo.maxLength,
        campo.mensaje || "",
        campo.mensajeOpcional || "",
      );
}

function materialesCrearValidadorImagen(imagen) {
  if (!imagen) {
    return null;
  }
  const inputImagen = document.getElementById(imagen.inputId);
  const alertaImagen = document.getElementById(imagen.alertaId);
  if (!inputImagen) {
    return null;
  }
  return () => {
    if (!inputImagen.files || inputImagen.files.length === 0) {
      if (alertaImagen) {
        alertaImagen.classList.add("d-none");
        alertaImagen.textContent = "";
      }
      materialesActualizarEstadoCampo(inputImagen);
      return true;
    }
    const archivo = inputImagen.files[0];
    const resultado = materialesValidarTamanoImagen(archivo, imagen.maxBytes);
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
  };
}

function materialesInicializarFormulario(opciones) {
  const form = document.getElementById(opciones.formularioId);
  if (!form) {
    return;
  }
  const campos = (opciones.campos || [])
    .map((cfg) => ({ ...cfg, elemento: form.querySelector(`[name="${cfg.name}"]`) }))
    .filter((campo) => campo.elemento);
  const camposValidacion = campos.map((campo) => campo.elemento);

  materialesSuprimirValidacionNativa(form);
  campos.forEach((campo) => {
    materialesRegistrarValidacionCampo(campo.elemento, () => materialesValidarCampo(campo));
  });

  const validarImagen = materialesCrearValidadorImagen(opciones.imagen);
  if (validarImagen) {
    const inputImagen = document.getElementById(opciones.imagen.inputId);
    inputImagen.addEventListener("change", validarImagen);
  }

  const antesDeEnviar = opciones.antesDeEnviar || (() => {
    campos.forEach((campo) => materialesValidarCampo(campo));
    camposValidacion.forEach(materialesActualizarEstadoCampo);
    return validarImagen ? validarImagen() : true;
  });

  camposValidacion.forEach(materialesActualizarEstadoCampo);

  materialesBindEnvio({
    formulario: form,
    camposValidacion,
    confirmar: opciones.confirmar,
    antesDeEnviar,
  });
}
