function sincronizarValidacionCampo(campo) {
  if (!campo) return;
  campo.setCustomValidity(campo.checkValidity() ? "" : "invalido");
  actualizarEstadoCampo(campo);
}

function toggleSections(tipo) {
  var secDoc = document.getElementById('sec-documento');
  var secUbi = document.getElementById('sec-ubicacion');
  var secFecha = document.getElementById('sec-fecha');
  var wrapperMapa = document.getElementById('wrapper-mapa');
  var wrapperCiudad = document.getElementById('wrapper-ciudad');
  var labelNombres = document.getElementById('label-nombres');
  var labelApellidos = document.getElementById('label-apellidos');
  var tipoDoc = document.getElementById('createUserTipoDocumento');
  var numDoc = document.getElementById('createUserNumeroDocumento');
  var localidad = document.getElementById('createUserLocalidad');

  var esAdmin = tipo === 'ADM';
  var esGestor = tipo === 'GECA';
  var esCiudadano = tipo === 'CIU';

  // Labels for Gestor ECA
  if (labelNombres) labelNombres.textContent = esGestor ? 'Institución / Punto ECA' : 'Nombres';
  if (labelApellidos) labelApellidos.textContent = esGestor ? 'Nombre del gestor responsable' : 'Apellidos';

  // Document section
  if (secDoc) {
    secDoc.classList.toggle('visible', esAdmin || esGestor);
    if (tipoDoc) {
      tipoDoc.required = esAdmin;
      if (!esAdmin) tipoDoc.value = '';
    }
    if (numDoc) {
      numDoc.required = esAdmin;
      if (!esAdmin) numDoc.value = '';
    }
  }

  // Location section
  if (secUbi) secUbi.classList.toggle('visible', esAdmin || esGestor);
  if (wrapperCiudad) wrapperCiudad.style.display = esGestor ? 'none' : '';
  if (localidad) localidad.required = esAdmin || esGestor;

  // Map (Gestor ECA only)
  if (wrapperMapa) wrapperMapa.style.display = esGestor ? 'block' : 'none';

  // Birth date (Admin only)
  if (secFecha) secFecha.classList.toggle('visible', esAdmin);

  // Revalidate all visible fields
  document.querySelectorAll('#createUserForm [required]').forEach(function(el) {
    if (el.offsetParent !== null || (el.closest('.usuario-section') && el.closest('.usuario-section').classList.contains('visible'))) {
      sincronizarValidacionCampo(el);
    }
  });
}

var mapa = null;
var marcador = null;

