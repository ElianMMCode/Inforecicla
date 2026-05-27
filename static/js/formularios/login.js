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
        // kept for backward compatibility with older templates that used #serverSwal
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

    const showServerSwals = () => {
        const placeholders = Array.from(document.querySelectorAll('.serverSwal'));
        if (placeholders.length === 0) return;

        const swal = globalThis.Swal;
        if (!swal?.fire) {
            placeholders.forEach((el) => {
                console.error('Swal not available, falling back to alert for server message');
                alert(el.dataset.swalText || el.textContent || el.innerText || '');
                el.remove();
            });
            return;
        }

        // Show them sequentially using an async loop to avoid deep nesting
        (async () => {
            for (const el of placeholders) {
                try {
                    // eslint-disable-next-line no-await-in-loop
                    await swal.fire({
                        icon: el.dataset.swalIcon || 'info',
                        title: el.dataset.swalTitle || '',
                        text: el.dataset.swalText || '',
                    });
                } catch (err) {
                    console.error('Error showing Swal:', err);
                }
                el.remove();
            }
        })();
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

    const initPasswordRequirements = () => {
        // Support both registration and recovery modal password inputs
        const pwdSelectors = ['#recoveryPassword', '#password'];
        let pwdInput = null;
        for (const sel of pwdSelectors) {
            pwdInput = document.querySelector(sel);
            if (pwdInput) break;
        }
        if (!pwdInput) return;

        const reqs = {
            lower: document.getElementById('reqMinusculas'),
            upper: document.getElementById('reqMayusculas'),
            num: document.getElementById('reqNumeros'),
            special: document.getElementById('reqEspeciales'),
            len: document.getElementById('reqLongitud'),
        };
        function checkPwd(val) {
            if (!reqs.lower) return;
            const hasLower = /[a-z]/.test(val);
            const hasUpper = /[A-Z]/.test(val);
            const hasNum = /\d/.test(val);
            const hasSpecial = /[@$!%*?&_]/.test(val);
            const longEnough = val.length >= 8;
            reqs.lower.classList.toggle('text-success', hasLower);
            reqs.upper.classList.toggle('text-success', hasUpper);
            reqs.num.classList.toggle('text-success', hasNum);
            reqs.special.classList.toggle('text-success', hasSpecial);
            reqs.len.classList.toggle('text-success', longEnough);
            reqs.lower.innerText = (hasLower ? '✅ ' : '❌ ') + 'Mínimo una letra minúscula (a-z)';
            reqs.upper.innerText = (hasUpper ? '✅ ' : '❌ ') + 'Mínimo una letra mayúscula (A-Z)';
            reqs.num.innerText = (hasNum ? '✅ ' : '❌ ') + 'Mínimo un número (0-9)';
            reqs.special.innerText = (hasSpecial ? '✅ ' : '❌ ') + 'Mínimo un carácter especial (por ejemplo: @ $ ! % * ? & _)';
            reqs.len.innerText = (longEnough ? '✅ ' : '❌ ') + 'Mínimo 8 caracteres';
        }

        pwdInput.addEventListener('input', function (e) { checkPwd(e.target.value); });
        checkPwd(pwdInput.value || '');
    };

    const buildFieldValidationMessages = (form) => {
        const result = { required: [], format: [], other: [] };
        const requiredControls = Array.from(form.querySelectorAll('input[required], textarea[required], select[required]'));
        requiredControls.forEach((control) => {
            const value = (control.value || '').toString().trim();
            if (!value) {
                let labelText = '';
                if (control.id) {
                    const label = form.querySelector(`label[for="${control.id}"]`);
                    if (label) labelText = label.textContent.trim();
                }
                if (!labelText) labelText = control.getAttribute('placeholder') || control.name || 'Campo requerido';
                result.required.push(labelText);
                return;
            }
            if (control.pattern) {
                try {
                    const re = new RegExp(`^(?:${control.pattern})$`);
                    if (!re.test(value)) {
                        result.format.push(`El campo ${control.name || control.id} tiene formato inválido.`);
                    }
                } catch (e) {
                    console.warn('Invalid pattern on control', control, e);
                }
            }
        });

        // additional custom checks for password confirm
        const pwd = form.querySelector('input[name="recovery_password"], input[name="password"]');
        const pwdConfirm = form.querySelector('input[name="recovery_password_confirm"], input[name="passwordConfirm"]');
        if (pwd && pwdConfirm) {
            const v1 = (pwd.value || '').toString();
            const v2 = (pwdConfirm.value || '').toString();
            if (v1 && v2 && v1 !== v2) {
                result.other.push('Las contraseñas no coinciden');
            }
        }

        return result;
    };

    const initRecoveryModalValidation = () => {
        const modal = document.getElementById('recoveryModal');
        if (!modal) return;
        const forms = Array.from(modal.querySelectorAll('form'));
        forms.forEach((form) => attachValidationToForm(form));
    };

    const attachValidationToForm = (form) => {
        const showFormValidationMessages = () => {
            const msgs = buildFieldValidationMessages(form);
            const swal = globalThis.Swal;

            // If there are only required-field issues, use browser/Bootstrap invalid-feedback
            const hasRequiredOnly = msgs.required.length > 0 && msgs.format.length === 0 && msgs.other.length === 0;
            if (hasRequiredOnly) {
                form.classList.add('was-validated');
                // focus first empty required control
                const firstEmpty = Array.from(form.querySelectorAll('input[required], textarea[required], select[required]')).find((c) => !(c.value || '').toString().trim());
                if (firstEmpty && typeof firstEmpty.focus === 'function') {
                    firstEmpty.focus();
                }
                return;
            }

            // For format errors or other errors (password mismatch), show Swal
            const all = [].concat(msgs.other, msgs.format, msgs.required.map((r) => `- ${r}`));
            const text = all.length > 0 ? all.join('\n') : 'Completa los campos requeridos.';
            if (swal?.fire) {
                swal.fire({ icon: 'warning', title: 'Validación', text });
            } else {
                alert(text);
            }
            form.classList.add('was-validated');
        };

        form.addEventListener('submit', (evt) => {
            if (form.checkValidity()) return;
            evt.preventDefault();
            evt.stopPropagation();
            showFormValidationMessages();
        }, true);

        const submitButtons = Array.from(form.querySelectorAll('button[type="submit"], input[type="submit"]'));
        submitButtons.forEach((btn) => {
            btn.addEventListener('click', (ev) => {
                if (form.checkValidity()) return;
                ev.preventDefault();
                ev.stopPropagation();
                showFormValidationMessages();
            }, true);
        });

        form.addEventListener('keydown', (ev) => {
            if (ev.key !== 'Enter') return;
            const target = ev.target;
            if (target?.tagName === 'TEXTAREA') return;
            if (form.checkValidity()) return;
            ev.preventDefault();
            ev.stopPropagation();
            showFormValidationMessages();
        }, true);
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
        showServerSwals();
        showCredentialSwalFromPlaceholder();
        replaceBootstrapCredentialAlertWithSwal();
        initRecoveryModalValidation();
        initPasswordRequirements();
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
})();
