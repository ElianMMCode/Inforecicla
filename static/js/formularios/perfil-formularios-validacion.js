import { showResultAlert, showValidationAlert } from './formulario-alertas.js';

const PerfilFormulariosValidacionModule = (() => {
    const FORM_IDS = ['formPunto', 'formEncargado'];
    const POINT_FORM_ID = 'formPunto';
    const DIGIT_ONLY_SELECTOR = 'input[data-digits-only]';
    const FILE_LIMITS = {
        logoPunto: {
            maxSizeBytes: 2 * 1024 * 1024,
            label: 'El logo del punto',
            previewId: 'previewLogoPunto',
        },
        fotoPunto: {
            maxSizeBytes: 5 * 1024 * 1024,
            label: 'La foto del punto',
            previewId: 'previewFotoPunto',
        },
    };

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

    function showFormValidationAlert(formId) {
        const formName = formId === 'formPunto' ? 'del punto ECA' : 'del encargado';
        return showValidationAlert(`Revisa los campos ${formName} y corrige los datos marcados.`);
    }

    function getPreviewElement(previewId) {
        const preview = document.getElementById(previewId);
        return preview instanceof HTMLImageElement ? preview : null;
    }

    function resetPreview(preview) {
        if (!preview) {
            return;
        }

        const originalSrc = preview.dataset.originalSrc || preview.getAttribute('src');
        if (originalSrc) {
            preview.src = originalSrc;
        }
    }

    function validateFileSize(input, config) {
        const file = input.files?.[0];
        if (!file) {
            return true;
        }

        if (file.size <= config.maxSizeBytes) {
            return true;
        }

        input.value = '';
        resetPreview(getPreviewElement(config.previewId));
        showResultAlert('warning', 'Archivo demasiado grande', `${config.label} no puede superar ${Math.round(config.maxSizeBytes / (1024 * 1024))} MB.`);
        return false;
    }

    function bindPointFileValidation(form) {
        Object.entries(FILE_LIMITS).forEach(([inputName, config]) => {
            const input = form.querySelector(`input[name="${inputName}"]`);
            if (!(input instanceof HTMLInputElement)) {
                return;
            }

            input.addEventListener('change', () => {
                validateFileSize(input, config);
            });
        });
    }

    async function submitPointForm(form) {
        const response = await globalThis.fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                Accept: 'application/json',
            },
        });

        const payload = await response.json().catch((error) => {
            if (globalThis.console?.debug) {
                globalThis.console.debug('No se pudo leer la respuesta JSON:', error);
            }
            return null;
        });

        if (!response.ok || !payload?.ok) {
            const errorMessage = payload?.message || 'No fue posible actualizar el punto ECA.';
            await showResultAlert('error', 'Error', errorMessage);
            return;
        }

        await showResultAlert('success', 'Punto actualizado', payload.message || 'Punto ECA actualizado correctamente.');
        globalThis.location.href = payload.redirect_url || form.action;
    }

    function bindPointForm(form) {
        bindPointFileValidation(form);

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const digitInputs = form.querySelectorAll(DIGIT_ONLY_SELECTOR);
            digitInputs.forEach((input) => {
                if (input instanceof HTMLInputElement) {
                    sanitizeDigitsInput(input);
                }
            });

            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                showFormValidationAlert(form.id);
                return;
            }

            for (const [inputName, config] of Object.entries(FILE_LIMITS)) {
                const input = form.querySelector(`input[name="${inputName}"]`);
                if (input instanceof HTMLInputElement && !validateFileSize(input, config)) {
                    return;
                }
            }

            form.classList.add('was-validated');

            try {
                await submitPointForm(form);
            } catch (error) {
                if (globalThis.console?.error) {
                    globalThis.console.error('Error al actualizar el punto ECA:', error);
                }
                await showResultAlert('error', 'Error', 'No se pudo conectar con el servidor.');
            }
        });
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

        if (form.id === POINT_FORM_ID) {
            bindPointForm(form);
            return;
        }

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
