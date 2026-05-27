(() => {
    const initLoginForm = () => {
        const loginForm = document.getElementById('loginForm');
        const resendActivationButton = document.getElementById('resendActivationButton');
        const loginActionInput = document.getElementById('loginAction');

        if (!loginForm) {
            return;
        }

        loginForm.addEventListener('submit', (event) => {
            if (loginForm.checkValidity()) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();
            loginForm.classList.add('was-validated');

            const swal = globalThis.Swal;
            if (swal && typeof swal.fire === 'function') {
                swal.fire({
                    icon: 'error',
                    title: 'Campos incompletos',
                    text: 'Completa los campos obligatorios antes de continuar.',
                });
            }
        });

        if (resendActivationButton && loginActionInput) {
            resendActivationButton.addEventListener('click', () => {
                loginActionInput.value = 'reenviar';
                loginForm.submit();
            });
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLoginForm, { once: true });
    } else {
        initLoginForm();
    }
})();
