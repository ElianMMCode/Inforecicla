document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("editPublicacionForm");
  if (!form) {
    return;
  }

  const camposValidacion = ["titulo", "contenido", "categoria_id", "estado"]
    .map((nombre) => form.querySelector(`[name="${nombre}"]`))
    .filter(Boolean);

  publicacionSuprimirValidacionNativa(form);

  publicacionBindEnvio({
    formulario: form,
    camposValidacion,
    confirmar: {
      title: "¿Guardar cambios?",
      text: "Se actualizará la información de la publicación.",
      confirmText: "Sí, guardar",
    },
  });
});
