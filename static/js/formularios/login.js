(() => {
    let credentialSwalShown = false;

    const showCredentialSwal = (title, text, icon = 'error') => {
        if (credentialSwalShown) {
            return;
        }

        const swal = globalThis.Swal;
        if (swal?.fire) {
            swal.fire({ icon, title, text });
            credentialSwalShown = true;
        }
    };

    const showCredentialSwalFromPlaceholder = () => {
        const placeholder = document.getElementById('serverSwal');
        if (!placeholder) {
            return;
        }

        showCredentialSwal(
            placeholder.dataset.swalTitle || 'Credenciales inválidas',
            placeholder.dataset.swalText || 'Verifica tu email y contraseña.',
            placeholder.dataset.swalIcon || 'error',
        );

        placeholder.remove();
    };

    const replaceBootstrapCredentialAlertWithSwal = () => {
        const credentialPhrase = 'Credenciales inválidas';
        const alerts = Array.from(document.querySelectorAll('.alert'));
        const matchedAlerts = alerts.filter((alert) => alert.textContent?.includes(credentialPhrase));

        if (matchedAlerts.length === 0) {
            return;
        }

        matchedAlerts.forEach((alert) => alert.remove());
        showCredentialSwal('Credenciales inválidas', 'Verifica tu email y contraseña.', 'error');
    };

    const initPasswordVisibilityToggle = () => {
        const toggleIcons = Array.from(document.querySelectorAll('.toggle-password'));

        toggleIcons.forEach((icon) => {
            icon.addEventListener('click', (event) => {
                event.preventDefault();

                const targetSelector = icon.dataset.target;
                if (!targetSelector) {
                    return;
                }

                const input = document.querySelector(targetSelector);
                if (!input) {
                    return;
                }

                const isPassword = input.type === 'password';
                input.type = isPassword ? 'text' : 'password';
                icon.classList.toggle('bi-eye', !isPassword);
                icon.classList.toggle('bi-eye-slash', isPassword);
            });
        });
    };

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
        });

        const controls = Array.from(loginForm.querySelectorAll('input, textarea, select'));
        controls.forEach((control) => {
            control.addEventListener('invalid', (event) => {
                event.preventDefault();
                event.stopPropagation();
                loginForm.classList.add('was-validated');
            }, true);
        });

        if (resendActivationButton && loginActionInput) {
            resendActivationButton.addEventListener('click', () => {
                loginActionInput.value = 'reenviar';

                if (loginForm.requestSubmit) {
                    loginForm.requestSubmit();
                } else {
                    loginForm.submit();
                }
            });
        }
    };

    const init = () => {
        initLoginForm();
        initPasswordVisibilityToggle();
        showCredentialSwalFromPlaceholder();
        replaceBootstrapCredentialAlertWithSwal();
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
})();
