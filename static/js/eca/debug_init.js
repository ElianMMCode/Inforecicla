document.addEventListener("DOMContentLoaded", function () {
  // Código para ejecutar una vez cargado el DOM
});

// Forzar inicialización Select2 SOBRE MODAL cada vez que se abre
var modal = document.getElementById("modalCrearEvento");
if (modal) {
  modal.addEventListener("shown.bs.modal", function () {
    if (window.inicializarSelect2Centros) {
      setTimeout(window.inicializarSelect2Centros, 50);
    }
  });
}
