// Script para el cambio de contraseña en la configuración del Punto ECA

const PASSWORD_RULES = [
    {
        test: (value) => /[a-z]/.test(value),
        validLabel: 'Mínimo una letra minúscula',
        invalidLabel: 'Mínimo una letra minúscula',
    },
    {
        test: (value) => /[A-Z]/.test(value),
        validLabel: 'Mínimo una letra mayúscula',
        invalidLabel: 'Mínimo una letra mayúscula',
    },
    {
        test: (value) => /\d/.test(value),
        validLabel: 'Mínimo un número',
        invalidLabel: 'Mínimo un número',
    },
    {
        test: (value) => /[@$!%*?&_]/.test(value),
        validLabel: 'Mínimo un carácter especial',
        invalidLabel: 'Mínimo un carácter especial',
    },
    {
        test: (value) => value.length >= 8,
        validLabel: 'Mínimo 8 caracteres',
        invalidLabel: (value) => `Mínimo 8 caracteres (${value.length}/8)`,
    },
];

function getPasswordFields() {
    const actual = document.getElementById('contrasenaActual');
    const nueva = document.getElementById('contrasenaNueva');
    const confirmar = document.getElementById('confirmarContrasena');

    if (!actual || !nueva || !confirmar) {
        console.error('❌ Elementos no encontrados');
        if (globalThis.Swal?.fire) {
            globalThis.Swal.fire({ icon: 'error', title: 'Error', text: 'No se encontraron los campos' });
        } else {
            alert('Error: No se encontraron los campos');
        }
        return null;
    }

    return { actual, nueva, confirmar };
}

function getPasswordValueState(fields) {
    return {
        actual: fields.actual.value.trim(),
        nueva: fields.nueva.value,
        confirmar: fields.confirmar.value,
    };
}

function getPasswordValidationMessage(values) {
    if (!values.actual || !values.nueva || !values.confirmar) {
        return '⚠️ Todos los campos son obligatorios';
    }

    if (values.nueva !== values.confirmar) {
        return '⚠️ Las contraseñas nuevas no coinciden';
    }

    const invalidRule = PASSWORD_RULES.find((rule) => !rule.test(values.nueva));
    if (invalidRule) {
        if (typeof invalidRule.invalidLabel === 'function') {
            return `⚠️ La contraseña debe tener ${invalidRule.invalidLabel(values.nueva)}`;
        }

        return `⚠️ La contraseña debe contener ${invalidRule.invalidLabel}`;
    }

    return null;
}

function updateRequirement(element, isValid, validLabel, invalidLabel) {
    if (!element) {
        return;
    }

    let label = validLabel;

    if (!isValid) {
        label = invalidLabel;
    }

    const prefix = isValid ? '✅' : '❌';
    const tone = isValid ? 'text-success' : 'text-danger';

    element.innerHTML = `${prefix} <span class="${tone}">${label}</span>`;
}

function updatePasswordRequirements(password) {
    const requirementElements = [
        document.getElementById('reqMinusculas'),
        document.getElementById('reqMayusculas'),
        document.getElementById('reqNumeros'),
        document.getElementById('reqEspeciales'),
        document.getElementById('reqLongitud'),
    ];

    PASSWORD_RULES.forEach((rule, index) => {
        const element = requirementElements[index];
        const isValid = rule.test(password);
        const invalidLabel = typeof rule.invalidLabel === 'function' ? rule.invalidLabel(password) : rule.invalidLabel;

        updateRequirement(element, isValid, rule.validLabel, invalidLabel);
    });
}

function updatePasswordMatchState() {
    const nueva = document.getElementById('contrasenaNueva');
    const confirmar = document.getElementById('confirmarContrasena');
    const msgCoincidencia = document.getElementById('mensajeCoincidencia');

    if (!nueva?.value || !confirmar?.value || !msgCoincidencia) {
        if (confirmar) {
            confirmar.classList.remove('is-valid', 'is-invalid');
        }
        if (msgCoincidencia) {
            msgCoincidencia.textContent = '';
        }
        return;
    }

    const passwordsMatch = nueva.value === confirmar.value;
    confirmar.classList.toggle('is-valid', passwordsMatch);
    confirmar.classList.toggle('is-invalid', !passwordsMatch);
    msgCoincidencia.innerHTML = passwordsMatch
        ? '<span class="text-success">✓ Coinciden</span>'
        : '<span class="text-danger">✗ No coinciden</span>';
}

async function sendPasswordChange(values) {
    const formData = new FormData();
    formData.append('contrasenaActual', values.actual);
    formData.append('contrasenaNueva', values.nueva);
    formData.append('confirmarContrasena', values.confirmar);

    console.log('📤 Enviando fetch a /punto-eca/cambiar-contrasena');

    try {
        const response = await fetch('/punto-eca/cambiar-contrasena', {
            method: 'POST',
            body: formData,
        });

        console.log('📨 Respuesta recibida:', response.status, response.redirected);

        if (response.redirected) {
            console.log('🔄 Redirigiendo a:', response.url);
            globalThis.location.href = response.url;
            return;
        }

        if (globalThis.Swal?.fire) {
            globalThis.Swal.fire({ icon: 'error', title: 'Error', text: 'Error al cambiar la contraseña' });
        } else {
            alert('Error al cambiar la contraseña');
        }
    } catch (error) {
        console.error('❌ Error en fetch:', error);
        if (globalThis.Swal?.fire) {
            globalThis.Swal.fire({ icon: 'error', title: 'Error', text: String(error) });
        } else {
            alert(`Error: ${error}`);
        }
    }
}

// Función global para cambiar contraseña
function cambiarContrasena() {
    console.log('🔘 Botón presionado - cambiarContrasena() ejecutado');

    const fields = getPasswordFields();
    if (!fields) {
        return;
    }

    console.log('📋 Elementos:', {
        actual: !!fields.actual,
        nueva: !!fields.nueva,
        confirmar: !!fields.confirmar,
    });

    const values = getPasswordValueState(fields);
    console.log('📝 Valores:', { a: !!values.actual, n: !!values.nueva, c: !!values.confirmar });

    const validationMessage = getPasswordValidationMessage(values);
    if (validationMessage) {
        if (globalThis.Swal?.fire) {
            globalThis.Swal.fire({ icon: 'error', title: 'Error', text: validationMessage });
        } else {
            alert(validationMessage);
        }
        return;
    }

    console.log('✅ Validación correcta, enviando...');
    sendPasswordChange(values);
}

function handlePasswordInput(event) {
    const target = event.target;

    if (!(target instanceof HTMLInputElement)) {
        return;
    }

    if (target.id === 'contrasenaNueva') {
        updatePasswordRequirements(target.value);
    }

    if (target.id === 'contrasenaNueva' || target.id === 'confirmarContrasena') {
        updatePasswordMatchState();
    }
}

function initializePasswordChangeModule() {
    document.addEventListener('input', handlePasswordInput);
    console.log('✅ Script de cambio de contraseña cargado');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePasswordChangeModule, { once: true });
} else {
    initializePasswordChangeModule();
}

globalThis.cambiarContrasena = cambiarContrasena;

