// Lee config desde window.App:
const CSRF = document.querySelector('meta[name="csrf-token"]')?.content;
const App = window.App || {};

document.addEventListener('DOMContentLoaded', () => {
  if (!App.permisos?.calendario) {
    console.warn('Sin permiso para ver calendario');
    return;
  }

  // Ejemplo fetch con CSRF
  fetch(App.rutas.cargar, {
    method: 'GET',
    headers: { 'X-CSRF-TOKEN': CSRF, 'Accept': 'application/json' }
  })
    .then(r => r.json())
    .then(data => {
      // renderiza calendario...
    })
    .catch(console.error);

  // Guardar:
  async function guardarEvento(payload) {
    const r = await fetch(App.rutas.guardar, {
      method: 'POST',
      headers: {
        'X-CSRF-TOKEN': CSRF,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    if (!r.ok) throw new Error('Error guardando');
    return r.json();
  }
});
