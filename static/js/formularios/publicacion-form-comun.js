const PUBLICACION_LIMITE_IMAGEN_MB = 6;
const PUBLICACION_LIMITE_VIDEO_MB = 100;
const PUBLICACION_MENSAJE_LIMITE_IMAGEN = `La imagen supera el límite de ${PUBLICACION_LIMITE_IMAGEN_MB} MB`;
const PUBLICACION_MENSAJE_LIMITE_VIDEO = `El video supera el límite de ${PUBLICACION_LIMITE_VIDEO_MB} MB`;
const PUBLICACION_MENSAJE_LIMITE_THUMBNAIL = `La miniatura supera el límite de ${PUBLICACION_LIMITE_IMAGEN_MB} MB`;
const PUBLICACION_BYTES_POR_MB = 1024 * 1024;
const PUBLICACION_IMAGEN_PREVIEW_ESTILO = "position:relative;width:80px;height:80px;";
const PUBLICACION_IMAGEN_PREVIEW_IMG_ESTILO =
  "width:80px;height:80px;object-fit:cover;border-radius:8px;border:2px solid #198754;";
const PUBLICACION_VIDEO_PREVIEW_ESTILO =
  "width:100%;max-height:200px;border-radius:8px;border:2px solid #198754;";
const PUBLICACION_COLOR_CONFIRMACION = "#198754";

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
    confirmButtonColor: PUBLICACION_COLOR_CONFIRMACION,
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
    confirmButtonColor: PUBLICACION_COLOR_CONFIRMACION,
    cancelButtonColor: "#6c757d",
  };
  if (typeof Swal === "undefined") {
    return Promise.resolve({
      isConfirmed: globalThis.confirm(mensaje.text || mensaje.title || ""),
    });
  }
  return Swal.fire(configuracion);
}

