// Script para edición de datos del ciudadano

const EMAIL_REGEX = /^[A-Za-z0-9+_.-]+@(.+)$/;
const PASSWORD_REQUIREMENTS = {
    minuscule: /[a-z]/,
    uppercase: /[A-Z]/,
    number: /\d/,
    special: /[@$!%*?&_]/,
};

function setInvalid(field) {
    field?.classList.add('is-invalid');
}

function clearInvalid(field) {
    field?.classList.remove('is-invalid');
}

function validateEmailField(value) {
    return !value || EMAIL_REGEX.test(value);
}

function validateCelularField(value) {
    return !value || value.length === 10;
}

function validatePasswordRequirements(value) {
    return value.length >= 8
        && PASSWORD_REQUIREMENTS.minuscule.test(value)
        && PASSWORD_REQUIREMENTS.uppercase.test(value)
        && PASSWORD_REQUIREMENTS.number.test(value)
        && PASSWORD_REQUIREMENTS.special.test(value);
}

function validatePasswordMatch(password, confirmation) {
    return !password || !confirmation || password === confirmation;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Script de ciudadano cargado');

    const form = document.querySelector('form[method="post"]');
    if (!form) {
        console.warn('⚠️ Formulario no encontrado');
        return;
    }

    console.log('✅ Formulario encontrado');

    const email = document.querySelector('input[name="email"]');
    const celular = document.querySelector('input[name="celular"]');

    const contrasenaActual = document.querySelector('input[name="contrasenaActual"]');
    const contrasenaNueva = document.querySelector('input[name="contrasenaNueva"]');
    const confirmarContrasena = document.querySelector('input[name="confirmarContrasena"]');
    const btnCancelar = form.querySelector('.btn-outline-secondary');

    if (email) {
        email.addEventListener('blur', function() {
            if (validateEmailField(this.value)) {
                clearInvalid(this);
            } else {
                setInvalid(this);
                console.warn('⚠️ Email inválido:', this.value);
            }
        });
    }

    if (celular) {
        celular.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '').substring(0, 10);
        });

        celular.addEventListener('blur', function() {
            if (validateCelularField(this.value)) {
                clearInvalid(this);
            } else {
                setInvalid(this);
                console.warn('⚠️ Celular debe tener 10 dígitos');
            }
        });
    }

    if (contrasenaNueva && confirmarContrasena) {
        function validarContrasena() {
            const password = contrasenaNueva.value;
            const confirmation = confirmarContrasena.value;

            if (password && confirmation) {
                confirmarContrasena.classList.toggle('is-valid', password === confirmation);
                confirmarContrasena.classList.toggle('is-invalid', password !== confirmation);
            } else {
                confirmarContrasena.classList.remove('is-valid', 'is-invalid');
            }
        }

        contrasenaNueva.addEventListener('input', validarContrasena);
        confirmarContrasena.addEventListener('input', validarContrasena);
    }

    if (btnCancelar) {
        btnCancelar.addEventListener('click', function(e) {
            e.preventDefault();
            globalThis.location.reload();
        });
    }

    function validateFormBeforeSubmit(event) {
        let isValid = true;

        if (validateEmailField(email?.value || '')) {
            clearInvalid(email);
        } else {
            setInvalid(email);
            console.warn('❌ Email inválido');
            isValid = false;
        }

        if (validateCelularField(celular?.value || '')) {
            clearInvalid(celular);
        } else {
            setInvalid(celular);
            console.warn('❌ Celular inválido');
            isValid = false;
        }

        if (contrasenaNueva?.value) {
            if (!contrasenaActual?.value) {
                alert('⚠️ Debes ingresar la contraseña actual para cambiar la contraseña');
                event.preventDefault();
                return false;
            }

            if (!validatePasswordRequirements(contrasenaNueva.value)) {
                alert('⚠️ La contraseña debe contener al menos una minúscula, una mayúscula, un número, un carácter especial y mínimo 8 caracteres');
                event.preventDefault();
                return false;
            }

            if (!validatePasswordMatch(contrasenaNueva.value, confirmarContrasena?.value || '')) {
                alert('⚠️ Las contraseñas no coinciden');
                event.preventDefault();
                return false;
            }
        }

        if (!isValid) {
            event.preventDefault();
            return false;
        }

        console.log('✅ Validación completada, enviando formulario');
        return true;
    }

    form.addEventListener('submit', validateFormBeforeSubmit);
});

console.log('✅ Script de ciudadano inicializado');

