function sincronizarValidacionCampo(campo) {
  if (!campo) return;
  campo.setCustomValidity(campo.checkValidity() ? "" : "invalido");
  actualizarEstadoCampo(campo);
}

function toggleDocSection(esAdmin, esGestor) {
  let sec = document.getElementById("sec-documento");
  if (!sec) return;
  sec.classList.toggle("visible", esAdmin || esGestor);
  let td = document.getElementById("createUserTipoDocumento");
  let nd = document.getElementById("createUserNumeroDocumento");
  if (td) td.required = esAdmin;
  if (nd) nd.required = esAdmin;
  if (!esAdmin) {
    if (td) { td.value = ""; td.classList.remove("is-valid", "is-invalid"); }
    if (nd) { nd.value = ""; nd.classList.remove("is-valid", "is-invalid"); }
  }
}

function toggleUbiSection(esAdmin, esGestor) {
  let sec = document.getElementById("sec-ubicacion");
  if (sec) sec.classList.toggle("visible", esAdmin || esGestor);
  let wc = document.getElementById("wrapper-ciudad");
  if (wc) wc.style.display = esGestor ? "none" : "";
  let loc = document.getElementById("createUserLocalidad");
  if (loc) {
    loc.required = esAdmin || esGestor;
    if (!loc.required) { loc.value = ""; loc.classList.remove("is-valid", "is-invalid"); }
  }
  let wm = document.getElementById("wrapper-mapa");
  if (wm) wm.style.display = esGestor ? "block" : "none";
}

function toggleSections(tipo) {
  let esAdmin = tipo === "ADM";
  let esGestor = tipo === "GECA";
  let ln = document.getElementById("label-nombres");
  let la = document.getElementById("label-apellidos");
  if (ln) ln.textContent = esGestor ? "Institución / Punto ECA" : "Nombres";
  if (la) la.textContent = esGestor ? "Nombre del gestor responsable" : "Apellidos";
  toggleDocSection(esAdmin, esGestor);
  toggleUbiSection(esAdmin, esGestor);
  let sf = document.getElementById("sec-fecha");
  if (sf) sf.classList.toggle("visible", esAdmin);
}

let mapa = null;
let marcador = null;

