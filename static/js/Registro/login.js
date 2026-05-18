document.addEventListener('DOMContentLoaded', function () {
  const loginForm = document.getElementById('loginForm');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const loginAction = document.getElementById('loginAction');
  const jsErrorContainer = document.getElementById('js-error-container');
  const recoveryModalEl = document.getElementById('recoveryModal');

  if (!loginForm || !emailInput || !passwordInput || !loginAction || !jsErrorContainer) {
    return;
  }

  function showErrors(errors) {
    const items = errors.map(function (error) {
      return '<li>' + error + '</li>';
    }).join('');
    jsErrorContainer.innerHTML = '<div class="alert alert-danger" role="alert"><ul style="margin-bottom: 0;">' + items + '</ul></div>';
  }

  loginForm.addEventListener('submit', function (event) {
    const errors = [];
    const emailValue = emailInput.value.trim();
    const passwordValue = passwordInput.value;
    const actionValue = loginAction.value;

    if (emailValue) {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(emailValue)) {
        errors.push('El correo electrónico no tiene un formato válido.');
      }
    } else {
      errors.push('El correo electrónico es obligatorio.');
    }

    if (actionValue !== 'reenviar' && !passwordValue) {
      errors.push('La contraseña es obligatoria.');
    }

    if (errors.length > 0) {
      event.preventDefault();
      showErrors(errors);

      if (!emailValue) {
        emailInput.focus();
      } else if (actionValue !== 'reenviar' && !passwordValue) {
        passwordInput.focus();
      }
      return;
    }

    if (actionValue === 'reenviar') {
      passwordInput.value = '';
    }
  });

  const currentAction = loginForm.dataset.currentAction || '';
  const recoveryStep = loginForm.dataset.recoveryStep || 'enviar';

  if (recoveryModalEl && (['recuperar_enviar', 'recuperar_validar', 'recuperar_cambiar'].includes(currentAction) || recoveryStep !== 'enviar')) {
    const recoveryModal = new bootstrap.Modal(recoveryModalEl);
    recoveryModal.show();
  }

  document.querySelectorAll('.toggle-password').forEach(function (icon) {
    icon.addEventListener('click', function () {
      const targetSelector = icon.dataset.target;
      const input = document.querySelector(targetSelector);

      if (!input) {
        return;
      }

      if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
      } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
      }
    });
  });
});
