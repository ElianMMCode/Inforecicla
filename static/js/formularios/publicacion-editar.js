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
      publicacionValidarBloqueVideo(inputVideo, previewVideo, null),
      publicacionValidarBloqueThumbnail(inputThumbnail, previewThumbnail),
    ]);
  }

  if (inputImagenes) {
    inputImagenes.addEventListener("change", () => {
      const bloque = publicacionValidarBloqueImagenes(inputImagenes, alertImagenes, previewImagenes);
      if (!bloque.valido) {
        return;
      }
      publicacionAgregarImagenesAPreview(inputImagenes.files, previewImagenes);
    });
  }

  if (inputVideo) {
    inputVideo.addEventListener("change", () => {
      const bloque = publicacionValidarBloqueVideo(inputVideo, previewVideo, null);
      if (!bloque.valido) {
        return;
      }
      publicacionRenderPreviewVideo(inputVideo.files[0], previewVideo, null);
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
    title: "¿Guardar cambios?",
    text: "Se actualizará la información de la publicación.",
    confirmText: "Sí, guardar",
    validadorArchivos: validarArchivos,
  }, camposValidacion);
});
