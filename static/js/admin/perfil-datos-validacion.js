import { showResultAlert } from '../formularios/formulario-alertas.js';
import { submitFormJson } from '../formularios/formulario-submit-json.js';

const PerfilDatosValidacionModule = (() => {
    const FORM_ID = 'formDatos';
    const FIELD_IDS = {
        nombres: 'datosNombres',
        apellidos: 'datosApellidos',
        email: 'datosEmail',
        celular: 'datosCelular',
        tipoDocumento: 'datosTipoDocumento',
        numeroDocumento: 'datosNumeroDocumento',
        ciudad: 'datosCiudad',
        localidad: 'datosLocalidad',
        fechaNacimiento: 'datosFechaNac',
    };
    const DIGIT_ONLY_SELECTOR = 'input[data-digits-only]';
    const DOMINIOS_EMAIL_PERMITIDOS = ['.com', '.co', '.edu.co', '.com.co', 'soy.sena.edu.co', 'sena.edu.co'];
    const TIPOS_DOCUMENTO_VALIDOS = new Set(['CC', 'TI', 'CE', 'PA', 'NIT', 'RC', 'PPT', 'SC', 'DIE']);

    function getFormElements() {
        const form = document.getElementById(FORM_ID);
        if (!(form instanceof HTMLFormElement)) {
            return null;
        }

        const fields = {};
        for (const [key, id] of Object.entries(FIELD_IDS)) {
            const element = document.getElementById(id);
            if (element instanceof HTMLInputElement || element instanceof HTMLSelectElement) {
                fields[key] = element;
            }
        }

        return { form, fields };
    }

    function bindNativeValidationSuppression(form) {
        form.addEventListener('invalid', (event) => {
            event.preventDefault();
        }, true);
    }

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

    function updateControlState(control, isValid) {
        if (!control) {
            return;
        }
        const hasValue = control.value.length > 0;
        control.classList.toggle('is-valid', isValid && hasValue);
        control.classList.toggle('is-invalid', !isValid && (hasValue || control.required));
    }

    function escaparHtml(texto) {
        return String(texto).replace(/[&<>"']/g, (caracter) => {
            const mapa = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;',
            };
            return mapa[caracter] || caracter;
        });
    }

    function limitarUnSoloArroba(valor) {
        const texto = String(valor || '');
        const primerArroba = texto.indexOf('@');
        if (primerArroba === -1) {
            return texto;
        }
        return texto.slice(0, primerArroba + 1) + texto.slice(primerArroba + 1).replaceAll('@', '');
    }

    function emailEsValido(email) {
        if (!email) {
            return false;
        }
        if (email.includes(' ')) {
            return false;
        }
        if (email.includes('..')) {
            return false;
        }
        const cantidadArrobas = (email.match(/@/g) || []).length;
        if (cantidadArrobas !== 1) {
            return false;
        }
        const dominio = email.split('@').pop() || '';
        return DOMINIOS_EMAIL_PERMITIDOS.some((sufijo) => dominio.endsWith(sufijo));
    }

    function validarEmail(emailInput) {
        if (!emailInput) {
            return true;
        }
        const normalizado = limitarUnSoloArroba(emailInput.value.trim().toLowerCase());
        if (emailInput.value !== normalizado) {
            emailInput.value = normalizado;
        }
        if (!normalizado) {
            emailInput.setCustomValidity('El correo electrónico es obligatorio.');
            updateControlState(emailInput, false);
            return false;
        }
        const valido = emailEsValido(normalizado);
        emailInput.setCustomValidity(
            valido
                ? ''
                : 'El correo debe tener un solo @, sin espacios, sin puntos consecutivos, y terminar en .com, .co, .edu.co, com.co, soy.sena.edu.co o sena.edu.co.',
        );
        updateControlState(emailInput, valido);
        return valido;
    }

    function validarCelular(celularInput) {
        if (!celularInput) {
            return true;
        }
        sanitizeDigitsInput(celularInput);
        const patron = /^3\d{9}$/;
        const valido = !celularInput.value || patron.test(celularInput.value);
        celularInput.setCustomValidity(valido ? '' : 'El celular debe iniciar con 3 y tener 10 dígitos.');
        updateControlState(celularInput, valido);
        return valido;
    }

    function validarNumeroDocumento(numeroDocumentoInput) {
        if (!numeroDocumentoInput) {
            return true;
        }
        sanitizeDigitsInput(numeroDocumentoInput);
        if (!numeroDocumentoInput.value) {
            numeroDocumentoInput.setCustomValidity('El número de documento es obligatorio.');
            updateControlState(numeroDocumentoInput, false);
            return false;
        }
        const patron = /^\d{6,20}$/;
        const valido = patron.test(numeroDocumentoInput.value);
        numeroDocumentoInput.setCustomValidity(
            valido ? '' : 'El número de documento debe tener entre 6 y 20 dígitos.',
        );
        updateControlState(numeroDocumentoInput, valido);
        return valido;
    }

    function validarTipoDocumento(tipoDocumentoInput) {
        if (!tipoDocumentoInput) {
            return true;
        }
        const valido = TIPOS_DOCUMENTO_VALIDOS.has(tipoDocumentoInput.value);
        tipoDocumentoInput.setCustomValidity(valido ? '' : 'Selecciona un tipo de documento.');
        updateControlState(tipoDocumentoInput, valido);
        return valido;
    }

    function validarFechaNacimiento(fechaInput) {
        if (!fechaInput) {
            return true;
        }
        return validarNormalizarFechaNacimiento(fechaInput, 18);
    }

    function validarFormulario(form, fields) {
        const validaciones = [
            () => validarEmail(fields.email),
            () => validarCelular(fields.celular),
            () => validarNumeroDocumento(fields.numeroDocumento),
            () => validarTipoDocumento(fields.tipoDocumento),
            () => validarFechaNacimiento(fields.fechaNacimiento),
        ];

        let todoValido = true;
        validaciones.forEach((fn) => {
            if (!fn()) {
                todoValido = false;
            }
        });

        Object.values(fields).forEach((field) => {
            if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement) {
                if (field.checkValidity()) {
                    updateControlState(field, true);
                } else {
                    updateControlState(field, false);
                    todoValido = false;
                }
            }
        });

        return todoValido;
    }

    function obtenerErroresFormulario(fields) {
        const errores = [];
        Object.values(fields).forEach((field) => {
            if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement) {
                const msg = field.validationMessage;
                if (msg) {
                    errores.push(msg);
                }
            }
        });
        return [...new Set(errores)];
    }

    function mostrarErroresSwal(errores) {
        if (typeof Swal === 'undefined' || !errores || errores.length === 0) {
            return;
        }
        Swal.fire({
            icon: 'error',
            title: 'Corrige los campos',
            html: `<div class="text-start"><ul class="mb-0 ps-3">${errores
                .map((error) => `<li>${escaparHtml(error)}</li>`)
                .join('')}</ul></div>`,
            confirmButtonColor: '#198754',
        });
    }

    function bindDataForm(form, fields) {
        const digitInputs = form.querySelectorAll(DIGIT_ONLY_SELECTOR);
        digitInputs.forEach((input) => {
            if (input instanceof HTMLInputElement) {
                bindDigitOnlyInput(input);
            }
        });

        const sync = () => {
            digitInputs.forEach((input) => {
                if (input instanceof HTMLInputElement) {
                    sanitizeDigitsInput(input);
                }
            });
        };

        fields.celular?.addEventListener('input', sync);
        fields.celular?.addEventListener('blur', sync);

        const validarCampo = (campo) => {
            if (!campo) {
                return;
            }
            switch (campo) {
                case fields.email:
                    validarEmail(campo);
                    break;
                case fields.celular:
                    validarCelular(campo);
                    break;
                case fields.numeroDocumento:
                    validarNumeroDocumento(campo);
                    break;
                case fields.tipoDocumento:
                    validarTipoDocumento(campo);
                    break;
                case fields.fechaNacimiento:
                    validarFechaNacimiento(campo);
                    break;
                default:
                    updateControlState(campo, campo.checkValidity());
            }
        };

        [fields.email, fields.celular, fields.numeroDocumento, fields.tipoDocumento, fields.fechaNacimiento].forEach((campo) => {
            if (!campo) {
                return;
            }
            const eventName = campo.tagName === 'SELECT' ? 'change' : 'input';
            campo.addEventListener(eventName, () => validarCampo(campo));
            campo.addEventListener('blur', () => {
                if (campo instanceof HTMLInputElement || campo instanceof HTMLSelectElement) {
                    updateControlState(campo, campo.checkValidity());
                }
            });
        });

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            event.stopPropagation();

            sync();

            if (!validarFormulario(form, fields)) {
                form.classList.add('was-validated');
                const errores = obtenerErroresFormulario(fields);
                if (errores.length > 0) {
                    mostrarErroresSwal(errores);
                }
                return;
            }

            form.classList.add('was-validated');

            const confirmacion = await Swal.fire({
                icon: 'question',
                title: '¿Guardar cambios?',
                text: 'Los datos están completos y listos para actualizarse.',
                showCancelButton: true,
                confirmButtonText: 'Sí, guardar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#198754',
                cancelButtonColor: '#6c757d',
            });

            if (!confirmacion.isConfirmed) {
                return;
            }

            try {
                const { response, payload } = await submitFormJson(form);

                if (!response.ok || !payload?.ok) {
                    const errorMessage = payload?.message || 'No fue posible actualizar los datos del perfil.';
                    await showResultAlert('error', 'Error', errorMessage);
                    return;
                }

                await showResultAlert('success', 'Datos actualizados', payload.message || 'Datos actualizados correctamente.');
            } catch (error) {
                if (globalThis.console?.error) {
                    globalThis.console.error('Error al actualizar los datos del perfil:', error);
                }
                await showResultAlert('error', 'Error', 'No se pudo conectar con el servidor.');
            }
        });
    }

    function init() {
        const elements = getFormElements();
        if (!elements) {
            return;
        }

        bindNativeValidationSuppression(elements.form);
        bindDataForm(elements.form, elements.fields);
    }

    return { init };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        PerfilDatosValidacionModule.init();
    }, { once: true });
} else {
    PerfilDatosValidacionModule.init();
}