function publicacionMostrarErrorSwal(titulo, errores) {
  if (typeof Swal === "undefined") {
    return;
  }
  Swal.fire({
    icon: "error",
    title: titulo,
    text: errores.join(" "),
    confirmButtonColor: PUBLICACION_COLOR_CONFIRMACION,
  });
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
  publicacionAgregarImagenesAPreview(archivos, contenedor);
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
  publicacionAgregarVideoAPreview(archivo, contenedor);
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

function publicacionOcultarAlertaImagenes(alerta) {
  if (!alerta) {
    return;
  }
  alerta.textContent = "";
  alerta.classList.add("d-none");
}

function publicacionEnlazarMaxlength(campo, contadorId) {
  if (!campo) {
    return;
  }
  const maximo = Number.parseInt(campo.dataset.maxLength || campo.maxLength || "0", 10);
  const contador = contadorId ? document.getElementById(contadorId) : null;
  const actualizar = () => {
    if (campo.value.length > maximo) {
      campo.value = campo.value.slice(0, maximo);
    }
    if (contador) {
      contador.textContent = String(campo.value.length);
    }
  };
  campo.addEventListener("input", actualizar);
  actualizar();
}

function publicacionValidarTipoArchivo(archivo, tiposPermitidos) {
  if (!archivo || !tiposPermitidos || tiposPermitidos.length === 0) {
    return { valido: true };
  }
  const tipo = (archivo.type || "").toLowerCase();
  if (tiposPermitidos.includes(tipo)) {
    return { valido: true };
  }
  return {
    valido: false,
    mensaje: `Tipo de archivo no permitido (${tipo || "desconocido"}). Tipos válidos: ${tiposPermitidos.join(", ")}.`,
  };
}

function publicacionExtraerTiposAceptados(entradaArchivo) {
  if (!entradaArchivo?.accept) {
    return [];
  }
  return entradaArchivo.accept
    .split(",")
    .map((valor) => valor.trim().toLowerCase())
    .filter(Boolean);
}

function publicacionValidarArchivosImagen(archivos, entrada, mensajeLimite) {
  if (!archivos || archivos.length === 0) {
    return { valido: true, errores: [] };
  }
  const limite = Number.parseInt(entrada.dataset.maxSize || "0", 10);
  const tipos = publicacionExtraerTiposAceptados(entrada);
  const errores = [];
  Array.from(archivos).forEach((archivo) => {
    const tipo = publicacionValidarTipoArchivo(archivo, tipos);
    if (!tipo.valido) {
      errores.push(`"${archivo.name}": ${tipo.mensaje}`);
    } else if (limite && archivo.size > limite) {
      errores.push(`"${archivo.name}": ${mensajeLimite} (${(archivo.size / 1048576).toFixed(2)} MB).`);
    }
  });
  return { valido: errores.length === 0, errores };
}

function publicacionValidarArchivoUnico(archivo, entrada, mensajeLimite) {
  if (!archivo) {
    return { valido: true, errores: [] };
  }
  const limite = Number.parseInt(entrada.dataset.maxSize || "0", 10);
  const tipos = publicacionExtraerTiposAceptados(entrada);
  const errores = [];
  const tipo = publicacionValidarTipoArchivo(archivo, tipos);
  if (!tipo.valido) {
    errores.push(`"${archivo.name}": ${tipo.mensaje}`);
  } else if (limite && archivo.size > limite) {
    errores.push(`"${archivo.name}": ${mensajeLimite} (${(archivo.size / 1048576).toFixed(2)} MB).`);
  }
  return { valido: errores.length === 0, errores };
}

function publicacionAgregarImagenesAPreview(archivos, contenedor) {
  Array.from(archivos).forEach((archivo) => {
    const reader = new FileReader();
    reader.onload = (evento) => {
      const wrapper = document.createElement("div");
      wrapper.style.cssText = PUBLICACION_IMAGEN_PREVIEW_ESTILO;
      const img = document.createElement("img");
      img.src = evento.target.result;
      img.style.cssText = PUBLICACION_IMAGEN_PREVIEW_IMG_ESTILO;
      wrapper.appendChild(img);
      contenedor.appendChild(wrapper);
    };
    reader.readAsDataURL(archivo);
  });
}

function publicacionAgregarVideoAPreview(archivo, contenedor) {
  const url = URL.createObjectURL(archivo);
  const video = document.createElement("video");
  video.src = url;
  video.controls = true;
  video.style.cssText = PUBLICACION_VIDEO_PREVIEW_ESTILO;
  contenedor.appendChild(video);
}

function publicacionRechazarImagenes(inputImagenes, alertImagenes, previewImagenes, errores) {
  publicacionMostrarAlertaImagenes(alertImagenes, errores.join(" "));
  inputImagenes.value = "";
  if (previewImagenes) {
    previewImagenes.innerHTML = "";
  }
}

function publicacionRechazarVideo(inputVideo, previewVideo, wrapperThumbnail, errores) {
  inputVideo.value = "";
  if (previewVideo) {
    previewVideo.innerHTML = "";
  }
  if (wrapperThumbnail) {
    wrapperThumbnail.style.display = "none";
  }
  publicacionMostrarErrorSwal("Video no válido", errores);
}

function publicacionRechazarThumbnail(inputThumbnail, previewThumbnail, errores) {
  inputThumbnail.value = "";
  if (previewThumbnail) {
    previewThumbnail.innerHTML = "";
  }
  publicacionMostrarErrorSwal("Miniatura no válida", errores);
}

function publicacionValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes) {
  if (!inputImagenes?.files?.length) {
    publicacionOcultarAlertaImagenes(alertImagenes);
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivosImagen(
    inputImagenes.files,
    inputImagenes,
    PUBLICACION_MENSAJE_LIMITE_IMAGEN,
  );
  if (!resultado.valido) {
    publicacionRechazarImagenes(inputImagenes, alertImagenes, previewImagenes, resultado.errores);
    return resultado;
  }
  publicacionOcultarAlertaImagenes(alertImagenes);
  return resultado;
}

function publicacionValidarBloqueVideo(inputVideo, previewVideo, wrapperThumbnail) {
  if (!inputVideo?.files?.length) {
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivoUnico(
    inputVideo.files[0],
    inputVideo,
    PUBLICACION_MENSAJE_LIMITE_VIDEO,
  );
  if (!resultado.valido) {
    publicacionRechazarVideo(inputVideo, previewVideo, wrapperThumbnail, resultado.errores);
    return resultado;
  }
  return resultado;
}

function publicacionValidarBloqueThumbnail(inputThumbnail, previewThumbnail) {
  if (!inputThumbnail?.files?.length) {
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivoUnico(
    inputThumbnail.files[0],
    inputThumbnail,
    PUBLICACION_MENSAJE_LIMITE_THUMBNAIL,
  );
  if (!resultado.valido) {
    publicacionRechazarThumbnail(inputThumbnail, previewThumbnail, resultado.errores);
    return resultado;
  }
  return resultado;
}

function publicacionRecolectarErrores(bloques) {
  return bloques.flatMap((bloque) => (bloque.valido ? [] : bloque.errores));
}

function publicacionEjecutarValidaciones(bloques) {
  const errores = publicacionRecolectarErrores(bloques);
  return { valido: errores.length === 0, errores };
}

function publicacionObtenerCamposValidacion(form, nombres) {
  return nombres
    .map((nombre) => form.querySelector(`[name="${nombre}"]`))
    .filter(Boolean);
}

function publicacionInicializarControlesBasicos(form, titulo, contenido) {
  publicacionSuprimirValidacionNativa(form);
  publicacionEnlazarMaxlength(titulo, null);
  publicacionEnlazarMaxlength(contenido, "pub_contenido_contador");
}

function publicacionManejarEnvioFormulario(form, configuracionSwal, camposValidacion) {
  return form.addEventListener("submit", (evento) => {
    if (configuracionSwal.validadorArchivos) {
      const validacion = configuracionSwal.validadorArchivos();
      if (!validacion.valido) {
        evento.preventDefault();
        evento.stopPropagation();
        form.classList.add("was-validated");
        publicacionMostrarErroresSwal(validacion.errores);
        return;
      }
    }
    if (!form.checkValidity()) {
      evento.preventDefault();
      evento.stopPropagation();
      form.classList.add("was-validated");
      publicacionMostrarErroresSwal(publicacionObtenerErroresFormulario(camposValidacion));
      return;
    }
    evento.preventDefault();
    form.classList.add("was-validated");
    publicacionConfirmarEnvioSwal({
      title: configuracionSwal.title,
      text: configuracionSwal.text,
      confirmText: configuracionSwal.confirmText,
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        form.submit();
      }
    });
  });
}
