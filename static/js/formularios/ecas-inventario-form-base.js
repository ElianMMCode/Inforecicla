const SWAL_CONFIRM_COLOR = '#198754';
const INVALID_PENDING_TITLE = 'Campos obligatorios pendientes';
const INVALID_PENDING_TEXT = 'Por favor completa todos los campos requeridos del inventario.';

export function createInventarioFormController({
    formId,
    submitButtonId,
    stockInputId,
    capacityInputId,
    crossFieldMessage,
    fieldMessages,
    buildPayload,
    submit,
}) {
    const fieldIds = Object.keys(fieldMessages);

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
        const stockInput = form.querySelector(`#${stockInputId}`);
        const capacityInput = form.querySelector(`#${capacityInputId}`);
        if (!(stockInput instanceof HTMLInputElement) || !(capacityInput instanceof HTMLInputElement)) {
            return true;
        }
        const stock = Number.parseFloat(stockInput.value);
        const capacity = Number.parseFloat(capacityInput.value);
        if (Number.isFinite(stock) && Number.isFinite(capacity) && stock > capacity) {
            setCrossFieldError(stockInput, crossFieldMessage);
            return false;
        }
        setCrossFieldError(stockInput, '');
        return true;
    }

    function attachCrossFieldLiveValidation(form) {
        const stockInput = form.querySelector(`#${stockInputId}`);
        const capacityInput = form.querySelector(`#${capacityInputId}`);
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
        fieldIds.forEach((fieldId) => {
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
                feedback.textContent = fieldMessages[fieldId];
                if (inputGroup) {
                    inputGroup.appendChild(feedback);
                } else {
                    input.after(feedback);
                }
            }
        });
    }

    function setSubmittingState(form, isSubmitting) {
        const submitBtn = form.querySelector(`#${submitButtonId}`);
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

    function attachResetCleanup(form) {
        form.addEventListener('reset', () => {
            form.classList.remove('was-validated');
            const stockInput = form.querySelector(`#${stockInputId}`);
            if (stockInput instanceof HTMLInputElement) {
                setCrossFieldError(stockInput, '');
            }
        });
    }

    async function handleSubmit(event) {
        const form = event.currentTarget;
        event.preventDefault();
        event.stopPropagation();

        validateCrossField(form);

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            await showSwal('warning', INVALID_PENDING_TITLE, INVALID_PENDING_TEXT);
            return;
        }

        form.classList.add('was-validated');
        const payload = buildPayload(form);
        await submit(form, payload, { setSubmittingState, showSwal, getCsrfToken });
    }

    function init() {
        const form = document.getElementById(formId);
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        ensureFieldMessages(form);
        attachInvalidCapture(form);
        attachCrossFieldLiveValidation(form);
        attachResetCleanup(form);
        form.addEventListener('submit', handleSubmit);
    }

    return { init };
}
