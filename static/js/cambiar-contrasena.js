// Script para el cambio de contraseña en la configuración del Punto ECA

// Función global para cambiar contraseña
function cambiarContrasena() {
    console.log('🔘 Botón presionado - cambiarContrasena() ejecutado');

    const actual = document.getElementById('contrasenaActual');
    const nueva = document.getElementById('contrasenaNueva');
    const confirmar = document.getElementById('confirmarContrasena');

    console.log('📋 Elementos:', { actual: !!actual, nueva: !!nueva, confirmar: !!confirmar });

    if (!actual || !nueva || !confirmar) {
        console.error('❌ Elementos no encontrados');
        alert('Error: No se encontraron los campos');
        return false;
    }

    const a = actual.value.trim();
    const n = nueva.value;
    const c = confirmar.value;

    console.log('📝 Valores:', { a: !!a, n: !!n, c: !!c });

    // Validar requisitos de la contraseña
    const m1 = /[a-z]/.test(n);
    const m2 = /[A-Z]/.test(n);
    const m3 = /\d/.test(n);
    const m4 = /[@$!%*?&]/.test(n);
    const m5 = n.length >= 8;

    // Validar que no estén vacíos
    if (!a || !n || !c) {
        alert('⚠️ Todos los campos son obligatorios');
        return false;
    }

    // Validar que coincidan
    if (n !== c) {
        alert('⚠️ Las contraseñas nuevas no coinciden');
        return false;
    }

    // Validar requisitos
    if (!m1) {
        alert('⚠️ La contraseña debe contener al menos una letra minúscula');
        return false;
    }
    if (!m2) {
        alert('⚠️ La contraseña debe contener al menos una letra mayúscula');
        return false;
    }
    if (!m3) {
        alert('⚠️ La contraseña debe contener al menos un número');
        return false;
    }
    if (!m4) {
        alert('⚠️ La contraseña debe contener al menos un carácter especial (@$!%*?&)');
        return false;
    }
    if (!m5) {
        alert('⚠️ La contraseña debe tener mínimo 8 caracteres');
        return false;
    }

    console.log('✅ Validación correcta, enviando...');

    const formData = new FormData();
    formData.append('contrasenaActual', a);
    formData.append('contrasenaNueva', n);
    formData.append('confirmarContrasena', c);

    console.log('📤 Enviando fetch a /punto-eca/cambiar-contrasena');

    fetch('/punto-eca/cambiar-contrasena', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('📨 Respuesta recibida:', response.status, response.redirected);
        if (response.redirected) {
            console.log('🔄 Redirigiendo a:', response.url);
            window.location.href = response.url;
        } else {
            alert('Error al cambiar la contraseña');
        }
    })
    .catch(error => {
        console.error('❌ Error en fetch:', error);
        alert('Error: ' + error);
    });

    return false;
}

// Validación en tiempo real para los campos
document.addEventListener('input', function(e) {
    if (e.target && e.target.id === 'contrasenaNueva') {
        const n = e.target.value;
        const reqMin = document.getElementById('reqMinusculas');
        const reqMay = document.getElementById('reqMayusculas');
        const reqNum = document.getElementById('reqNumeros');
        const reqEsp = document.getElementById('reqEspeciales');
        const reqLen = document.getElementById('reqLongitud');

        const m1 = /[a-z]/.test(n);
        const m2 = /[A-Z]/.test(n);
        const m3 = /\d/.test(n);
        const m4 = /[@$!%*?&]/.test(n);
        const m5 = n.length >= 8;

        if (reqMin) reqMin.innerHTML = m1 ? '✅ <span class="text-success">Mínimo una letra minúscula</span>' : '❌ <span class="text-danger">Mínimo una letra minúscula</span>';
        if (reqMay) reqMay.innerHTML = m2 ? '✅ <span class="text-success">Mínimo una letra mayúscula</span>' : '❌ <span class="text-danger">Mínimo una letra mayúscula</span>';
        if (reqNum) reqNum.innerHTML = m3 ? '✅ <span class="text-success">Mínimo un número</span>' : '❌ <span class="text-danger">Mínimo un número</span>';
        if (reqEsp) reqEsp.innerHTML = m4 ? '✅ <span class="text-success">Mínimo un carácter especial</span>' : '❌ <span class="text-danger">Mínimo un carácter especial</span>';
        if (reqLen) reqLen.innerHTML = m5 ? '✅ <span class="text-success">Mínimo 8 caracteres</span>' : `❌ <span class="text-danger">Mínimo 8 caracteres (${n.length}/8)</span>`;
    }

    if (e.target && (e.target.id === 'contrasenaNueva' || e.target.id === 'confirmarContrasena')) {
        const nueva = document.getElementById('contrasenaNueva');
        const confirmar = document.getElementById('confirmarContrasena');
        const msgCoincidencia = document.getElementById('mensajeCoincidencia');

        if (nueva && confirmar && msgCoincidencia) {
            if (nueva.value && confirmar.value) {
                if (nueva.value === confirmar.value) {
                    confirmar.classList.remove('is-invalid');
                    confirmar.classList.add('is-valid');
                    msgCoincidencia.innerHTML = '<span class="text-success">✓ Coinciden</span>';
                } else {
                    confirmar.classList.remove('is-valid');
                    confirmar.classList.add('is-invalid');
                    msgCoincidencia.innerHTML = '<span class="text-danger">✗ No coinciden</span>';
                }
            } else {
                confirmar.classList.remove('is-valid', 'is-invalid');
                msgCoincidencia.textContent = '';
            }
        }
    }
});

console.log('✅ Script de cambio de contraseña cargado');

