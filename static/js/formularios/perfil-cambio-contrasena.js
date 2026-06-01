const PerfilCambioContrasenaModule = (() => {
    const FORM_ID = 'formPass';
    const FIELD_IDS = {
        actual: 'passwordActual',
        nueva: 'password',
        confirmar: 'passwordConfirm',
    };

    const RULES = [
        { id: 'reqMinusculas', test: (value) => /[a-z]/.test(value), label: 'Mínimo una letra minúscula (a-z)' },
        { id: 'reqMayusculas', test: (value) => /[A-Z]/.test(value), label: 'Mínimo una letra mayúscula (A-Z)' },
        { id: 'reqNumeros', test: (value) => /\d/.test(value), label: 'Mínimo un número (0-9)' },
        { id: 'reqEspeciales', test: (value) => /[@$!%*?&_]/.test(value), label: 'Mínimo un carácter especial (@$!%*?&_)' },
        { id: 'reqLongitud', test: (value) => value.length >= 8, label: 'Mínimo 8 caracteres' },
    ];

    function getFormElements() {
        const form = document.getElementById(FORM_ID);
        const actual = document.getElementById(FIELD_IDS.actual);
        const nueva = document.getElementById(FIELD_IDS.nueva);
        const confirmar = document.getElementById(FIELD_IDS.confirmar);

        if (!(form instanceof HTMLFormElement) || !(actual instanceof HTMLInputElement) || !(nueva instanceof HTMLInputElement) || !(confirmar instanceof HTMLInputElement)) {
            return null;
        }

        return { form, actual, nueva, confirmar };
    }

    function showValidationAlert() {
        if (globalThis.Swal?.fire) {
            globalThis.Swal.fire({
                icon: 'warning',
                title: 'Campos obligatorios pendientes',
                text: 'Revisa y completa los campos requeridos antes de continuar.',
                confirmButtonText: 'Entendido',
                confirmButtonColor: '#198754',
            });
            return;
        }

        globalThis.alert('Revisa y completa los campos requeridos antes de continuar.');
    }

    function showResultAlert(icon, title, text) {
        if (globalThis.Swal?.fire) {
            return globalThis.Swal.fire({
                icon,
                title,
                text,
                confirmButtonText: 'Entendido',
                confirmButtonColor: '#198754',
            });
        }

        globalThis.alert(text);
        return Promise.resolve();
    }

    function bindNativeValidationSuppression(form) {
        form.addEventListener('invalid', (event) => {
            event.preventDefault();
        }, true);
    }

    function getFeedback(control) {
        const container = control.closest('.col-12, .col-lg-6, .col-md-4, .form-group, .mb-3');
        return container ? container.querySelector('.invalid-feedback') : null;
    }

    function updateControlState(control, isValid) {
        if (!control) {
            return;
        }

        control.classList.toggle('is-valid', isValid);
        control.classList.toggle('is-invalid', !isValid && control.value.length > 0);

        const feedback = getFeedback(control);
        if (feedback) {
            feedback.style.display = isValid || control.value.length === 0 ? 'none' : 'block';
        }
    }

    function updateRequirement(rule, isValid) {
        const element = document.getElementById(rule.id);
        if (!element) {
            return;
        }

        element.classList.toggle('text-success', isValid);
        element.classList.toggle('text-danger', !isValid);
        element.innerText = `${isValid ? '✅' : '❌'} ${rule.label}`;
    }

    function validatePassword(nuevaInput, confirmarInput) {
        const value = nuevaInput.value || '';
        const confirmValue = confirmarInput.value || '';

        RULES.forEach((rule) => {
            updateRequirement(rule, rule.test(value));
        });

        const requirementsOk = RULES.every((rule) => rule.test(value));
        nuevaInput.setCustomValidity(value && !requirementsOk ? 'La contraseña no cumple los requisitos de seguridad.' : '');

        const passwordsMatch = !confirmValue || value === confirmValue;
        confirmarInput.setCustomValidity(confirmValue && !passwordsMatch ? 'Las contraseñas no coinciden.' : '');

        updateControlState(nuevaInput, !value || requirementsOk);
        updateControlState(confirmarInput, !confirmValue || passwordsMatch);

        return requirementsOk && passwordsMatch;
    }

    function bindPasswordVisibilityToggles() {
        document.querySelectorAll('.toggle-password').forEach((toggle) => {
            toggle.addEventListener('click', () => {
                const selector = toggle.dataset.target;
                const input = selector ? document.querySelector(selector) : null;
                if (!(input instanceof HTMLInputElement)) {
                    return;
                }

                const isPassword = input.type === 'password';
                input.type = isPassword ? 'text' : 'password';
                toggle.classList.toggle('bi-eye', !isPassword);
                toggle.classList.toggle('bi-eye-slash', isPassword);
            });
        });
    }

    function bindPasswordSync(form, actualInput, nuevaInput, confirmarInput) {
        const sync = () => {
            validatePassword(nuevaInput, confirmarInput);
            updateControlState(actualInput, actualInput.value.length > 0 ? actualInput.checkValidity() : true);
        };

        actualInput.addEventListener('input', sync);
        nuevaInput.addEventListener('input', sync);
        confirmarInput.addEventListener('input', sync);
        nuevaInput.addEventListener('blur', sync);
        confirmarInput.addEventListener('blur', sync);

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const passwordOk = validatePassword(nuevaInput, confirmarInput);
            const actualOk = actualInput.checkValidity();

            updateControlState(actualInput, actualOk);
            updateControlState(nuevaInput, passwordOk);
            updateControlState(confirmarInput, confirmarInput.checkValidity());

            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                showValidationAlert();
                return;
            }

            form.classList.add('was-validated');

            try {
                const response = await globalThis.fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form),
                    credentials: 'same-origin',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        Accept: 'application/json',
                    },
                });

                const payload = await response.json().catch((error) => {
                    if (globalThis.console?.debug) {
                        globalThis.console.debug('No se pudo leer la respuesta JSON:', error);
                    }
                    return null;
                });

                if (!response.ok || !payload?.ok) {
                    const errorMessage = payload?.message || 'No fue posible actualizar la contraseña.';
                    await showResultAlert('error', 'Error', errorMessage);
                    return;
                }

                form.reset();
                nuevaInput.setCustomValidity('');
                confirmarInput.setCustomValidity('');
                actualInput.setCustomValidity('');
                actualInput.classList.remove('is-valid', 'is-invalid');
                nuevaInput.classList.remove('is-valid', 'is-invalid');
                confirmarInput.classList.remove('is-valid', 'is-invalid');
                validatePassword(nuevaInput, confirmarInput);
                await showResultAlert('success', 'Contraseña actualizada', payload.message || 'Contraseña actualizada correctamente.');
            } catch (error) {
                if (globalThis.console?.error) {
                    globalThis.console.error('Error al actualizar la contraseña:', error);
                }
                await showResultAlert('error', 'Error', 'No se pudo conectar con el servidor.');
            }
        });

        sync();
    }

    function init() {
        const elements = getFormElements();
        if (!elements) {
            return;
        }

        bindNativeValidationSuppression(elements.form);
        bindPasswordVisibilityToggles();
        bindPasswordSync(elements.form, elements.actual, elements.nueva, elements.confirmar);
    }

    return { init };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        PerfilCambioContrasenaModule.init();
    }, { once: true });
} else {
    PerfilCambioContrasenaModule.init();
}