function initMapaGECA() {
  var contenedor = document.getElementById('mapa-crear-usuario');
  var wrapper = document.getElementById('wrapper-mapa');
  if (!contenedor || wrapper.style.display === 'none') return;
  if (mapa) { mapa.invalidateSize(); return; }
  if (typeof L === 'undefined') return;
  mapa = L.map('mapa-crear-usuario').setView([4.711, -74.0721], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(mapa);
  var latInput = document.getElementById('latitud');
  var lngInput = document.getElementById('longitud');
  var latInicial = latInput && latInput.value ? parseFloat(latInput.value) : NaN;
  var lngInicial = lngInput && lngInput.value ? parseFloat(lngInput.value) : NaN;
  if (!isNaN(latInicial) && !isNaN(lngInicial)) {
    marcador = L.marker([latInicial, lngInicial]).addTo(mapa);
    mapa.setView([latInicial, lngInicial], 14);
  }
  mapa.on('click', function(e) {
    if (marcador) mapa.removeLayer(marcador);
    marcador = L.marker([e.latlng.lat, e.latlng.lng]).addTo(mapa);
    if (latInput) latInput.value = e.latlng.lat.toFixed(4);
    if (lngInput) lngInput.value = e.latlng.lng.toFixed(4);
  });
}

document.addEventListener("DOMContentLoaded", function() {
  var form = document.getElementById("createUserForm");
  if (!form) return;

  initPasswordVisibilityToggle();

  var tipoUsuario = document.getElementById("createUserTipoUsuario");
  if (tipoUsuario) {
    toggleSections(tipoUsuario.value);
    tipoUsuario.addEventListener("change", function() {
      toggleSections(this.value);
      if (this.value === 'GECA') {
        setTimeout(initMapaGECA, 100);
      }
    });
  }

  var fechaNacimientoInput = form.querySelector('[name="fechaNacimiento"]');
  var nombresInput = form.querySelector('[name="nombres"]');
  var apellidosInput = form.querySelector('[name="apellidos"]');
  var emailInput = form.querySelector('[name="email"]');
  var celularInput = form.querySelector('[name="celular"]');
  var tipoDocumentoInput = form.querySelector('[name="tipoDocumento"]');
  var localidadInput = form.querySelector('[name="localidad"]');
  var numeroDocumentoInput = form.querySelector('[name="numeroDocumento"]');
  var passwordInput = form.querySelector('[name="password"]');
  var passwordConfirmInput = form.querySelector('[name="passwordConfirm"]');
  var mensajeCoincidencia = document.getElementById("mensajeCoincidencia");
  var passwordRequirementsBox = document.getElementById("passwordRequirementsBox");
  var camposObligatorios = Array.from(form.querySelectorAll("[required]"));
  var camposValidacionRapida = [
    nombresInput, apellidosInput, emailInput, celularInput,
    tipoDocumentoInput, localidadInput, numeroDocumentoInput,
    fechaNacimientoInput, passwordInput, passwordConfirmInput,
  ].filter(Boolean);

  function actualizarEstadoCajaContrasena(cumpleTodo) {
    if (!passwordRequirementsBox) return;
    passwordRequirementsBox.classList.remove("alert-light", "alert-success", "border-success", "bg-success", "bg-opacity-10");
    passwordRequirementsBox.classList.add(cumpleTodo ? "alert-success border-success bg-success bg-opacity-10" : "alert-light border");
  }

  function ejecutarValidacionesCrearUsuario() {
    validarTexto(nombresInput, 3, 30, null, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres.");
    validarTexto(apellidosInput, 3, 40, null, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres.");
    validarEmail(emailInput);
    if (passwordInput && passwordConfirmInput) {
      var cumpleTodo = contrasenaCumpleReglas(passwordInput.value);
      passwordInput.setCustomValidity(cumpleTodo ? "" : "La contraseña no cumple los requisitos.");
      actualizarEstadoCajaContrasena(cumpleTodo);
    }
    validarNormalizarFechaNacimiento(fechaNacimientoInput, 18);
    validarCelular(celularInput);
    if (numeroDocumentoInput && numeroDocumentoInput.closest('.usuario-section').classList.contains('visible')) {
      validarNumeroDocumento(numeroDocumentoInput);
    }
    if (localidadInput && localidadInput.closest('.usuario-section').classList.contains('visible')) {
      validarLocalidad(localidadInput, "Selecciona una localidad.");
    }
    camposObligatorios.forEach(function(c) { actualizarEstadoCampo(c); });
    if (passwordInput) actualizarEstadoCampo(passwordInput);
    if (passwordConfirmInput) actualizarEstadoCampo(passwordConfirmInput);
  }

  form.addEventListener("invalid", function(e) {
    e.preventDefault();
    actualizarEstadoCampo(e.target);
  }, true);

  camposObligatorios.forEach(function(campo) {
    var eventName = campo.tagName === "SELECT" ? "change" : "input";
    campo.addEventListener(eventName, function() {
      if (campo === nombresInput) {
        validarTexto(nombresInput, 3, 30, null, "El nombre debe tener al menos 3 caracteres.", "El nombre no puede superar 30 caracteres.");
        return;
      }
      if (campo === apellidosInput) {
        validarTexto(apellidosInput, 3, 40, null, "Los apellidos deben tener al menos 3 caracteres.", "Los apellidos no pueden superar 40 caracteres.");
        return;
      }
      if (campo === emailInput) { validarEmail(emailInput); return; }
      if (campo === fechaNacimientoInput) { validarNormalizarFechaNacimiento(fechaNacimientoInput, 18); return; }
      if (campo === celularInput) { validarCelular(celularInput); return; }
      if (campo === numeroDocumentoInput) { validarNumeroDocumento(numeroDocumentoInput); return; }
      if (campo === localidadInput) { validarLocalidad(localidadInput, "Selecciona una localidad."); return; }
      sincronizarValidacionCampo(campo);
    });
    campo.addEventListener("blur", function() { actualizarEstadoCampo(campo); });
  });

  bindPasswordRealtime(passwordInput, passwordConfirmInput, mensajeCoincidencia);
  camposObligatorios.forEach(function(c) { actualizarEstadoCampo(c); });

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
