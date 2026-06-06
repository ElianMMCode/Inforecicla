const LIMITE_IMAGEN_MB_EDITAR = 6;
const LIMITE_VIDEO_MB_EDITAR = 100;
const MENSAJE_LIMITE_IMAGEN_EDITAR = `La imagen supera el límite de ${LIMITE_IMAGEN_MB_EDITAR} MB`;
const MENSAJE_LIMITE_VIDEO_EDITAR = `El video supera el límite de ${LIMITE_VIDEO_MB_EDITAR} MB`;
const MENSAJE_LIMITE_THUMBNAIL_EDITAR = `La miniatura supera el límite de ${LIMITE_IMAGEN_MB_EDITAR} MB`;

function publicacionEditarMostrarErrorSwal(titulo, errores) {
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

function publicacionEditarRechazarVideo(inputVideo, previewVideo, errores) {
  inputVideo.value = "";
  if (previewVideo) {
    previewVideo.innerHTML = "";
  }
  publicacionEditarMostrarErrorSwal("Video no válido", errores);
}

function publicacionEditarRechazarThumbnail(inputThumbnail, previewThumbnail, errores) {
  inputThumbnail.value = "";
  if (previewThumbnail) {
    previewThumbnail.innerHTML = "";
  }
  publicacionEditarMostrarErrorSwal("Miniatura no válida", errores);
}

function publicacionEditarRechazarImagenes(inputImagenes, alertImagenes, previewImagenes, errores) {
  publicacionMostrarAlertaImagenes(alertImagenes, errores.join(" "));
  inputImagenes.value = "";
  if (previewImagenes) {
    previewImagenes.innerHTML = "";
  }
}

function publicacionEditarValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes) {
  if (!inputImagenes?.files?.length) {
    publicacionOcultarAlertaImagenes(alertImagenes);
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivosImagen(
    inputImagenes.files,
    inputImagenes,
    MENSAJE_LIMITE_IMAGEN_EDITAR,
  );
  if (!resultado.valido) {
    publicacionEditarRechazarImagenes(inputImagenes, alertImagenes, previewImagenes, resultado.errores);
    return resultado;
  }
  publicacionOcultarAlertaImagenes(alertImagenes);
  return resultado;
}

function publicacionEditarValidarBloqueVideo(inputVideo, previewVideo) {
  if (!inputVideo?.files?.length) {
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivoUnico(
    inputVideo.files[0],
    inputVideo,
    MENSAJE_LIMITE_VIDEO_EDITAR,
  );
  if (!resultado.valido) {
    publicacionEditarRechazarVideo(inputVideo, previewVideo, resultado.errores);
    return resultado;
  }
  return resultado;
}

function publicacionEditarValidarBloqueThumbnail(inputThumbnail, previewThumbnail) {
  if (!inputThumbnail?.files?.length) {
    return { valido: true, errores: [] };
  }
  const resultado = publicacionValidarArchivoUnico(
    inputThumbnail.files[0],
    inputThumbnail,
    MENSAJE_LIMITE_THUMBNAIL_EDITAR,
  );
  if (!resultado.valido) {
    publicacionEditarRechazarThumbnail(inputThumbnail, previewThumbnail, resultado.errores);
    return resultado;
  }
  return resultado;
}

function publicacionEditarRecolectarErrores(bloques) {
  return bloques.flatMap((bloque) => (bloque.valido ? [] : bloque.errores));
}

function publicacionEditarRenderPreviewImagenes(archivos, contenedor) {
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
}

function publicacionEditarRenderPreviewVideo(archivo, contenedor) {
  contenedor.innerHTML = "";
  if (!archivo) {
    return;
  }
  const url = URL.createObjectURL(archivo);
  const video = document.createElement("video");
  video.src = url;
  video.controls = true;
  video.style.cssText =
    "width:100%;max-height:200px;border-radius:8px;border:2px solid #198754;";
  contenedor.appendChild(video);
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("editPublicacionForm");
  if (!form) {
    return;
  }

  const inputImagenes = document.getElementById("inputImagenes");
  const inputVideo = document.getElementById("inputVideo");
  const inputThumbnail = document.getElementById("inputThumbnail");
  const previewImagenes = document.getElementById("previewImagenes");
  const previewVideo = document.getElementById("previewVideo");
  const previewThumbnail = document.getElementById("previewThumbnail");
  const alertImagenes = document.getElementById("alertImagenes");
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
      publicacionEditarValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes),
      publicacionEditarValidarBloqueVideo(inputVideo, previewVideo),
      publicacionEditarValidarBloqueThumbnail(inputThumbnail, previewThumbnail),
    ];
    const errores = publicacionEditarRecolectarErrores(bloques);
    return { valido: errores.length === 0, errores };
  }

  if (inputImagenes) {
    inputImagenes.addEventListener("change", () => {
      const bloque = publicacionEditarValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes);
      if (!bloque.valido) {
        return;
      }
      publicacionEditarRenderPreviewImagenes(inputImagenes.files, previewImagenes);
    });
  }

  if (inputVideo) {
    inputVideo.addEventListener("change", () => {
      const bloque = publicacionEditarValidarBloqueVideo(inputVideo, previewVideo);
      if (!bloque.valido) {
        return;
      }
      publicacionEditarRenderPreviewVideo(inputVideo.files[0], previewVideo);
    });
  }

  if (inputThumbnail) {
    inputThumbnail.addEventListener("change", () => {
      const bloque = publicacionEditarValidarBloqueThumbnail(inputThumbnail, previewThumbnail);
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
      title: "¿Guardar cambios?",
      text: "Se actualizará la información de la publicación.",
      confirmText: "Sí, guardar",
    }).then((resultado) => {
      if (resultado.isConfirmed) {
        form.submit();
      }
    });
  });
});
