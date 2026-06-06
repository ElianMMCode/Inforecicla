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
  const tituloInput = form.querySelector('[name="titulo"]');
  const contenidoInput = form.querySelector('[name="contenido"]');
  const categoriaInput = form.querySelector('[name="categoria_id"]');
  const estadoInput = form.querySelector('[name="estado"]');
  const camposValidacion = [tituloInput, contenidoInput, categoriaInput, estadoInput].filter(Boolean);

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
      previewImagenes.innerHTML = "";
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
      if (!validarTamanoImagenes()) {
        return;
      }
      publicacionRenderPreviewImagenes(
        inputImagenes.files,
        previewImagenes,
        LIMITE_BYTES,
      );
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

  form.addEventListener("submit", (evento) => {
    if (!validarTamanoImagenes()) {
      evento.preventDefault();
      evento.stopPropagation();
      form.classList.add("was-validated");
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
