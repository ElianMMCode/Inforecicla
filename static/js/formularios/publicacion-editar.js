document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("editPublicacionForm");
  if (!form) {
    return;
  }

  const tituloInput = form.querySelector('[name="titulo"]');
  const contenidoInput = form.querySelector('[name="contenido"]');
  const categoriaInput = form.querySelector('[name="categoria_id"]');
  const estadoInput = form.querySelector('[name="estado"]');
  const camposValidacion = [tituloInput, contenidoInput, categoriaInput, estadoInput].filter(Boolean);

  publicacionSuprimirValidacionNativa(form);

  form.addEventListener("submit", (evento) => {
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
