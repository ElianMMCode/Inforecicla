const PerfilCambioContrasenaModule = (() => {
    const FORM_ID = 'formPass';
    const FIELD_IDS = {
        nueva: 'nuevaPass',
        confirmar: 'confirmarPass',
    };

    function getFormElements() {
        const form = document.getElementById(FORM_ID);
        if (!(form instanceof HTMLFormElement)) {
            return null;
        }

        const nueva = document.getElementById(FIELD_IDS.nueva);
        const confirmar = document.getElementById(FIELD_IDS.confirmar);

        if (!(nueva instanceof HTMLInputElement) || !(confirmar instanceof HTMLInputElement)) {
            return null;
        }

        return { form, nueva, confirmar };
    }

    function setConfirmPasswordValidity(nuevaInput, confirmarInput) {
        const hasConfirmValue = confirmarInput.value.length > 0;
        const isMatch = nuevaInput.value === confirmarInput.value;

        confirmarInput.setCustomValidity(hasConfirmValue && !isMatch ? 'Las contrasenas no coinciden.' : '');
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

    function bindNativeValidationSuppression(form) {
        form.addEventListener('invalid', (event) => {
            event.preventDefault();
        }, true);
    }

    function bindPasswordSync(form, nuevaInput, confirmarInput) {
        const sync = () => {
            setConfirmPasswordValidity(nuevaInput, confirmarInput);
        };

        nuevaInput.addEventListener('input', sync);
        confirmarInput.addEventListener('input', sync);

        form.addEventListener('submit', (event) => {
            setConfirmPasswordValidity(nuevaInput, confirmarInput);

            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add('was-validated');
                showValidationAlert();
                return;
            }

            form.classList.add('was-validated');
        });
    }

    function init() {
        const elements = getFormElements();
        if (!elements) {
            return;
        }

        bindNativeValidationSuppression(elements.form);
        bindPasswordSync(elements.form, elements.nueva, elements.confirmar);
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
