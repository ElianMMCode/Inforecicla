
    (function() {
      'use strict';
      const form = document.getElementById('loginForm');
      const emailInput = document.getElementById('email');
      const passwordInput = document.getElementById('password');
      const errorDiv = document.getElementById('loginError');
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      const users = {
        'admin@inforecicla.com': 'admin123',
        'ciudadano@inforecicla.com': 'ciudadano123',
        'gestoreca@inforecicla.com': 'gestoreca123'
      };
      const redirectMap = {
        'admin@inforecicla.com': '../Admin/admin.html',
        'ciudadano@inforecicla.com': '../Ciudadano/ciudadano.html',
        'gestoreca@inforecicla.com': '../PuntoECA/GestionInventario.html'
      };

      form.addEventListener('submit', function(event) {
        event.preventDefault();
        errorDiv.style.display = 'none';
        emailInput.classList.remove('is-invalid');

          
        const emailValid = emailRegex.test(emailInput.value);
        if (!emailValid) {
          emailInput.classList.add('is-invalid');
        }

        if (!form.checkValidity() || !emailValid) {
          form.classList.add('was-validated');
          return;
        }

		const email = emailInput.value;
        const password = passwordInput.value;
        if (users[email] && password === users[email]) {
          window.location.href = redirectMap[email];
        } else {
          errorDiv.style.display = 'block';
        }
      }, false);
    })();