function initMapaGECA() {
  let contenedor = document.getElementById("mapa-crear-usuario");
  let wrapper = document.getElementById("wrapper-mapa");
  if (!contenedor || wrapper.style.display === "none") return;
  if (mapa) {
    mapa.invalidateSize();
    return;
  }
  if (typeof L === "undefined") return;
  mapa = L.map("mapa-crear-usuario").setView([4.711, -74.0721], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(mapa);
  let latInput = document.getElementById("latitud");
  let lngInput = document.getElementById("longitud");
  let latInicial = latInput?.value ? Number.parseFloat(latInput.value) : Number.NaN;
  let lngInicial = lngInput?.value ? Number.parseFloat(lngInput.value) : Number.NaN;
  if (!Number.isNaN(latInicial) && !Number.isNaN(lngInicial)) {
    marcador = L.marker([latInicial, lngInicial]).addTo(mapa);
    mapa.setView([latInicial, lngInicial], 14);
  }
  mapa.on("click", function (e) {
    if (marcador) mapa.removeLayer(marcador);
    marcador = L.marker([e.latlng.lat, e.latlng.lng]).addTo(mapa);
    if (latInput) latInput.value = e.latlng.lat.toFixed(4);
    if (lngInput) lngInput.value = e.latlng.lng.toFixed(4);
  });
}

document.addEventListener("DOMContentLoaded", function () {
  let form = document.getElementById("createUserForm");
  if (!form) return;

  initPasswordVisibilityToggle();

  let tipoUsuario = document.getElementById("createUserTipoUsuario");
  if (tipoUsuario) {
    toggleSections(tipoUsuario.value);
    tipoUsuario.addEventListener("change", function () {
      toggleSections(this.value);
      if (this.value === "GECA") {
        setTimeout(initMapaGECA, 100);
      }
    });
  }

  let fechaNacimientoInput = form.querySelector('[name="fechaNacimiento"]');
  let nombresInput = form.querySelector('[name="nombres"]');
  let apellidosInput = form.querySelector('[name="apellidos"]');
  let emailInput = form.querySelector('[name="email"]');
  let celularInput = form.querySelector('[name="celular"]');
  let tipoDocumentoInput = form.querySelector('[name="tipoDocumento"]');
  let localidadInput = form.querySelector('[name="localidad"]');
  let numeroDocumentoInput = form.querySelector('[name="numeroDocumento"]');
  let passwordInput = form.querySelector('[name="password"]');
  let passwordConfirmInput = form.querySelector('[name="passwordConfirm"]');
  let mensajeCoincidencia = document.getElementById("mensajeCoincidencia");
  let passwordRequirementsBox = document.getElementById(
    "passwordRequirementsBox",
  );
  let camposObligatorios = Array.from(form.querySelectorAll("[required]"));
  let camposValidacionRapida = [
    nombresInput,
    apellidosInput,
    emailInput,
    celularInput,
    tipoDocumentoInput,
    localidadInput,
    numeroDocumentoInput,
    fechaNacimientoInput,
    passwordInput,
    passwordConfirmInput,
  ].filter(Boolean);

  function actualizarEstadoCajaContrasena(cumpleTodo) {
    if (!passwordRequirementsBox) return;
    passwordRequirementsBox.classList.remove(
      "alert-light",
      "alert-success",
      "border-success",
      "bg-success",
      "bg-opacity-10",
    );
    if (cumpleTodo) {
      passwordRequirementsBox.classList.add(
        "alert-success",
        "border-success",
        "bg-success",
        "bg-opacity-10",
      );
    } else {
      passwordRequirementsBox.classList.add("alert-light", "border");
    }
  }

  function ejecutarValidacionesCrearUsuario() {
    validarTexto(
      nombresInput,
      3,
      30,
      null,
      "El nombre debe tener al menos 3 caracteres.",
      "El nombre no puede superar 30 caracteres.",
    );
    validarTexto(
      apellidosInput,
      3,
      40,
      null,
      "Los apellidos deben tener al menos 3 caracteres.",
      "Los apellidos no pueden superar 40 caracteres.",
    );
    validarEmail(emailInput);
    if (passwordInput && passwordConfirmInput) {
      let cumpleTodo = contrasenaCumpleReglas(passwordInput.value);
      passwordInput.setCustomValidity(
        cumpleTodo ? "" : "La contraseña no cumple los requisitos.",
      );
      actualizarEstadoCajaContrasena(cumpleTodo);
    }
    validarNormalizarFechaNacimiento(fechaNacimientoInput, 18);
    validarCelular(celularInput);
    if (numeroDocumentoInput?.closest(".usuario-section")?.classList.contains("visible")) {
      validarNumeroDocumento(numeroDocumentoInput);
    }
    if (localidadInput?.closest(".usuario-section")?.classList.contains("visible")) {
      validarLocalidad(localidadInput, "Selecciona una localidad.");
    }
    camposObligatorios.forEach(function (c) {
      actualizarEstadoCampo(c);
    });
    if (passwordInput) actualizarEstadoCampo(passwordInput);
    if (passwordConfirmInput) actualizarEstadoCampo(passwordConfirmInput);
  }

  form.addEventListener(
    "invalid",
    function (e) {
      e.preventDefault();
      e.target.classList.add("is-invalid");
    },
    true,
  );

  camposObligatorios.forEach(function (campo) {
    let eventName = campo.tagName === "SELECT" ? "change" : "input";
    campo.addEventListener(eventName, function () {
      if (campo === nombresInput) {
        validarTexto(
          nombresInput,
          3,
          30,
          null,
          "El nombre debe tener al menos 3 caracteres.",
          "El nombre no puede superar 30 caracteres.",
        );
        return;
      }
      if (campo === apellidosInput) {
        validarTexto(
          apellidosInput,
          3,
          40,
          null,
          "Los apellidos deben tener al menos 3 caracteres.",
          "Los apellidos no pueden superar 40 caracteres.",
        );
        return;
      }
      if (campo === emailInput) {
        validarEmail(emailInput);
        return;
      }
      if (campo === fechaNacimientoInput) {
        validarNormalizarFechaNacimiento(fechaNacimientoInput, 18);
        return;
      }
      if (campo === celularInput) {
        validarCelular(celularInput);
        return;
      }
      if (campo === numeroDocumentoInput) {
        validarNumeroDocumento(numeroDocumentoInput);
        return;
      }
      if (campo === localidadInput) {
        validarLocalidad(localidadInput, "Selecciona una localidad.");
        return;
      }
      sincronizarValidacionCampo(campo);
    });
    campo.addEventListener("blur", function () {
      actualizarEstadoCampo(campo);
    });
  });

  bindPasswordRealtime(
    passwordInput,
    passwordConfirmInput,
    mensajeCoincidencia,
  );
  camposObligatorios.forEach(function (c) {
    if (c.value) actualizarEstadoCampo(c);
  });

  bindSubmitUsuario({
    formulario: form,
    camposValidacion: camposValidacionRapida,
    confirmar: {
      title: "¿Crear usuario?",
      text: "El formulario está completo y listo para enviarse.",
      confirmText: "Sí, crear",
    },
    antesDeEnviar: ejecutarValidacionesCrearUsuario,
  });
});
