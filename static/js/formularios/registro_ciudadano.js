// static/js/formularios/registro_ciudadano.js
// Módulo ES6 para `form-registro-ciudadano` - validación desacoplada y UX con Bootstrap 5 + SweetAlert2

document.addEventListener('DOMContentLoaded', () => {
  const FORM_ID = 'form-registro-ciudadano';
  const form = document.getElementById(FORM_ID);
  if (!form) return;

  const passwordRules = {
    lower: document.getElementById('reqMinusculas'),
    upper: document.getElementById('reqMayusculas'),
    num: document.getElementById('reqNumeros'),
    special: document.getElementById('reqEspeciales'),
    len: document.getElementById('reqLongitud'),
  };

  const passwordPattern = {
    lower: /[a-z]/,
    upper: /[A-Z]/,
    num: /\d/,
    special: /[@$!%*?&_]/,
    len: /^.{8,}$/,
  };

  const passwordRuleEntries = [
    ['lower', 'Mínimo una letra minúscula (a-z)'],
    ['upper', 'Mínimo una letra mayúscula (A-Z)'],
    ['num', 'Mínimo un número (0-9)'],
    ['special', 'Mínimo un carácter especial (@$!%*?&_)'],
    ['len', 'Mínimo 8 caracteres'],
  ];

  // Bloquear tooltips nativos del navegador (capture phase)
  form.addEventListener('invalid', (ev) => {
    ev.preventDefault();
  }, true);

  // Helper: SweetAlert2 modal
  const showMissingFieldsModal = () => {
    if (typeof Swal !== 'undefined' && Swal.fire) {
      Swal.fire({
        icon: 'warning',
        title: 'Campos obligatorios incompletos',
        text: 'Por favor completa los campos obligatorios del formulario.',
        confirmButtonColor: '#198754',
        confirmButtonText: 'Entendido',
      });
    }
  };

  const getFieldFeedback = (control) => {
    const container = control.closest('.form-group, .form-check');
    return container ? container.querySelector('.invalid-feedback') : null;
  };

  const setControlState = (control, isValid) => {
    if (control) {
      control.classList.toggle('is-valid', isValid);
      control.classList.toggle('is-invalid', !isValid);

      const feedback = getFieldFeedback(control);
      if (feedback) {
        feedback.style.display = isValid ? 'none' : 'block';
      }
    }
  };

  const updatePasswordRule = (ruleKey, isValid) => {
    const ruleElement = passwordRules[ruleKey];
    if (!ruleElement) return;

    const [/* unused */, label] = passwordRuleEntries.find(([key]) => key === ruleKey) || [];
    ruleElement.classList.toggle('text-success', isValid);
    ruleElement.classList.toggle('text-danger', !isValid);
    ruleElement.innerText = `${isValid ? '✅' : '❌'} ${label}`;
  };

  // Validaciones extra: password complex requirements and match
  const validatePasswordConstraints = () => {
    const pwd = form.querySelector('#password');
    const pwdConfirm = form.querySelector('#passwordConfirm');
    if (pwd && pwdConfirm) {
      const value = pwd.value || '';
      const valueConfirm = pwdConfirm.value || '';
      const hasLower = passwordPattern.lower.test(value);
      const hasUpper = passwordPattern.upper.test(value);
      const hasNum = passwordPattern.num.test(value);
      const hasSpecial = passwordPattern.special.test(value);
      const longEnough = passwordPattern.len.test(value);

      updatePasswordRule('lower', hasLower);
      updatePasswordRule('upper', hasUpper);
      updatePasswordRule('num', hasNum);
      updatePasswordRule('special', hasSpecial);
      updatePasswordRule('len', longEnough);

      const passwordOk = hasLower && hasUpper && hasNum && hasSpecial && longEnough;
      pwd.setCustomValidity(passwordOk ? '' : 'La contraseña no cumple los requisitos de seguridad.');

      if (valueConfirm) {
        pwdConfirm.setCustomValidity(value === valueConfirm ? '' : 'Las contraseñas no coinciden.');
      } else {
        pwdConfirm.setCustomValidity('');
      }

      return passwordOk && pwdConfirm.checkValidity();
    }

    return true;
  };

  const validateField = (control) => {
    if (control) {
      if (control.id === 'password' || control.id === 'passwordConfirm') {
        const result = validatePasswordConstraints();
        const password = form.querySelector('#password');
        const passwordConfirm = form.querySelector('#passwordConfirm');
        setControlState(password, password?.checkValidity());
        setControlState(passwordConfirm, passwordConfirm?.checkValidity());
        return result;
      }

      const valid = control.checkValidity();
      setControlState(control, valid);
      return valid;
    }

    return true;
  };

  const syncFormState = () => {
    const controls = Array.from(form.querySelectorAll('input, select, textarea')).filter((control) => typeof control.checkValidity === 'function');
    controls.forEach((control) => validateField(control));
    return controls.every((control) => control.checkValidity());
  };

  // Submit interceptor
  form.addEventListener('submit', (event) => {
    // Ejecutar validaciones adicionales
    const valid = syncFormState();

    if (valid) {
      return true;
    }

    event.preventDefault();
    event.stopPropagation();

    // focus al primer campo inválido
    const elements = Array.from(form.elements).filter((el) => typeof el.checkValidity === 'function');
    const firstInvalid = elements.find((el) => el.checkValidity() === false);
    if (firstInvalid && typeof firstInvalid.focus === 'function') {
      firstInvalid.focus();
    }

    showMissingFieldsModal();
    return false;
  }, { passive: false });

  // Limpiar mensajes personalizados on input
  const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
  inputs.forEach((el) => {
    el.addEventListener('input', () => {
      el.setCustomValidity('');
      validateField(el);
    });

    el.addEventListener('blur', () => {
      validateField(el);
    });
  });

  // Estado inicial de la ayuda de contraseña; el feedback se mantiene oculto hasta validar
  validatePasswordConstraints();
});
