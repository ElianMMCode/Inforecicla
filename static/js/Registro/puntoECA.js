    (function() {
      const geoBtn = document.getElementById('geoBtn');
      const display = document.getElementById('locationDisplay');
      geoBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            () => display.textContent = 'Permiso de ubicación concedido.',
            () => display.textContent = 'No se obtuvo permiso de ubicación.'
          );
        } else {
          display.textContent = 'Geolocalización no soportada.';
        }
      });

      const form = document.getElementById('puntoForm');
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        form.classList.add('was-validated');
        if (!form.checkValidity()) return;
        alert('Punto ECA registrado con éxito.');
        window.location.href = '../PuntoECA/PerfilECA.html';
      }, false);
    })();