const LIMITE_IMAGEN_MB = 6;
const LIMITE_VIDEO_MB = 100;
const MENSAJE_LIMITE_IMAGEN = `La imagen supera el límite de ${LIMITE_IMAGEN_MB} MB`;
const MENSAJE_LIMITE_VIDEO = `El video supera el límite de ${LIMITE_VIDEO_MB} MB`;
const MENSAJE_LIMITE_THUMBNAIL = `La miniatura supera el límite de ${LIMITE_IMAGEN_MB} MB`;

function publicacionCrearMostrarErrorSwal(titulo, errores) {
  if (typeof Swal === "undefined") {
    return;
  }
  Swal.fire({
    icon: "error",
    title: titulo,
    text: errores.join(" "),
    confirmButtonColor: "#198754",
  });
}

function publicacionCrearRechazarVideo(inputVideo, previewVideo, wrapperThumbnail, errores) {
  inputVideo.value = "";
  if (previewVideo) {
    previewVideo.innerHTML = "";
  }
  if (wrapperThumbnail) {
    wrapperThumbnail.style.display = "none";
  }
  publicacionCrearMostrarErrorSwal("Video no válido", errores);
}

function publicacionCrearRechazarThumbnail(inputThumbnail, previewThumbnail, errores) {
  inputThumbnail.value = "";
  if (previewThumbnail) {
    previewThumbnail.innerHTML = "";
  }
  publicacionCrearMostrarErrorSwal("Miniatura no válida", errores);
}

function publicacionCrearRechazarImagenes(inputImagenes, alertImagenes, previewImagenes, errores) {
  publicacionMostrarAlertaImagenes(alertImagenes, errores.join(" "));
  inputImagenes.value = "";
  previewImagenes.innerHTML = "";
}

function publicacionCrearValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes) {
  if (!inputImagenes?.files?.length) {
    publicacionOcultarAlertaImagenes(alertImagenes);
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivosImagen(
    inputImagenes.files,
    inputImagenes,
    MENSAJE_LIMITE_IMAGEN,
  );
  if (!resultado.valido) {
    publicacionCrearRechazarImagenes(inputImagenes, alertImagenes, previewImagenes, resultado.errores);
    return resultado;
  }
  publicacionOcultarAlertaImagenes(alertImagenes);
  return resultado;
}

function publicacionCrearValidarBloqueVideo(inputVideo, previewVideo, wrapperThumbnail) {
  if (!inputVideo?.files?.length) {
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivoUnico(
    inputVideo.files[0],
    inputVideo,
    MENSAJE_LIMITE_VIDEO,
  );
  if (!resultado.valido) {
    publicacionCrearRechazarVideo(inputVideo, previewVideo, wrapperThumbnail, resultado.errores);
    return resultado;
  }
  return resultado;
}

function publicacionCrearValidarBloqueThumbnail(inputThumbnail, previewThumbnail) {
  if (!inputThumbnail?.files?.length) {
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivoUnico(
    inputThumbnail.files[0],
    inputThumbnail,
    MENSAJE_LIMITE_THUMBNAIL,
  );
  if (!resultado.valido) {
    publicacionCrearRechazarThumbnail(inputThumbnail, previewThumbnail, resultado.errores);
    return resultado;
  }
  return resultado;
}

function publicacionCrearRecolectarErrores(bloques) {
  return bloques.flatMap((bloque) => (bloque.valido ? [] : bloque.errores));
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createPublicacionForm");
  if (!form) {
    return;
  }

  const LIMITE_BYTES = LIMITE_IMAGEN_MB * 1024 * 1024;
  const inputImagenes = document.getElementById("inputImagenes");
  const inputVideo = document.getElementById("inputVideo");
  const inputThumbnail = document.getElementById("inputThumbnail");
  const previewImagenes = document.getElementById("previewImagenes");
  const previewVideo = document.getElementById("previewVideo");
  const previewThumbnail = document.getElementById("previewThumbnail");
  const alertImagenes = document.getElementById("alertImagenes");
  const wrapperThumbnail = document.getElementById("wrapperThumbnail");
  const tituloInput = form.querySelector('[name="titulo"]');
  const contenidoInput = form.querySelector('[name="contenido"]');
  const categoriaInput = form.querySelector('[name="categoria_id"]');
  const estadoInput = form.querySelector('[name="estado"]');
  const camposValidacion = [tituloInput, contenidoInput, categoriaInput, estadoInput].filter(Boolean);

  publicacionSuprimirValidacionNativa(form);
  publicacionEnlazarMaxlength(tituloInput, null);
  publicacionEnlazarMaxlength(contenidoInput, "pub_contenido_contador");

  function validarArchivos() {
    const bloques = [
      publicacionCrearValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes),
      publicacionCrearValidarBloqueVideo(inputVideo, previewVideo, wrapperThumbnail),
      publicacionCrearValidarBloqueThumbnail(inputThumbnail, previewThumbnail),
    ];
    const errores = publicacionCrearRecolectarErrores(bloques);
    return { valido: errores.length === 0, errores };
  }

  if (inputImagenes) {
    inputImagenes.addEventListener("change", () => {
      const bloque = publicacionCrearValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes);
      if (!bloque.valido) {
        return;
      }
      publicacionRenderPreviewImagenes(inputImagenes.files, previewImagenes, LIMITE_BYTES);
    });
  }

  if (inputVideo) {
    inputVideo.addEventListener("change", () => {
      const bloque = publicacionCrearValidarBloqueVideo(inputVideo, previewVideo, wrapperThumbnail);
      if (!bloque.valido) {
        return;
      }
      publicacionRenderPreviewVideo(inputVideo.files[0], previewVideo, wrapperThumbnail);
    });
  }

  if (inputThumbnail) {
    inputThumbnail.addEventListener("change", () => {
      const bloque = publicacionCrearValidarBloqueThumbnail(inputThumbnail, previewThumbnail);
      if (!bloque.valido) {
        return;
      }
      publicacionRenderPreviewThumbnail(inputThumbnail.files[0], previewThumbnail);
    });
  }

  form.addEventListener("submit", (evento) => {
    const validacionArchivos = validarArchivos();
    if (!validacionArchivos.valido) {
      evento.preventDefault();
      evento.stopPropagation();
      form.classList.add("was-validated");
      publicacionMostrarErroresSwal(validacionArchivos.errores);
      return;
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
      title: "¿Crear publicación?",
      text: "El formulario está completo y listo para enviarse.",
      confirmText: "Sí, crear",
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        form.submit();
      }
    });
  });
});
