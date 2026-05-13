// --- Archivo de JavaScript para Eventos del Calendario (Extraído de HTML) ---

// ==== Esperar a que el DOM esté cargado ==== //
document.addEventListener("DOMContentLoaded", function () {
  // Obtener cookies para CSRF
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (const cookie of cookies) {
        const trimmedCookie = cookie.trim();
        if (trimmedCookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(
            trimmedCookie.substring(name.length + 1),
          );
          break;
        }
      }
    }
    return cookieValue;
  }

  // Botón Guardar Evento
  const btnGuardar = document.getElementById("btnGuardarEvento");
  if (!btnGuardar) {
    alert("No se encontró el botón Guardar Evento");
  } else {
    btnGuardar.addEventListener("click", async function () {
      const data = {
        materialId: document.getElementById("selectMaterial").value,
        centroAcopioId: document.getElementById("selectCentroAcopio").value,
        puntoEcaId: document.getElementById("inputPuntoEcaId").value,
        usuarioId: document.getElementById("inputUsuarioId").value,
        titulo: document.getElementById("inputTitulo").value,
        descripcion: document.getElementById("inputDescripcion").value,
        fechaInicio: document.getElementById("inputFechaInicio").value,
        horaInicio: document.getElementById("inputHoraInicio").value,
        horaFin: document.getElementById("inputHoraFin").value,
        color: document.getElementById("inputColor").value,
        tipoRepeticion: document.getElementById("selectTipoRepeticion").value,
        fechaFinRepeticion: document.getElementById("inputFechaFinRepeticion")
          .value,
        observaciones: document.getElementById("inputObservaciones").value,
      };

      // Validar campos completos
      const faltan = [];
      if (!data.materialId) faltan.push("Material");
      if (!data.puntoEcaId) faltan.push("Punto ECA");
      if (!data.usuarioId) faltan.push("Usuario");
      if (!data.titulo) faltan.push("Título");
      if (!data.fechaInicio) faltan.push("Fecha Inicio");
      if (!data.horaInicio) faltan.push("Hora Inicio");
      if (!data.horaFin) faltan.push("Hora Fin");

      if (faltan.length > 0) {
        document.getElementById("alertErrorText").innerText =
          "Faltan campos obligatorios: " + faltan.join(", ");
        document.getElementById("alertError").classList.remove("d-none");
        console.warn("Datos enviados:", data);
        return;
      }

      // Enviar datos al backend
      try {
        const response = await fetch("/punto-eca/calendario/evento/nuevo/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify(data),
        });
        const result = await response.json();
        if (result.success) {
          document.getElementById("alertError").classList.add("d-none");
          document.getElementById("alertSuccess").classList.remove("d-none");
        } else {
          document.getElementById("alertErrorText").innerText =
            result.error || "Error desconocido al crear el evento";
          document.getElementById("alertError").classList.remove("d-none");
        }
      } catch (error) {
        console.error("Caught error:", error);
        document.getElementById("alertErrorText").innerText =
          "Error de red o servidor";
        document.getElementById("alertError").classList.remove("d-none");
      }
    });
  }
});
