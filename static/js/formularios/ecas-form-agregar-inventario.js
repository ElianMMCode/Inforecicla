const EcAsFormAgregarInventario = (() => {
    const FORM_ID = 'formAgregarInventario';
    const MODAL_ID = 'agregarInventarioModal';
    const SUBMIT_ENDPOINT = '/punto-eca/materiales/inventario/agregar/';
    const SUCCESS_RELOAD_DELAY_MS = 1200;
    const SWAL_CONFIRM_COLOR = '#198754';
    const CROSS_FIELD_MESSAGE = 'El stock inicial no puede superar la capacidad máxima.';

    const FIELD_MESSAGES = {
        stockInicial: 'Ingresa el stock inicial (mayor o igual a 0).',
        capacidadMaxima: 'Ingresa la capacidad máxima (mayor o igual a 0).',
        unidadMedida: 'Selecciona una unidad de medida.',
        precioCompra: 'Ingresa el precio de compra (mayor o igual a 0).',
        precioVenta: 'Ingresa el precio de venta (mayor o igual a 0).',
        umbralAlerta: 'Ingresa el umbral de alerta (entre 0 y 100).',
        umbralCritico: 'Ingresa el umbral crítico (entre 0 y 100).',
    };

    const FIELD_IDS = Object.keys(FIELD_MESSAGES);

    function showSwal(icon, title, text) {
        if (globalThis.Swal?.fire) {
            return globalThis.Swal.fire({
                icon,
                title,
                text,
                confirmButtonColor: SWAL_CONFIRM_COLOR,
                confirmButtonText: 'Entendido',
            });
        }
        if (globalThis.console?.warn) {
            globalThis.console.warn('SweetAlert2 no disponible:', title, text);
        }
        return Promise.resolve({ isConfirmed: true });
    }

    function getCsrfToken() {
        const cookieToken = globalThis.getCSRFToken?.();
        return typeof cookieToken === 'string' ? cookieToken : '';
    }

    function attachInvalidCapture(form) {
        const elements = form.querySelectorAll('input, select, textarea');
        elements.forEach((element) => {
            element.addEventListener('invalid', (event) => {
                event.preventDefault();
            }, true);
        });
    }

    function removeCrossFieldFeedback(input) {
        const wrapper = input.closest('.input-group') || input.parentElement;
        const existing = wrapper?.querySelector('.invalid-feedback.cross-field');
        if (existing) {
            existing.remove();
        }
    }

    function setCrossFieldError(input, message) {
        if (!(input instanceof HTMLInputElement)) {
            return;
        }
        if (message) {
            input.setCustomValidity(message);
            const wrapper = input.closest('.input-group') || input.parentElement;
            if (!wrapper) {
                return;
            }
            let feedback = wrapper.querySelector('.invalid-feedback.cross-field');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback cross-field';
                wrapper.appendChild(feedback);
            }
            feedback.textContent = message;
            return;
        }
        input.setCustomValidity('');
        removeCrossFieldFeedback(input);
    }

    function validateCrossField(form) {
        const stockInput = form.querySelector('#stockInicial');
        const capacityInput = form.querySelector('#capacidadMaxima');
        if (!(stockInput instanceof HTMLInputElement) || !(capacityInput instanceof HTMLInputElement)) {
            return true;
        }
        const stock = Number.parseFloat(stockInput.value);
        const capacity = Number.parseFloat(capacityInput.value);
        if (Number.isFinite(stock) && Number.isFinite(capacity) && stock > capacity) {
            setCrossFieldError(stockInput, CROSS_FIELD_MESSAGE);
            return false;
        }
        setCrossFieldError(stockInput, '');
        return true;
    }

    function attachCrossFieldLiveValidation(form) {
        const stockInput = form.querySelector('#stockInicial');
        const capacityInput = form.querySelector('#capacidadMaxima');
        [stockInput, capacityInput].forEach((input) => {
            if (input instanceof HTMLInputElement) {
                input.addEventListener('input', () => {
                    if (input.validity.customError) {
                        validateCrossField(form);
                    }
                });
            }
        });
    }

    function ensureFieldMessages(form) {
        FIELD_IDS.forEach((fieldId) => {
            const input = form.querySelector(`#${fieldId}`);
            if (!input) {
                return;
            }
            const inputGroup = input.closest('.input-group');
            const wrapper = inputGroup || input.parentElement;
            if (!wrapper) {
                return;
            }
            if (!wrapper.querySelector(`#${fieldId} ~ .invalid-feedback, .invalid-feedback[data-for="${fieldId}"]`)) {
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.dataset.for = fieldId;
                feedback.textContent = FIELD_MESSAGES[fieldId];
                if (inputGroup) {
                    inputGroup.appendChild(feedback);
                } else {
                    input.after(feedback);
                }
            }
        });
    }

    function buildPayload(form) {
        const puntoInput = form.querySelector('#agregarPuntoId');
        const materialInput = form.querySelector('#agregarMaterialId');
        return {
            materialId: materialInput instanceof HTMLInputElement ? materialInput.value : '',
            puntoEcaId: puntoInput instanceof HTMLInputElement ? puntoInput.value : '',
            stockActual: Number.parseFloat(form.querySelector('#stockInicial')?.value) || 0,
            capacidadMaxima: Number.parseFloat(form.querySelector('#capacidadMaxima')?.value) || 0,
            unidadMedida: form.querySelector('#unidadMedida')?.value || '',
            precioCompra: Number.parseFloat(form.querySelector('#precioCompra')?.value) || 0,
            precioVenta: Number.parseFloat(form.querySelector('#precioVenta')?.value) || 0,
            umbralAlerta: Number.parseInt(form.querySelector('#umbralAlerta')?.value, 10) || 0,
            umbralCritico: Number.parseInt(form.querySelector('#umbralCritico')?.value, 10) || 0,
        };
    }

    function setSubmittingState(form, isSubmitting) {
        const submitBtn = form.querySelector('#btnGuardarInventario');
        if (!(submitBtn instanceof HTMLButtonElement)) {
            return null;
        }
        if (isSubmitting) {
            if (!submitBtn.dataset.originalHtml) {
                submitBtn.dataset.originalHtml = submitBtn.innerHTML;
            }
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Guardando...';
        } else {
            submitBtn.disabled = false;
            if (submitBtn.dataset.originalHtml) {
                submitBtn.innerHTML = submitBtn.dataset.originalHtml;
                delete submitBtn.dataset.originalHtml;
            }
        }
        return submitBtn;
    }

    async function submitInventario(form) {
        const csrf = getCsrfToken();
        setSubmittingState(form, true);
        const payload = buildPayload(form);

        try {
            const response = await globalThis.fetch(SUBMIT_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            const data = await response.json().catch(() => null);

            if (response.ok && !data?.error) {
                await showSwal('success', '¡Operación exitosa!', 'El material fue agregado al inventario.');
                form.reset();
                const modalEl = document.getElementById(MODAL_ID);
                const modalInstance = modalEl ? globalThis.bootstrap?.Modal?.getInstance(modalEl) : null;
                if (modalInstance) {
                    modalInstance.hide();
                }
                globalThis.setTimeout(() => globalThis.location.reload(), SUCCESS_RELOAD_DELAY_MS);
                return;
            }

            const errorMessage = data?.mensaje || data?.message || data?.error || 'No fue posible guardar el inventario.';
            await showSwal('error', 'Error al guardar', errorMessage);
        } catch (error) {
            if (globalThis.console?.error) {
                globalThis.console.error('[AGREGAR-INVENTARIO] Error en fetch:', error);
            }
            await showSwal('error', 'Error', 'No se pudo conectar con el servidor.');
        } finally {
            setSubmittingState(form, false);
        }
    }

    async function handleSubmit(event) {
        const form = event.currentTarget;
        event.preventDefault();
        event.stopPropagation();

        validateCrossField(form);

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            await showSwal(
                'warning',
                'Campos obligatorios pendientes',
                'Por favor completa todos los campos requeridos del inventario.'
            );
            return;
        }

        form.classList.add('was-validated');
        await submitInventario(form);
    }

    function attachResetCleanup(form) {
        form.addEventListener('reset', () => {
            form.classList.remove('was-validated');
            const stockInput = form.querySelector('#stockInicial');
            if (stockInput instanceof HTMLInputElement) {
                setCrossFieldError(stockInput, '');
            }
        });
    }

    function init() {
        const form = document.getElementById(FORM_ID);
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        ensureFieldMessages(form);
        attachInvalidCapture(form);
        attachCrossFieldLiveValidation(form);
        attachResetCleanup(form);
        form.addEventListener('submit', (event) => {
            handleSubmit(event);
        });
    }

    return { init };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        EcAsFormAgregarInventario.init();
    }, { once: true });
} else {
    EcAsFormAgregarInventario.init();
}
