function publicacionSuprimirValidacionNativa(formulario) {
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

function _mensajePublicacionES(campo) {
  let etiqueta = '';
  if (campo.name === 'titulo') etiqueta = 'T\u00edtulo';
  else if (campo.name === 'contenido') etiqueta = 'Contenido';
  else if (campo.name === 'categoria_id') etiqueta = 'Categor\u00eda';
  else if (campo.name === 'estado') etiqueta = 'Estado';
  else if (campo.name === 'multimedia') etiqueta = 'Multimedia';
  else etiqueta = campo.name.charAt(0).toUpperCase() + campo.name.slice(1);

  if (campo.validity.valid && !campo.validity.customError) return '';
  if (campo.validity.valueMissing) return etiqueta + ' es obligatorio.';
  if (campo.validity.patternMismatch) return etiqueta + ': Debe contener al menos 3 caracteres e incluir letras.';
  if (campo.validity.tooShort) return etiqueta + ': Debe tener al menos ' + campo.minLength + ' caracteres.';
  if (campo.validity.tooLong) return etiqueta + ': Debe tener m\u00e1ximo ' + campo.maxLength + ' caracteres.';
  if (campo.validity.typeMismatch) return etiqueta + ': El formato no es correcto.';
  if (campo.validity.customError) return etiqueta + ': ' + campo.validationMessage;
  if (campo.validity.badInput) return etiqueta + ': El valor ingresado no es v\u00e1lido.';
  return etiqueta + ': El valor ingresado no es v\u00e1lido.';
}

function publicacionObtenerErroresFormulario(campos) {
  return Array.from(
    new Set(campos.map(function (c) { return _mensajePublicacionES(c); }).filter(Boolean)),
  );
}

function publicacionMostrarErroresSwal(errores) {
  if (typeof Swal === "undefined" || !errores || errores.length === 0) {
    return;
  }
  const html = `<div class="text-start">${errores
    .map(function (e) { return publicacionEscaparHtml(e); })
    .join(' ')}</div>`;
  return Swal.fire({
    icon: "error",
    title: "Corrige los campos",
    html,
    confirmButtonColor: "#198754",
  });
}

function publicacionEscaparHtml(texto) {
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

function publicacionConfirmarEnvioSwal(mensaje) {
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
    return Promise.resolve({
      isConfirmed: globalThis.confirm(mensaje.text || mensaje.title || ""),
    });
  }
  return Swal.fire(configuracion);
}

function publicacionValidarTamanoArchivos(archivos, limiteBytes, mensajeLimite) {
  if (!archivos || archivos.length === 0) {
    return { valido: true, grandes: [] };
  }
  const grandes = Array.from(archivos).filter((archivo) => archivo.size > limiteBytes);
  if (grandes.length === 0) {
    return { valido: true, grandes: [] };
  }
  const nombres = grandes.map((archivo) => `"${archivo.name}"`).join(", ");
  return {
    valido: false,
    grandes,
    mensaje: `${mensajeLimite}: ${nombres}.`,
  };
}

function publicacionRenderPreviewImagenes(archivos, contenedor, limiteBytes) {
  if (!contenedor) {
    return;
  }
  contenedor.innerHTML = "";
  const resultado = publicacionValidarTamanoArchivos(
    archivos,
    limiteBytes,
    "Las siguientes imágenes superan el límite",
  );
  if (!resultado.valido) {
    return resultado;
  }
  Array.from(archivos).forEach((archivo) => {
    const reader = new FileReader();
    reader.onload = (evento) => {
      const wrapper = document.createElement("div");
      wrapper.style.cssText = "position:relative;width:80px;height:80px;";
      const img = document.createElement("img");
      img.src = evento.target.result;
      img.style.cssText =
        "width:80px;height:80px;object-fit:cover;border-radius:8px;border:2px solid #198754;";
      wrapper.appendChild(img);
      contenedor.appendChild(wrapper);
    };
    reader.readAsDataURL(archivo);
  });
  return resultado;
}

function publicacionRenderPreviewVideo(archivo, contenedor, wrapperThumbnail) {
  if (!contenedor) {
    return;
  }
  contenedor.innerHTML = "";
  if (!archivo) {
    if (wrapperThumbnail) {
      wrapperThumbnail.style.display = "none";
    }
    return;
  }
  const url = URL.createObjectURL(archivo);
  const video = document.createElement("video");
  video.src = url;
  video.controls = true;
  video.style.cssText =
    "width:100%;max-height:200px;border-radius:8px;border:2px solid #198754;";
  contenedor.appendChild(video);
  if (wrapperThumbnail) {
    wrapperThumbnail.style.display = "";
  }
}

function publicacionRenderPreviewThumbnail(archivo, contenedor) {
  if (!contenedor) {
    return;
  }
  contenedor.innerHTML = "";
  if (!archivo) {
    return;
  }
  const reader = new FileReader();
  reader.onload = (evento) => {
    const img = document.createElement("img");
    img.src = evento.target.result;
    img.style.cssText =
      "height:80px;border-radius:8px;border:2px solid #198754;";
    contenedor.appendChild(img);
  };
  reader.readAsDataURL(archivo);
}

function publicacionMostrarAlertaImagenes(alerta, mensaje) {
  if (!alerta) {
    return;
  }
  alerta.textContent = mensaje;
  alerta.classList.remove("d-none");
  alerta.scrollIntoView({ behavior: "smooth", block: "center" });
}

function _recolectarErroresValidacion(camposValidacion) {
  const errs = [];
  const invalidFields = [];
  for (const campo of camposValidacion) {
    if (campo && !campo.checkValidity()) {
      const msg = _mensajePublicacionES(campo);
      if (msg) {
        errs.push(msg);
        invalidFields.push({ field: campo, msg: msg });
      }
    }
  }
  return { errs, invalidFields };
}

function _marcarCamposInvalidos(prom, invalidFields) {
  prom.then(function () {
    for (const item of invalidFields) {
      item.field.classList.add('is-invalid');
      const contenedor = item.field.closest('.col-12, .col-md-6, .col-md-12, .mb-3');
      if (contenedor) {
        const fb = contenedor.querySelector('.invalid-feedback');
        if (fb) fb.textContent = item.msg;
      }
    }
  });
}

function publicacionBindEnvio({ formulario, camposValidacion, confirmar, antesDeEnviar }) {
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
      const { errs, invalidFields } = _recolectarErroresValidacion(camposValidacion);
      const prom = publicacionMostrarErroresSwal(errs);
      if (prom?.then) {
        _marcarCamposInvalidos(prom, invalidFields);
      }
      return;
    }
    formulario.classList.add("was-validated");
    publicacionConfirmarEnvioSwal(confirmar).then((resultado) => {
      if (resultado.isConfirmed) {
        formulario.submit();
      }
    });
  });
}
