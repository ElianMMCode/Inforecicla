(function() {
      const form = document.getElementById('formRegistro');
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        let valid = true;
        const nombre = document.getElementById('nombre');
        if (!nombre.value.trim()) {
          nombre.classList.add('is-invalid'); valid = false;
        } else { nombre.classList.remove('is-invalid'); }
        const email = document.getElementById('email');
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!re.test(email.value)) {
          email.classList.add('is-invalid'); valid = false;
        } else { email.classList.remove('is-invalid'); }
        const pass = document.getElementById('pass');
        if (pass.value.length < 8 || pass.value.length > 20) {
          pass.classList.add('is-invalid'); valid = false;
        } else { pass.classList.remove('is-invalid'); }
        const confirm = document.getElementById('confirmPass');
        if (confirm.value !== pass.value || !confirm.value) {
          confirm.classList.add('is-invalid'); valid = false;
        } else { confirm.classList.remove('is-invalid'); }
        const rol = document.getElementById('rol');
        const roleVal = rol.value;
        if (!roleVal) {
          rol.classList.add('is-invalid'); valid = false;
        } else { rol.classList.remove('is-invalid'); }

        if (!valid) return;

        const key = email.value.toLowerCase();
        const users = JSON.parse(localStorage.getItem('users') || '{}');
        if (users[key]) {
          alert('Este correo ya está registrado.');
          return;
        }
        users[key] = { name: nombre.value, pass: pass.value, role: roleVal };
        localStorage.setItem('users', JSON.stringify(users));

        if (roleVal === 'gestor') {
          alert('Registro exitoso! Completa tu perfil de Gestor ECA.');
          window.location.href = 'puntoECA.html';
        } else {
          alert('Registro exitoso! Inicia sesión.');
          window.location.href = 'inicioSesion.html';
        }
      });
    })();