document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createPublicacionForm");
  if (!form) {
    return;
  }

  const LIMITE_BYTES = 6 * 1024 * 1024;
  const inputImagenes = document.getElementById("inputImagenes");
  const inputVideo = document.getElementById("inputVideo");
  const inputThumbnail = document.getElementById("inputThumbnail");
  const previewImagenes = document.getElementById("previewImagenes");
  const previewVideo = document.getElementById("previewVideo");
  const previewThumbnail = document.getElementById("previewThumbnail");
  const alertImagenes = document.getElementById("alertImagenes");
  const wrapperThumbnail = document.getElementById("wrapperThumbnail");
  const camposValidacion = ["titulo", "contenido", "categoria_id", "estado"]
    .map((nombre) => form.querySelector(`[name="${nombre}"]`))
    .filter(Boolean);

  publicacionSuprimirValidacionNativa(form);

  function validarTamanoImagenes() {
    if (!inputImagenes) {
      return true;
    }
    const resultado = publicacionValidarTamanoArchivos(
      inputImagenes.files,
      LIMITE_BYTES,
      "Las siguientes imágenes superan 6 MB y no se pueden subir",
    );
    if (!resultado.valido) {
      publicacionMostrarAlertaImagenes(alertImagenes, resultado.mensaje);
      inputImagenes.value = "";
      if (previewImagenes) {
        previewImagenes.innerHTML = "";
      }
      return false;
    }
    if (alertImagenes) {
      alertImagenes.classList.add("d-none");
      alertImagenes.textContent = "";
    }
    return true;
  }

  if (inputImagenes) {
    inputImagenes.addEventListener("change", () => {
      if (validarTamanoImagenes()) {
        publicacionRenderPreviewImagenes(inputImagenes.files, previewImagenes, LIMITE_BYTES);
      }
    });
  }

  if (inputVideo) {
    inputVideo.addEventListener("change", () => {
      publicacionRenderPreviewVideo(
        inputVideo.files && inputVideo.files[0],
        previewVideo,
        wrapperThumbnail,
      );
    });
  }

  if (inputThumbnail) {
    inputThumbnail.addEventListener("change", () => {
      publicacionRenderPreviewThumbnail(
        inputThumbnail.files && inputThumbnail.files[0],
        previewThumbnail,
      );
    });
  }

  publicacionBindEnvio({
    formulario: form,
    camposValidacion,
    confirmar: {
      title: "¿Crear publicación?",
      text: "El formulario está completo y listo para enviarse.",
      confirmText: "Sí, crear",
    },
    antesDeEnviar: validarTamanoImagenes,
  });
});
