document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("createPublicacionForm");
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
  const wrapperThumbnail = document.getElementById("wrapperThumbnail");

  const camposValidacion = publicacionObtenerCamposValidacion(form, [
    "titulo", "contenido", "categoria_id", "estado",
  ]);
  publicacionInicializarControlesBasicos(
    form,
    form.querySelector('[name="titulo"]'),
    form.querySelector('[name="contenido"]'),
  );

  function validarArchivos() {
    return publicacionEjecutarValidaciones([
      publicacionValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes),
      publicacionValidarBloqueVideo(inputVideo, previewVideo, wrapperThumbnail),
      publicacionValidarBloqueThumbnail(inputThumbnail, previewThumbnail),
    ]);
  }

  if (inputImagenes) {
    inputImagenes.addEventListener("change", () => {
      const bloque = publicacionValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes);
      if (!bloque.valido) {
        return;
      }
      publicacionRenderPreviewImagenes(
        inputImagenes.files,
        previewImagenes,
        PUBLICACION_LIMITE_IMAGEN_MB * PUBLICACION_BYTES_POR_MB,
      );
    });
  }

  if (inputVideo) {
    inputVideo.addEventListener("change", () => {
      const bloque = publicacionValidarBloqueVideo(inputVideo, previewVideo, wrapperThumbnail);
      if (!bloque.valido) {
        return;
      }
      publicacionRenderPreviewVideo(inputVideo.files[0], previewVideo, wrapperThumbnail);
    });
  }

  if (inputThumbnail) {
    inputThumbnail.addEventListener("change", () => {
      const bloque = publicacionValidarBloqueThumbnail(inputThumbnail, previewThumbnail);
      if (!bloque.valido) {
        return;
      }
      publicacionRenderPreviewThumbnail(inputThumbnail.files[0], previewThumbnail);
    });
  }

  publicacionManejarEnvioFormulario(form, {
    title: "¿Crear publicación?",
    text: "El formulario está completo y listo para enviarse.",
    confirmText: "Sí, crear",
    validadorArchivos: validarArchivos,
  }, camposValidacion);
});
