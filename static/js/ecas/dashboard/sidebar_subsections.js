// 1. Extraemos la lógica de scroll y apertura a una función independiente
function hacerScrollASeccion(anchor) {
  const section = document.querySelector(anchor);
  if (!section) return;

  // Condición positiva primero
  if (section.classList.contains("show")) {
    section.scrollIntoView({ behavior: "smooth", block: "center" });
  } else {
    // Caso negativo: si está cerrado, primero lo abrimos
    const header = document.querySelector(`[data-bs-target="${anchor}"]`);
    if (header) header.click();

    setTimeout(() => {
      section.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 420);
  }
}

// 2. Extraemos el manejador del clic para evitar anidar tanto código
function manejarClickSidebar(e) {
  // ¡Aquí está la corrección de .dataset! (SonarQube S7761)
  const anchor = this.dataset.anchor;
  const urlBase = this.getAttribute("href").split("#")[0];

  if (
    globalThis.location.pathname === urlBase ||
    globalThis.location.pathname === `${urlBase}/`
  ) {
    e.preventDefault();

    setTimeout(() => {
      hacerScrollASeccion(anchor);
    }, 60);
  }
}

// 3. El listener principal queda súper limpio (Nivel de anidamiento bajó de 5 a 2)
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".sidebar-subsection-link").forEach((link) => {
    link.addEventListener("click", manejarClickSidebar);
  });
});
