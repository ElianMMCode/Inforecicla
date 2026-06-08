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

function publicacionObtenerErroresFormulario(campos) {
  return Array.from(
    new Set(campos.map((campo) => campo.validationMessage).filter(Boolean)),
  );
}

function publicacionMostrarErroresSwal(errores) {
  if (typeof Swal === "undefined" || !errores || errores.length === 0) {
    return;
  }
  const html = `<div class="text-start"><ul class="mb-0 ps-3">${errores
    .map((error) => `<li>${publicacionEscaparHtml(error)}</li>`)
    .join("")}</ul></div>`;
  Swal.fire({
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
      publicacionMostrarErroresSwal(publicacionObtenerErroresFormulario(camposValidacion));
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
