const BOGOTA = [4.7110, -74.0721];
const map = L.map('map', { zoomControl: true }).setView(BOGOTA, 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap', maxZoom: 19
}).addTo(map);

const markers = new Map();
const lista = document.getElementById('lista');
const modalEl = document.getElementById('modalPunto');
const modal = (typeof bootstrap !== 'undefined' && bootstrap.Modal) ? new bootstrap.Modal(modalEl) : null;

function abrirModal(p) {
  if (!modal) return;
  document.getElementById('modalTitle').textContent = p.nombre || 'Punto ECA';
  document.getElementById('modalImg').src = p.img || '/images/eca-default.png';
  document.getElementById('modalCategoria').textContent = p.categoria || '—';
  document.getElementById('modalLocalidad').textContent = p.localidad || '—';
  document.getElementById('modalDireccion').textContent = p.direccion || '—';
  document.getElementById('modalHorario').textContent = p.horario || '—';
  document.getElementById('modalCorreo').textContent = p.correo || '—';
  document.getElementById('modalTelefono').textContent = p.telefono || '—';
  const a = document.getElementById('modalWeb'); if (a) { a.textContent = p.web ? 'Visitar sitio' : '—'; a.href = p.web || '#'; }
  modal.show();
}

function renderLista(items) {
  if (!lista) return;
  if (!items.length) { lista.innerHTML = '<div class="text-muted small">No hay puntos para mostrar.</div>'; return; }
  lista.innerHTML = items.map(p => `
    <article class="card card-hover shadow-sm" data-id="${String(p.id)}">
      <div class="card-body">
        <div class="d-flex align-items-start gap-3">
          <img src="${p.img || '/images/eca-default.png'}" width="64" height="64" class="rounded" style="object-fit:cover" alt="">
          <div class="flex-grow-1">
            <div class="d-flex justify-content-between">
              <h6 class="mb-1">${p.nombre ?? 'Punto ECA'}</h6>
              <span class="badge text-bg-light border">${p.localidad ?? '—'}</span>
            </div>
            <div class="small text-muted">${p.direccion ?? ''}</div>
            ${p.horario ? `<div class="small mt-1"><strong>Horarios:</strong> ${p.horario}</div>` : ''}
          </div>
        </div>
      </div>
    </article>
  `).join('');

  lista.querySelectorAll('[data-id]').forEach(card => {
    card.addEventListener('click', () => {
      const id = String(card.dataset.id);
      const p = window.__PUNTOS.find(x => String(x.id) === id);
      if (!p) return;
      if (p.lng != null && p.lat != null) {
        map.setView([p.lat, p.lng], 14, { animate: true });
        const mk = markers.get(String(id)); if (mk) mk.openPopup();
      }
      abrirModal(p);
    });
  });
}

fetch('/puntos.geojson')
  .then(r => r.json())
  .then(geo => {
    const puntos = geo.features.map(f => ({
      id: String(f.properties.id),
      nombre: f.properties.nombre,
      direccion: f.properties.direccion,
      localidad: f.properties.localidad,
      correo: f.properties.correo,
      telefono: f.properties.telefono,
      web: f.properties.web,
      img: f.properties.img,
      horario: f.properties.horario,
      categoria: f.properties.categoria,
      lng: f.geometry.coordinates[0],
      lat: f.geometry.coordinates[1],
    }));
    window.__PUNTOS = puntos;

    // Marcadores
    puntos.forEach(p => {
      const m = L.marker([p.lat, p.lng]).addTo(map);
      m.bindPopup(`<strong>${p.nombre}</strong><br><small>${p.direccion || ''}</small>`);
      m.on('click', () => abrirModal(p));
      markers.set(String(p.id), m);
    });

    renderLista(puntos);
  })
  .catch(err => {
    console.error('Error cargando /puntos.geojson', err);
    renderLista([]);
  });

// Filtro
const filtro = document.getElementById('filtro');
if (filtro) {
  filtro.addEventListener('input', e => {
    const q = (e.target.value || '').toLowerCase().trim();
    const filtered = (window.__PUNTOS || []).filter(p =>
      (p.nombre || '').toLowerCase().includes(q) ||
      (p.localidad || '').toLowerCase().includes(q) ||
      (p.direccion || '').toLowerCase().includes(q)
    );
    renderLista(filtered);
  });
}
