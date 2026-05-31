const PerfilFormulariosValidacionModule = (() => {
    const FORM_IDS = ['formPunto', 'formEncargado'];
    const DIGIT_ONLY_SELECTOR = 'input[data-digits-only]';

    function sanitizeDigitsInput(input) {
        const maxLength = Number.parseInt(input.dataset.digitsOnly || input.maxLength || '0', 10);
        const digits = input.value.replace(/\D+/g, '');
        input.value = Number.isFinite(maxLength) && maxLength > 0 ? digits.slice(0, maxLength) : digits;
    }

    function bindDigitOnlyInput(input) {
        const sync = () => sanitizeDigitsInput(input);

        input.addEventListener('input', sync);
        input.addEventListener('blur', sync);
        input.addEventListener('paste', () => {
            globalThis.setTimeout(sync, 0);
        });

        sync();
    }

    function showValidationAlert(formId) {
        const formName = formId === 'formPunto' ? 'del punto ECA' : 'del encargado';

        if (globalThis.Swal?.fire) {
            globalThis.Swal.fire({
                icon: 'warning',
                title: 'Campos obligatorios pendientes',
                text: `Revisa los campos ${formName} y corrige los datos marcados.`,
                confirmButtonText: 'Entendido',
                confirmButtonColor: '#198754',
            });
            return;
        }

        globalThis.alert(`Revisa los campos ${formName} y corrige los datos marcados.`);
    }

    function attachValidation(form) {
        form.addEventListener('invalid', (event) => {
            event.preventDefault();
        }, true);

        const digitInputs = form.querySelectorAll(DIGIT_ONLY_SELECTOR);
        digitInputs.forEach((input) => {
            if (input instanceof HTMLInputElement) {
                bindDigitOnlyInput(input);
            }
        });

        form.addEventListener('submit', (event) => {
            digitInputs.forEach((input) => {
                if (input instanceof HTMLInputElement) {
                    sanitizeDigitsInput(input);
                }
            });

            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add('was-validated');
                showValidationAlert(form.id);
                return;
            }

            form.classList.add('was-validated');
        });
    }

    function init() {
        FORM_IDS.forEach((formId) => {
            const form = document.getElementById(formId);
            if (form instanceof HTMLFormElement) {
                attachValidation(form);
            }
        });
    }

    return { init };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        PerfilFormulariosValidacionModule.init();
    }, { once: true });
} else {
    PerfilFormulariosValidacionModule.init();
}
