// Script para edición de datos del ciudadano

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Script de ciudadano cargado');

    // Obtener el formulario y elementos
    const form = document.querySelector('form[method="post"]');
    const btnGuardar = form ? form.querySelector('button[type="submit"]') : null;
    const btnCancelar = form ? form.querySelector('.btn-outline-secondary') : null;

    if (!form) {
        console.warn('⚠️ Formulario no encontrado');
        return;
    }

    console.log('✅ Formulario encontrado');

    // Campos de información personal
    const nombres = document.querySelector('input[name="nombres"]');
    const apellidos = document.querySelector('input[name="apellidos"]');
    const email = document.querySelector('input[name="email"]');
    const ciudad = document.querySelector('input[name="ciudad"]');
    const celular = document.querySelector('input[name="celular"]');
    const fechaNacimiento = document.querySelector('input[name="fechaNacimiento"]');

    // Campos de contraseña
    const contrasenaActual = document.querySelector('input[name="contrasenaActual"]');
    const contrasenaNueva = document.querySelector('input[name="contrasenaNueva"]');
    const confirmarContrasena = document.querySelector('input[name="confirmarContrasena"]');

    // Validar email en tiempo real
    if (email) {
        email.addEventListener('blur', function() {
            const emailRegex = /^[A-Za-z0-9+_.-]+@(.+)$/;
            if (this.value && !emailRegex.test(this.value)) {
                this.classList.add('is-invalid');
                console.warn('⚠️ Email inválido:', this.value);
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }

    // Validar celular en tiempo real (10 dígitos)
    if (celular) {
        celular.addEventListener('input', function() {
            // Solo permitir números
            this.value = this.value.replace(/\D/g, '').substring(0, 10);
        });

        celular.addEventListener('blur', function() {
            if (this.value && this.value.length !== 10) {
                this.classList.add('is-invalid');
                console.warn('⚠️ Celular debe tener 10 dígitos');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }

    // Validación de contraseña
    if (contrasenaNueva && confirmarContrasena) {
        function validarContrasena() {
            const n = contrasenaNueva.value;
            const c = confirmarContrasena.value;

            // Validar requisitos
            const m1 = /[a-z]/.test(n);
            const m2 = /[A-Z]/.test(n);
            const m3 = /\d/.test(n);
            const m4 = /[@$!%*?&]/.test(n);
            const m5 = n.length >= 8;

            // Validar coincidencia
            if (n && c) {
                if (n === c) {
                    confirmarContrasena.classList.remove('is-invalid');
                    confirmarContrasena.classList.add('is-valid');
                } else {
                    confirmarContrasena.classList.remove('is-valid');
                    confirmarContrasena.classList.add('is-invalid');
                }
            } else {
                confirmarContrasena.classList.remove('is-valid', 'is-invalid');
            }
        }

        contrasenaNueva.addEventListener('input', validarContrasena);
        confirmarContrasena.addEventListener('input', validarContrasena);
    }

    // Botón cancelar
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.reload();
        });
    }

    // Validación antes de enviar formulario
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;

            // Validar email si tiene valor
            if (email && email.value) {
                const emailRegex = /^[A-Za-z0-9+_.-]+@(.+)$/;
                if (!emailRegex.test(email.value)) {
                    email.classList.add('is-invalid');
                    console.warn('❌ Email inválido');
                    isValid = false;
                }
            }

            // Validar celular si tiene valor
            if (celular && celular.value) {
                if (celular.value.length !== 10) {
                    celular.classList.add('is-invalid');
                    console.warn('❌ Celular inválido');
                    isValid = false;
                }
            }

            // Validar contraseña nueva si se proporciona
            if (contrasenaNueva && contrasenaNueva.value) {
                const n = contrasenaNueva.value;

                if (!contrasenaActual || !contrasenaActual.value) {
                    alert('⚠️ Debes ingresar la contraseña actual para cambiar la contraseña');
                    e.preventDefault();
                    return false;
                }

                // Validar requisitos
                const m1 = /[a-z]/.test(n);
                const m2 = /[A-Z]/.test(n);
                const m3 = /\d/.test(n);
                const m4 = /[@$!%*?&]/.test(n);
                const m5 = n.length >= 8;

                if (!m1) {
                    alert('⚠️ La contraseña debe contener al menos una letra minúscula');
                    e.preventDefault();
                    return false;
                }
                if (!m2) {
                    alert('⚠️ La contraseña debe contener al menos una letra mayúscula');
                    e.preventDefault();
                    return false;
                }
                if (!m3) {
                    alert('⚠️ La contraseña debe contener al menos un número');
                    e.preventDefault();
                    return false;
                }
                if (!m4) {
                    alert('⚠️ La contraseña debe contener al menos un carácter especial (@$!%*?&)');
                    e.preventDefault();
                    return false;
                }
                if (!m5) {
                    alert('⚠️ La contraseña debe tener mínimo 8 caracteres');
                    e.preventDefault();
                    return false;
                }

                // Validar que coincidan
                if (n !== confirmarContrasena.value) {
                    alert('⚠️ Las contraseñas no coinciden');
                    e.preventDefault();
                    return false;
                }
            }

            if (!isValid) {
                e.preventDefault();
                return false;
            }

            console.log('✅ Validación completada, enviando formulario');
        });
    }
});

console.log('✅ Script de ciudadano inicializado');

