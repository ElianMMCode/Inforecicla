// --- Archivo de JavaScript para Eventos del Calendario (Refactorizado) ---

document.addEventListener("DOMContentLoaded", function () {
  // Helper para obtener cookies (simplificado con .startsWith)
  function getCookie(name) {
    if (!document.cookie) return null;
    for (const cookie of document.cookie.split(";")) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + "=")) {
        return decodeURIComponent(trimmed.substring(name.length + 1));
      }
    }
    return null;
  }

  // Helpers de DOM para evitar repetir document.getElementById
  const getVal = (id) => document.getElementById(id)?.value || "";
  const alertError = document.getElementById("alertError");
  const alertErrorText = document.getElementById("alertErrorText");
  const alertSuccess = document.getElementById("alertSuccess");

  // Helpers para manejo de alertas
  function mostrarError(msg, debugData = null) {
    if (alertErrorText && alertError) {
      alertErrorText.innerText = msg;
      alertError.classList.remove("d-none");
    }
    if (debugData) console.warn("Datos enviados:", debugData);
  }

  function mostrarExito() {
    if (alertError) alertError.classList.add("d-none");
    if (alertSuccess) alertSuccess.classList.remove("d-none");
  }

  // Inicio de lógica principal
  const btnGuardar = document.getElementById("btnGuardarEvento");
  if (!btnGuardar) {
    console.warn("No se encontró el botón Guardar Evento");
    return;
  }

  btnGuardar.addEventListener("click", async function () {
    // 1. Extracción de datos súper limpia
    const data = {
      materialId: getVal("selectMaterial"),
      centroAcopioId: getVal("selectCentroAcopio"),
      puntoEcaId: getVal("inputPuntoEcaId"),
      usuarioId: getVal("inputUsuarioId"),
      titulo: getVal("inputTitulo"),
      descripcion: getVal("inputDescripcion"),
      fechaInicio: getVal("inputFechaInicio"),
      horaInicio: getVal("inputHoraInicio"),
      horaFin: getVal("inputHoraFin"),
      color: getVal("inputColor"),
      tipoRepeticion: getVal("selectTipoRepeticion"),
      fechaFinRepeticion: getVal("inputFechaFinRepeticion"),
      observaciones: getVal("inputObservaciones"),
    };

    // 2. Validación dinámica y automatizada
    const requeridos = {
      materialId: "Material",
      puntoEcaId: "Punto ECA",
      usuarioId: "Usuario",
      titulo: "Título",
      fechaInicio: "Fecha Inicio",
      horaInicio: "Hora Inicio",
      horaFin: "Hora Fin",
    };

    const faltan = Object.keys(requeridos)
      .filter((key) => !data[key])
      .map((key) => requeridos[key]);

    if (faltan.length > 0) {
      mostrarError("Faltan campos obligatorios: " + faltan.join(", "), data);
      return;
    }

    // 3. Envío al backend
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
        mostrarExito();
      } else {
        mostrarError(result.error || "Error desconocido al crear el evento");
      }
    } catch (error) {
      console.error("Caught error:", error);
      mostrarError("Error de red o servidor");
    }
  });
});
