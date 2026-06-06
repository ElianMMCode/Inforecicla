document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createPublicacionForm");
  if (!form) {
    return;
  }

  const LIMITE_BYTES = 6 * 1024 * 1024;
  const LIMITE_VIDEO_BYTES = 100 * 1024 * 1024;
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
    let errores = [];

    if (inputImagenes && inputImagenes.files && inputImagenes.files.length > 0) {
      const resultado = publicacionValidarArchivosImagen(
        inputImagenes.files,
        inputImagenes,
        "La imagen supera el límite de 6 MB",
      );
      if (!resultado.valido) {
        errores = errores.concat(resultado.errores);
        publicacionMostrarAlertaImagenes(alertImagenes, resultado.errores.join(" "));
        inputImagenes.value = "";
        previewImagenes.innerHTML = "";
      } else {
        publicacionOcultarAlertaImagenes(alertImagenes);
      }
    } else {
      publicacionOcultarAlertaImagenes(alertImagenes);
    }

    if (inputVideo && inputVideo.files && inputVideo.files.length > 0) {
      const resultado = publicacionValidarArchivoUnico(
        inputVideo.files[0],
        inputVideo,
        "El video supera el límite de 100 MB",
      );
      if (!resultado.valido) {
        errores = errores.concat(resultado.errores);
        inputVideo.value = "";
        if (previewVideo) {
          previewVideo.innerHTML = "";
        }
        if (wrapperThumbnail) {
          wrapperThumbnail.style.display = "none";
        }
      }
    }

    if (inputThumbnail && inputThumbnail.files && inputThumbnail.files.length > 0) {
      const resultado = publicacionValidarArchivoUnico(
        inputThumbnail.files[0],
        inputThumbnail,
        "La miniatura supera el límite de 6 MB",
      );
      if (!resultado.valido) {
        errores = errores.concat(resultado.errores);
        inputThumbnail.value = "";
        if (previewThumbnail) {
          previewThumbnail.innerHTML = "";
        }
      }
    }

    return { valido: errores.length === 0, errores };
  }

  if (inputImagenes) {
    inputImagenes.addEventListener("change", () => {
      const archivosValidos = (inputImagenes.files || []).length === 0 ||
        publicacionValidarArchivosImagen(
          inputImagenes.files,
          inputImagenes,
          "La imagen supera el límite de 6 MB",
        ).valido;
      if (!archivosValidos) {
        const res = publicacionValidarArchivosImagen(
          inputImagenes.files,
          inputImagenes,
          "La imagen supera el límite de 6 MB",
        );
        publicacionMostrarAlertaImagenes(alertImagenes, res.errores.join(" "));
        inputImagenes.value = "";
        previewImagenes.innerHTML = "";
        return;
      }
      publicacionOcultarAlertaImagenes(alertImagenes);
      publicacionRenderPreviewImagenes(
        inputImagenes.files,
        previewImagenes,
        LIMITE_BYTES,
      );
    });
  }

  if (inputVideo) {
    inputVideo.addEventListener("change", () => {
      const archivo = inputVideo.files && inputVideo.files[0];
      if (archivo) {
        const res = publicacionValidarArchivoUnico(
          archivo,
          inputVideo,
          "El video supera el límite de 100 MB",
        );
        if (!res.valido) {
          inputVideo.value = "";
          if (previewVideo) {
            previewVideo.innerHTML = "";
          }
          if (wrapperThumbnail) {
            wrapperThumbnail.style.display = "none";
          }
          if (typeof Swal !== "undefined") {
            Swal.fire({
              icon: "error",
              title: "Video no válido",
              text: res.errores.join(" "),
              confirmButtonColor: "#198754",
            });
          }
          return;
        }
      }
      publicacionRenderPreviewVideo(archivo, previewVideo, wrapperThumbnail);
    });
  }

  if (inputThumbnail) {
    inputThumbnail.addEventListener("change", () => {
      const archivo = inputThumbnail.files && inputThumbnail.files[0];
      if (archivo) {
        const res = publicacionValidarArchivoUnico(
          archivo,
          inputThumbnail,
          "La miniatura supera el límite de 6 MB",
        );
        if (!res.valido) {
          inputThumbnail.value = "";
          if (previewThumbnail) {
            previewThumbnail.innerHTML = "";
          }
          if (typeof Swal !== "undefined") {
            Swal.fire({
              icon: "error",
              title: "Miniatura no válida",
              text: res.errores.join(" "),
              confirmButtonColor: "#198754",
            });
          }
          return;
        }
      }
      publicacionRenderPreviewThumbnail(archivo, previewThumbnail);
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
