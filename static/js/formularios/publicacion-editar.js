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

  if (inputImagenes) {
    inputImagenes.addEventListener("change", () => {
      if (inputImagenes.files && inputImagenes.files.length > 0) {
        const res = publicacionValidarArchivosImagen(
          inputImagenes.files,
          inputImagenes,
          "La imagen supera el límite de 6 MB",
        );
        if (!res.valido) {
          publicacionMostrarAlertaImagenes(alertImagenes, res.errores.join(" "));
          inputImagenes.value = "";
          if (previewImagenes) {
            previewImagenes.innerHTML = "";
          }
          return;
        }
        publicacionOcultarAlertaImagenes(alertImagenes);
        Array.from(inputImagenes.files).forEach((archivo) => {
          const reader = new FileReader();
          reader.onload = (evento) => {
            const wrapper = document.createElement("div");
            wrapper.style.cssText = "position:relative;width:80px;height:80px;";
            const img = document.createElement("img");
            img.src = evento.target.result;
            img.style.cssText =
              "width:80px;height:80px;object-fit:cover;border-radius:8px;border:2px solid #198754;";
            wrapper.appendChild(img);
            previewImagenes.appendChild(wrapper);
          };
          reader.readAsDataURL(archivo);
        });
      }
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
      if (previewVideo) {
        previewVideo.innerHTML = "";
        if (archivo) {
          const url = URL.createObjectURL(archivo);
          const video = document.createElement("video");
          video.src = url;
          video.controls = true;
          video.style.cssText =
            "width:100%;max-height:200px;border-radius:8px;border:2px solid #198754;";
          previewVideo.appendChild(video);
        }
      }
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
    let errores = [];

    if (inputImagenes && inputImagenes.files && inputImagenes.files.length > 0) {
      const res = publicacionValidarArchivosImagen(
        inputImagenes.files,
        inputImagenes,
        "La imagen supera el límite de 6 MB",
      );
      if (!res.valido) {
        errores = errores.concat(res.errores);
        inputImagenes.value = "";
        if (previewImagenes) {
          previewImagenes.innerHTML = "";
        }
      }
    }

    if (inputVideo && inputVideo.files && inputVideo.files.length > 0) {
      const res = publicacionValidarArchivoUnico(
        inputVideo.files[0],
        inputVideo,
        "El video supera el límite de 100 MB",
      );
      if (!res.valido) {
        errores = errores.concat(res.errores);
        inputVideo.value = "";
        if (previewVideo) {
          previewVideo.innerHTML = "";
        }
      }
    }

    if (inputThumbnail && inputThumbnail.files && inputThumbnail.files.length > 0) {
      const res = publicacionValidarArchivoUnico(
        inputThumbnail.files[0],
        inputThumbnail,
        "La miniatura supera el límite de 6 MB",
      );
      if (!res.valido) {
        errores = errores.concat(res.errores);
        inputThumbnail.value = "";
        if (previewThumbnail) {
          previewThumbnail.innerHTML = "";
        }
      }
    }

    if (errores.length > 0) {
      evento.preventDefault();
      evento.stopPropagation();
      form.classList.add("was-validated");
      publicacionMostrarErroresSwal(errores);
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
